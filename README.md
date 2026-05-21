# INFILINK EMS Gateway

光綺科技 EMS 閘道器：透過 Modbus RTU 讀取電表資料，並以 MQTT 上傳至雲端平台。  
內含 Flask Web UI 可進行 MQTT、電表、Token 等設定管理。

---

## 目錄

1. [系統需求](#系統需求)
2. [部署步驟](#部署步驟)
3. [設定說明](#設定說明)
4. [開機自動執行](#開機自動執行)
5. [首次登入](#首次登入)

---

## 系統需求

| 項目 | 建議版本 |
|------|---------|
| 目標硬體 | AAEON AM62 Gateway |
| 作業系統 | Ubuntu 22.04 LTS（或相容 Debian 系發行版） |
| Python | 3.11 以上（建議 3.13） |
| Serial Port | `/dev/ttyUSB0`（RS-485 USB 轉接器）或 `/dev/ttyS*` |

---

## 部署步驟

### 1. 上傳程式碼

將整個專案資料夾複製至 AM62，例如放在：

```bash
/home/infilink/Gateway_EMS
```

使用 SCP 或 SFTP：

```bash
scp -r ./Gateway_EMS infilink@<AM62-IP>:/home/infilink/
```

---

### 2. 安裝 Python（若尚未安裝）

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
```

> 若作業系統已內建 Python 3.11+，可跳過此步驟。  
> 確認版本：`python3 --version`

---

### 3. 建立虛擬環境 `infilink_ems`

```bash
cd /home/infilink/Gateway_EMS

python3 -m venv infilink_ems
```

啟用虛擬環境：

```bash
source infilink_ems/bin/activate
```

---

### 4. 安裝相依套件

#### 方法 A：使用 requirements.txt（建議）

```bash
pip install -r requirements.txt
```

#### 方法 B：逐一安裝（可指定版本）

```bash
pip install \
    flask==3.1.2 \
    werkzeug==3.1.5 \
    jinja2==3.1.6 \
    markupsafe==3.0.3 \
    blinker==1.9.0 \
    click==8.3.1 \
    itsdangerous==2.2.0 \
    paho-mqtt==1.6.1 \
    pymodbus==3.13.0 \
    pyserial==3.5 \
    schedule==1.2.2
```

#### 套件版本對照表（開發機實測版本）

| 套件 | 版本 | 說明 |
|------|------|------|
| Flask | 3.1.2 | Web UI 框架 |
| Werkzeug | 3.1.5 | Flask 底層依賴、密碼雜湊 |
| Jinja2 | 3.1.6 | HTML 樣板引擎 |
| MarkupSafe | 3.0.3 | Jinja2 依賴 |
| blinker | 1.9.0 | Flask 信號機制依賴 |
| click | 8.3.1 | Flask CLI 依賴 |
| itsdangerous | 2.2.0 | Flask Session 簽章依賴 |
| paho-mqtt | 1.6.1 | MQTT 客戶端 |
| pymodbus | 3.13.0 | Modbus RTU 通訊 |
| pyserial | 3.5 | Serial Port 驅動（pymodbus 依賴） |
| schedule | 1.2.2 | 定時排程 |

---

### 5. Serial Port 權限設定

Linux 預設需要 `dialout` 群組權限才能存取 Serial Port：

```bash
sudo usermod -aG dialout $USER
```

> 設定後需**重新登入**或重新啟動服務才能生效。

---

### 6. 調整 Serial Port 設定

AM62 上的 Serial Port 路徑與 Windows 不同。請進入 Web UI **設備清單** 頁面，  
將 `COM4` 改為實際的 Linux 裝置路徑，例如：

| Windows | Linux（常見） |
|---------|--------------|
| `COM4`  | `/dev/ttyUSB0` |
| `COM3`  | `/dev/ttyS0` |

確認裝置路徑：

```bash
ls /dev/tty*          # 列出所有 serial 裝置
dmesg | grep tty      # 查看核心偵測到的 serial 裝置
```

---

### 7. 手動測試執行

```bash
cd /home/infilink/Gateway_EMS
source infilink_ems/bin/activate
python app.py
```

開啟瀏覽器連至 `http://<AM62-IP>:9000`，確認 Web UI 正常運作後，再設定開機自動執行。

---

## 設定說明

所有設定檔位於 `config/` 資料夾：

| 檔案 | 說明 |
|------|------|
| `mqtt_config.json` | MQTT Broker 連線設定 |
| `meters.json` | 電表裝置清單（含 Serial Port、Slave ID、上傳間隔） |
| `access_tokens.json` | 各電表的 Access Token 與 Payload 類型 |
| `auth.json` | Web UI 登入帳號密碼（bcrypt 雜湊）|
| `secret.key` | Flask Session 金鑰（自動產生，請勿刪除）|

---

## 開機自動執行

使用 **systemd** 設定服務，確保 AM62 開機後自動啟動程式，  
且程式異常退出時自動重啟。

### 1. 建立 systemd 服務檔

```bash
sudo nano /etc/systemd/system/infilink-ems.service
```

貼入以下內容（請將 `infilink` 改為實際使用者名稱）：

```ini
[Unit]
Description=INFILINK EMS Gateway
Documentation=https://infilink.app
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=infilink
Group=dialout
WorkingDirectory=/home/infilink/Gateway_EMS
ExecStart=/home/infilink/Gateway_EMS/infilink_ems/bin/python app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

> **注意**：`Group=dialout` 確保服務有 Serial Port 存取權限。

---

### 2. 啟用並啟動服務

```bash
# 重新載入 systemd 設定
sudo systemctl daemon-reload

# 設定開機自動啟動
sudo systemctl enable infilink-ems.service

# 立即啟動服務
sudo systemctl start infilink-ems.service
```

---

### 3. 確認服務狀態

```bash
sudo systemctl status infilink-ems.service
```

正常運作時顯示 `Active: active (running)`。

---

### 4. 查看即時 Log

```bash
# 即時追蹤 log（Ctrl+C 離開）
sudo journalctl -u infilink-ems.service -f

# 查看最近 100 行
sudo journalctl -u infilink-ems.service -n 100
```

---

### 5. 服務管理指令

```bash
sudo systemctl stop    infilink-ems.service   # 停止
sudo systemctl restart infilink-ems.service   # 重啟
sudo systemctl disable infilink-ems.service   # 取消開機自動啟動
```

---

## 首次登入

服務啟動後，開啟瀏覽器：

```
http://<AM62-IP>:9000
```

| 項目 | 預設值 |
|------|--------|
| 帳號 | `admin` |
| 密碼 | `admin` |

> **請於首次登入後立即至「帳號設定」頁面修改預設密碼。**

---

## requirements.txt

專案根目錄已包含 `requirements.txt`，內容如下（供參考）：

```
flask==3.1.2
werkzeug==3.1.5
jinja2==3.1.6
markupsafe==3.0.3
blinker==1.9.0
click==8.3.1
itsdangerous==2.2.0
paho-mqtt==1.6.1
pymodbus==3.13.0
pyserial==3.5
schedule==1.2.2
```

---

*INFILINK Technology Co., Ltd.*
