"""invoice_generator.py
功能概述
------------------------------------------------------------
- generate_invoice(company_data, …)
  依「公司資料 dict」產生單張 PDF 發票。  
  支援 *含稅 / 未稅*、多月期數、分店(台)數量，並自動以公司名稱命名檔案。

- (選用)CLI 介面  
  直接執行本檔可用指令列快速產生單張發票，方便測試或排程腳本呼叫。

依賴環境
------------------------------------------------------------
1. Python 3.9+
2. 套件: pip install Jinja2 pdfkit
3. wkhtmltopdf
     Windows 預設安裝於：
         C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe
     其他系統請安裝後確定可執行，或以環境變數 WKHTMLTOPDF_PATH 指定路徑。
4. HTML 範本預設放在同路徑下,檔名 invoice_template.html,可自行更換。

函式介面
------------------------------------------------------------
    generate_invoice(
        company_data: dict,                   # 公司資料（見上）
        output_dir: str | pathlib.Path = "output_pdfs",
        unit_price: int = 2600,               # 每月單價（預設未稅）
        period_months: int = 6,               # 期繳月數；6=半年、12=一年…
        price_includes_tax: bool = False,     # True 表示 unit_price 已含稅
        tax_rate: float = 0.05,               # 稅率；台灣營業稅 5%
        template_name: str = "invoice_template.html",
    ) -> pathlib.Path                         # 傳回產出的 PDF 檔案路徑。

快速範例（程式內呼叫）
------------------------------------------------------------
    from invoice_generator import generate_invoice

    company = {
        "company_name": "甲公司",
        "branches": ["台北店", "台中店"],
    }

    pdf_path = generate_invoice(
        company_data=company,
        unit_price=2600,
        period_months=6,
        price_includes_tax=False,
    )

    print(f"PDF 已輸出：{pdf_path}")
"""

import os
import re
import base64
from decimal import Decimal, ROUND_HALF_UP
import calendar
from datetime import date, datetime, timedelta
from pathlib import Path

import pdfkit
from jinja2 import Environment, FileSystemLoader

# ────────────────────────────────────────────────
# 共用工具
# ────────────────────────────────────────────────

def round0(num):
    """銀行家四捨五入到整數 (避免浮點誤差)"""
    return int(Decimal(num).quantize(0, ROUND_HALF_UP))


def thousands(n: int) -> str:
    """千分位格式化"""
    return f"{n:,}"


# ────────────────────────────────────────────────
# 核心：產生單一公司 PDF
# ────────────────────────────────────────────────

def generate_invoice(
    company_data: dict,
    output_dir: str | Path = "output_pdfs",
    unit_price: int = 2600,
    period_months: int = 6,
    price_includes_tax: bool = False,
    tax_rate: float = 0.05,
    template_name: str = "invoice_template.html",
) -> Path:
    """依公司資料產生一份 PDF。回傳 PDF 檔路徑。"""

    # 1) 準備輸出資料夾
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2) Base‑64 Logo
    logo_path = Path("logo.png")
    if not logo_path.exists():
        raise FileNotFoundError("找不到 logo.png，請確認路徑")
    logo_base64 = base64.b64encode(logo_path.read_bytes()).decode()

    # 3) 解析公司資料
    company_name: str = company_data["company_name"]
    branches: list[str] = company_data["branches"]
    branch_qty = len(branches)

    # 4) 金額區
    unit_price = 2600                                  # 未稅單價
    subtotal    = unit_price * branch_qty * period_months   # 未稅小計
    tax_amount  = round0(subtotal * tax_rate)                 # 5% 稅額
    if price_includes_tax:
        # 含稅 
        total_gross = subtotal + tax_amount                       # 含稅總價
    else:
        # 未稅
        total_gross = subtotal

    show_unit = unit_price  # 說明欄仍顯示 2,600    

    # 5) 期間文字（從當月起算 period_months）
    def add_months(d: date, n: int) -> date:
        """回傳 d 往後 n 個月『同一天』，若該月天數不足則退到月底。"""
        # 先算目標年月
        y, m = divmod(d.year * 12 + d.month - 1 + n, 12)
        y += 0
        m += 1
        # 嘗試同一天；若溢出就退到月底
        try:
            return d.replace(year=y, month=m)
        except ValueError:
            # 例如 3/31 +1 月 → 4/31 無效，改成 4/30
            return (date(y, m, 1) + timedelta(days=31)).replace(day=1) - timedelta(days=1)

    # 5) 期間文字 —— 從「次月 1 號」起算 period_months
    today = date.today()
    start_date = add_months(today.replace(day=1), 1)           # 下個月第一天
    period_end = add_months(start_date, period_months) - timedelta(days=1)
    period_text = f"{start_date:%Y/%m/%d}–{period_end:%Y/%m/%d}"

    last_day = calendar.monthrange(today.year, today.month)[1]  # 本月天數
    due_date = date(today.year, today.month, last_day).strftime("%Y/%m/%d")

    # 6) items 列表
    items = [
        {
            "item": f"POS 月租費 {company_name} {branch}",
            "description": f"{thousands(show_unit)} 元 ×{period_months} 月 ({period_text})",
            "quantity": 1,
            "amount": thousands(round0(show_unit * period_months)),
        }
        for branch in branches
    ]

    # 7) 帳戶資訊：含稅用公司帳戶，未稅用個人帳戶
    if price_includes_tax:
        account_info = {
            "name": "全葳軟體資訊有限公司",
            "account_number": "0886-940-022172",
            "bank": "808 玉山銀行-林口分行",
            "contact_name": "謝彥偉",
            "contact_phone": "0913-201-320",
        }
    else:
        account_info = {
            "name": "謝彥偉",
            "account_number": "0750-968-031436",
            "bank": "808 玉山銀行-竹北分行",
            "contact_name": "謝彥偉",
            "contact_phone": "0913-201-320",
        }


    # 8) Jinja2 渲染
    # template_name = "invoice_template_含稅.html" if price_includes_tax else "invoice_template_未稅.html"
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template(template_name)
    invoice_date = date.today().strftime("%Y/%m/%d")
    invoice_number = f"INV-{invoice_date.replace('/', '')}-{re.sub(r'[^\w-]', '', company_name)}"

    html = template.render(
        logo_base64=logo_base64,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        customer_name=company_name,
        show_tax=price_includes_tax,
        items=items,
        tax_amount=thousands(tax_amount),
        total_amount_with_tax=thousands(total_gross),
        due_date=due_date,
        account_info=account_info,
    )

    # 9) PDF 生成
    wk_path = r"C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe"
    if not Path(wk_path).exists():
        raise FileNotFoundError("wkhtmltopdf.exe 不存在，請確認路徑")
    config = pdfkit.configuration(wkhtmltopdf=wk_path)
    options = {
        "encoding": "UTF-8",
        "enable-local-file-access": None,
        "quiet": None,
        "page-size": "A4",
        "dpi": 300,
        "margin-top": "20mm",
        "margin-bottom": "20mm",
        "margin-left": "20mm",
        "margin-right": "20mm",
    }

    tax_flag = "含稅" if price_includes_tax else "未稅"
    safe_name = re.sub(r"[^\w-]", "_", company_name)
    output_file = output_dir / f"invoice_{safe_name}_{invoice_date.replace('/', '')}_{tax_flag}.pdf"
    pdfkit.from_string(html, str(output_file), options=options, configuration=config)

    return output_file


# ────────────────────────────────────────────────
# CLI 測試
# ────────────────────────────────────────────────
if __name__ == "__main__":
    sample_companies = [
        {
            "company_name": "昶詠",
            "branches": ["遠傳民生二店"],
            "license_count": 0,
            "payment_plan": 1,  # 月繳
        },
        # 更多公司...
    ]

    generate_invoice(sample_companies)
