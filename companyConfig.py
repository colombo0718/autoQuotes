import pyodbc
import pandas as pd
import re

# 設定連線資訊
server = 'www.cwsoft.com.tw,1226'
username = 'Pos'
password = 'sql2wsxCFT^3edc'
driver = 'ODBC Driver 17 for SQL Server'

# 連線第一個資料庫 POSConfig
database1 = 'POSConfig'
conn_str1 = f'DRIVER={{{driver}}};SERVER={server};DATABASE={database1};UID={username};PWD={password}'
conn1 = pyodbc.connect(conn_str1)
cursor1 = conn1.cursor()

# 查詢分店設定檔資料表
cursor1.execute("SELECT * FROM 分店設定檔")
rows1 = cursor1.fetchall()

# 取得表頭並找到所需欄位索引
columns1 = [column[0] for column in cursor1.description]
main_index = columns1.index("主索引")
db_name_index = columns1.index("資料庫名")
plan_type_index = columns1.index("方案類別")
online_fee_index = columns1.index("線上收費")
disable_index = columns1.index("停用")
company_name_index = columns1.index("公司名稱")

# 關閉連線
cursor1.close()
conn1.close()

# 過濾資料並處理線上收費與公司名稱欄位
filtered_data = [
    [
        row[main_index],
        row[db_name_index],
        row[plan_type_index],
        1 if row[online_fee_index] is True else 0
    ]
    for row in rows1 if row[disable_index] != 1 and not re.match(r'^0', str(row[company_name_index]))
]

# 轉為 DataFrame 並輸出到 XLSX
df = pd.DataFrame(filtered_data, columns=["主索引", "資料庫名", "方案類別", "線上收費"])
df.to_excel('payment_settings.xlsx', index=False, engine='openpyxl')

print("已生成 payment_settings.xlsx")