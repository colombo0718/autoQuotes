"""
quote_peripheral.py

功能概述
------------------------------------------------------------
- generate_peripheral_quote(customer_name, items, …)
  依「客戶名稱＋周邊商品清單」產生 PDF 報價單。

特色：
- 多項周邊商品（紙卷、碳帶…）自動計算小計
- 未滿門檻自動加一筆「運費」項目
- 支援含稅 / 未稅顯示
- 檔名格式：perip_客戶_YYYYMM.pdf
- 使用 quote_template_peri.html 作為綠色系模板
"""

import re
import base64
from decimal import Decimal, ROUND_HALF_UP
import calendar
from datetime import date
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
    """千分位格式化（千分位逗號）"""
    return f"{n:,}"


# ────────────────────────────────────────────────
# 核心：周邊商品報價單
# ────────────────────────────────────────────────

def generate_peripheral_quote(
    customer_name: str,
    items: list[dict],
    output_dir: str | Path = "output_quotes",
    price_includes_tax: bool = False,
    tax_rate: float = 0.05,
    auto_add_shipping: bool = True,
    shipping_threshold: int = 6000,
    shipping_fee: int = 200,
    template_name: str = "quote_template_peri.html",
    file_month: str | None = None,  # 檔名月份，例如 "202512"
) -> Path:
    """
    產生周邊商品報價單 PDF，回傳輸出路徑 Path。

    參數說明
    --------------------------------------------------------
    customer_name: 客戶名稱（例如 "乙希"）
    items: 商品清單 list[dict]，每筆格式：
        {
            "item": "碳帶",
            "unit_price": 75,       # 單價（整數）
            "qty": 10,              # 數量（整數）
            "description": "75 × 10 卷"  # 可省略，會自動生成
        }
    output_dir: PDF 輸出資料夾（預設 "output_quotes"）
    price_includes_tax: 是否顯示含稅總額（影響模板 show_tax 與 tax_amount）
    tax_rate: 稅率（預設 0.05）
    auto_add_shipping: 是否自動判斷運費
    shipping_threshold: 未滿此金額會加運費（預設 6000） 
    shipping_fee: 運費金額（預設 200）
    template_name: 使用的 Jinja2 HTML 模板檔名
    file_month: 檔名用的年月字串 "YYYYMM"，例如 "202512"；
                不給的話就用執行當下的年月。
    """

    # 1) 準備輸出資料夾
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2) Logo → Base64
    logo_path = Path("logo.png")
    if not logo_path.exists():
        raise FileNotFoundError("找不到 logo.png，請放在與程式同一層資料夾")
    logo_base64 = base64.b64encode(logo_path.read_bytes()).decode()

    # 3) 計算所有品項小計
    computed_items = []
    subtotal = 0  # 商品＋運費之前的總額（未稅）

    for row in items:
        unit_price = int(row["unit_price"])
        qty = int(row["qty"])
        line_total = unit_price * qty
        subtotal += line_total

        computed_items.append({
            "item": row["item"],
            "unit_price": thousands(unit_price),
            "quantity": qty,
            "amount": thousands(line_total),
            "description": row.get("description") or f"{unit_price} × {qty}",
        })

    # 4) 自動加運費：小計未滿門檻 → 多加一列「運費」
    if auto_add_shipping and subtotal < shipping_threshold:
        subtotal += shipping_fee
        computed_items.append({
            "item": "運費",
            "unit_price": thousands(shipping_fee),
            "quantity": 1,
            "amount": thousands(shipping_fee),
            "description": f"未滿 {shipping_threshold} 元酌收運費 {shipping_fee} 元",
        })

    # 5) 稅額與總金額
    if price_includes_tax:
        tax_amount_value = round0(subtotal * tax_rate)
    else:
        tax_amount_value = 0

    total_amount = subtotal + tax_amount_value

    # 6) 日期、檔名月份、到期日
    today = date.today()
    quote_date = today.strftime("%Y/%m/%d")

    # 檔名用月份：預設使用今天的年月
    if file_month is None:
        file_month = today.strftime("%Y%m")

    # 解析 file_month 當作基準月，用來決定到期日（該月最後一天）
    try:
        base_year = int(file_month[:4])
        base_month = int(file_month[4:6])
        last_day = calendar.monthrange(base_year, base_month)[1]
        due_date = date(base_year, base_month, last_day).strftime("%Y/%m/%d")
    except Exception:
        # fallback：若 file_month 格式怪怪的，就用本月最後一天
        last_day = calendar.monthrange(today.year, today.month)[1]
        due_date = date(today.year, today.month, last_day).strftime("%Y/%m/%d")

    # 編號：PERI-YYYYMM-客戶縮寫（給內部識別用）
    customer_slug = re.sub(r"[^\w-]", "", customer_name)
    quote_number = f"PERI-{file_month}-{customer_slug or 'CUST'}"

    # 7) 帳戶資訊（沿用你月租邏輯：含稅→公司戶，未稅→個人戶）
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

    # 8) 用 Jinja2 套用 HTML 模板（quote_template_peri.html）
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template(template_name)

    html = template.render(
        logo_base64=logo_base64,
        quote_number=quote_number,
        quote_date=quote_date,
        customer_name=customer_name,
        show_tax=price_includes_tax,
        items=computed_items,
        tax_amount=thousands(tax_amount_value),
        total_amount_with_tax=thousands(total_amount),
        due_date=due_date,
        account_info=account_info,
    )

    # 9) 轉成 PDF
    wk_path = r"C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe"
    if not Path(wk_path).exists():
        raise FileNotFoundError("找不到 wkhtmltopdf.exe，請確認安裝路徑")

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

    # 檔名：perip_乙希_202512.pdf 這種格式
    safe_name = re.sub(r"[^\w-]", "_", customer_name)
    # 新增：依是否含稅決定檔名尾巴
    tax_flag = "含稅" if price_includes_tax else "未稅"
    output_file = output_dir / f"perip_{safe_name}_{file_month}_{tax_flag}.pdf"

    pdfkit.from_string(html, str(output_file), configuration=config, options=options)

    return output_file


# ────────────────────────────────────────────────
# CLI 測試（直接執行本檔）
# ────────────────────────────────────────────────

if __name__ == "__main__":
    # 示範用兩樣商品
    test_items = [
        {"item": "橫一刀紙卷", "unit_price": 130, "qty": 40},
        {"item": "碳帶",       "unit_price": 75,  "qty": 5},
        {"item": "條碼機 TSC ttp-244ce",       "unit_price": 7800,  "qty": 1},
    ]

    pdf_path = generate_peripheral_quote(
        customer_name="乙希",
        items=test_items,
        price_includes_tax=True,
        file_month="202512",              # 檔名會變成 perip_乙希_202512.pdf
        template_name="quote_template_peri.html",
        # template_name="quote_template2.html",
    )

    print("周邊商品報價單已輸出：", pdf_path)
