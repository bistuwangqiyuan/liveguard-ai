# liveguard-algo · 多模态算法引擎

> 守播 LiveGuard AI 的算法核心 — 边缘 + 云端通用。
> 实现 Requirements §3 (REQ-ALGO-001..008)、Design §5–§6 全部能力。

## 设计要点

- **可解释决策** — 决策融合采用 DFSM（确定性有限状态机），每一次状态转移记录贡献信号。
- **多模态投票** — face/person/Re-ID/liveness/action/audio 6 路加权融合。
- **可插拔模型** — `runtime/registry.py` 注册器；ONNXRuntime 多 EP（CPU/CUDA/NPU）。
- **零依赖默认运行** — 测试 / Demo 场景下使用 `MockDetector`，无需下载 GB 级模型权重即可端到端跑通。
- **生产权重单独发布** — 真实推理需从内部 OCI 仓库拉取 `liveguard/weights:v1.x`。

## 快速开始

```bash
pip install -e ".[inference,audio]"

# 状态机 demo（无需模型权重）
python -m liveguard_algo.demos.dfsm_demo

# 模拟"主播离开 65s → 告警"全链路
python -m liveguard_algo.demos.offline_simulator --duration 70 --absence-start 5

# 算法基准（产出 BP §4.4 KPI 表）
python -m liveguard_algo.benchmarks.run_bench
```

## 模块

| 子包 | 用途 | Trace |
|------|------|-------|
| `runtime/` | ONNXRuntime 包装、模型注册表 | design §5.1 |
| `face/` | 人脸检测（SCRFD / RetinaFace） | REQ-ALGO-001 |
| `person/` | 人形检测 + ByteTrack | REQ-ALGO-002 |
| `reid/` | OSNet 重识别 | REQ-ALGO-003 |
| `liveness/` | Silent-FAS + Deepfake | REQ-ALGO-004 |
| `action/` | VideoMAE 行为识别 | REQ-ALGO-005 |
| `audio/` | Silero VAD + ECAPA-TDNN | REQ-ALGO-006 |
| `fusion/` | 决策融合 DFSM + 反作弊子状态机 | REQ-ALGO-007, REQ-SYS-004 |
| `pipelines/` | 端到端 pipeline | design §5.2-§5.3 |
| `benchmarks/` | 一键基准复现 | design §20.3 |
| `demos/` | 不依赖模型权重的演示脚本 | — |
| `tests/` | 单元 + 集成测试 | — |

## 测试覆盖目标

`pytest --cov` ≥ 85%（CI 强制）。

## 许可证

Apache-2.0；微调权重附带各自的许可证（见 `weights/LICENSE.txt`）。
