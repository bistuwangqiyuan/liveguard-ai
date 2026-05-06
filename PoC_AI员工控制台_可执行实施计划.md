# PoC 实施计划：AI 员工 / 数字公司控制台
> 技术栈：**Paperclip**（控制平面） + **Hermes Agent**（运行时） + **assistant-ui/tool-ui**（自研 Web UI 基座） + **Langfuse**（可观测）
>
> 目标：**14 个工程交付物（M0 → M3）**，最终输出一个能演示给客户的、可商业化的 PoC 原型。
>
> 文档使用方式：每节都给「目标 / 验收标准 / 命令 / 关键代码」。每完成一节后回到本文勾掉对应清单。

---

## 0. 总体架构与目录结构

### 0.1 PoC 阶段架构图

```
┌──────────────────────────────────────────────────────────────────┐
│  Browser                                                          │
│  Web UI (Next.js 14 + TS + assistant-ui + tool-ui)               │
│   ├─ /console        → Paperclip 4 视图（Org / Tasks / Cost / Audit）
│   ├─ /run/:runId     → 运行视图（左 Chat 流 + 右 Workspace 标签）
│   └─ /observability  → 嵌 Langfuse iframe（PoC 阶段不自渲染）
└────────────────┬─────────────────────────────────────────────────┘
                 │ HTTPS / SSE
        ┌────────▼────────┐         ┌────────────────────────┐
        │ Web BFF (Node)  │◄────────┤ Paperclip Web UI 包    │
        │ Next.js Route   │         │ (内置在 monorepo)      │
        │ Handlers        │         └────────────────────────┘
        └────────┬────────┘
                 │ REST
        ┌────────▼─────────────────┐
        │ Paperclip Server         │  Node 20+ / TS / SQLite
        │  - Org / Task / Cost     │  http://localhost:3100
        │  - Audit Log             │
        │  - HTTP Adapter          │  → POST 唤醒 Hermes
        └────────┬─────────────────┘
                 │ HTTP Webhook
        ┌────────▼─────────────────┐
        │ Hermes Adapter Bridge    │  Python / FastAPI
        │  - 接收 Paperclip POST   │  http://localhost:8650
        │  - 转 Hermes API 调用    │
        │  - SSE 转发流式输出      │
        │  - OTel 打点 → Langfuse  │
        └────────┬─────────────────┘
                 │ OpenAI-compat HTTP
        ┌────────▼─────────────────┐
        │ Hermes Agent             │  Python 3.11+
        │  - run_agent.py 主循环   │  http://localhost:8642 (API)
        │  - Skills / Memory       │  http://localhost:8644 (Webhook)
        │  - 40+ Tools / MCP       │
        └────────┬─────────────────┘
                 │ Daytona / Docker
        ┌────────▼─────────────────┐
        │ Sandbox（Workspace）     │  本地 Docker（PoC 阶段）
        └──────────────────────────┘

旁路：所有 LLM 调用、工具调用、Token 使用 → Langfuse（http://localhost:3000）
```

### 0.2 Monorepo 目录结构（PoC 阶段建议）

```
ai-staff-console/
├── apps/
│   ├── web/                      # Next.js 14 自研控制台（核心）
│   │   ├── app/
│   │   │   ├── (console)/        # Paperclip 4 视图重做
│   │   │   ├── (run)/[runId]/    # 运行视图
│   │   │   └── api/              # tRPC + SSE 转发
│   │   ├── components/
│   │   │   ├── runtime/          # 运行视图：左 Chat + 右 Workspace
│   │   │   ├── console/          # Org Chart / Task / Cost / Audit
│   │   │   └── ui/               # shadcn / assistant-ui / tool-ui 二开
│   │   └── package.json
│   │
│   └── adapter-bridge/           # Python FastAPI 适配器（核心新增）
│       ├── app/
│       │   ├── main.py           # FastAPI 入口
│       │   ├── paperclip.py      # 接收 Paperclip webhook、回调
│       │   ├── hermes.py         # 调用 Hermes API + SSE
│       │   ├── otel.py           # OpenTelemetry → Langfuse
│       │   └── schemas.py        # pydantic 数据契约
│       ├── pyproject.toml
│       └── Dockerfile
│
├── vendor/                       # 第三方源码 fork（锁版本）
│   ├── paperclip/                # git submodule，锁 v?.?.?
│   └── hermes-agent/             # git submodule，锁 v2026.4.16
│
├── infra/
│   ├── docker-compose.yml        # 一键拉起所有服务
│   ├── langfuse/                 # 自托管 Langfuse 配置
│   └── nginx/                    # 反代（可选）
│
├── scripts/
│   ├── bootstrap.sh              # 一键初始化
│   ├── smoke-test.sh             # 端到端冒烟脚本
│   └── seed-demo.ts              # 灌一个 Demo Agent + Task
│
├── docs/
│   ├── runbook.md
│   └── decisions/                # ADR 架构决策记录
│
├── .env.example
└── README.md
```

---

## 1. M0 — 环境就绪（验证基础链路）

### 1.1 验收标准

- [ ] 本地一个 `make up` 起所有服务，无报错
- [ ] 浏览器能访问：Paperclip UI、Langfuse UI、Hermes API、Adapter Bridge `/health`
- [ ] 所有 vendor 子模块锁定到具体 commit，能离线 build

### 1.2 操作步骤

```bash
# 1. 创建 monorepo
mkdir ai-staff-console && cd ai-staff-console
git init
pnpm init
mkdir -p apps/web apps/adapter-bridge vendor infra/{langfuse,nginx} scripts docs/decisions

# 2. 引入 vendor（锁定 commit，避免上游 break）
git submodule add https://github.com/paperclipai/paperclip vendor/paperclip
git submodule add https://github.com/NousResearch/hermes-agent vendor/hermes-agent
git submodule add https://github.com/langfuse/langfuse vendor/langfuse
( cd vendor/paperclip && git checkout main )       # 之后 pin commit
( cd vendor/hermes-agent && git checkout v2026.4.16 )

# 3. Web 应用初始化
cd apps/web
pnpm dlx create-next-app@latest . --ts --tailwind --app --src-dir --import-alias "@/*"
pnpm dlx shadcn@latest init
pnpm add @assistant-ui/react @assistant-ui/react-markdown @assistant-ui/react-ai-sdk
pnpm add @tanstack/react-query zustand
cd ../..

# 4. Adapter Bridge 初始化（Python）
cd apps/adapter-bridge
python3.11 -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn[standard] httpx pydantic-settings \
            opentelemetry-sdk opentelemetry-instrumentation-fastapi \
            opentelemetry-exporter-otlp openinference-instrumentation-openai
cd ../..

# 5. 起 Langfuse（自托管）
cp vendor/langfuse/docker-compose.yml infra/langfuse/docker-compose.yml
cd infra/langfuse && docker compose up -d
```

### 1.3 关键文件：`infra/docker-compose.yml`

```yaml
version: "3.9"

services:
  paperclip:
    image: node:20-alpine
    working_dir: /app
    volumes: ["../vendor/paperclip:/app"]
    command: sh -c "npm ci && npm run start"
    ports: ["3100:3100"]
    env_file: ../.env

  hermes:
    build:
      context: ../vendor/hermes-agent
      dockerfile: Dockerfile
    environment:
      API_SERVER_ENABLED: "true"
      API_SERVER_KEY: "${HERMES_API_KEY}"
      WEBHOOK_ENABLED: "true"
      WEBHOOK_PORT: "8644"
      WEBHOOK_SECRET: "${HERMES_WEBHOOK_SECRET}"
    ports: ["8642:8642", "8644:8644"]
    volumes: ["hermes-data:/root/.hermes"]

  adapter-bridge:
    build: ../apps/adapter-bridge
    environment:
      PAPERCLIP_API_URL: "http://paperclip:3100"
      PAPERCLIP_API_KEY: "${PAPERCLIP_API_KEY}"
      HERMES_API_URL: "http://hermes:8642"
      HERMES_API_KEY: "${HERMES_API_KEY}"
      OTEL_EXPORTER_OTLP_ENDPOINT: "http://langfuse-web:3000/api/public/otel"
      OTEL_EXPORTER_OTLP_HEADERS: "Authorization=Basic ${LANGFUSE_AUTH}"
    depends_on: [paperclip, hermes]
    ports: ["8650:8650"]

  web:
    build: ../apps/web
    environment:
      NEXT_PUBLIC_PAPERCLIP_URL: "http://localhost:3100"
      NEXT_PUBLIC_BRIDGE_URL: "http://localhost:8650"
      NEXT_PUBLIC_LANGFUSE_URL: "http://localhost:3000"
    ports: ["3001:3000"]
    depends_on: [adapter-bridge]

volumes:
  hermes-data:
```

`.env.example`：

```bash
PAPERCLIP_API_KEY=pp_local_dev_key
HERMES_API_KEY=hermes_local_dev_key
HERMES_WEBHOOK_SECRET=change-me
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_AUTH=base64(pk:sk)
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-or-...
```

---

## 2. M1 — 打通最小链路（HTTP Heartbeat → Hermes → 回调）

> ⚠️ 风险点：Paperclip Issue #3146 提到 OpenClaw Gateway 在 wake 时找不到 `PAPERCLIP_API_KEY`。**M1 必须先用最简单的 HTTP Adapter 验通，不要走 OpenClaw Gateway**。

### 2.1 验收标准

- [ ] Paperclip 创建一个 Task，触发 wake
- [ ] Adapter Bridge 收到 Paperclip POST，看到完整 payload
- [ ] Bridge 调用 Hermes `POST /v1/chat/completions`，拿到回复
- [ ] Bridge 通过 `PAPERCLIP_API_URL` 把结果回写为 Task Comment
- [ ] Paperclip Audit 日志中能看到完整一轮记录

### 2.2 在 Paperclip 创建 HTTP Adapter Agent（管理员 UI 操作）

```json
{
  "name": "PoC Agent (via Hermes)",
  "adapterType": "http",
  "adapterConfig": {
    "url": "http://adapter-bridge:8650/wake",
    "method": "POST",
    "headers": {
      "Authorization": "Bearer ${BRIDGE_TOKEN}",
      "Content-Type": "application/json",
      "X-Paperclip-Run": "{{run.id}}"
    },
    "timeoutMs": 60000,
    "payloadTemplate": {
      "agentId": "{{agent.id}}",
      "runId": "{{run.id}}",
      "taskId": "{{task.id}}",
      "companyId": "{{company.id}}",
      "wakeReason": "{{wakeReason}}",
      "prompt": "{{renderedPrompt}}"
    }
  }
}
```

### 2.3 关键代码：`apps/adapter-bridge/app/main.py`

```python
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
import httpx, os, json
from .schemas import WakeRequest, AdapterResult
from .otel import setup_tracing

app = FastAPI(title="Hermes-Paperclip Bridge")
setup_tracing(app)

PAPERCLIP_URL = os.environ["PAPERCLIP_API_URL"]
PAPERCLIP_KEY = os.environ["PAPERCLIP_API_KEY"]
HERMES_URL    = os.environ["HERMES_API_URL"]
HERMES_KEY    = os.environ["HERMES_API_KEY"]


@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/wake", response_model=AdapterResult)
async def wake(req: WakeRequest, authorization: str = Header(...)):
    # 1. 简单鉴权
    if authorization != f"Bearer {os.environ['BRIDGE_TOKEN']}":
        raise HTTPException(401)

    # 2. 调用 Hermes（OpenAI-compat）
    async with httpx.AsyncClient(timeout=120) as cli:
        r = await cli.post(
            f"{HERMES_URL}/v1/chat/completions",
            headers={"Authorization": f"Bearer {HERMES_KEY}"},
            json={
                "model": "default",
                "messages": [
                    {"role": "system", "content": "You are an AI staff member."},
                    {"role": "user", "content": req.prompt},
                ],
                "metadata": {
                    "paperclip_run_id": req.runId,
                    "paperclip_task_id": req.taskId,
                },
            },
        )
        r.raise_for_status()
        data = r.json()

    answer = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})

    # 3. 回写 Paperclip Task Comment
    async with httpx.AsyncClient(timeout=30) as cli:
        await cli.post(
            f"{PAPERCLIP_URL}/api/tasks/{req.taskId}/comments",
            headers={
                "Authorization": f"Bearer {PAPERCLIP_KEY}",
                "X-Paperclip-Run": req.runId,
            },
            json={"body": answer, "type": "agent_response"},
        )

    return AdapterResult(
        sessionId=req.runId,
        summary=answer[:200],
        usage={
            "promptTokens": usage.get("prompt_tokens", 0),
            "completionTokens": usage.get("completion_tokens", 0),
            "costUsd": estimate_cost(usage),
        },
        errors=[],
    )


def estimate_cost(usage: dict) -> float:
    # PoC 阶段简单按 GPT-4o-mini 价目估算
    prompt = usage.get("prompt_tokens", 0)
    completion = usage.get("completion_tokens", 0)
    return round((prompt * 0.15 + completion * 0.6) / 1_000_000, 6)
```

`apps/adapter-bridge/app/schemas.py`：

```python
from pydantic import BaseModel

class WakeRequest(BaseModel):
    agentId: str
    runId: str
    taskId: str
    companyId: str
    wakeReason: str | None = None
    prompt: str

class Usage(BaseModel):
    promptTokens: int
    completionTokens: int
    costUsd: float

class AdapterResult(BaseModel):
    sessionId: str
    summary: str
    usage: Usage
    errors: list[str] = []
```

### 2.4 冒烟脚本：`scripts/smoke-test.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail
BRIDGE=http://localhost:8650

# 1. 健康检查
curl -fsS $BRIDGE/health | jq .

# 2. 模拟 Paperclip 唤醒
curl -fsS -X POST $BRIDGE/wake \
  -H "Authorization: Bearer ${BRIDGE_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "agentId":"agent_demo",
    "runId":"run_smoke_001",
    "taskId":"task_smoke_001",
    "companyId":"co_demo",
    "wakeReason":"manual",
    "prompt":"Say hello in one sentence and tell me todays UTC date."
  }' | jq .

echo "✅ Smoke pass"
```

---

## 3. M2 — 自研运行视图（左 Chat + 右 Workspace）

### 3.1 验收标准

- [ ] 进入 `/run/:runId` 能看到一个左右分栏页面
- [ ] 左侧实时流式渲染 Hermes 的 `chat completions` 输出（含 tool call 气泡）
- [ ] 右侧标签页：`Browser` / `Terminal` / `Files` / `Diff`，至少两个能展示真实数据
- [ ] 用户在输入框追加消息，能"打断并改向"（对应 Hermes 的 interrupt-and-redirect）
- [ ] 关键操作（写文件 / 执行命令 / 调外部 API）出现 **Approval Card**，点 Approve 才继续

### 3.2 关键技术决策

| 选项 | 决策 | 理由 |
|---|---|---|
| 流式协议 | **SSE** | Hermes / OpenAI 兼容；浏览器原生支持；穿透代理友好 |
| 状态管理 | **Zustand** + TanStack Query | 简单；和 assistant-ui 兼容 |
| Workspace 后端 | **本地 Docker exec**（PoC） + **Daytona**（M3 升级） | PoC 不引入云依赖 |
| Approval | **tool-ui 的 Approval Card** | 现成，零开发 |

### 3.3 关键代码：`apps/web/components/runtime/RuntimeView.tsx`

```tsx
"use client";

import { Thread } from "@assistant-ui/react";
import { useChatRuntime } from "@assistant-ui/react-ai-sdk";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { BrowserPane } from "./BrowserPane";
import { TerminalPane } from "./TerminalPane";
import { FilesPane } from "./FilesPane";
import { DiffPane } from "./DiffPane";
import { ApprovalCard } from "./ApprovalCard";

export function RuntimeView({ runId }: { runId: string }) {
  const runtime = useChatRuntime({
    api: `/api/run/${runId}/stream`,
  });

  return (
    <div className="grid h-screen grid-cols-[minmax(380px,1fr)_1.4fr]">
      {/* 左：Chat 流 */}
      <section className="border-r bg-background flex flex-col">
        <header className="px-4 py-3 border-b text-sm font-medium">
          Run <code>{runId}</code>
        </header>
        <Thread runtime={runtime} components={{ ToolCall: ApprovalCard }} />
      </section>

      {/* 右：Workspace 多标签 */}
      <section className="bg-muted/30 flex flex-col">
        <Tabs defaultValue="browser" className="flex flex-col h-full">
          <TabsList className="rounded-none border-b bg-background">
            <TabsTrigger value="browser">Browser</TabsTrigger>
            <TabsTrigger value="terminal">Terminal</TabsTrigger>
            <TabsTrigger value="files">Files</TabsTrigger>
            <TabsTrigger value="diff">Diff</TabsTrigger>
          </TabsList>
          <TabsContent value="browser" className="flex-1"><BrowserPane runId={runId} /></TabsContent>
          <TabsContent value="terminal" className="flex-1"><TerminalPane runId={runId} /></TabsContent>
          <TabsContent value="files" className="flex-1"><FilesPane runId={runId} /></TabsContent>
          <TabsContent value="diff" className="flex-1"><DiffPane runId={runId} /></TabsContent>
        </Tabs>
      </section>
    </div>
  );
}
```

### 3.4 SSE 转发：`apps/web/app/api/run/[runId]/stream/route.ts`

```ts
import { NextRequest } from "next/server";

export const runtime = "nodejs";

export async function POST(req: NextRequest, { params }: { params: { runId: string } }) {
  const body = await req.text();
  const upstream = await fetch(`${process.env.NEXT_PUBLIC_BRIDGE_URL}/run/${params.runId}/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });
  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      "X-Accel-Buffering": "no",
    },
  });
}
```

### 3.5 Approval Card（核心 UX）

```tsx
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

export function ApprovalCard({ toolName, args, onApprove, onReject }: any) {
  const sensitive = ["fs.write", "shell.exec", "http.post", "deploy"].some(p => toolName.startsWith(p));
  if (!sensitive) return null;

  return (
    <Card className="border-amber-300 bg-amber-50/50 my-2">
      <CardHeader className="text-sm font-medium flex items-center gap-2">
        ⚠️ Agent 想执行：<code className="text-xs">{toolName}</code>
      </CardHeader>
      <CardContent>
        <pre className="text-xs bg-background p-2 rounded border overflow-auto max-h-48">
{JSON.stringify(args, null, 2)}
        </pre>
        <div className="flex gap-2 mt-3">
          <Button size="sm" onClick={onApprove}>批准</Button>
          <Button size="sm" variant="outline" onClick={onReject}>拒绝</Button>
        </div>
      </CardContent>
    </Card>
  );
}
```

---

## 4. M3 — 控制台四视图 + 可观测 + Demo 场景

### 4.1 验收标准

- [ ] `/console` 主页有四个 Tab：Org / Tasks / Cost / Audit
- [ ] **Org Chart**：显示已注册的 Agent + 当前状态徽章（idle/working/blocked），用 React Flow 实现
- [ ] **Tasks**：Linear 风格列表 + 详情抽屉；点开能跳到 `/run/:runId`
- [ ] **Cost**：日/周/月切换的折线图 + 每 Agent 排行 + Hard Budget 告警条
- [ ] **Audit**：表格 + 高级筛选（Agent / Tool / 时间窗 / 失败状态）
- [ ] `/observability` 内嵌 Langfuse iframe，能看到刚才的 trace
- [ ] 一个完整 Demo 场景：**"研究并起草一份周报"**，从老板在 Web UI 派单 → Agent 执行 → 出现 2 次审批 → 在 Cost 看板看到本次花费 → Audit 留痕

### 4.2 关键依赖

```bash
cd apps/web
pnpm add reactflow recharts date-fns @tanstack/react-table lucide-react
```

### 4.3 Org Chart 关键骨架（`components/console/OrgChart.tsx`）

```tsx
"use client";
import ReactFlow, { Background, Controls, Node, Edge } from "reactflow";
import "reactflow/dist/style.css";
import { useAgents } from "@/hooks/useAgents";

const STATUS_COLOR = {
  idle: "border-slate-300 bg-slate-50",
  working: "border-blue-400 bg-blue-50 animate-pulse",
  blocked: "border-rose-400 bg-rose-50",
} as const;

export function OrgChart() {
  const { data: agents = [] } = useAgents();

  const nodes: Node[] = agents.map((a, i) => ({
    id: a.id,
    position: { x: (i % 4) * 240, y: Math.floor(i / 4) * 160 },
    data: { label: <AgentNode agent={a} /> },
    type: "default",
    className: STATUS_COLOR[a.status],
  }));

  const edges: Edge[] = agents.flatMap(a =>
    a.reportsTo ? [{ id: `${a.id}->${a.reportsTo}`, source: a.id, target: a.reportsTo }] : []
  );

  return (
    <div className="h-[calc(100vh-12rem)]">
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
}

function AgentNode({ agent }: any) {
  return (
    <div className="text-xs">
      <div className="font-medium">{agent.name}</div>
      <div className="text-muted-foreground">{agent.role}</div>
      <div className="mt-1 text-[10px]">${agent.costToday?.toFixed(2)} today</div>
    </div>
  );
}
```

### 4.4 OpenTelemetry 接入 Langfuse（`apps/adapter-bridge/app/otel.py`）

```python
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

def setup_tracing(app):
    provider = TracerProvider(resource=Resource.create({"service.name": "adapter-bridge"}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
```

把每次 `/wake` 调用作为一个 root span，每次 Hermes 子调用作为 child span，Langfuse 自动按 OpenTelemetry 协议消费。

### 4.5 Demo 场景脚本：`scripts/seed-demo.ts`

```ts
import { paperclipApi } from "./paperclip-client";

async function seed() {
  // 1. 注册 3 个 Agent（CEO / Researcher / Writer）
  const ceo = await paperclipApi.createAgent({ name: "CEO", role: "manager", adapterType: "http", ... });
  const researcher = await paperclipApi.createAgent({ name: "Researcher", role: "ic", reportsTo: ceo.id, ... });
  const writer = await paperclipApi.createAgent({ name: "Writer", role: "ic", reportsTo: ceo.id, ... });

  // 2. 设预算
  await paperclipApi.setBudget(ceo.id, { monthlyUsd: 10 });

  // 3. 创建任务
  await paperclipApi.createTask({
    title: "起草本周公司周报",
    assignee: ceo.id,
    description: "综合 Researcher 收集到的本周关键信息，由 Writer 润色为最终周报。",
  });

  console.log("✅ Demo seeded");
}

seed();
```

---

## 5. 时间线与依赖关系（不写日历，只写交付里程碑）

| 里程碑 | 交付物 | 依赖 | Demo |
|---|---|---|---|
| **M0** | Monorepo + docker-compose 起所有服务 | — | `make up` 全绿 |
| **M1** | Adapter Bridge 打通 Heartbeat 链路 | M0 | smoke-test.sh 通过 |
| **M2** | 运行视图（左 Chat + 右 Workspace + Approval） | M1 | 手动派单看到流式输出 + 审批 |
| **M3** | 四视图 + Langfuse + Demo 场景 | M2 | 录一段视频跑「起草周报」 |

每个里程碑结束都生成一份 `docs/decisions/M{n}-summary.md` 记录踩坑与决策。

---

## 6. 风险登记 + 缓解策略

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| Paperclip Issue #3146（API Key 找不到） | 中 | 高 | M1 用最简 HTTP Adapter（不走 OpenClaw Gateway）；自己注入 env var；准备 fork patch |
| Hermes API 在 v2026.x 内不稳定 | 中 | 中 | 锁定 `v2026.4.16`；submodule 模式；自动化 schema 校验 |
| Daytona 沙箱在国内不通 | 高 | 中 | PoC 用本地 Docker；M4 再切 |
| Paperclip License 自定义条款限制 | 低 | 高 | 立项前法务确认，必要时仅参考其 UI 设计、后端用 Paperclip 但不二次分发 |
| 流式 SSE 在企业 Nginx 后端被 buffer | 中 | 中 | 文档化 `proxy_buffering off` 配置；提供 nginx 模板 |
| 国内 LLM 接入（DeepSeek/Kimi/通义） | 中 | 中 | Hermes 已支持 OpenAI-compat，绝大多数国产模型直接通 |
| 多租户 RBAC Paperclip 不满足 | 高 | 高 | M3 之后必须自建 IAM 层（Clerk / Casbin） |

---

## 7. PoC 退出标准（DoD）

完成下面 6 件事，PoC 即结束、可立项进入 V1 商业化开发：

1. ✅ 完整跑通"老板派单 → 多 Agent 协同 → 出现审批 → 完成回写 → 看到成本"的端到端流程
2. ✅ 录制不少于 3 个 Demo 视频（含失败场景演示）
3. ✅ 在 Langfuse 中能复现任意一次 run 的完整 trace
4. ✅ 输出一份《商业化版本架构修订》文档（基于 PoC 真实踩坑）
5. ✅ 输出一份《License 合规报告》给法务签字
6. ✅ 完成 1 次内部"客户视角"评审，至少邀请 3 名非工程同事打分（≥7/10 才过）

---

## 8. 进入 V1 商业化前的关键升级清单（PoC 之后再做，先列在这里防止漏）

- [ ] 替换 Paperclip 自带 React UI，全部用自研控制台
- [ ] 接入 Clerk/WorkOS 完整 SSO + RBAC
- [ ] Workspace 后端切到 Daytona 或自建 K8s + Firecracker
- [ ] Hermes 改造：抽出"运行时核心"，去掉 TUI/消息平台（避免重复维护）
- [ ] 多租户隔离：每租户独立 Hermes 实例 + Sandbox 网络隔离
- [ ] 灾备：Paperclip 数据库（SQLite → Postgres） + Hermes Skills 数据备份
- [ ] 计费：Stripe + 用量上报（覆盖 Token / 沙箱时长 / 工具调用次数三类）
- [ ] 安全审计：所有 Approval Card 决策上链或写不可变存储
- [ ] 接入"行业领域专用 Tool UI 组件库"（差异化护城河）

---

## 9. 备查：关键文档与命令

| 资源 | URL |
|---|---|
| Paperclip HTTP Adapter | https://docs.paperclip.ing/adapters/http |
| Paperclip Heartbeat Protocol | https://paperclip.inc/docs/guides/agent-developer/heartbeat-protocol |
| Hermes API Server | https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server |
| Hermes Webhooks | https://hermes-agent.nousresearch.com/docs/user-guide/messaging/webhooks |
| Hermes Architecture | https://hermes-agent.nousresearch.com/docs/developer-guide/architecture |
| assistant-ui | https://www.assistant-ui.com |
| tool-ui | https://www.tool-ui.com |
| Langfuse OTel | https://langfuse.com/docs/opentelemetry/get-started |
| React Flow | https://reactflow.dev |

```bash
# 常用命令速查
make up              # 起全部服务
make down            # 停全部
make logs s=hermes   # 看某服务日志
pnpm --filter web dev
( cd apps/adapter-bridge && uvicorn app.main:app --reload --port 8650 )
bash scripts/smoke-test.sh
```
