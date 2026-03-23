# ADK Logistics Agent Workbench

一个围绕 **Google ADK** 构建的物流智能体工作台后端方案，用于完成“基于物流 API 文档实现 AI Agent 工作流”的实践任务。

本项目当前重点完成的是 **后端智能体系统**：使用 Google ADK 作为主框架，在没有真实物流 API 凭证、也不依赖真实在线 LLM Key 的前提下，搭建一个**可运行、可测试、可演示、可扩展**的物流业务智能体后端。

---

## 1. 项目目标

这个项目要解决的不是“做一个聊天机器人”，而是把物流业务需求抽象成一个真正的 Agent 系统。

目标包括：

- 能理解类似以下请求：
  - `查询订单 #12345 的运输状态`
  - `创建从深圳到洛杉矶的新货运单`
  - `先查一下美国报价`
- 能基于物流 API 文档模拟真实接口行为
- 能处理多轮补槽、状态延续、确认执行、结构化结果返回
- 保持代码结构清晰，接近真实生产系统的分层设计

---

## 2. 为什么选 Google ADK

题目明确要求使用 **Google ADK**，因此本项目将 ADK 作为唯一主框架，而不是用 LangGraph、LangChain 或其他框架替代。

本项目实际使用到的 ADK 核心能力包括：

- `BaseAgent`
- `InMemoryRunner`
- `Event`
- `FunctionTool`

这里的取舍是：

- **遵守题目要求**：主框架必须是 ADK
- **保证可演示性**：当前版本采用离线 deterministic planner，不依赖真实在线模型
- **保证可扩展性**：后续如果需要接入 Gemini 或其他 LLM，只替换 planner / orchestration 层即可，不需要重写业务工作流

---

## 3. 整体设计思路

后端采用“**会话状态 + 规划层 + 工作流层 + 工具层 + Mock Gateway**”的结构。

### 3.1 设计原则

- **Agent 负责编排，不直接耦合业务细节**
- **工具层负责调用能力，不负责对话状态**
- **会话状态由后端统一持有，不让前端伪造业务状态机**
- **Mock 数据结构尽量贴近物流文档字段**
- **前端可观测信息由后端生成，避免前端自行猜测执行过程**

### 3.2 后端执行链路

每轮请求的后端链路如下：

1. 接收用户消息
2. 从 ADK session 中恢复当前会话状态
3. 由 deterministic planner 识别意图和抽取实体
4. 将请求分发到对应 workflow
5. workflow 校验槽位、调用工具、记录 trace
6. 根协调 agent 汇总：
   - `reply`
   - `traceSteps`
   - `cards`
   - `pendingAction`
   - `sessionState`
7. 以 ADK `Event` 的形式返回最终结果

---

## 4. 后端分层结构

```text
apps/
  agent-server/
    src/app/
      agents/          ADK agents and workflows
      api/             FastAPI routes
      domain/          typed models and contracts
      mock_gateway/    logistics API simulation
      observability/   trace recorder
      services/        planner and business services
      tools/           ADK tool wrappers
contracts/            shared JSON-schema style examples
docs/
  adr/                architecture decisions
  frontend-handoff.md frontend implementation handoff
```

### 4.1 `domain`

负责定义系统中最核心的结构化模型，见：

- [models.py](./apps/agent-server/src/app/domain/models.py)

关键对象包括：

- `ConversationRequest`
- `ConversationResponse`
- `WorkspaceSessionState`
- `ShipmentDraft`
- `QuoteDraft`
- `TraceStep`
- `PendingAction`
- `ResponseCard`
- `ToolResult`

这一层的意义是统一：

- API contract
- session state
- workflow 输入输出
- 前端渲染载荷

### 4.2 `services`

负责规划与槽位管理，当前实现见：

- [planner.py](./apps/agent-server/src/app/services/planner.py)

它负责：

- 意图识别
- 规则化实体抽取
- 建单 / 报价 draft 合并
- 缺失槽位判断
- 确认语义判断

当前 planner 是 deterministic 的，便于离线演示和稳定测试。

### 4.3 `agents`

负责 ADK agent 组织与 workflow 编排：

- [root_agent.py](./apps/agent-server/src/app/agents/root_agent.py)
- [workflows.py](./apps/agent-server/src/app/agents/workflows.py)

#### Root Agent

根协调 agent 只做三件事：

- 识别意图
- 选择 workflow
- 汇总输出

#### Workflow Agents

当前包含的 workflow：

- `ReferenceResolutionWorkflow`
- `TrackShipmentWorkflow`
- `CreateShipmentWorkflow`
- `QuoteWorkflow`
- `OrderLookupWorkflow`

这样拆分是为了让每个业务流有清晰边界，而不是把所有逻辑塞进一个超大 agent。

### 4.4 `tools`

工具层见：

- [logistics_tools.py](./apps/agent-server/src/app/tools/logistics_tools.py)

作用：

- 把 mock gateway 的业务能力包装成 ADK `FunctionTool`
- 为 workflow 层提供统一调用入口

当前覆盖的高价值工具：

- `track_order`
- `create_order`
- `create_forecast_order`
- `search_price`
- `list_orders`
- `resolve_waybill_number`
- `list_channels`
- `list_destinations`
- `list_product_types`
- `list_currencies`

### 4.5 `mock_gateway`

见：

- [catalog.py](./apps/agent-server/src/app/mock_gateway/catalog.py)

作用：

- 模拟物流 API 文档中的核心接口
- 提供固定种子数据和失败场景
- 保持返回字段尽量贴近原文档风格

已覆盖场景：

- 正常查轨迹
- 单号解析失败
- 正常报价
- 指定渠道不支持报价
- 创建草稿单
- 草稿单重复更新
- 预报单重复拒绝

### 4.6 `observability`

见：

- [trace.py](./apps/agent-server/src/app/observability/trace.py)

后端显式记录以下类型的步骤：

- `decision`
- `validation`
- `tool`
- `summary`

这样前端右侧 trace 面板可以直接渲染，不需要自己猜“这一步是做什么的”。

---

## 5. 关键业务设计

### 5.1 查轨迹为什么先做引用解析

题目里的“订单号 #12345”在物流系统里未必是最终运单号，它可能是：

- 客户参考号
- 系统单号
- 运单号

因此不能直接查轨迹，而是先走：

1. `resolve_waybill_number`
2. 再调用 `track_order`

这就是 `ReferenceResolutionWorkflow` 的职责。

### 5.2 创建货运单为什么必须多轮补槽

建单不是单步动作，而是典型多轮业务流。当前后端流程是：

1. 抽取用户已给字段
2. 合并到 `ShipmentDraft`
3. 检查必填槽位
4. 如果缺字段，逐项追问
5. 如果字段齐全，生成 `pendingAction`
6. 用户回复 `确认` 后才真正调用 `create_order`

这样可以避免：

- 前端自己维护建单状态机
- 模型幻觉直接“默认字段”
- 未确认就执行 destructive action

### 5.3 为什么不把确认做成单独接口

当前确认流程仍然走 `POST /api/chat`，用户点击确认按钮时，前端只发送字面消息：

- `确认`
- `取消`

原因是：

- 保持 agent 对话统一入口
- 不引入额外确认 API
- 会话上下文仍然由后端 session state 统一维护

---

## 6. 对外 API

### `POST /api/chat`

请求：

```json
{
  "sessionId": "optional",
  "message": "查询订单 #12345 的运输状态",
  "mode": "offline-demo"
}
```

响应字段：

- `sessionId`
- `reply`
- `traceSteps`
- `cards`
- `pendingAction`
- `sessionState`

### `GET /api/sessions/{sessionId}/trace`

返回该 session 最新的：

- `traceSteps`
- `sessionState`

相关代码见：

- [routes.py](./apps/agent-server/src/app/api/routes.py)

---

## 7. 当前实现的能力边界

已实现：

- 查运单轨迹
- 解析模糊编号
- 查报价
- 创建货运单
- 多轮补槽
- 建单确认
- recent orders 查询
- 后端 trace 输出

未实现：

- 标签下载
- 附件下载
- 收货图片上传
- 真实物流 API 凭证接入
- 真实 Gemini / live LLM
- 持久化数据库

---

## 8. 为什么当前版本不用真实 LLM

因为这次任务要求里：

- 没有提供真实物流 API 凭证
- 当前目标是稳定展示 agent 设计能力，而不是追求模型开放式生成

所以当前选择是：

- **ADK 保留**
- **Planner 离线 deterministic**
- **Workflow 保持企业级分层**

这让系统有几个明显优点：

- 可本地直接运行
- 测试稳定
- 演示不会受外部模型或网络波动影响
- 未来升级真实 LLM 时只需替换 planner 层

---

## 9. 环境要求

- Python `3.12.x`

注意：

- 当前机器默认 `Python 3.14 beta` 与 `google-adk` 不兼容
- 本项目开发时已切换到 `Python 3.12`

---

## 10. 安装与运行

### 10.1 创建虚拟环境

Windows PowerShell：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .\apps\agent-server[dev]
```

### 10.2 启动后端

```powershell
cd .\apps\agent-server
..\..\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir src --host 127.0.0.1 --port 8011 --reload
```

如果你直接在仓库根目录执行，也可以改成绝对路径方式。

### 10.3 运行测试

```powershell
cd .\apps\agent-server
..\..\.venv\Scripts\python.exe -m pytest -q
```

---

## 11. 已验证结果

当前后端已完成本地验证：

- `pytest` 通过
- 本地 `uvicorn` 成功启动
- `/docs` 可访问
- `/api/chat` 可返回真实结果

示例请求：

- `查询订单 #12345 的运输状态`

示例返回效果：

- `reply` 正常
- `cards` 返回 2 个
- `traceSteps` 返回 5 个

---

## 12. 示例提示词

- `查询订单 #12345 的运输状态`
- `创建从深圳到洛杉矶的新货运单`
- `先查一下美国报价 2kg 1件`
- `渠道用香港TNT 参考号 SZ-LA-1001 1件 2kg 收件人 Alice 地址 123 Main Street`
- `确认`
- `取消`

---

## 13. 前端协作说明

前端实现说明已单独写入：

- [frontend-handoff.md](./docs/frontend-handoff.md)

这份文档明确了：

- 页面布局
- 组件结构
- API contract
- trace 和 cards 的渲染规则
- pendingAction 的确认逻辑
- 视觉规范

---

## 14. ADR

已补充三份架构决策记录：

- [0001-adk-as-core.md](./docs/adr/0001-adk-as-core.md)
- [0002-offline-deterministic-planner.md](./docs/adr/0002-offline-deterministic-planner.md)
- [0003-workflow-first-orchestration.md](./docs/adr/0003-workflow-first-orchestration.md)

---

## 15. 后续可扩展方向

如果继续往生产方向推进，优先级建议如下：

1. 将 `MockLogisticsGateway` 替换成真实 HTTP client
2. 接入持久化 session / database
3. 将 deterministic planner 替换为真实 LLM planner
4. 增加 tool-level policy / auth / audit
5. 增加更完整的物流 API 覆盖范围

---

## 16. 当前结论

这个版本的重点不是“模型多聪明”，而是：

- ADK 框架使用正确
- 工作流分层明确
- 会话状态清晰
- 工具边界清晰
- 对前端输出结构稳定
- 可以本地运行和测试

这使它更像一个真正可交付的 AI Agent 后端，而不是一个只有 prompt 的 demo。
