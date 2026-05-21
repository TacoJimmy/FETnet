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
import threading
import time

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
AUTH_FILE   = os.path.join(CONFIG_DIR, "auth.json")


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
    """背景執行緒：讀表 + MQTT 排程上傳"""
    global _g_reader
    try:
        mqtt_cfg      = _load_cfg(MQTT_FILE)
        meter_devices = _load_cfg(METERS_FILE)
        reader    = MeterReader()
        _g_reader = reader          # 共享給 Web 測試端點使用
        publisher = MQTTPublisher(mqtt_cfg)
        publisher.connect()

        for device in meter_devices:
            interval = device.get("publish_interval", 60)
            publish_one(device, reader, publisher)
            schedule.every(interval).seconds.do(publish_one, device, reader, publisher)
            logger.info("[%s] 排程已啟動，每 %s 秒發佈一次", device["name"], interval)

        while True:
            if not _is_paused():
                schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        logger.error("採集執行緒異常: %s", e)
    finally:
        try:
            reader.close_all()
            publisher.stop()
        except Exception:
            pass


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


# ══════════════════════════════════════════════════════════════════
#  啟動
# ══════════════════════════════════════════════════════════════════
def main():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    _ensure_auth_file()
    init_db()

    # 資料採集在背景執行緒運行（daemon=True 讓主程式結束時自動關閉）
    t = threading.Thread(target=collection_loop, daemon=True, name="CollectionLoop")
    t.start()
    logger.info("資料採集執行緒已啟動")

    # Flask Web UI 在主執行緒運行
    logger.info("Web UI 啟動於 http://0.0.0.0:9000")
    app.run(host="0.0.0.0", port=9000, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
