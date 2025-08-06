from pathlib import Path
from flask import Flask, send_from_directory, abort

app = Flask(__name__)

# 改成你的儲存資料夾；相對路徑或絕對路徑皆可
PDF_DIR = Path("output_quotes")

@app.route("/")
def index():
    """
    列出資料夾內所有 PDF，產生超連結方便點選。
    """
    if not PDF_DIR.exists():
        return "<p>尚未產生任何報價單。</p>"
    links = [
        f'<a href="/quote/{f.name}">{f.name}</a>'
        for f in PDF_DIR.glob("*.pdf")
    ]
    return "<h2>報價單列表</h2>" + "<br>".join(links)

@app.route("/quote/<path:filename>")
def quote(filename):
    """
    直接把指定 PDF 傳給瀏覽器（inline 預覽）。
    若要改成強制下載可把 as_attachment=True。
    """
    pdf_path = PDF_DIR / filename
    if pdf_path.exists() and pdf_path.suffix.lower() == ".pdf":
        return send_from_directory(PDF_DIR, filename, as_attachment=False)
    return abort(404)

if __name__ == "__main__":
    # Flask 監聽 5000，對應到你啟動的 ngrok 隧道
    app.run(port=5000, debug=True)