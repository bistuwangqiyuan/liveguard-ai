# build.ps1 — 守播 LiveGuard 商业计划书 v4.0 一键构建（Windows / PowerShell）
#
# 用法：
#   cd liveguard
#   ./build.ps1            # 全流程：模型 → 拼装 → DOCX（v4.0，仅 DOCX）
#   ./build.ps1 models     # 仅跑 21 个 Python 模型
#   ./build.ps1 docx       # 仅渲染 DOCX

param([string]$target = "all")

$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$models = Join-Path $here "models/python_models"
$build = Join-Path $here "bp_build"

function Run-Models {
  Write-Host "== 运行 21 个 Python 模型 ==" -ForegroundColor Cyan
  Push-Location $models
  python run_all.py
  Pop-Location
}
function Assemble { Write-Host "== 拼装根目录 Markdown (v4.0) ==" -ForegroundColor Cyan; python (Join-Path $build "assemble_md.py") }
function Docx { Assemble; Write-Host "== 渲染 DOCX (v4.0) ==" -ForegroundColor Cyan; python (Join-Path $build "render_docx.py") }

switch ($target) {
  "models" { Run-Models }
  "assemble" { Assemble }
  "docx" { Docx }
  "all" { Run-Models; Assemble; Docx }
  default { Write-Host "Unknown target: $target (models / assemble / docx / all)" -ForegroundColor Red }
}
Write-Host "Done: $target" -ForegroundColor Green
