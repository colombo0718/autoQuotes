import pandas as pd
import pyodbc

# ====== Excel 檔案路徑 ======
excel_path = "客戶付費方式_已解析.xlsx"

# ====== SQL Server 連線資訊 ======
server = 'www.cwsoft.com.tw,1226'
database = 'POSConfig'
username = 'Pos'
password = 'sql2wsxCFT^3edc'
driver = 'ODBC Driver 17 for SQL Server'

# 建立資料庫連線
conn_str = f'DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# 讀取 Excel
df = pd.read_excel(excel_path)

# 更新資料庫
for idx, row in df.iterrows():
    db_name = row["資料庫名"]
    charge_months = row["收費月數"]
    discount = row["月租折扣"]
    bonus_months = row["贈送月數"]
    has_contract = row["維護合約"]

    try:
        cursor.execute("""
            UPDATE [分店設定檔]
            SET [收費月數] = ?, [月租折扣] = ?, [贈送月數] = ?, [維護合約] = ?
            WHERE [資料庫名] = ?
        """, charge_months, discount, bonus_months, has_contract, db_name)
    except Exception as e:
        print(f"更新失敗：{db_name}，原因：{e}")

# 提交變更並關閉連線
conn.commit()
cursor.close()
conn.close()

print("✅ 所有資料更新完成！")
