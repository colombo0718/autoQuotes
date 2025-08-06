import pyodbc
import re
from quote_generator import generate_quote
import csv
from datetime import date
from pathlib import Path

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

# 取得表頭並找到"停用"和"資料庫名"欄位索引
columns1 = [column[0] for column in cursor1.description]
disable_index = columns1.index("停用")
db_name_index = columns1.index("資料庫名")

# 關閉第一個資料庫連線
cursor1.close()
conn1.close()

# 連線第二個資料庫 POSV3shared
database2 = 'POSV3shared'
conn_str2 = f'DRIVER={{{driver}}};SERVER={server};DATABASE={database2};UID={username};PWD={password}'
conn2 = pyodbc.connect(conn_str2)
cursor2 = conn2.cursor()

# 查詢線上付款_已購買授權資料表
cursor2.execute("SELECT * FROM 線上付款_已購買授權")
rows2 = cursor2.fetchall()

# 取得第二個資料表的表頭
columns2 = [column[0] for column in cursor2.description]
print("第二個資料表表頭：", columns2)

# 儲存公司資料
companies_data = []

# 比對並收集公司資料
for row1 in rows1:
    main_index = row1[0]  # 第一個資料表的"主索引"
    company_name = row1[1]  # 第一個資料表的"公司名稱"
    disable_value = row1[disable_index]  # 第一個資料表的"停用"
    db_name = row1[db_name_index]  # 第一個資料表的"資料庫名"
    if disable_value == 1:  # 若停用=1，跳過
        continue
    # 移除公司名稱前面的數字
    company_name_cleaned = re.sub(r'^\d+', '', company_name)
    for row2 in rows2:
        branch_index = row2[1]  # 第二個資料表的"分店設定檔主索引"
        auth_type = row2[2]     # 第二個資料表的"授權類別"
        auth_quantity = row2[3] # 第二個資料表的"授權數量"
        if main_index == branch_index and auth_type == 1:
            branch_names = []
            try:
                print(driver,server,db_name,username,password)
                conn3 = pyodbc.connect(f'DRIVER={{{driver}}};SERVER={server};DATABASE={db_name};UID={username};PWD={password}')
                cursor3 = conn3.cursor()
                cursor3.execute("SELECT * FROM 分店")
                rows3 = cursor3.fetchall()
                columns3 = [column[0] for column in cursor3.description]
                online_payment_disable_index = columns3.index("線上付款_停用")
                closed_index = columns3.index("是否已收店")  # 新增「是否已收店」欄位索引
                for row3 in rows3:
                    online_payment_disable = row3[online_payment_disable_index]
                    is_closed = row3[closed_index]  # 取得「是否已收店」值
                    branch_name = row3[1]
                    # 排除已停用、名稱為"總倉"或已收店的分店
                    if online_payment_disable == 1 or branch_name == "總倉" or is_closed == 1:
                        continue
                    branch_names.append(branch_name)
                cursor3.close()
                conn3.close()
            except pyodbc.Error as e:
                print(f"無法連線到資料庫 {db_name}：{e}")
                branch_names = []
            branch_count = len(branch_names)
            if auth_quantity < branch_count:
                print(f"主索引 {main_index}，公司名稱：{db_name}，資料庫名：{db_name}，授權數量：{auth_quantity}，分店數：{branch_count}")
                # print(branch_names)
                # 收集公司資料
                company_data = {
                    "company_name": db_name,
                    "branches": branch_names,
                    "license_count": auth_quantity
                }
                companies_data.append(company_data)

# 關閉第二個資料庫連線
cursor2.close()
conn2.close()


monthly_companies = {"有支手機", "布魯斯", "紳鴻"}

# === 1. 計算 need_payment 欄位 =================================
for comp in companies_data:
    branch_count   = len(comp["branches"])
    license_count  = comp["license_count"]
    comp["need_payment"] =  int(license_count < branch_count)   # True / False
    # 收費方案：月繳 = 1；半年繳 = 6
    comp["payment_plan"] = 1 if comp["company_name"] in monthly_companies else 6
    comp["branch_count"] = branch_count                   # 寫進 CSV 會比較直觀

# === 2. 輸出 CSV =============================================
csv_headers = ["company_name", "branch_count", "license_count", "need_payment","payment_plan" ]
today_str   = date.today().strftime("%Y%m%d")             # 20250714
outfile     = Path(__file__).with_name(f"companies_{today_str}.csv")

with outfile.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=csv_headers)
    writer.writeheader()
    for row in companies_data:
        writer.writerow({h: row[h] for h in csv_headers})

print(f"[INFO] 產生完成 → {outfile}")

# exit()

i = 0
for company in companies_data:
    # 只處理月繳公司
    # if company.get("payment_plan") != 1:
    #     continue

    try:
        output_file = generate_quote(
            company_data = company,
            period_months = 1,          # 月繳
            price_includes_tax = False  # 或 True，看你的單價設定
        )
        i += 1
        print(f"已生成報價單：{output_file}")
    except Exception as e:
        print(f"生成 {company['company_name']} 報價單失敗：{e}")

print(f"共完成 {i} 份月繳報價單")