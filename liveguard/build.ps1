# build.ps1 — 守播 LiveGuard 商业计划书一键构建（Windows / PowerShell）
#
# 用法：
#   cd liveguard
#   ./build.ps1            # 全流程：模型 → 拼装 → DOCX → PDF
#   ./build.ps1 models     # 仅跑 16 个 Python 模型
#   ./build.ps1 docx       # 仅渲染 DOCX
#   ./build.ps1 pdf        # 仅渲染 PDF

param([string]$target = "all")

$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$models = Join-Path $here "models/python_models"
$build = Join-Path $here "bp_build"

function Run-Models {
  Write-Host "== 运行 16 个 Python 模型 ==" -ForegroundColor Cyan
  Push-Location $models
  python run_all.py
  Pop-Location
}
function Assemble { Write-Host "== 拼装根目录 Markdown ==" -ForegroundColor Cyan; python (Join-Path $build "assemble_md.py") }
function Docx { Assemble; Write-Host "== 渲染 DOCX ==" -ForegroundColor Cyan; python (Join-Path $build "render_docx.py") }
function Pdf  { Assemble; Write-Host "== 渲染 PDF ==" -ForegroundColor Cyan; python (Join-Path $build "render_pdf.py") }

switch ($target) {
  "models" { Run-Models }
  "assemble" { Assemble }
  "docx" { Docx }
  "pdf" { Pdf }
  "all" { Run-Models; Assemble; Docx; Pdf }
  default { Write-Host "未知 target: $target" -ForegroundColor Red }
}
Write-Host "✓ 完成: $target" -ForegroundColor Green
