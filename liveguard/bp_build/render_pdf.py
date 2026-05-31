"""
render_pdf.py
=============

把 `守播LiveGuard_商业计划书_v2.0.md` 渲染为同名 .pdf：

  1. pandoc → 自包含 HTML body（含 TOC）
  2. 注入 cover.html + style.css，并把图片相对路径转为 file:// 绝对路径
  3. Chromium 内核（Edge / Chrome）--headless --print-to-pdf 输出 A4 PDF

Windows 友好：自动探测 msedge.exe / chrome.exe。
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent.parent.parent
BUILD = ROOT / "liveguard" / "bp_build"
MD = ROOT / "守播LiveGuard_商业计划书_v2.0.md"
COVER = BUILD / "cover.html"
CSS = BUILD / "style.css"
HTML = BUILD / "_bp.html"
PDF = ROOT / "守播LiveGuard_商业计划书_v2.0.pdf"


def find_browser() -> str:
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    for name in ("msedge", "chrome", "google-chrome", "chromium"):
        p = shutil.which(name)
        if p:
            return p
    raise SystemExit("未找到 Edge / Chrome 可执行文件，无法生成 PDF。")


def md_to_html_body() -> str:
    cmd = [
        "pandoc", str(MD),
        "--from", "markdown+pipe_tables+task_lists",
        "--to", "html5", "--toc", "--toc-depth=2", "--no-highlight",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=str(ROOT))
    if res.returncode != 0:
        print("STDERR:", res.stderr)
        raise SystemExit(res.returncode)
    return res.stdout


def fix_image_paths(body: str) -> str:
    """把 <img src="liveguard/docs/..."> 转为 file:// 绝对路径，确保 headless 渲染加载本地图片。"""
    def repl(m):
        src = m.group(1)
        if src.startswith(("http", "file:", "data:")):
            return m.group(0)
        abs_path = (ROOT / src).resolve()
        uri = abs_path.as_uri()
        return f'src="{uri}"'
    return re.sub(r'src="([^"]+)"', repl, body)


def assemble_html(body: str) -> str:
    cover_html = COVER.read_text(encoding="utf-8")
    css_text = CSS.read_text(encoding="utf-8")
    body = body.replace('<nav id="TOC" role="doc-toc">', '<nav id="TOC" class="toc">')
    body = fix_image_paths(body)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>守播 LiveGuard AI · 商业计划书 v2.0</title>
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
    browser = find_browser()
    print(f"── 使用浏览器内核：{browser} ──")
    body = md_to_html_body()
    html = assemble_html(body)
    HTML.write_text(html, encoding="utf-8")
    print(f"✓ HTML 写入 {HTML}  大小 {HTML.stat().st_size/1024:.1f} KB")

    if PDF.exists():
        PDF.unlink()

    user_data_dir = tempfile.mkdtemp(prefix="edge_pdf_")
    try:
        cmd = [
            browser, "--headless=new", "--disable-gpu",
            "--no-sandbox", "--disable-dev-shm-usage",
            "--no-first-run", "--no-default-browser-check",
            f"--user-data-dir={user_data_dir}",
            "--no-pdf-header-footer",
            "--print-to-pdf=" + str(PDF),
            "--virtual-time-budget=20000",
            "--run-all-compositor-stages-before-draw",
            "--hide-scrollbars",
            HTML.as_uri(),
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.time() + 180
        last_size = 0
        stable = 0
        while time.time() < deadline:
            time.sleep(2)
            if PDF.exists():
                size = PDF.stat().st_size
                if size > 1000 and size == last_size:
                    stable += 1
                    if stable >= 3:
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
        raise SystemExit("PDF 生成失败（文件缺失或过小）")
    print(f"✓ PDF 写入 {PDF}  大小 {PDF.stat().st_size/1024/1024:.2f} MB")


if __name__ == "__main__":
    html_to_pdf()
