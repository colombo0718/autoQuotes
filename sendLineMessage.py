import requests

# 設置 Channel Access Token 和 userID
CHANNEL_ACCESS_TOKEN = "pECFyW0nU67uld3MRDM+RmmNP6+GQVAvOUjDJptV5I0u4Ze5P4YZk4nTxYbSxndl6buVetJrp1D2NclLqx7hpSL7htdDN9NH7wAt0evpBYGnZjAEcIWauKleAqZXu3g5fyrkqP1y7yFA6XbiN6xa1QdB04t89/1O/w1cDnyilFU="
USER_ID = "U0053e659a383ee64d46ac973abdc84be" # 自己
# USER_ID = "U145660126c71f5f0d89d6f5c6aaccefc" # 羿宏
# USER_ID = "Uf300bfeaecce2c1d350b30e3a933ce85" # 學長

# 發送訊息
def send_message():
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "to": USER_ID,
        "messages": [
            {
                "type": "text",
                "text": "這是一則測試訊息，發送給自己！"
            }
        ]
    }
    response = requests.post(url, headers=headers, json=payload)
    print(response.json())

    # 圖片 URL
IMAGE_URL = "https://www.cwsoft.com.tw/Content/Images/logo.png"
PDF_URL = "https://e616816c05f9.ngrok-free.app/"

# 發送圖片
def send_image():
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "to": USER_ID,
        "messages": [
            {
                "type": "image",
                "originalContentUrl": IMAGE_URL,
                "previewImageUrl": IMAGE_URL
            }
        ]
    }
    response = requests.post(url, headers=headers, json=payload)
    print(response.json())

# 發送 PDF 連結（改為文字訊息）
def send_pdf_link():
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "to": USER_ID,
        "messages": [
            {
                "type": "text",
                "text": f"本月報價單：{PDF_URL}"
            }
        ]
    }
    response = requests.post(url, headers=headers, json=payload)
    print("PDF 連結發送結果:", response.json())

# 查詢帳號狀態
def check_bot_status():
    url = "https://api.line.me/v2/bot/info"
    headers = {"Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"帳號狀態: {data.get('status')}")
        print(f"帳號類型: {data.get('mode')}")
    else:
        print(f"查詢帳號狀態失敗: {response.json()}")

# 查詢訊息額度
def check_message_quota():
    url = "https://api.line.me/v2/bot/message/quota"
    headers = {"Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"訊息類型: {data.get('type')}")
    else:
        print(f"查詢額度失敗: {response.json()}")

# 查詢已用訊息量
def check_message_consumption():
    url = "https://api.line.me/v2/bot/message/quota/consumption"
    headers = {"Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"已用訊息量: {data.get('totalUsage', 'N/A')}")
    else:
        print(f"查詢已用量失敗: {response.json()}")


if __name__ == "__main__":
    # send_message()
    # send_image()
    send_pdf_link() 
    # check_bot_status()  # 查詢帳號狀態
    # check_message_quota()  # 查詢額度類型
    # check_message_consumption()  # 查詢已用量