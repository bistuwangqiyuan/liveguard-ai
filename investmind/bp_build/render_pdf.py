"""
render_pdf.py
=============

把 `投智云InvestMind_商业计划书_v1.0.md` 渲染为同名 .pdf：

  1. pandoc → 自包含 HTML（含 TOC）
  2. 注入 cover.html + style.css
  3. Chrome --headless --print-to-pdf 输出 A4 PDF（中文友好）
"""

from __future__ import annotations
import re
import subprocess
import shutil
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
BUILD = ROOT / "investmind" / "bp_build"
MD = ROOT / "投智云InvestMind_商业计划书_v1.0.md"
COVER = BUILD / "cover.html"
CSS = BUILD / "style.css"
HTML = BUILD / "_bp.html"
PDF = ROOT / "投智云InvestMind_商业计划书_v1.0.pdf"


def md_to_html_body() -> str:
    """pandoc 渲染 markdown → HTML body（无包装）。"""
    cmd = [
        "pandoc",
        str(MD),
        "--from", "markdown+pipe_tables+task_lists",
        "--to", "html5",
        "--toc", "--toc-depth=2",
        "--no-highlight",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    if res.returncode != 0:
        print("STDERR:", res.stderr)
        raise SystemExit(res.returncode)
    return res.stdout


def assemble_html(body: str) -> str:
    cover_html = COVER.read_text(encoding="utf-8")
    css_text = CSS.read_text(encoding="utf-8")

    # pandoc 默认 toc class，调整为我们的样式
    body = body.replace('<nav id="TOC" role="doc-toc">', '<nav id="TOC" class="toc">')

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>投智云 InvestMind AI · 商业计划书 v1.0</title>
<style>
{css_text}
</style>
</head>
<body>
{cover_html}
{body}
</body>
</html>"""


def html_to_pdf():
    body = md_to_html_body()
    html = assemble_html(body)
    HTML.write_text(html, encoding="utf-8")
    print(f"✓ HTML 写入 {HTML}  大小 {HTML.stat().st_size/1024:.1f} KB")

    if PDF.exists():
        PDF.unlink()

    user_data_dir = tempfile.mkdtemp(prefix="chrome_pdf_")
    try:
        cmd = [
            "google-chrome",
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--disable-features=DBus,VizDisplayCompositor",
            "--disable-extensions",
            "--disable-background-networking",
            "--no-default-browser-check",
            "--no-first-run",
            f"--user-data-dir={user_data_dir}",
            "--no-pdf-header-footer",
            "--print-to-pdf=" + str(PDF),
            "--print-to-pdf-no-header",
            "--virtual-time-budget=15000",
            "--run-all-compositor-stages-before-draw",
            "--hide-scrollbars",
            "file://" + str(HTML),
        ]
        print("Chrome:", " ".join(cmd[:2]), "...", str(HTML))
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        import time
        deadline = time.time() + 180
        last_size = 0
        stable_count = 0
        while time.time() < deadline:
            time.sleep(2)
            if PDF.exists():
                size = PDF.stat().st_size
                if size > 1000 and size == last_size:
                    stable_count += 1
                    if stable_count >= 3:
                        break
                last_size = size

        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)
    finally:
        shutil.rmtree(user_data_dir, ignore_errors=True)

    if not PDF.exists() or PDF.stat().st_size < 50_000:
        raise SystemExit("PDF generation failed (file missing or too small)")

    print(f"✓ PDF 写入 {PDF}  大小 {PDF.stat().st_size/1024/1024:.2f} MB")


if __name__ == "__main__":
    html_to_pdf()
