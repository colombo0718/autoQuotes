import os
import pyodbc
from dotenv import load_dotenv

# 載入 .env
load_dotenv()

server = os.getenv("DB_SERVER")
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
driver = os.getenv("DB_DRIVER")

conn_str = (
    f"DRIVER={{{driver}}};"
    f"SERVER={server};"
    f"UID={username};"
    f"PWD={password};"
    f"TrustServerCertificate=yes;"
)

sql = """
SELECT
      [IMEI],
      [回應辭],
      [分店設定檔主索引],
      [員工編號],
      [備註]
FROM [POSConfig].[dbo].[行動裝置設定檔]
WHERE [是否停用] = 0
"""

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute(sql)

    rows = cursor.fetchall()

    if not rows:
        print("查無資料")
    else:
        for row in rows:
            print(
                f"回應辭: {row.回應辭}, "
                f"分店設定檔主索引: {row.分店設定檔主索引}, "
                f"員工編號: {row.員工編號}, "
                f"備註: {row.備註}"
            )

except Exception as e:
    print("發生錯誤：", e)

finally:
    try:
        cursor.close()
        conn.close()
    except:
        pass