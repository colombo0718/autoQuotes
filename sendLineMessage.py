import requests

# 設置 Channel Access Token 和 userID
# 全葳官網
# CHANNEL_ACCESS_TOKEN = "pECFyW0nU67uld3MRDM+RmmNP6+GQVAvOUjDJptV5I0u4Ze5P4YZk4nTxYbSxndl6buVetJrp1D2NclLqx7hpSL7htdDN9NH7wAt0evpBYGnZjAEcIWauKleAqZXu3g5fyrkqP1y7yFA6XbiN6xa1QdB04t89/1O/w1cDnyilFU="
# USER_ID = "U0053e659a383ee64d46ac973abdc84be" # 士豪
# USER_ID = "U145660126c71f5f0d89d6f5c6aaccefc" # 羿宏
# USER_ID = "Uf300bfeaecce2c1d350b30e3a933ce85" # 彥偉

# 全葳小助手
CHANNEL_ACCESS_TOKEN = "RA3hROIUnPP44Ruk7ranS+dLpf6O6pxKNS7nTca9udeIBeUkmyA/9qUTkBIXX/3hxPennnpu5dY1xFyjqYR5UWVX/qTQ7gCL7l9oOoFRTNSIfZsPfgeK/2Db2zv3TQK8rehw+OQeXJtHRsq3LwVxIgdB04t89/1O/w1cDnyilFU="
USER_ID = "U38daae74d279bef697f99a22c65c3751" # 士豪
# USER_ID = "Ua52624cb319bcccab4d12703ef28929c" # 羿宏
# USER_ID = "U34e144c9bf7d30bc07c543a4ebae0df1" # 彥偉

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


def push_pdf():
    file_name = "全紅_202602_未稅.pdf"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }

    flex = {
        "type": "flex",
        "altText": f"報價單：{file_name}",
        "contents": {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": [
                    {"type": "text", "text": "📄 報價單已產生", "weight": "bold", "size": "lg"},
                    {"type": "text", "text": file_name, "wrap": True, "size": "md"},
                    {"type": "text", "text": "點下方按鈕直接開啟下載", "wrap": True, "size": "sm", "color": "#888888"}
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {
                            "type": "uri",
                            "label": "下載 PDF",
                            "uri":  "https://cwsoft.leaflune.org/output_quotes/quote_%E5%85%A8%E7%B4%98_202602_%E6%9C%AA%E7%A8%85.pdf"
                        }
                    }
                ]
            }
        }
    }

    payload = {"to": USER_ID, "messages": [flex]}

    res = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers=headers,
        json=payload
    )
    print("Status:", res.status_code)
    print("Response:", res.text)


def push_image_pdf():

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }

    messages = [
        {
            "type": "image",
            "originalContentUrl": IMAGE_URL,
            "previewImageUrl": IMAGE_URL
        },
        {
            "type": "text",
            "text": f"📄 下載完整PDF：\n{PDF_URL}"
        }
    ]

    payload = {
        "to": USER_ID,
        "messages": messages
    }

    res = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers=headers,
        json=payload
    )

    print("Status:", res.status_code)
    print("Response:", res.text)

def push_branch_carousel():
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }

    flex = {
        "type": "flex",
        "altText": "門市導覽",
        "contents": {
            "type": "carousel",
            "contents": [
                {
                    "type": "bubble",
                    "size": "kilo",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "contents": [
                            {"type": "text", "text": "向日葵店", "weight": "bold", "size": "lg", "wrap": True},
                            {"type": "text", "text": "桃園市中壢區遠東路135號", "size": "sm", "wrap": True}
                        ]
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "button",
                                "style": "primary",
                                "action": {
                                    "type": "uri",
                                    "label": "📍 開啟地圖",
                                    "uri": "https://www.google.com/maps/search/?api=1&query=%E6%A1%83%E5%9C%92%E5%B8%82%E4%B8%AD%E5%A3%A2%E5%8D%80%E9%81%A0%E6%9D%B1%E8%B7%AF135%E8%99%9F"
                                }
                            }
                        ]
                    }
                },
                {
                    "type": "bubble",
                    "size": "kilo",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "contents": [
                            {"type": "text", "text": "丁香店", "weight": "bold", "size": "lg", "wrap": True},
                            {"type": "text", "text": "桃園市中壢區中北路200號", "size": "sm", "wrap": True}
                        ]
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "button",
                                "style": "primary",
                                "action": {
                                    "type": "uri",
                                    "label": "📍 開啟地圖",
                                    "uri": "https://www.google.com/maps/search/?api=1&query=%E6%A1%83%E5%9C%92%E5%B8%82%E4%B8%AD%E5%A3%A2%E5%8D%80%E4%B8%AD%E5%8C%97%E8%B7%AF200%E8%99%9F"
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }

    payload = {"to": USER_ID, "messages": [flex]}

    res = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers=headers,
        json=payload
    )

    print("Status:", res.status_code)
    print("Response:", res.text)

if __name__ == "__main__":
    # send_message()
    # send_image()
    # send_pdf_link() 
    # push_pdf()
    # push_image_pdf()
    push_branch_carousel()
    # check_bot_info()  # 查詢帳號狀態
    # check_message_quota()  # 查詢額度類型
    check_message_consumption()  # 查詢已用量