# 守播 LiveGuard AI · 顶级开发命令
# Use:  make help

.PHONY: help install dev test lint format models bench seed up down clean spec-status

PYTHON ?= python3
PNPM   ?= pnpm

help:                    ## 显示所有命令
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'

install:                 ## 安装 Python + Node 依赖
	$(PYTHON) -m pip install -e ".[dev]"
	$(PYTHON) -m pip install -e algo
	$(PYTHON) -m pip install -e backend
	$(PYTHON) -m pip install -e models
	$(PYTHON) -m pip install -e edge/python
	$(PYTHON) -m pip install -e notify
	$(PNPM) install

dev:                     ## docker-compose 启动本地全栈
	docker compose -f infra/docker-compose.yml up -d

down:                    ## 关闭本地全栈
	docker compose -f infra/docker-compose.yml down

test:                    ## 单元测试 + 覆盖率
	$(PYTHON) -m pytest -q --cov

lint:                    ## 代码风格检查
	$(PYTHON) -m ruff check .
	$(PYTHON) -m mypy algo backend models notify edge/python || true
	$(PNPM) lint

format:                  ## 自动格式化
	$(PYTHON) -m ruff check --fix .
	$(PYTHON) -m black .
	$(PNPM) format

models:                  ## 跑全部商业/技术模型，输出 outputs/
	cd models && $(PYTHON) run_all.py

bench:                   ## 算法基准复现
	$(PYTHON) -m liveguard_algo.benchmarks.run_bench

seed:                    ## 数据库种子数据
	$(PYTHON) -m backend.scripts.seed

clean:                   ## 清理构建产物
	find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache -o -name .ruff_cache \) -exec rm -rf {} +
	rm -rf dist build htmlcov .coverage

spec-status:             ## 显示 Kiro spec 任务进度
	@$(PYTHON) tools/spec_status.py
