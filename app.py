# -*- coding: utf-8 -*-
"""
EMS Gateway — 資料採集 + Web 設定管理 合一執行
  - 資料採集：背景執行緒，依排程讀表並上傳 MQTT
  - Web UI  ：http://localhost:5000  （設定 MQTT / 電表 / Token）
啟動: python app.py
"""
import io
import json
import logging
import os
import ssl
import sqlite3
import re
import subprocess
import threading
import time
from datetime import datetime

import sys

import paho.mqtt.client as mqtt
import schedule
from flask import (Flask, jsonify, redirect, render_template,
                   request, send_file, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from PowerMeter import MeterReader

# ── 日誌 ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Flask ─────────────────────────────────────────────────────────
app = Flask(__name__, template_folder="templates", static_folder="static")

# ── 全域共用讀表器（輪詢 & Web 測試共用，避免 COM port 衝突）────
_reader_lock: threading.Lock = threading.Lock()
_g_reader: MeterReader | None = None

# ── Watchdog（超過 1 小時無採集動作則重啟整個程式）──────────────
WATCHDOG_TIMEOUT   = 3600          # 秒
_watchdog_lock     = threading.Lock()
_last_activity_ts  = time.time()   # 初始值避免啟動時立即觸發

def _touch_activity():
    global _last_activity_ts
    with _watchdog_lock:
        _last_activity_ts = time.time()

def watchdog_loop():
    """每分鐘檢查一次，超過 WATCHDOG_TIMEOUT 秒無採集動作則重啟程式"""
    while True:
        time.sleep(60)
        with _watchdog_lock:
            idle = time.time() - _last_activity_ts
        if idle > WATCHDOG_TIMEOUT:
            logger.warning("Watchdog：已 %.0f 秒無採集動作，重啟程式…", idle)
            os.execv(sys.executable, [sys.executable] + sys.argv)

# ── 輪詢狀態（可被 Web UI 暫停最多 60 秒，到期自動恢復）──────────
PAUSE_MAX_SEC      = 60
_polling_lock      = threading.Lock()
_polling_paused    = False
_polling_resume_at = 0.0  # epoch 秒，到期後自動恢復

def _is_paused() -> bool:
    global _polling_paused
    with _polling_lock:
        if _polling_paused and time.time() >= _polling_resume_at:
            _polling_paused = False
            logger.info("輪詢自動恢復")
        return _polling_paused

# ── 設定檔路徑 ────────────────────────────────────────────────────
CONFIG_DIR  = "config"
MQTT_FILE   = os.path.join(CONFIG_DIR, "mqtt_config.json")
METERS_FILE = os.path.join(CONFIG_DIR, "meters.json")
TOKENS_FILE = os.path.join(CONFIG_DIR, "access_tokens.json")
AUTH_FILE    = os.path.join(CONFIG_DIR, "auth.json")
NETWORK_FILE = os.path.join(CONFIG_DIR, "network.json")
PING_FILE    = os.path.join(CONFIG_DIR, "ping_watchdog.json")


def _get_secret_key() -> bytes:
    key_file = os.path.join(CONFIG_DIR, "secret.key")
    if os.path.exists(key_file):
        with open(key_file, "rb") as f:
            return f.read()
    os.makedirs(CONFIG_DIR, exist_ok=True)
    key = os.urandom(32)
    with open(key_file, "wb") as f:
        f.write(key)
    return key

app.secret_key = _get_secret_key()


def _ensure_auth_file():
    if not os.path.exists(AUTH_FILE):
        _save_cfg(AUTH_FILE, {
            "username":      "admin",
            "password_hash": generate_password_hash("admin"),
        })
        logger.info("已建立預設帳號 admin / admin，請登入後立即修改密碼")


# ── 登入檢查（所有路由，/login /logout /static 除外）─────────────
@app.before_request
def require_login():
    public = {"/login", "/logout"}
    if request.path in public or request.path.startswith("/static/"):
        return None
    if not session.get("logged_in"):
        if request.path.startswith("/api/"):
            return jsonify({"status": "fail", "message": "未登入，請重新整理頁面"}), 401
        return redirect(url_for("login_page"))


def _load_cfg(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def _save_cfg(path: str, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _as_attachment(data, filename: str):
    buf = io.BytesIO(json.dumps(data, ensure_ascii=False, indent=2).encode())
    return send_file(buf, mimetype="application/json",
                     as_attachment=True, download_name=filename)


# ══════════════════════════════════════════════════════════════════
#  SQLite 離線緩衝
# ══════════════════════════════════════════════════════════════════
DB_PATH = "pending_payloads.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pending_payloads (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                ts      INTEGER NOT NULL,
                topic   TEXT    NOT NULL,
                payload TEXT    NOT NULL
            )
        """)
        conn.commit()

def save_to_db(topic: str, payload: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO pending_payloads (ts, topic, payload) VALUES (?, ?, ?)",
            (int(time.time() * 1000), topic, payload),
        )
        conn.commit()
    logger.warning("無法發佈，Payload 已暫存至 SQLite")

def flush_pending(publisher: "MQTTPublisher"):
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT id, topic, payload FROM pending_payloads ORDER BY id ASC"
        ).fetchall()
    if not rows:
        return
    logger.info("通訊恢復，補傳 %d 筆離線暫存資料…", len(rows))
    for row_id, topic, payload in rows:
        ok = publisher.publish(topic, payload)
        if ok:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("DELETE FROM pending_payloads WHERE id = ?", (row_id,))
                conn.commit()
            logger.info("補傳成功，刪除暫存 id=%s", row_id)
        else:
            logger.warning("補傳失敗，保留 id=%s 以後繼續重試", row_id)
            break


# ══════════════════════════════════════════════════════════════════
#  Payload 建構
# ══════════════════════════════════════════════════════════════════
def build_payload(device: dict, meter_data: dict) -> str:
    name      = device["name"]
    token_cfg = _load_cfg(TOKENS_FILE).get(name, {})
    payload_type = (
        device.get("payload_type")
        or token_cfg.get("payload_type", "meter3p")
    )
    ts_ms = (int(time.time()) // 60) * 60 * 1000
    payload = [
        {
            "access_token": token_cfg.get("token", ""),
            "type":         payload_type,
            "data": [{"ts": ts_ms, "values": meter_data}],
        }
    ]
    return json.dumps(payload, ensure_ascii=False)


# ══════════════════════════════════════════════════════════════════
#  MQTT Client 封裝
# ══════════════════════════════════════════════════════════════════
class MQTTPublisher:
    def __init__(self, config: dict):
        self.config = config
        self._connected = False

        self.client = mqtt.Client(client_id="", clean_session=True, protocol=mqtt.MQTTv311)
        self.client.username_pw_set(config["username"], config["password"])

        if config.get("use_tls"):
            ctx = ssl.create_default_context()
            if config.get("tls_insecure"):
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
            self.client.tls_set_context(ctx)

        self.client.reconnect_delay_set(
            min_delay=config["reconnect_min_delay_sec"],
            max_delay=config["reconnect_max_delay_sec"],
        )
        self.client.on_connect    = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish    = self._on_publish

    def _on_connect(self, client, userdata, flags, rc):
        self._connected = (rc == 0)
        if rc == 0:
            logger.info("MQTT 已連線至 %s:%s", self.config["broker"], self.config["port"])
        else:
            logger.warning("MQTT 連線失敗，rc=%s", rc)

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        if rc != 0:
            logger.warning("MQTT 非預期斷線 (rc=%s)，等待自動重連…", rc)

    def _on_publish(self, client, userdata, mid):
        logger.debug("訊息已發佈 mid=%s", mid)

    def connect(self):
        logger.info("連線至 %s:%s …", self.config["broker"], self.config["port"])
        self.client.connect_async(
            host=self.config["broker"],
            port=self.config["port"],
            keepalive=self.config["keepalive"],
        )
        self.client.loop_start()
        deadline = time.time() + self.config["connect_timeout_sec"]
        while not self._connected and time.time() < deadline:
            time.sleep(0.1)
        if not self._connected:
            logger.error("MQTT 連線逾時，將在背景繼續重試")

    def publish(self, topic: str, payload: str) -> bool:
        if not self._connected:
            logger.warning("MQTT 尚未連線，跳過本次發佈")
            return False
        result = self.client.publish(topic, payload, qos=1)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            logger.error("發佈失敗，錯誤碼=%s", result.rc)
            return False
        return True

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()


# ══════════════════════════════════════════════════════════════════
#  資料採集（背景執行緒）
# ══════════════════════════════════════════════════════════════════
def publish_one(device: dict, reader: MeterReader, publisher: MQTTPublisher):
    name     = device["name"]
    dev_type = device["type"]
    port     = device["port"]
    slave_id = device["slave_id"]

    logger.info("讀取電表 [%s] port=%s slave=%s type=%s", name, port, slave_id, dev_type)

    with _reader_lock:
        if dev_type == "adtek_cpm12d":
            data = reader.read_adtek_cpm12d(port, slave_id)
        elif dev_type == "dae_PM210":
            data = reader.read_dae_PM210(port, slave_id)
        else:
            logger.warning("未知電表類型: %s，略過", dev_type)
            return

    payload = build_payload(device, data)
    logger.info("[%s] Payload: %s", name, payload)

    topic = _load_cfg(MQTT_FILE)["topic"]
    ok = publisher.publish(topic, payload)
    if ok:
        logger.info("[%s] 發佈成功", name)
        flush_pending(publisher)
    else:
        save_to_db(topic, payload)


def collection_loop():
    """背景執行緒：讀表 + MQTT 排程上傳；任何例外皆自動重啟"""
    global _g_reader
    while True:
        reader    = None
        publisher = None
        try:
            mqtt_cfg      = _load_cfg(MQTT_FILE)
            meter_devices = _load_cfg(METERS_FILE)
            reader    = MeterReader()
            _g_reader = reader          # 共享給 Web 測試端點使用
            publisher = MQTTPublisher(mqtt_cfg)
            publisher.connect()

            schedule.clear()
            for device in meter_devices:
                interval = device.get("publish_interval", 60)
                publish_one(device, reader, publisher)
                schedule.every(interval).seconds.do(publish_one, device, reader, publisher)
                logger.info("[%s] 排程已啟動，每 %s 秒發佈一次", device["name"], interval)

            while True:
                if not _is_paused():
                    schedule.run_pending()
                _touch_activity()
                time.sleep(1)
        except Exception as e:
            logger.error("採集執行緒異常: %s，30 秒後重啟…", e)
        finally:
            _g_reader = None
            schedule.clear()
            try:
                if reader:
                    reader.close_all()
            except Exception:
                pass
            try:
                if publisher:
                    publisher.stop()
            except Exception:
                pass
        time.sleep(30)


# ══════════════════════════════════════════════════════════════════
#  Flask Web UI
# ══════════════════════════════════════════════════════════════════
@app.route("/")
def index():
    return render_template("index.html", username=session.get("username", ""))


# ── 登入 / 登出 / 修改帳號密碼 ────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login_page():
    if session.get("logged_in"):
        return redirect(url_for("index"))
    error = None
    if request.method == "POST":
        auth     = _load_cfg(AUTH_FILE)
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == auth["username"] and check_password_hash(auth["password_hash"], password):
            session["logged_in"] = True
            session["username"]  = username
            return redirect(url_for("index"))
        error = "帳號或密碼錯誤"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))

@app.route("/api/auth/change", methods=["POST"])
def change_auth():
    body        = request.json
    current_pw  = body.get("current_password", "")
    new_username = body.get("new_username", "").strip()
    new_pw      = body.get("new_password", "")
    confirm_pw  = body.get("confirm_password", "")

    auth = _load_cfg(AUTH_FILE)
    if not check_password_hash(auth["password_hash"], current_pw):
        return jsonify({"status": "fail", "message": "目前密碼錯誤"})
    if not new_username:
        return jsonify({"status": "fail", "message": "帳號不可為空"})
    if len(new_pw) < 4:
        return jsonify({"status": "fail", "message": "新密碼至少需要 4 個字元"})
    if new_pw != confirm_pw:
        return jsonify({"status": "fail", "message": "新密碼與確認密碼不符"})

    _save_cfg(AUTH_FILE, {
        "username":      new_username,
        "password_hash": generate_password_hash(new_pw),
    })
    session["username"] = new_username
    return jsonify({"status": "ok", "message": "帳號密碼已更新，請重新登入以確認"})


# ── MQTT 設定 ─────────────────────────────────────────────────────
@app.route("/api/mqtt", methods=["GET"])
def get_mqtt():
    return jsonify(_load_cfg(MQTT_FILE))

@app.route("/api/mqtt", methods=["POST"])
def save_mqtt():
    _save_cfg(MQTT_FILE, request.json)
    return jsonify({"status": "ok"})

@app.route("/api/mqtt/download")
def download_mqtt():
    return _as_attachment(_load_cfg(MQTT_FILE), "mqtt_config.json")

@app.route("/api/mqtt/upload", methods=["POST"])
def upload_mqtt():
    _save_cfg(MQTT_FILE, json.load(request.files["file"]))
    return jsonify({"status": "ok"})


# ── 電表清單 ──────────────────────────────────────────────────────
@app.route("/api/meters", methods=["GET"])
def get_meters():
    return jsonify(_load_cfg(METERS_FILE))

@app.route("/api/meters", methods=["POST"])
def save_meters():
    _save_cfg(METERS_FILE, request.json)
    return jsonify({"status": "ok"})

@app.route("/api/meters/download")
def download_meters():
    return _as_attachment(_load_cfg(METERS_FILE), "meters.json")

@app.route("/api/meters/upload", methods=["POST"])
def upload_meters():
    _save_cfg(METERS_FILE, json.load(request.files["file"]))
    return jsonify({"status": "ok"})


# ── 上行設定 ──────────────────────────────────────────────────────
@app.route("/api/tokens", methods=["GET"])
def get_tokens():
    return jsonify(_load_cfg(TOKENS_FILE))

@app.route("/api/tokens", methods=["POST"])
def save_tokens():
    _save_cfg(TOKENS_FILE, request.json)
    return jsonify({"status": "ok"})

@app.route("/api/tokens/download")
def download_tokens():
    return _as_attachment(_load_cfg(TOKENS_FILE), "access_tokens.json")

@app.route("/api/tokens/upload", methods=["POST"])
def upload_tokens():
    _save_cfg(TOKENS_FILE, json.load(request.files["file"]))
    return jsonify({"status": "ok"})


# ── 測試 MQTT ─────────────────────────────────────────────────────
@app.route("/api/test/mqtt", methods=["POST"])
def test_mqtt():
    cfg = _load_cfg(MQTT_FILE)
    connected = [False]
    err_msg   = [None]

    def on_connect(*args):
        rc = args[3]
        if rc == 0:
            connected[0] = True
        else:
            err_msg[0] = f"Broker 拒絕連線，rc={rc}"

    client = mqtt.Client(clean_session=True, protocol=mqtt.MQTTv311)
    client.username_pw_set(cfg["username"], cfg["password"])
    if cfg.get("use_tls"):
        ctx = ssl.create_default_context()
        if cfg.get("tls_insecure"):
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        client.tls_set_context(ctx)
    client.on_connect = on_connect

    try:
        client.connect(cfg["broker"], cfg["port"], keepalive=10)
        client.loop_start()
        deadline = time.time() + cfg.get("connect_timeout_sec", 10)
        while not connected[0] and err_msg[0] is None and time.time() < deadline:
            time.sleep(0.1)
        if connected[0]:
            return jsonify({"status": "ok",
                            "message": f"連線成功 → {cfg['broker']}:{cfg['port']}"})
        return jsonify({"status": "fail",
                        "message": err_msg[0] or "連線逾時，請確認網路與 Broker 設定"})
    except Exception as e:
        return jsonify({"status": "fail", "message": str(e)})
    finally:
        try:
            client.loop_stop()
            client.disconnect()
        except Exception:
            pass


# ── 測試電表 ──────────────────────────────────────────────────────
@app.route("/api/test/meter/<name>", methods=["POST"])
def test_meter(name):
    meters = _load_cfg(METERS_FILE)
    device = next((m for m in meters if m["name"] == name), None)
    if not device:
        return jsonify({"status": "fail", "message": f"找不到電表：{name}"}), 404

    dev_type = device["type"]
    # 優先使用輪詢共用的 reader（同一 COM port 實例），避免 port 衝突
    with _reader_lock:
        reader     = _g_reader or MeterReader()
        own_reader = _g_reader is None
        try:
            if dev_type == "adtek_cpm12d":
                data = reader.read_adtek_cpm12d(device["port"], device["slave_id"])
            elif dev_type == "dae_PM210":
                data = reader.read_dae_PM210(device["port"], device["slave_id"])
            else:
                return jsonify({"status": "fail", "message": f"未知設備類型：{dev_type}"})
            alive = bool(data.get("alive", 0))
            return jsonify({
                "status":  "ok"      if alive else "fail",
                "message": "讀取成功" if alive else "電表無回應 (alive=0)",
                "data":    data,
            })
        except Exception as e:
            return jsonify({"status": "fail", "message": str(e)})
        finally:
            if own_reader:
                reader.close_all()


# ── 清除電表累計電量（adtek_cpm12d Reg 0x0048 ← 0x55）────────────
@app.route("/api/meter/<name>/clear-energy", methods=["POST"])
def clear_energy(name):
    meters = _load_cfg(METERS_FILE)
    device = next((m for m in meters if m["name"] == name), None)
    if not device:
        return jsonify({"status": "fail", "message": f"找不到設備：{name}"}), 404
    if device.get("type") != "adtek_cpm12d":
        return jsonify({"status": "fail", "message": "此功能僅支援 adtek_cpm12d 設備"}), 400

    with _reader_lock:
        reader     = _g_reader or MeterReader()
        own_reader = _g_reader is None
        try:
            client = reader._get_client(device["port"])
            if not client.connect():
                return jsonify({"status": "fail", "message": "無法連接至設備"})
            response = client.write_register(
                address=0x0048, value=0x55, device_id=device["slave_id"]
            )
            if response.isError():
                return jsonify({"status": "fail", "message": f"寫入失敗：{response}"})
            logger.info("已清除 %s 累計電量 (reg 0x0048 ← 0x55)", name)
            return jsonify({"status": "ok", "message": "累計電量已清除"})
        except Exception as e:
            return jsonify({"status": "fail", "message": str(e)})
        finally:
            if own_reader:
                reader.close_all()


# ── 輪詢控制 ─────────────────────────────────────────────────────
@app.route("/api/polling/status", methods=["GET"])
def polling_status():
    with _polling_lock:
        paused    = _polling_paused and time.time() < _polling_resume_at
        resume_in = max(0, int(_polling_resume_at - time.time())) if paused else 0
    return jsonify({"paused": paused, "resume_in": resume_in})

@app.route("/api/polling/pause", methods=["POST"])
def pause_polling():
    global _polling_paused, _polling_resume_at
    with _polling_lock:
        _polling_paused    = True
        _polling_resume_at = time.time() + PAUSE_MAX_SEC
    logger.info("輪詢已暫停，%s 秒後自動恢復", PAUSE_MAX_SEC)
    return jsonify({"status": "paused", "resume_in": PAUSE_MAX_SEC})

@app.route("/api/polling/resume", methods=["POST"])
def resume_polling():
    global _polling_paused
    with _polling_lock:
        _polling_paused = False
    logger.info("輪詢已手動恢復")
    return jsonify({"status": "running"})


# ── Ping 監控 ────────────────────────────────────────────────────
_PING_DEFAULT: dict = {
    "enabled":      False,
    "ip1":          "10.59.7.194",
    "ip2":          "10.59.6.194",
    "interval":     600,   # 預設每 10 分鐘 ping 一次
    "reboot_after": 3600,
}

_ping_lock  = threading.Lock()
_ping_state = {
    "ip1_ok":          None,
    "ip1_last":        0.0,
    "ip2_ok":          None,
    "ip2_last":        0.0,
    "both_fail_since": None,
    "fail_count":      0,    # 連續兩 IP 同時失聯的累計次數
}

def _load_ping_cfg() -> dict:
    if os.path.exists(PING_FILE):
        return {**_PING_DEFAULT, **_load_cfg(PING_FILE)}
    return dict(_PING_DEFAULT)

def _do_ping(ip: str) -> bool:
    try:
        r = subprocess.run(["ping", "-c", "1", "-W", "2", ip],
                           capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False

def ping_watchdog_loop():
    last_ping = 0.0
    while True:
        time.sleep(5)
        cfg = _load_ping_cfg()

        if not cfg.get("enabled", False):
            with _ping_lock:
                _ping_state["both_fail_since"] = None
            continue

        now      = time.time()
        interval = max(10, int(cfg.get("interval", 60)))
        if now - last_ping < interval:
            continue

        ip1 = cfg.get("ip1", "10.59.7.194")
        ip2 = cfg.get("ip2", "10.59.6.194")
        reboot_after = max(60, int(cfg.get("reboot_after", 3600)))

        ip1_ok = _do_ping(ip1)
        ip2_ok = _do_ping(ip2)
        ts = time.time()
        last_ping = ts
        logger.debug("Ping：%s=%s  %s=%s", ip1, ip1_ok, ip2, ip2_ok)

        with _ping_lock:
            _ping_state["ip1_ok"]   = ip1_ok
            _ping_state["ip1_last"] = ts
            _ping_state["ip2_ok"]   = ip2_ok
            _ping_state["ip2_last"] = ts

            both_fail = not ip1_ok and not ip2_ok
            if both_fail:
                _ping_state["fail_count"] += 1
                if _ping_state["both_fail_since"] is None:
                    _ping_state["both_fail_since"] = ts
                    logger.warning("Ping 監控：%s 及 %s 同時失聯，開始計時（第 %d 次）",
                                   ip1, ip2, _ping_state["fail_count"])
                fail_dur = ts - _ping_state["both_fail_since"]
                if fail_dur >= reboot_after:
                    logger.warning("Ping 監控：持續 %.0f 秒失聯（累計 %d 次），觸發重新開機",
                                   fail_dur, _ping_state["fail_count"])
                    subprocess.Popen(["systemctl", "reboot"])
            else:
                if _ping_state["fail_count"] > 0:
                    logger.info("Ping 監控：連線已恢復，重置失聯計數（原 %d 次）",
                                _ping_state["fail_count"])
                _ping_state["fail_count"]      = 0
                _ping_state["both_fail_since"] = None


@app.route("/api/ping/config", methods=["GET"])
def get_ping_config():
    return jsonify(_load_ping_cfg())

@app.route("/api/ping/config", methods=["POST"])
def save_ping_config():
    _save_cfg(PING_FILE, request.json)
    return jsonify({"status": "ok"})

@app.route("/api/ping/status", methods=["GET"])
def get_ping_status():
    cfg = _load_ping_cfg()
    with _ping_lock:
        state = dict(_ping_state)
    now = time.time()
    return jsonify({
        "enabled":         cfg.get("enabled", False),
        "ip1":             cfg.get("ip1", ""),
        "ip2":             cfg.get("ip2", ""),
        "interval":        cfg.get("interval", 60),
        "reboot_after":    cfg.get("reboot_after", 3600),
        "ip1_ok":          state["ip1_ok"],
        "ip1_last":        state["ip1_last"],
        "ip2_ok":          state["ip2_ok"],
        "ip2_last":        state["ip2_last"],
        "both_fail_since": state["both_fail_since"],
        "fail_duration":   round(now - state["both_fail_since"]) if state["both_fail_since"] else 0,
        "fail_count":      state["fail_count"],
    })


# ── 網路設定 ─────────────────────────────────────────────────────
NETWORKD_DIR  = "/etc/systemd/network"
CELLULAR_CONF = os.path.join(NETWORKD_DIR, "20-wwan.network")

_NETWORK_DEFAULT: dict = {
    "eth": [
        {"interface": "eth0", "dhcp": True,
         "address": "", "prefix": "24", "gateway": "", "dns": ""},
        {"interface": "eth1", "dhcp": True,
         "address": "", "prefix": "24", "gateway": "", "dns": ""},
    ],
    "cellular": {
        "enabled": False,
        "apn":  "WVPN",
        "dns1": "10.59.7.194",
        "dns2": "10.59.6.194",
    },
}

def _load_network_cfg() -> dict:
    if os.path.exists(NETWORK_FILE):
        return _load_cfg(NETWORK_FILE)
    return json.loads(json.dumps(_NETWORK_DEFAULT))

def _networkd_eth_content(cfg: dict) -> str:
    name = cfg["interface"]
    if cfg.get("dhcp", True):
        return f"[Match]\nName={name}\n\n[Network]\nDHCP=yes\n\n[DHCP]\nUseDNS=yes\n"
    lines = [f"[Match]\nName={name}\n\n[Network]\n",
             f"Address={cfg.get('address','')}/{cfg.get('prefix','24')}\n"]
    if cfg.get("gateway"):
        lines.append(f"Gateway={cfg['gateway']}\n")
    for d in cfg.get("dns", "").split():
        lines.append(f"DNS={d}\n")
    return "".join(lines)

def _get_modem_path() -> str:
    r = subprocess.run(["mmcli", "-L"], capture_output=True, text=True, timeout=5)
    for line in r.stdout.splitlines():
        if "/Modem/" in line:
            return line.strip().split()[0]
    return ""

def _apply_cellular(cel: dict):
    enabled = cel.get("enabled", False)
    apn  = cel.get("apn",  "WVPN")
    dns1 = cel.get("dns1", "10.59.7.194")
    dns2 = cel.get("dns2", "10.59.6.194")

    # 為 wwan 介面寫入 DNS 設定（不論是否啟用都預先寫入）
    os.makedirs(NETWORKD_DIR, exist_ok=True)
    with open(CELLULAR_CONF, "w") as f:
        f.write(f"[Match]\nName=wwan*\n\n[Network]\nDNS={dns1}\nDNS={dns2}\n")

    modem = _get_modem_path()
    if not modem:
        if not enabled:
            return
        raise RuntimeError("找不到 4G 模組，請確認 EG25-G 已連接且 ModemManager 已安裝")

    if not enabled:
        subprocess.run(["mmcli", "-m", modem, "--simple-disconnect"],
                       capture_output=True, timeout=15)
        return

    subprocess.run(["mmcli", "-m", modem, "--enable"],
                   check=True, timeout=15)
    subprocess.run(["mmcli", "-m", modem, f"--simple-connect=apn={apn}"],
                   check=True, timeout=30)
    subprocess.run(["networkctl", "reload"], capture_output=True, timeout=10)


@app.route("/api/network/config", methods=["GET"])
def get_network_config():
    return jsonify(_load_network_cfg())

@app.route("/api/network/config", methods=["POST"])
def save_network_config():
    cfg = request.json
    _save_cfg(NETWORK_FILE, cfg)
    errors = []

    try:
        os.makedirs(NETWORKD_DIR, exist_ok=True)
        for eth in cfg.get("eth", []):
            if not eth.get("interface"):
                continue
            path = os.path.join(NETWORKD_DIR, f"10-{eth['interface']}.network")
            with open(path, "w") as f:
                f.write(_networkd_eth_content(eth))
        # 先嘗試 reload（不中斷連線）；若 networkd 尚未啟動則啟動它
        r = subprocess.run(["networkctl", "reload"], capture_output=True, timeout=10)
        if r.returncode != 0:
            subprocess.run(["systemctl", "start", "systemd-networkd"],
                           capture_output=True, timeout=15)
            subprocess.run(["networkctl", "reload"], capture_output=True, timeout=10)
    except Exception as e:
        errors.append(f"Ethernet：{e}")

    try:
        _apply_cellular(cfg.get("cellular", {}))
    except Exception as e:
        errors.append(f"4G：{e}")

    if errors:
        return jsonify({"status": "partial", "message": "；".join(errors)})
    return jsonify({"status": "ok"})

@app.route("/api/network/status", methods=["GET"])
def network_status():
    try:
        r = subprocess.run(["ip", "-j", "addr"],
                           capture_output=True, text=True, timeout=5)
        result = {}
        for iface in json.loads(r.stdout):
            name = iface.get("ifname", "")
            if name == "lo":
                continue
            ipv4 = [a for a in iface.get("addr_info", [])
                    if a.get("family") == "inet"]
            result[name] = {
                "up":      "UP" in iface.get("flags", []),
                "address": f"{ipv4[0]['local']}/{ipv4[0]['prefixlen']}" if ipv4 else "",
            }
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "fail", "message": str(e)}), 500


# ── 硬體設定 ─────────────────────────────────────────────────────
TIMESYNCD_CONF = "/etc/systemd/timesyncd.conf"

def _read_timesyncd_conf() -> tuple[str, str]:
    """讀取 /etc/systemd/timesyncd.conf 中有效（未被 # 註解）的 NTP 設定"""
    ntp = fallback = ""
    if not os.path.exists(TIMESYNCD_CONF):
        return ntp, fallback
    with open(TIMESYNCD_CONF) as f:
        for line in f:
            s = line.strip()
            if re.match(r'^NTP\s*=', s):
                ntp = s.split("=", 1)[1].strip()
            elif re.match(r'^FallbackNTP\s*=', s):
                fallback = s.split("=", 1)[1].strip()
    return ntp, fallback

def _write_timesyncd_conf(ntp: str, fallback: str):
    """在 /etc/systemd/timesyncd.conf 的 [Time] 區段更新 NTP= 與 FallbackNTP="""
    if os.path.exists(TIMESYNCD_CONF):
        with open(TIMESYNCD_CONF) as f:
            lines = f.readlines()
    else:
        lines = ["[Time]\n"]

    in_time = False
    ntp_done = fallback_done = False
    result = []

    for line in lines:
        s = line.strip()
        if s.startswith("["):
            in_time = (s == "[Time]")
        if in_time and re.match(r'^\s*#?\s*NTP\s*=', line):
            if not ntp_done:
                result.append(f"NTP={ntp}\n" if ntp else "#NTP=\n")
                ntp_done = True
            continue
        if in_time and re.match(r'^\s*#?\s*FallbackNTP\s*=', line):
            if not fallback_done:
                result.append(f"FallbackNTP={fallback}\n" if fallback else "#FallbackNTP=\n")
                fallback_done = True
            continue
        result.append(line)

    # 若 [Time] 區段內沒有對應的行，補在最後
    if not ntp_done and ntp:
        result.append(f"NTP={ntp}\n")
    if not fallback_done and fallback:
        result.append(f"FallbackNTP={fallback}\n")

    with open(TIMESYNCD_CONF, "w") as f:
        f.writelines(result)

def _timedatectl_props() -> dict:
    result = subprocess.run(
        ["timedatectl", "show"], capture_output=True, text=True, timeout=5
    )
    props = {}
    for line in result.stdout.splitlines():
        k, _, v = line.partition("=")
        props[k.strip()] = v.strip()
    return props

@app.route("/api/system/info", methods=["GET"])
def system_info():
    try:
        props = _timedatectl_props()
        return jsonify({
            "datetime":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ntp_enabled": props.get("NTP", "no").lower() == "yes",
            "ntp_synced":  props.get("NTPSynchronized", "no").lower() == "yes",
        })
    except Exception as e:
        logger.error("system_info 錯誤: %s", e)
        return jsonify({"status": "fail", "message": str(e)}), 500

@app.route("/api/system/ntp/detail", methods=["GET"])
def ntp_detail():
    try:
        # 從 timedatectl show-timesync 取得目前使用的伺服器與同步細節
        ts = subprocess.run(
            ["timedatectl", "show-timesync", "--all"],
            capture_output=True, text=True, timeout=5
        )
        ts_props = {}
        for line in ts.stdout.splitlines():
            k, _, v = line.partition("=")
            ts_props[k.strip()] = v.strip()

        # 人類可讀的同步狀態
        st = subprocess.run(
            ["timedatectl", "timesync-status"],
            capture_output=True, text=True, timeout=5
        )

        # 從設定檔讀取已儲存的伺服器設定
        ntp, fallback = _read_timesyncd_conf()

        return jsonify({
            "current_server":     ts_props.get("ServerName", ""),
            "current_server_ip":  ts_props.get("ServerAddress", ""),
            "system_ntp":         ts_props.get("SystemNTPServers", ""),
            "fallback_ntp":       ts_props.get("FallbackNTPServers", ""),
            "configured_ntp":     ntp,
            "configured_fallback": fallback,
            "status_text":        st.stdout.strip() or st.stderr.strip(),
        })
    except Exception as e:
        logger.error("ntp_detail 錯誤: %s", e)
        return jsonify({"status": "fail", "message": str(e)}), 500

@app.route("/api/system/ntp/config", methods=["POST"])
def save_ntp_config():
    body     = request.json
    ntp      = body.get("ntp",      "").strip()
    fallback = body.get("fallback", "").strip()
    try:
        _write_timesyncd_conf(ntp, fallback)
        subprocess.run(
            ["systemctl", "restart", "systemd-timesyncd"],
            check=True, timeout=10
        )
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "fail", "message": str(e)})

@app.route("/api/system/ntp", methods=["POST"])
def set_ntp():
    enabled = request.json.get("enabled", True)
    try:
        subprocess.run(
            ["timedatectl", "set-ntp", "1" if enabled else "0"],
            check=True, timeout=10
        )
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "fail", "message": str(e)})

@app.route("/api/system/datetime", methods=["POST"])
def set_datetime():
    dt_str = request.json.get("datetime", "")
    try:
        datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        subprocess.run(
            ["timedatectl", "set-time", dt_str],
            check=True, timeout=10
        )
        return jsonify({"status": "ok"})
    except ValueError:
        return jsonify({"status": "fail", "message": "日期時間格式錯誤"})
    except Exception as e:
        return jsonify({"status": "fail", "message": str(e)})

@app.route("/api/system/reboot", methods=["POST"])
def reboot_system():
    try:
        subprocess.Popen(["systemctl", "reboot"])
        return jsonify({"status": "ok", "message": "系統即將重新開機，請稍候約 30 秒再重新連線"})
    except Exception as e:
        return jsonify({"status": "fail", "message": str(e)})


# ══════════════════════════════════════════════════════════════════
#  啟動
# ══════════════════════════════════════════════════════════════════
def main():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    _ensure_auth_file()
    init_db()

    # Watchdog 執行緒
    wt = threading.Thread(target=watchdog_loop, daemon=True, name="Watchdog")
    wt.start()
    logger.info("Watchdog 已啟動（逾時 %s 秒）", WATCHDOG_TIMEOUT)

    # Ping 監控執行緒
    pt = threading.Thread(target=ping_watchdog_loop, daemon=True, name="PingWatchdog")
    pt.start()
    logger.info("Ping 監控執行緒已啟動")

    # 資料採集在背景執行緒運行（daemon=True 讓主程式結束時自動關閉）
    t = threading.Thread(target=collection_loop, daemon=True, name="CollectionLoop")
    t.start()
    logger.info("資料採集執行緒已啟動")

    # Flask Web UI 在主執行緒運行
    logger.info("Web UI 啟動於 http://0.0.0.0:9000")
    app.run(host="0.0.0.0", port=9000, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
