import requests
import pandas as pd

# 設置 Channel Access Token
CHANNEL_ACCESS_TOKEN = "pECFyW0nU67uld3MRDM+RmmNP6+GQVAvOUjDJptV5I0u4Ze5P4YZk4nTxYbSxndl6buVetJrp1D2NclLqx7hpSL7htdDN9NH7wAt0evpBYGnZjAEcIWauKleAqZXu3g5fyrkqP1y7yFA6XbiN6xa1QdB04t89/1O/w1cDnyilFU="

# 取得所有 userID
def get_follower_ids():
    url = "https://api.line.me/v2/bot/followers/ids"
    headers = {"Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"}
    params = {"limit": 300}
    all_user_ids = []

    while True:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        all_user_ids.extend(data.get("userIds", []))
        next_token = data.get("next")
        if not next_token:
            break
        params["start"] = next_token

    return all_user_ids

# 取得用戶名稱
def get_user_profile(user_id):
    url = f"https://api.line.me/v2/bot/profile/{user_id}"
    headers = {"Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("displayName", "N/A")
    return "N/A"

# 主程式
def main():
    # 取得所有 userID
    user_ids = get_follower_ids()
    
    # 儲存 userID 與名稱
    user_data = []
    for user_id in user_ids:
        display_name = get_user_profile(user_id)
        user_data.append({"userId": user_id, "displayName": display_name})
    
    # 轉成 DataFrame 並寫入 XLSX
    df = pd.DataFrame(user_data)
    df.to_excel("line_users.xlsx", index=False, engine="openpyxl")
    
    print(f"已儲存 {len(user_data)} 筆用戶資料至 line_users.xlsx")

if __name__ == "__main__":
    main()