from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from datetime import date,timedelta
import pyodbc
import re
import sys
import json
from dateutil.relativedelta import relativedelta  # 需要 pip install python-dateutil


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
    SELECT 主索引, 資料庫名, 停用, 線上收費, 收費月數, 月租折扣,贈送月數
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
    bonus_month_idx = columns1.index("贈送月數")
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
        bonus_months = row1[bonus_month_idx] or 0 
        discount = row1[discount_idx] or 0
        unit_price = int(2600 * ((100-discount) / 100))

        license_count = 0
        for row2 in rows2:
            if row2[1] == row1[0] and row2[2] == 1:
                license_count = row2[3]

        
        conn3 = pyodbc.connect(f'DRIVER={{{driver}}};SERVER={server};DATABASE={db_name};UID={username};PWD={password}')
        cursor3 = conn3.cursor()
        # cursor3.execute("SELECT * FROM 分店")
        cursor3.execute("SELECT 分店編號, 店名, 是否已收店, 線上付款_停用, 建立日期 FROM 分店")
        rows3 = cursor3.fetchall()
        # print(rows3)
        columns3 = [col[0] for col in cursor3.description]
        # print(columns3)
        close_idx = columns3.index("是否已收店")
        onlinepay_disable_idx = columns3.index("線上付款_停用")
        create_idx = columns3.index("建立日期")

        cursor3.execute("SELECT 名稱, 設定值 FROM 基本設定 WHERE 名稱='總倉編號'")
        rows5=cursor3.fetchall()
        main_warehouse_id=rows5[0][1] # 總倉編號

        # 計算30天前的日期
        since_date = date.today() - timedelta(days=30)


        active_count = 0
        charge_count = 0
        branches_info = []
        active_branch_names=[]
        charge_branch_names=[]

        for row3 in rows3:
            onlinepay_disable = row3[onlinepay_disable_idx]
            is_closed = row3[close_idx]  # 取得「是否已收店」值
            branch_numb = f"{row3[0]:02d}" # 分店編號變兩位數
            branch_name = row3[1]
            # # 排除已停用、名稱為"總倉"或已收店的分店
            # if onlinepay_disable == 1  or is_closed == 1 or branch_name == "總倉":
            if onlinepay_disable == 1  or is_closed == 1:
                continue
            # print(f"{branch_numb:02d}",branch_name)
            # print( branch_numb ,branch_name)

            # 初始化分店資訊
            branch_info = {
                "name": branch_name,
                "is_main": False,   # 總倉標記
                "is_active": False, # 預設未活躍
                "doc_num": None,    # 最近一張單號
                "sale_count": 0,
                "ship_count": 0,
                "repair_count": 0,
            }


            
            
            current_date = date.today()
            yymm = f"{str(current_date.year)[2:]}{current_date.month:02d}"  # 取年份後兩位，月補零
            yymmdd = f"{str(current_date.year)[2:]}{current_date.month:02d}{current_date.day:02d}"  # 取年份後兩位，月補零
            # print(yymmdd)


            def count_docs(table, date_col, branch_col="分店編號"):
                sql = f"""
                    SELECT COUNT(*)
                    FROM {table}
                    WHERE {branch_col} = ?
                    AND {date_col} >= ?
                """
                # print(sql)
                cursor3.execute(sql, (row3[0], since_date))  # row3[0] 是分店編號（整數）
                return cursor3.fetchone()[0] or 0

            created_dt = row3[create_idx]  # SQL Server 通常回 datetime/datetime2
            print(created_dt)
            is_new_branch = False
            if created_dt:
                created_date = created_dt.date() if hasattr(created_dt, "date") else created_dt
                is_new_branch = created_date >= since_date
                print("新開店 : ",is_new_branch)

            if is_new_branch:
                # 新店：直接視為活躍（即使 0 單據）
                branch_info["is_active"] = True
                # counts 維持 0，不用打 3 次 count_docs
            else :
                # [檢索三種單據]
                sale_count   = count_docs("銷貨單", "單據日期")
                ship_count   = count_docs("出貨單", "單據日期")
                repair_count = count_docs("維修單", "單據日期")

                branch_info["sale_count"]   = sale_count
                branch_info["ship_count"]   = ship_count
                branch_info["repair_count"] = repair_count

                total_count = sale_count + ship_count + repair_count
                branch_info["is_active"] = total_count > 0

            # print(driver,server,db_name,username,password)
            # conn3 = pyodbc.connect(f'DRIVER={{{driver}}};SERVER={server};DATABASE={db_name};UID={username};PWD={password}')

            # cursor3 = conn3.cursor()
            # cursor3.execute("SELECT 單據編號 FROM 銷貨單")
            # rows4 = cursor3.fetchall()
            # for row4 in reversed(rows4):
            #     document_number=row4[0]
            #     if document_number[1:5]==yymm:
            #         if document_number[7:9] == branch_numb :
            #             print(document_number)
            #             branch_info["is_active"] = True
            #             branch_info["doc_num"] = document_number
            #             break

            # cursor3.execute("SELECT 單據編號 FROM 出貨單")
            # rows4 = cursor3.fetchall()
            # for row4 in reversed(rows4):
            #     document_number=row4[0]
            #     if document_number[1:5]==yymm:
            #         if document_number[7:9] == branch_numb :
            #             print(document_number)
            #             branch_info["is_active"] = True
            #             branch_info["doc_num"] = document_number
            #             break

            # cursor3.execute("SELECT 單據編號 FROM 維修單")
            # rows4 = cursor3.fetchall()
            # for row4 in reversed(rows4):
            #     document_number=row4[0]
            #     if document_number[1:5]==yymm:
            #         if document_number[7:9] == branch_numb :
            #             print(document_number)
            #             branch_info["is_active"] = True
            #             branch_info["doc_num"] = document_number
            #             break

            # 總倉不收費
            if int(main_warehouse_id) == row3[0] :
                print(branch_name,'是總倉')
                branch_info["is_main"] = True
                branch_info["is_active"] = False
            else :
                # 非總倉店家，用於收費
                charge_branch_names.append(branch_name)
                charge_count+=1 # 收費店家數，用於推估到期月

            if branch_info["is_active"]: 
                active_branch_names.append(branch_name)
                active_count+=1  # 活躍店家數，用於扣點

            branches_info.append(branch_info)

        # 判斷需報價
        quote_required=0
        if  active_count >= license_count and online_pay:
            quote_required=1

        # 計算當前月份
        remain_months = license_count // (charge_count or 1)
        # 當前年月
        now = date.today()
        current_ym = now.strftime("%Y%m")
        # 計算到期月份
        due_date = now + relativedelta(months=remain_months)
        due_month = due_date.strftime("%Y/%m")

        receivable=unit_price*charge_months*active_count
        # print("remain_months =", remain_months)
        # print("due_month =", due_month)

        # print(active_branch_names)
        # print(charge_branch_names)
        companies.append({
            "primary_key":primary_key,
            "company_name": db_name,
            "branches_info": branches_info,
            "branches": active_branch_names,  # 過度給generate_quote()的資料
            "license_count": license_count,
            "active_count": active_count,
            "charge_count": charge_count,
            "remain_months":remain_months,
            "due_month":due_month,
            "receivable":receivable, 
            "online_pay":online_pay,
            "quote_required":quote_required,
            "charge_months": charge_months,
            "discount": discount,
            "unit_price":unit_price,
            "bonus_months": bonus_months,
        })

    return companies

# 主程式
if __name__ == "__main__":
    companies_data = get_companies_data()
    for company in companies_data:

        # if company["quote_required"]==1 :
        quote_path = generate_quote(
            company_data=company,
            charge_months=company["charge_months"],
            # bonus_months=company["bonus_months"],
            due_month=company["due_month"],
            price_includes_tax=True,
            unit_price=company["unit_price"],
            template_name="quote_template2.html",  # 或改成 quote_template.html
            output_dir="output_quotes"
        )
        company["quote_path"] = str(quote_path).replace("\\", "/")
        # else :
        #     company["quote_path"] = ""

    # 2) 輸出 JSON —— 作為 SoT 給前端與 API 使用
    Path("companies_payment_data.json").write_text(
        json.dumps(companies_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # # 產出 HTML 儀表板
    # env = Environment(loader=FileSystemLoader("."))
    # template = env.get_template("dashboard_template.html")
    # html_output = template.render(companies=companies_data)
    # Path("dashboard.html").write_text(html_output, encoding="utf-8")
    # print("✅ 已完成 dashboard.html") 
