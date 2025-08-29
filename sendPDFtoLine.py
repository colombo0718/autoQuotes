import requests

# === 基本設定 ===
BASE_URL = "https://topposnas.synology.me"
STORE_ID = "86E951CF"
LINE_UIDS = ["Uf300bfeaecce2c1d350b30e3a933ce85"]

# 你要上傳的檔案路徑與名稱
LOCAL_FILE_PATH = "quote_xxx.pdf"
FILE_NAME = "quote_xxx.pdf"


# === Step 1. 上傳檔案 ===
def upload_file(file_path):
    url = f"{BASE_URL}/upload_file"
    files = {"file": open(file_path, "rb")}
    try:
        response = requests.post(url, files=files, timeout=30)
        print("Upload Status Code:", response.status_code)
        print("Upload Response:", response.text)
        return response.ok
    except Exception as e:
        print("Upload Error:", e)
        return False


# === Step 2. 寄送檔案 ===
def send_file(file_name):
    url = f"{BASE_URL}/send_file"
    payload = {
        "store_id": STORE_ID,
        "line_uids": LINE_UIDS,
        "file_name": file_name
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print("Send Status Code:", response.status_code)
        print("Send Response:", response.text)
    except Exception as e:
        print("Send Error:", e)


if __name__ == "__main__":
    if upload_file(LOCAL_FILE_PATH):
        send_file(FILE_NAME)
