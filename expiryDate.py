import pyodbc
import csv
from datetime import date, datetime
from pathlib import Path

# Database connection settings
server = 'www.cwsoft.com.tw,1226'
username = 'Pos'
password = 'sql2wsxCFT^3edc'
driver = 'ODBC Driver 17 for SQL Server'

# Function to mimic dbo.getsix (assuming it returns YYYYMM format)
def getsix(dt):
    return dt.strftime('%Y%m')

# Connect to 各資料庫設定 database to get database names
database_config = '各資料庫設定'
conn_str_config = f'DRIVER={{{driver}}};SERVER={server};DATABASE={database_config};UID={username};PWD={password}'
conn_config = pyodbc.connect(conn_str_config)
cursor_config = conn_config.cursor()

# Get database names excluding system databases and ensuring online billing
cursor_config.execute("""
    SELECT 資料庫名 
    FROM 各資料庫設定.dbo.資料庫設定檔 
    WHERE 資料庫名 NOT IN ('msdb', 'POSConfig', 'POSV3Promo', 'POSV3Shared', '各資料庫設定')
    AND 資料庫名 IN (SELECT 資料庫名 FROM POSConfig.dbo.分店設定檔 WHERE 線上收費=1)
""")
db_names = [row[0] for row in cursor_config.fetchall()]
cursor_config.close()
conn_config.close()

# Initialize data list for temporary table
dt = []

# Get current date in YYYYMM format for filtering
current_date = getsix(date.today().replace(day=1))

# Iterate through each database
for db_name in db_names:
    try:
        # Connect to the specific database
        conn_str_db = f'DRIVER={{{driver}}};SERVER={server};DATABASE={db_name};UID={username};PWD={password}'
        conn_db = pyodbc.connect(conn_str_db)
        cursor_db = conn_db.cursor()

        # Query to get active branches, expiration date, and admin management
        query = f"""
        SELECT 
            '{db_name}' AS 資料庫名,
            COUNT(DISTINCT 分店編號) AS 有使用的分店,
            (SELECT MAX(線上付款_停用時間) 
             FROM {db_name}.dbo.分店 
             WHERE 是否已收店=0 AND 線上付款_停用=0) AS 目前到期日,
            (SELECT COUNT(*) 
             FROM (
                SELECT 1 AS a 
                FROM {db_name}.dbo.基本設定 
                WHERE 名稱='行政管理' AND 設定值<>''
                UNION 
                SELECT 1 AS a 
                FROM {db_name}.dbo.基本設定 
                WHERE 名稱='行政管理v3' AND 設定值<>0
             ) a) AS 行政管理
        FROM (
            SELECT 分店編號 
            FROM {db_name}.dbo.銷貨單 
            WHERE 單據編號>'P{current_date}'
            UNION 
            SELECT 分店編號 
            FROM {db_name}.dbo.出貨單 
            WHERE 單據編號>'E{current_date}'
        ) a 
        WHERE 分店編號<>(SELECT TOP 1 設定值 
                           FROM {db_name}.dbo.基本設定 
                           WHERE 名稱='總倉編號')
        """
        cursor_db.execute(query)
        dt.append(cursor_db.fetchone())

        cursor_db.close()
        conn_db.close()
    except Exception as e:
        print(f"Error processing database {db_name}: {e}")

# Connect to POSConfig and POSV3shared for final report
conn_posconfig = pyodbc.connect(f'DRIVER={{{driver}}};SERVER={server};DATABASE=POSConfig;UID={username};PWD={password}')
cursor_posconfig = conn_posconfig.cursor()

conn_posv3shared = pyodbc.connect(f'DRIVER={{{driver}}};SERVER={server};DATABASE=POSV3shared;UID={username};PWD={password}')
cursor_posv3shared = conn_posv3shared.cursor()

# Final query to generate report
final_data = []
for row in dt:
    db_name, active_branches, expiry_date, admin_mgmt = row
    if expiry_date is None:
        expiry_date = datetime.now()  # Fallback to current date if None
    query_final = f"""
    SELECT 
        a.主索引 AS 客戶編號,
        a.公司名稱,
        b.授權數量 AS POS點數,
        {active_branches} AS 有使用的分店,
        CASE {active_branches}
            WHEN 0 THEN b.授權數量
            ELSE FLOOR(b.授權數量 / {active_branches})
        END AS 可使用月份,
        CONVERT(nvarchar(30), DATEADD(MONTH, 
            CASE {active_branches}
                WHEN 0 THEN b.授權數量
                ELSE FLOOR(b.授權數量 / {active_branches})
            END, '{expiry_date}'), 111) AS 預計到期日,
        {admin_mgmt} AS 行政管理
    FROM POSConfig.dbo.分店設定檔 a
    JOIN (
        SELECT 分店設定檔主索引, 授權數量 
        FROM POSV3shared.dbo.線上付款_已購買授權 
        WHERE 授權類別=1
    ) b ON a.主索引 = b.分店設定檔主索引
    WHERE a.停用 = 0 
    AND a.線上收費 = 1 
    AND a.資料庫名 = '{db_name}'
    """
    cursor_posconfig.execute(query_final)
    final_data.extend(cursor_posconfig.fetchall())

# Sort by projected expiry date and company name
final_data.sort(key=lambda x: (x[5], x[1]))

# Write to CSV
output_path = Path("customer_auth_report.csv")
with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
    writer = csv.writer(csvfile)
    # Write header
    writer.writerow(['客戶編號', '公司名稱', 'POS點數', '有使用的分店', '可使用月份', '預計到期日', '行政管理'])
    # Write data
    for row in final_data:
        writer.writerow(row)

# Close connections
cursor_posconfig.close()
conn_posconfig.close()
cursor_posv3shared.close()
conn_posv3shared.close()

print(f"Report generated and saved to {output_path}")