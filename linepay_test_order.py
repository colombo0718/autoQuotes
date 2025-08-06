import uuid
import requests
import hashlib
import hmac
import base64
import datetime
import json
import os

# ─────────────────────────────
# LINE Pay 測試商店參數（請依照實際資訊填入）
# ─────────────────────────────
CHANNEL_ID = '2007825031'
CHANNEL_SECRET = 'd3b935eb5102d00437df5be5a68e3a23'
REQUEST_URL = 'https://sandbox-api-pay.line.me/v3/payments/request'
NONCE = str(uuid.uuid4())

# ─────────────────────────────
# 訂單內容
# ─────────────────────────────
ORDER_ID = 'ORD' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
AMOUNT = 2600
DESCRIPTION = 'POS 月租費'

body = {
    "amount": AMOUNT,
    "currency": "TWD",
    "orderId": ORDER_ID,
    "packages": [{
        "id": "package1",
        "amount": AMOUNT,
        "name": "POS 月租費",
        "products": [{
            "name": DESCRIPTION,
            "quantity": 1,
            "price": AMOUNT
        }]
    }],
    "redirectUrls": {
        "confirmUrl": "https://e616816c05f9.ngrok-free.app/confirm.html",  # ← 替換為你實際的 ngrok URL
        "cancelUrl": "https://e616816c05f9.ngrok-free.app/cancel.html"
    }
}

# ─────────────────────────────
# 簽章計算
# ─────────────────────────────
API_PATH = '/v3/payments/request'
FULL_URL = 'https://sandbox-api-pay.line.me' + API_PATH
body_str = json.dumps(body, separators=(',', ':'))
raw_signature = CHANNEL_SECRET + API_PATH + body_str + NONCE

signature = base64.b64encode(
    hmac.new(
        CHANNEL_SECRET.encode('utf-8'),
        raw_signature.encode('utf-8'),
        hashlib.sha256
    ).digest()
).decode('utf-8')

# ─────────────────────────────
# Header 組裝
# ─────────────────────────────
headers = {
    "Content-Type": "application/json",
    "X-LINE-ChannelId": CHANNEL_ID,
    "X-LINE-Authorization-Nonce": NONCE,
    "X-LINE-Authorization": signature
}

# ─────────────────────────────
# Debug 輸出
# ─────────────────────────────
print("=== LINE Pay Request Debug Info ===")
print("Request URL:", REQUEST_URL)
print("Body:", body_str)
print("Nonce:", NONCE)
print("Raw Signature:", raw_signature)
print("Signature:", signature)
print("Headers:", headers)
print("====================================")

# ─────────────────────────────
# 發送請求
# ─────────────────────────────
res = requests.post(REQUEST_URL, headers=headers, data=body_str)
response = res.json()

print("== LINE Pay Response ==")
print(json.dumps(response, indent=2, ensure_ascii=False))

# ─────────────────────────────
# 若成功，產生跳轉 HTML
# ─────────────────────────────
if response.get("returnCode") == "0000":
    payment_url = response["info"]["paymentUrl"]["web"]
    os.makedirs("static", exist_ok=True)
    with open("static/linepay_payment.html", "w", encoding="utf-8") as f:
        f.write(f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head><meta charset="UTF-8"><title>LINE Pay 付款</title></head>
<body>
  <p>正在轉跳至 LINE Pay 付款頁...</p>
  <script>window.location.href = "{payment_url}";</script>
</body>
</html>
""")
    print("付款頁已建立：static/linepay_payment.html")
else:
    print("建立付款失敗：", response.get("returnMessage"))
