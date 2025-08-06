from flask import Flask, send_from_directory

app = Flask(__name__)

# 首頁 → 顯示 dashboard.html
@app.route("/")
def index():
    return send_from_directory(".", "dashboard.html")

# 提供報價單 PDF 檔案
@app.route("/output_quotes/<path:filename>")
def quote_file(filename):
    return send_from_directory("output_quotes", filename)

if __name__ == "__main__":
    app.run(debug=True)