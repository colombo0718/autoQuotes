from ecpay_payment_sdk import ECPayPaymentSdk
from datetime import datetime

# 初始化SDK
sdk = ECPayPaymentSdk(
    MerchantID='3002607',
    HashKey='pwFHCqoQZGmho4w6',
    HashIV='EkRm7iFT261dpevs'
)

# 測試訂單參數
order_params = {
    'MerchantTradeNo': datetime.now().strftime("NO%Y%m%d%H%M%S"),
    'MerchantTradeDate': datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
    'PaymentType': 'aio',
    'TotalAmount': 2600,
    'TradeDesc': 'POS月租費測試',
    'ItemName': 'POS月租費',
    'ReturnURL': 'https://e616816c05f9.ngrok-free.app/callback',
    'ChoosePayment': 'Credit',
    'ClientBackURL': 'https://e616816c05f9.ngrok-free.app/confirm.html',
    'EncryptType': 1,
}

# 創建訂單並生成HTML表單
try:
    params = sdk.create_order(order_params)
    html = sdk.gen_html_post_form('https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5', params)
    with open('static/ecpay_payment.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("HTML 內容已保存至 static/ecpay_payment.html")
except Exception as e:
    print(f'錯誤：{e}')