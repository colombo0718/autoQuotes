from flask import Flask, send_from_directory, request, jsonify
from pathlib import Path
from quote_generator import generate_quote
import time
import json

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

# 首頁 → 顯示 dashboard.html
@app.route("/")
def index():
    return send_from_directory(".", "dashboard.html")

# 提供報價單 PDF 檔案
@app.route("/output_quotes/<path:filename>")
def quote_file(filename):
    return send_from_directory("output_quotes", filename)

# ===== 新增：讀取 companies_data.json 並依公司名稱回傳一筆資料 =====
DATA_FILE = Path("companies_data.json")

def load_companies():
    if not DATA_FILE.exists():
        return []
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))

def find_by_name(data, name: str):
    # 先精準
    for c in data:
        if c.get("company_name") == name:
            return c
    # 再模糊（回第一筆）
    for c in data:
        if name in c.get("company_name", ""):
            return c
    return None

def parse_bool(val, default=True):
    if val is None:
        return default
    s = str(val).strip().lower()
    return s in ("1", "true", "t", "yes", "y", "on")

@app.get("/api/company")
def get_company_by_name():
    """
    用法：
      GET /api/company?name=太子
    回傳：
      { "ok": true, "data": {...公司資料...} }
      找不到會回 404：
      { "ok": false, "error": "not found" } 
    """
    name = (request.args.get("name") or "").strip()
    if not name:
        return jsonify(ok=False, error="missing 'name'"), 400

    companies = load_companies()
    # 先找「完全相等」
    for c in companies:
        if c.get("company_name") == name:
            return jsonify(ok=True, data=c), 200

    # 再嘗試「包含關鍵字」：若多筆，回第一筆（保持簡單）
    partial = [c for c in companies if name in c.get("company_name", "")]
    if partial:
        return jsonify(ok=True, data=partial[0], note="partial match"), 200

    return jsonify(ok=False, error="not found"), 404


@app.get("/api/quote")
def get_or_regenerate_quote():
    """
    1) 只取現有：GET /api/quote?name=太子
       → 回傳現有 quote_path（若沒有就 404）

    2) 覆蓋參數重產：GET /api/quote?name=太子&charge_months=12&price_includes_tax=true&unit_price=2400
       可用參數：charge_months, price_includes_tax, unit_price, template_name
       → 現場重產並只回新路徑（不寫回 JSON）
    """
    name = (request.args.get("name") or "").strip()
    if not name:
        return jsonify(ok=False, error="missing 'name'"), 400

    data = load_companies()
    c = find_by_name(data, name)
    if not c:
        return jsonify(ok=False, error="company not found"), 404

    wants_regen = any(k in request.args for k in ("charge_months","price_includes_tax","unit_price","template_name"))
    if not wants_regen:
        qp = c.get("quote_path")
        if qp:
            return jsonify(ok=True, quote_path=qp)
        return jsonify(ok=False, error="no existing quote"), 404

    # 需要重產 → 參數（未提供就用 JSON 內預設）
    period_months     = int(request.args.get("charge_months",   c.get("charge_months", 6)))
    price_includes_tx = parse_bool(request.args.get("price_includes_tax"), True)
    unit_price        = int(request.args.get("unit_price",      c.get("unit_price", 2600)))
    template_name     = request.args.get("template_name", "quote_template2.html")

    branches = c.get("branches") or []
    if not branches:
        return jsonify(ok=False, error="no branches to bill"), 400

    pdf_path = generate_quote(
        company_data={"company_name": c["company_name"], "branches": branches},
        period_months=period_months,
        price_includes_tax=price_includes_tx,
        unit_price=unit_price,
        template_name=template_name,
        output_dir="output_quotes",
    )

    return jsonify(ok=True, quote_path=str(pdf_path).replace("\\","/"))    

if __name__ == "__main__":
    app.run(debug=True)