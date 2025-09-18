from flask import Flask, send_from_directory, request, jsonify
from pathlib import Path
from quote_generator import generate_quote
import time
import json
import subprocess, sys

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
# app = Flask(__name__)
app.json.ensure_ascii = False  # 關鍵：不要把中文轉成 \uXXXX
app.config["JSONIFY_MIMETYPE"] = "application/json; charset=utf-8"

# 首頁 → 顯示 dashboard.html
@app.route("/")
def index():
    return send_from_directory(".", "dashboard2.html")

# 首頁 → 顯示 dashboard.html
@app.route("/liff")
def liff():
    return send_from_directory(".", "liffPage.html")

# 提供報價單 PDF 檔案
@app.route("/output_quotes/<path:filename>")
def quote_file(filename):
    return send_from_directory("output_quotes", filename)


@app.route("/api/refresh_companies")
def refresh_companies():
    print('run get_companies_payment_data.py')
    subprocess.Popen([sys.executable, "get_companies_payment_data.py"])
    return jsonify(ok=True)
    # try:
    #     # 呼叫同目錄下的 get_companies_payment_data.py
    #     res = subprocess.run(
    #         [sys.executable, "get_companies_payment_data.py"],
    #         capture_output=True,
    #         text=True
    #     )
    #     if res.returncode == 0:
    #         return jsonify(ok=True, message=res.stdout.strip())
    #     else:
    #         return jsonify(ok=False, error=res.stderr.strip()), 500
    # except Exception as e:
    #     return jsonify(ok=False, error=str(e)), 500

# ===== 新增：讀取 companies_payment_data.json 並依公司名稱回傳一筆資料 =====
DATA_FILE = Path("companies_payment_data.json")

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

@app.get("/api/companies")
def list_companies():
    return jsonify(ok=True, data=load_companies())

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


def _is_empty_like(v):
    if v is None: 
        return True
    if isinstance(v, str) and v.strip().lower() in ("", "null", "none", "undefined"):
        return True
    return False

def _get_arg_or(default, key):
    v = request.args.get(key)
    return default if _is_empty_like(v) else v

def _to_int_or(v, default):
    if _is_empty_like(v):
        return default
    try:
        return int(v)
    except:
        return default

def _to_bool_or(v, default):
    if _is_empty_like(v):
        return default
    s = str(v).strip().lower()
    if s in ("1","true","t","yes","y","on"):  return True
    if s in ("0","false","f","no","n","off"): return False
    return default



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

    # 是否帶了任何重產參數（多包含 due_month）
    wants_regen = any(
        k in request.args 
        for k in ("charge_months", "price_includes_tax", "unit_price", "template_name", "due_month")
    ) 

    # 若沒有帶重產參數，且 JSON 內已經有現成 quote_path，就直接回傳
    if not wants_regen:
        qp = c.get("quote_path")
        if qp:
            return jsonify(ok=True, quote_path=qp)
        # return jsonify(ok=False, error="no existing quote"), 404

    # # 需要重產 → 參數（未提供就用 JSON 內預設）
    # charge_months     = int(request.args.get("charge_months",   c.get("charge_months", 6)))
    # price_includes_tx = parse_bool(request.args.get("price_includes_tax"), True)
    # unit_price        = int(request.args.get("unit_price",      c.get("unit_price", 2600)))
    # template_name     = request.args.get("template_name", "quote_template2.html")
    # due_month     = request.args.get("due_month")  # 允許為 None

    # 需要重產 → 參數（null/"" 一律當未提供，回退到 JSON 內預設）
    charge_months     = _to_int_or(_get_arg_or(c.get("charge_months", 6), "charge_months"), c.get("charge_months", 6))
    price_includes_tx = _to_bool_or(_get_arg_or(c.get("price_includes_tax", True), "price_includes_tax"), c.get("price_includes_tax", True))
    unit_price        = _to_int_or(_get_arg_or(c.get("unit_price", 2600), "unit_price"), c.get("unit_price", 2600))
    template_name     = _get_arg_or("quote_template2.html", "template_name")
    due_month         = _get_arg_or(None, "due_month")  # "null"→None

    # 正規化 due_month（如果有給）
    # due_month = None
    # if due_month_raw:
    #     print(due_month_raw)
    #     try:
    #         y, m = map(int, due_month_raw.split("/"))
    #         # 驗證年月
    #         _ = date(y, m, 1)
    #         due_month = f"{y:04d}/{m:02d}"
    #     except Exception:
    #         return jsonify(ok=False, error="invalid 'due_month', expected YYYY/MM"), 400

    branches = c.get("branches") or []
    # if not branches:
    #     return jsonify(ok=False, error="no branches to bill"), 400

    pdf_path = generate_quote(
        company_data={"company_name": c["company_name"], "branches": branches},
        due_month=due_month,
        charge_months=charge_months,
        price_includes_tax=price_includes_tx,
        unit_price=unit_price,
        template_name=template_name,
        output_dir="output_quotes",
    )

    return jsonify(ok=True, quote_path=str(pdf_path).replace("\\","/"))    

if __name__ == "__main__":
    app.run(debug=True)