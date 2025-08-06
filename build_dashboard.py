from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from datetime import date
import pyodbc
import re
import sys

# 讓 Python 能匯入 quote_generator.py
sys.path.append(".")

from quote_generator import generate_quote

# 資料庫連線資訊
server = 'www.cwsoft.com.tw,1226'
username = 'Pos'
password = 'sql2wsxCFT^3edc'
driver = 'ODBC Driver 17 for SQL Server'

def get_companies_data():
    companies = []
    today = date.today()
    yymm = f"{str(today.year)[2:]}{today.month:02d}"

    # 連接 POSConfig 撈出公司設定
    query = """
    SELECT 主索引, 資料庫名, 停用, 線上收費, 收費月數, 月租折扣
    FROM 分店設定檔
    """

    conn1 = pyodbc.connect(f'DRIVER={{{driver}}};SERVER={server};DATABASE=POSConfig;UID={username};PWD={password}')
    cursor1 = conn1.cursor()
    # cursor1.execute("SELECT * FROM 分店設定檔")
    cursor1.execute(query)
    rows1 = cursor1.fetchall()
    columns1 = [col[0] for col in cursor1.description]
    disable_idx = columns1.index("停用")
    dbname_idx = columns1.index("資料庫名")
    onlinepay_idx = columns1.index("線上收費")
    charge_month_idx = columns1.index("收費月數")
    discount_idx = columns1.index("月租折扣")
    cursor1.close()
    conn1.close()

    # 連接 POSV3shared 撈出授權數
    conn2 = pyodbc.connect(f'DRIVER={{{driver}}};SERVER={server};DATABASE=POSV3shared;UID={username};PWD={password}')
    cursor2 = conn2.cursor()
    cursor2.execute("SELECT * FROM 線上付款_已購買授權")
    rows2 = cursor2.fetchall()
    cursor2.close()
    conn2.close()

    for row1 in rows1:
        print('============')
        print(row1)
        # print(disable_idx,onlinepay_idx)
        # print(row1[disable_idx],row1[onlinepay_idx])
        
        # if row1[disable_idx] == 1 or row1[onlinepay_idx] == 0:
        if row1[disable_idx] == 1  :
        # if row1[onlinepay_idx] == 0:
            continue
        db_name = row1[dbname_idx]
        if db_name in ['msdb', 'POSConfig', 'POSV3promo', 'POSV3shared', '各資料庫設定','POSV3測試專用','Demo用']:
            continue
        primary_key=row1[0]
        online_pay= 1 if row1[onlinepay_idx] else 0
        charge_months = row1[charge_month_idx] or 6
        discount = row1[discount_idx] or 0
        unit_price = int(2600 * ((100-discount) / 100))

        auth_quantity = 0
        for row2 in rows2:
            if row2[1] == row1[0] and row2[2] == 1:
                auth_quantity = row2[3]

        
        conn3 = pyodbc.connect(f'DRIVER={{{driver}}};SERVER={server};DATABASE={db_name};UID={username};PWD={password}')
        cursor3 = conn3.cursor()
        # cursor3.execute("SELECT * FROM 分店")
        cursor3.execute("SELECT 分店編號, 店名, 是否已收店, 線上付款_停用 FROM 分店")
        rows3 = cursor3.fetchall()
        columns3 = [col[0] for col in cursor3.description]
        close_idx = columns3.index("是否已收店")
        onlinepay_disable_idx = columns3.index("線上付款_停用")

        active_branches = 0
        active_branch_names=[]

        for row3 in rows3:
            onlinepay_disable = row3[onlinepay_disable_idx]
            is_closed = row3[close_idx]  # 取得「是否已收店」值
            branch_numb = f"{row3[0]:02d}" # 分店編號變兩位數
            branch_name = row3[1]
            # # 排除已停用、名稱為"總倉"或已收店的分店
            if onlinepay_disable == 1  or is_closed == 1 or branch_name == "總倉":
                continue
            # print(f"{branch_numb:02d}",branch_name)
            # print( branch_numb ,branch_name)
            

            # [檢索兩種單據]
            is_active = False # 預設為未活躍
            current_date = date.today()
            yymm = f"{str(current_date.year)[2:]}{current_date.month:02d}"  # 取年份後兩位，月補零

            # print(driver,server,db_name,username,password)
            # conn3 = pyodbc.connect(f'DRIVER={{{driver}}};SERVER={server};DATABASE={db_name};UID={username};PWD={password}')
            cursor3 = conn3.cursor()
            cursor3.execute("SELECT 單據編號 FROM 銷貨單")
            rows4 = cursor3.fetchall()
            for row4 in reversed(rows4):
                document_number=row4[0]
                if document_number[1:5]==yymm:
                    if document_number[7:9] == branch_numb :
                        print(document_number)
                        is_active = True
                        break

            cursor3.execute("SELECT 單據編號 FROM 出貨單")
            rows4 = cursor3.fetchall()
            for row4 in reversed(rows4):
                document_number=row4[0]
                if document_number[1:5]==yymm:
                    if document_number[7:9] == branch_numb :
                        print(document_number)
                        is_active = True
                        break
            # print( branch_numb ,branch_name,is_active)
            # if branch_name not in ['ABC', "鑫瑞總倉", "XYZ總倉",'總部']: # 專門針對總倉的折衷辦法
            #     active_branch_names.append(branch_name)
            if is_active :
                active_branches+=1
                active_branch_names.append(branch_name)
            
        #     for r in rows3:
        #         if r[onlinepay_disable_idx] == 1 or r[close_idx] == 1 or r[1] == "總倉":
        #             continue
        #         active_branches.append(r[1])
        #     cursor3.close()
        #     conn3.close()
        # except Exception as e:
        #     print(f"⚠ 無法連線 {db_name}：{e}")
        #     active_branches = []

        # 判斷需報價
        quote_required=0
        if  active_branches >= auth_quantity and online_pay:
            quote_required=1

        print(active_branch_names)
        companies.append({
            "primary_key":primary_key,
            "company_name": db_name,
            "branches": active_branch_names,
            "active_branche_num": active_branches,
            "license_count": auth_quantity,
            "online_pay":online_pay,
            "quote_required":quote_required,
            "charge_months": charge_months,
            "discount": discount
        })

    return companies

# 主程式
if __name__ == "__main__":
    companies_data = get_companies_data()
    for company in companies_data:
        unit_price = 2600
        months = 6
        if company["company_name"] in ["紳鴻", "有支手機", "布魯斯"]:
            months = 1
        if company["company_name"] == "艾瑪":
            unit_price = 1300

        pdf_path = generate_quote(
            company_data=company,
            period_months=months,
            price_includes_tax=True,
            unit_price=unit_price,
            template_name="quote_template_html.txt",  # 或改成 quote_template.html
            output_dir="output_quotes"
        )
        company["pdf_path"] = str(pdf_path).replace("\\", "/")
        company["active_count"] = len(company["branches"])

    # 產出 HTML 儀表板
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("dashboard_template.html")
    html_output = template.render(companies=companies_data)
    Path("dashboard.html").write_text(html_output, encoding="utf-8")
    print("✅ 已完成 dashboard.html")
