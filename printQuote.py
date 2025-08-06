import pdfkit
import os
import base64
from jinja2 import Environment, FileSystemLoader

# 確保輸出資料夾存在
os.makedirs("output_pdfs", exist_ok=True)

# 讀取 logo.png 並轉為 Base64
logo_path = "logo.png"
if not os.path.exists(logo_path):
    raise FileNotFoundError("logo.png 不存在，請確認檔案路徑")
with open(logo_path, "rb") as f:
    logo_base64 = base64.b64encode(f.read()).decode("utf-8")

# 設定 Jinja2 模板環境
env = Environment(loader=FileSystemLoader("."))
template = env.get_template("invoice_template.html")

# 範例數據（包含兩筆資料）
items = [
    {
        "item": "POS月租費 布魯斯通訊 頭份尚順",
        "description": "2,600元*1月=2,600元 (2025/6/1~2025/6/30)",
        "quantity": 1,
        "amount": 2600
    },
    {
        "item": "POS月租費 布魯斯通訊 竹南立達",
        "description": "2,600元*1月=2,600元 (2025/6/1~2025/6/30)",
        "quantity": 1,
        "amount": 2600
    }
]

# 計算總金額和營業稅
total_amount = sum(item["amount"] for item in items)  # $5,200
tax_amount = int(total_amount * 0.05)  # $260
total_amount_with_tax = total_amount + tax_amount  # $5,460
# 格式化金額（千位分隔符）
total_amount_with_tax_formatted = f"{total_amount_with_tax:,}"

# 數據
data = {
    "logo_base64": logo_base64,
    "invoice_number": "INV-20250601-001",
    "invoice_date": "2025/5/21",
    "customer_name": "布魯斯通訊",
    "items": items,
    "tax_amount": tax_amount,
    "total_amount_with_tax": total_amount_with_tax_formatted,
    "due_date": "2025/5/31",
    "account_info": {
        "name": "謝彥偉",
        "account_number": "0750-968-031436",
        "bank": "808 玉山銀行-竹北分行",
        "contact_name": "謝彥偉",
        "contact_phone": "0913-201-320"
    }
}

# 渲染 HTML
html_content = template.render(**data)

# pdfkit 配置
options = {
    "encoding": "UTF-8",
    "enable-local-file-access": None,
    "dpi": 300,
    "no-stop-slow-scripts": None,
    "quiet": None,
    "page-size": "A4",
    "margin-top": "20mm",
    "margin-bottom": "20mm",
    "margin-left": "20mm",
    "margin-right": "20mm"
}
wkhtmltopdf_path = "C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe"
if not os.path.exists(wkhtmltopdf_path):
    raise FileNotFoundError("wkhtmltopdf.exe 不存在，請確認路徑")
config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

# 轉為 PDF
pdfkit.from_string(html_content, "output_pdfs/sample_invoice.pdf", options=options, configuration=config)

print("PDF 已生成：output_pdfs/sample_invoice.pdf")