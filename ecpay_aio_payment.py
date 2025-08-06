import requests
import hashlib
import urllib.parse
from datetime import datetime

# 綠界API設定（測試環境）
ECPAY_URL = "https://payment-stage.ecpay.com.tw/Cashier/AIO"
MERCHANT_ID = "3002607"  # 測試MerchantID，正式環境需替換
HASH_KEY = "pwFHcQoQZgmho4w6"  # 測試HashKey，正式環境需替換
HASH_IV = "EkRm7iFTz61dpevs"  # 測試HashIV，正式環境需替換
RETURN_URL = "https://yourdomain.com/callback"  # 支付完成回調URL

def generate_checksum(params, hash_key, hash_iv):
    """生成綠界API的CheckMacValue"""
    sorted_params = sorted(params.items())
    query_string = urllib.parse.urlencode(sorted_params)
    raw_data = f"HashKey={hash_key}&{query_string}&HashIV={hash_iv}"
    checksum = hashlib.sha256(raw_data.encode()).hexdigest().upper()
    return checksum

def create_payment_order(branch_id, branch_name, amount, trade_no):
    """為單一分店創建支付訂單"""
    params = {
        "MerchantID": MERCHANT_ID,
        "MerchantTradeNo": trade_no,  # 唯一交易ID，例如：分店ID+時間戳
        "MerchantTradeDate": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        "PaymentType": "aio",
        "TotalAmount": int(amount),  # 整數金額，例如2600
        "TradeDesc": f"POS月租費 - {branch_name}",
        "ItemName": f"POS月租費 {branch_name}",
        "ChoosePayment": "Credit",  # 可選：Credit, ATM, CVS
        "ReturnURL": RETURN_URL,
        "ClientBackURL": "https://yourdomain.com/success",  # 支付完成後跳轉
        "EncryptType": 1,  # SHA256加密
    }
    params["CheckMacValue"] = generate_checksum(params, HASH_KEY, HASH_IV)
    return params

def send_payment_request(params):
    """發送支付訂單請求，獲取繳費連結"""
    try:
        response = requests.post(ECPAY_URL, data=params)
        if response.status_code == 200:
            # 解析回應，獲取支付頁面URL（實際回應為HTML表單，需提取）
            return response.text  # 簡化處理，實際需解析為URL
        else:
            print(f"請求失敗，狀態碼：{response.status_code}")
            return None
    except Exception as e:
        print(f"請求錯誤：{e}")
        return None

def batch_create_payments(branch_data):
    """批量為多間分店創建支付訂單"""
    payment_links = []
    for branch in branch_data:
        trade_no = f"{branch['branch_id']}_{int(datetime.now().timestamp())}"
        params = create_payment_order(
            branch["branch_id"],
            branch["branch_name"],
            branch["amount"],
            trade_no
        )
        payment_url = send_payment_request(params)
        if payment_url:
            payment_links.append({
                "branch_id": branch["branch_id"],
                "branch_name": branch["branch_name"],
                "line_user_id": branch["line_user_id"],
                "payment_url": payment_url
            })
    return payment_links

# 模擬分店資料（從POSConfig與LINE會員身分表格）
branch_data = [
    {
        "branch_id": "B001",
        "branch_name": "六六屋中壢店",
        "amount": 2600,
        "line_user_id": "U123456789"
    },
    {
        "branch_id": "B002",
        "branch_name": "六六屋桃園店",
        "amount": 2600,
        "line_user_id": "U987654321"
    }
]

# 執行批量支付訂單創建
payment_links = batch_create_payments(branch_data)
for link in payment_links:
    print(f"分店：{link['branch_name']}，LINE用戶ID：{link['line_user_id']}，繳費連結：{link['payment_url']}")