from flask import Flask, request, send_from_directory
import subprocess
import os

app = Flask(__name__, static_url_path='', static_folder='static')

# 綠界付款回呼（ECPay）
@app.route("/callback", methods=["POST"])
def callback():
    data = request.form
    print(f"收到 ECPay 回調：{data}")
    return "1|OK"

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

# 綠界付款頁（ecpay_payment.html）
@app.route("/ecpay")
def serve_ecpay():
    try:
        result = subprocess.run(["python", "ecpay_test_order.py"], capture_output=True, text=True)
        if result.returncode != 0:
            return f"生成 ECPay 訂單失敗：{result.stderr}", 500
        return send_from_directory(app.static_folder, "ecpay_payment.html")
    except Exception as e:
        return f"錯誤：{e}", 500

# LINE Pay 付款頁（linepay_payment.html）
@app.route("/linepay")
def serve_linepay():
    try:
        result = subprocess.run(["python", "linepay_test_order.py"], capture_output=True, text=True)
        if result.returncode != 0:
            return f"生成 LINE Pay 訂單失敗：{result.stderr}", 500
        return send_from_directory(app.static_folder, "linepay_payment.html")
    except Exception as e:
        return f"錯誤：{e}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

@app.route("/confirm")
def confirm():
    return send_from_directory(app.static_folder, "confirm.html")

@app.route("/cancel")
def cancel():
    return send_from_directory(app.static_folder, "cancel.html")
