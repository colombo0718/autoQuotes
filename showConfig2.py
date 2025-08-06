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
online_pay_index = columns1.index("線上收費")

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

# 關閉第二個資料庫連線
cursor2.close()
conn2.close()

# 儲存公司資料
companies_data = []


for row1 in rows1:
    main_index = row1[0]  # 第一個資料表的"主索引"
    # company_name = row1[1]  # 第一個資料表的"公司名稱"
    disable_value = row1[disable_index]  # 第一個資料表的"停用"
    db_name = row1[db_name_index]  # 第一個資料表的"資料庫名"
    online_pay = row1[online_pay_index]
    # company_name_cleaned = re.sub(r'^\d+', '', company_name)# 移除公司名稱前面的數字
    if disable_value == 1 or online_pay==0:  # 若停用=1，跳過
        continue
    if db_name in ['msdb', 'POSConfig', 'POSV3Promo', 'POSV3Shared', '各資料庫設定']:
        continue
        # print(company_name_cleaned)
    # print(driver,server,db_name,username,password)
    # print(db_name)

    auth_quantity=0 # 授權數量
    for row2 in rows2:
        branch_index = row2[1]  # 第二個資料表的"分店設定檔主索引"
        auth_type = row2[2]     # 第二個資料表的"授權類別"
        
        if main_index == branch_index and auth_type == 1:
            auth_quantity = row2[3] # 第二個資料表的"授權數量"
    # print("授權數量:",auth_quantity)

    conn3 = pyodbc.connect(f'DRIVER={{{driver}}};SERVER={server};DATABASE={db_name};UID={username};PWD={password}')
    cursor3 = conn3.cursor()
    cursor3.execute("SELECT * FROM 分店")
    # cursor3.execute("SELECT 分店編號, 店名, 是否已收店, 線上付款_停用 FROM 分店")
    rows3 = cursor3.fetchall()
    columns3 = [column[0] for column in cursor3.description]
    online_payment_disable_index = columns3.index("線上付款_停用")
    closed_index = columns3.index("是否已收店")  # 新增「是否已收店」欄位索引

    active_branches=0
    active_branch_names=[]
    for row3 in rows3:
        online_payment_disable = row3[online_payment_disable_index]
        is_closed = row3[closed_index]  # 取得「是否已收店」值
        branch_numb = f"{row3[0]:02d}" # 分店編號變兩位數
        branch_name = row3[1]
        # # 排除已停用、名稱為"總倉"或已收店的分店
        if online_payment_disable == 1  or is_closed == 1 or branch_name == "總倉":
            continue
        # print(f"{branch_numb:02d}",branch_name)
        # print( branch_numb ,branch_name)
        # 預設為未活躍
        

        # [檢索兩種單據]
        is_active = False
        current_date = date.today()
        yymm = f"{str(current_date.year)[2:]}{current_date.month:02d}"  # 取年份後兩位，月補零

        # print(driver,server,db_name,username,password)
        # conn3 = pyodbc.connect(f'DRIVER={{{driver}}};SERVER={server};DATABASE={db_name};UID={username};PWD={password}')
        cursor3 = conn3.cursor()
        cursor3.execute("SELECT 單據編號 FROM 銷貨單")
        rows4 = cursor3.fetchall()
        for row4 in reversed(rows4):
            # print(row4)
            document_number=row4[0]
            if document_number[1:5]==yymm:
                if document_number[7:9] == branch_numb :
                    is_active = True
                    break

        cursor3.execute("SELECT 單據編號 FROM 出貨單")
        rows4 = cursor3.fetchall()
        for row4 in reversed(rows4):
            # print(row4)
            document_number=row4[0]
            if document_number[1:5]==yymm:
                if document_number[7:9] == branch_numb :
                    is_active = True
                    break

        # print( branch_numb ,branch_name,is_active)
        if branch_name not in ['ABC', "鑫瑞總倉", "XYZ總倉",'總部']: # 專門針對總倉的折衷辦法
            active_branch_names.append(branch_name)
        if is_active :
            active_branches+=1
            # active_branch_names.append(branch_name)

    # print("活躍分店數:",active_branches)
    if active_branches > auth_quantity or (active_branches == 0 and auth_quantity == 0):
        print(driver,server,db_name,username,password)
        print("授權數量:",auth_quantity)
        print("活躍分店數:",active_branches)
        print(active_branch_names)

        company_data = {
            "company_name": db_name,
            "branches": active_branch_names,
            "license_count": auth_quantity
        }
        companies_data.append(company_data)
        
i = 0
for company in companies_data:
    # 只處理月繳公司
    # if company.get("payment_plan") != 1:
    #     continue

    try:
        unit_price=2600
        months = 6          # 月繳
        if company["company_name"] in ["紳鴻", "有支手機", "布魯斯"]:
            months = 1
        # print(company)
        if company["company_name"] == "艾瑪":
            unit_price=1300
        print(unit_price)
        output_file = generate_quote(
            company_data = company,
            period_months = months,          # 月繳
            price_includes_tax = False,  # 或 True，看你的單價設定
            unit_price=unit_price  
        )
        i += 1
        print(f"已生成報價單：{output_file}")
    except Exception as e:
        print(f"生成 {company['company_name']} 報價單失敗：{e}")

print(f"共完成 {i} 份月繳報價單")