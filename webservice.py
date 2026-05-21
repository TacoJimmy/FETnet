# -*- coding: utf-8 -*-
"""
EMS Gateway 設定管理 Web 服務
執行: python webservice.py
瀏覽器: http://localhost:5000
"""
import io
import json
import logging
import os
import ssl
import time

import paho.mqtt.client as mqtt
from flask import Flask, jsonify, render_template, request, send_file

from PowerMeter import MeterReader

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CONFIG_DIR       = "config"
MQTT_FILE        = os.path.join(CONFIG_DIR, "mqtt_config.json")
METERS_FILE      = os.path.join(CONFIG_DIR, "meters.json")
TOKENS_FILE      = os.path.join(CONFIG_DIR, "access_tokens.json")


# ── 共用工具 ─────────────────────────────────────────────────────
def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def _save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _as_attachment(data, filename):
    buf = io.BytesIO(json.dumps(data, ensure_ascii=False, indent=2).encode())
    return send_file(buf, mimetype="application/json",
                     as_attachment=True, download_name=filename)


# ── Web UI ───────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


# ── MQTT 設定 ────────────────────────────────────────────────────
@app.route("/api/mqtt", methods=["GET"])
def get_mqtt():
    return jsonify(_load(MQTT_FILE))

@app.route("/api/mqtt", methods=["POST"])
def save_mqtt():
    _save(MQTT_FILE, request.json)
    return jsonify({"status": "ok"})

@app.route("/api/mqtt/download")
def download_mqtt():
    return _as_attachment(_load(MQTT_FILE), "mqtt_config.json")

@app.route("/api/mqtt/upload", methods=["POST"])
def upload_mqtt():
    _save(MQTT_FILE, json.load(request.files["file"]))
    return jsonify({"status": "ok"})


# ── 電表清單 ─────────────────────────────────────────────────────
@app.route("/api/meters", methods=["GET"])
def get_meters():
    return jsonify(_load(METERS_FILE))

@app.route("/api/meters", methods=["POST"])
def save_meters():
    _save(METERS_FILE, request.json)
    return jsonify({"status": "ok"})

@app.route("/api/meters/download")
def download_meters():
    return _as_attachment(_load(METERS_FILE), "meters.json")

@app.route("/api/meters/upload", methods=["POST"])
def upload_meters():
    _save(METERS_FILE, json.load(request.files["file"]))
    return jsonify({"status": "ok"})


# ── 上行設定 ─────────────────────────────────────────────────────
@app.route("/api/tokens", methods=["GET"])
def get_tokens():
    return jsonify(_load(TOKENS_FILE))

@app.route("/api/tokens", methods=["POST"])
def save_tokens():
    _save(TOKENS_FILE, request.json)
    return jsonify({"status": "ok"})

@app.route("/api/tokens/download")
def download_tokens():
    return _as_attachment(_load(TOKENS_FILE), "access_tokens.json")

@app.route("/api/tokens/upload", methods=["POST"])
def upload_tokens():
    _save(TOKENS_FILE, json.load(request.files["file"]))
    return jsonify({"status": "ok"})


# ── 測試 MQTT 連線 ────────────────────────────────────────────────
@app.route("/api/test/mqtt", methods=["POST"])
def test_mqtt():
    cfg = _load(MQTT_FILE)
    connected = [False]
    err_msg   = [None]

    def on_connect(client, userdata, flags, rc):
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


# ── 測試電表讀取 ──────────────────────────────────────────────────
@app.route("/api/test/meter/<name>", methods=["POST"])
def test_meter(name):
    meters = _load(METERS_FILE)
    device = next((m for m in meters if m["name"] == name), None)
    if not device:
        return jsonify({"status": "fail", "message": f"找不到電表：{name}"}), 404

    reader = MeterReader()
    try:
        dev_type = device["type"]
        if dev_type == "adtek_cpm12d":
            data = reader.read_adtek_cpm12d(device["port"], device["slave_id"])
        elif dev_type == "dae_PM210":
            data = reader.read_dae_PM210(device["port"], device["slave_id"])
        else:
            return jsonify({"status": "fail", "message": f"未知設備類型：{dev_type}"})

        alive = bool(data.get("alive", 0))
        return jsonify({
            "status":  "ok"   if alive else "fail",
            "message": "讀取成功" if alive else "電表無回應 (alive=0)",
            "data":    data,
        })
    except Exception as e:
        return jsonify({"status": "fail", "message": str(e)})
    finally:
        reader.close_all()


# ── 啟動 ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs(CONFIG_DIR, exist_ok=True)
    logger.info("Web 服務啟動於 http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
