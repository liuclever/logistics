# ADK Logistics Agent Workbench

一个基于 **Google ADK** 的物流智能体工作台。项目目标不是做一个普通聊天机器人，而是实现一个可演示、可测试、可扩展的 **物流业务 Agent 系统**，能够围绕物流 API 文档完成查询、报价、建单和多轮补槽等工作流。

支持的典型请求：

- `查询订单 #12345 的运输状态`
- `创建从深圳到洛杉矶的新货运单`
- `先查一下美国报价 3kg 1件`
- `查询最近订单`

---

## 1. 项目概览

### 目标

- 使用 **Google ADK** 作为 Agent 主框架
- 在没有真实 API 凭证的情况下，基于文档模拟物流 API
- 让系统能够处理结构化业务流程，而不是只返回一句自然语言
- 输出前端可直接消费的 `reply / cards / traceSteps / pendingAction / sessionState`

### 当前技术方案

- 后端：Python + FastAPI + Google ADK
- 前端：React + TypeScript + Vite + TDesign
- Planner：离线 deterministic planner
- API：Mock Gateway，模拟真实物流接口行为

---

## 2. 架构设计

### 后端架构

```text
apps/agent-server/src/app/
  agents/          Root Agent + workflow agents
  api/             FastAPI routes
  domain/          typed models and contracts
  mock_gateway/    mock logistics API implementation
  observability/   trace recorder
  services/        planner and business helpers
  tools/           ADK FunctionTool wrappers
```

核心职责划分：

- `RootCoordinatorAgent`：负责任务路由和结果汇总
- `DeterministicPlanner`：负责意图识别、实体抽取、补槽判断、候选动作生成
- `Workflow Agents`：负责具体业务流
- `Tool Registry`：把物流能力包装成 ADK `FunctionTool`
- `Mock Gateway`：模拟物流 API 的返回结构和业务场景
- `Trace Recorder`：记录决策、校验、工具调用、汇总步骤

当前 workflow 包括：

- `ReferenceResolutionWorkflow`
- `TrackShipmentWorkflow`
- `QuoteWorkflow`
- `OrderLookupWorkflow`
- `CreateShipmentWorkflow`

### 前端架构

```text
apps/web/src/
  api/             frontend API client
  components/      cards / chat / trace / workbench
  hooks/           local session hook
  styles/          global workbench styles
  types/           frontend contracts
  utils/           display and storage helpers
```

页面采用三栏工作台：

- 左侧：导航、历史会话、快捷任务、统计概览
- 中间：聊天线程、业务结果卡片、输入区
- 右侧：执行轨迹、工作编排流、确认状态

设计原则：

- 前端只负责渲染结构化数据
- 后端负责业务状态、工作流控制和确认逻辑
- 不把业务状态机放在前端浏览器里

---

## 3. 工具系统设计

当前高价值工具包括：

- `track_order`
- `create_order`
- `create_forecast_order`
- `search_price`
- `list_orders`
- `get_price_analysis`
- `resolve_waybill_number`
- `list_channels`
- `list_destinations`
- `list_product_types`
- `list_currencies`

工具层原则：

- 工具只负责“能力调用”
- Workflow 负责“业务流程”
- Planner 负责“路由与补槽”

这样可以避免把所有逻辑都塞到一个 Agent 或一个 Prompt 中。

---

## 4. 错误处理与边界情况

项目里重点考虑了以下边界：

- 单号可能是客户参考号、系统单号或运单号，因此先做引用解析
- 建单属于 destructive action，必须先确认再执行
- 报价和建单都支持多轮补槽，不要求用户一次性填完
- 单号不存在、渠道不支持、目的地不支持、重复参考号等都会返回结构化错误卡片
- 后端统一输出 trace，前端不自行猜测流程

已覆盖的典型场景：

- 正常查轨迹
- 查不到单号
- 正常报价
- 报价字段不全
- 指定渠道不支持
- 创建草稿单
- 重复参考号
- 用户确认 / 取消建单

---

## 5. 我的思考过程

这次实现不是直接上手写代码，而是先把它当成一个完整产品去拆。

### 5.1 先用 GPT 做产品头脑风暴

第一步不是写接口，而是先明确这到底要交付什么。

我先用 GPT 做了产品层面的头脑风暴，核心目的是回答三个问题：

- 这个项目的本质是聊天机器人，还是物流工作台
- 用户真正要完成的动作是什么
- 前后端分别应该承担什么职责

经过这一步，方向被明确为：

- 这不是一个普通问答页，而是一个 **物流智能体工作台**
- 核心价值不是“回答一句话”，而是“把物流动作编排出来”
- 前端负责承接结构化结果，后端负责状态、流程、工具和决策摘要

### 5.2 再用 AI 做原型和交互逻辑确认

方向确定后，没有马上进入实现，而是先用 AI 产出原型和页面逻辑。

这个阶段主要确认：

- 三栏工作台是否合理
- 聊天区、执行轨迹区、工作编排流是否需要同时存在
- 用户是更多依赖手输，还是应该多用动作气泡和确认卡片
- 哪些信息该前台展示，哪些信息必须隐藏

最终确定的原型逻辑是：

- 左侧做导航、会话和快捷任务
- 中间做聊天和业务结果卡片
- 右侧做 trace 和 workflow 可视化
- AI 思考过程不直接暴露原始 chain-of-thought，只展示产品化决策摘要

### 5.3 用 AI 分工协作，而不是把所有代码混在一起

在实现阶段，我把 AI 协作拆成了 3 类角色，而不是让一个 AI 同时承担所有事情。

#### 产品主管 AI

负责：

- 拆分任务
- 约束前后端边界
- 检查接口契约
- 审查页面是否符合原型目标
- 做最终联调检查

它更像项目里的产品负责人加技术协调者。

#### 前端 AI

负责：

- 按约定好的 contract 开发 React + TDesign 工作台
- 实现聊天区、结果卡片、轨迹面板、工作编排流
- 不自创业务状态，不额外发明后端协议

#### 后端 AI

负责：

- 设计 Google ADK Agent 架构
- 拆 Root Agent、Planner、Workflow、Tool、Mock Gateway
- 维护 session state
- 输出结构化 cards / traceSteps / pendingAction / sessionState

### 5.4 前后端协作的关键约定

前后端开发不是各写各的，而是先约定协议，再并行开发。

约定内容包括：

- 统一聊天入口 `POST /api/chat`
- 统一 trace 查询入口 `GET /api/sessions/{sessionId}/trace`
- 前端不单独创建确认接口
- 确认和取消都回到聊天主入口
- 后端只输出结构化卡片，不输出不可控的长文本推理
- 前端只负责展示，不在浏览器里维护业务状态机

这套约定的核心目的是：

- 降低并行开发时的摩擦
- 避免前后端反复返工
- 保证系统边界清晰

### 5.5 最后由“产品主管 AI”做收口检查

当前后端和前端各自完成后，再由一个更偏“产品 / 协调 / 验收”的角色统一检查：

- 页面交互是否符合最初原型
- 后端返回的数据是否真的适合前端渲染
- 有没有出现字段正确但体验别扭的问题
- 用户是不是被迫输入太多内容
- 流程是否真的像“工作台”，而不是拼凑的 demo

这一轮检查推动了后续优化，例如：

- 把普通动作提示改成动作卡片和可点击气泡
- 增加工作编排流可视化
- 把“AI 思考流”改成可折叠的决策摘要
- 把最近订单从原始对象平铺改成格式化订单卡

### 5.6 最后通过自制 MCP 做部署

在交付阶段，我使用自制 MCP 工具链辅助部署和联调，而不是把部署当成最后单独补的一步。

这样做的价值在于：

- 可以把开发、验证、部署衔接起来
- 能更快发现前后端集成问题
- 更接近真实工程里“开发完成后立即验证可上线性”的节奏

总结来说，这次项目的实现方式并不是“一个 AI 从头写到尾”，而是：

1. 用 GPT 做产品头脑风暴，确定方向
2. 用 AI 出原型，确认交互逻辑
3. 用多角色 AI 分工协作前后端开发
4. 用一个更高层的 AI 角色做验收和收口
5. 最后结合自制 MCP 做部署与验证

这套过程本身也是我想展示的能力：**不仅能写代码，还能把 AI 作为产品和工程协作工具，组织成一套完整交付流程。**

---

## 6. 为什么当前版本是离线 Demo

当前版本明确采用：

- Google ADK runtime
- deterministic planner
- mock logistics gateway

原因是：

- 没有真实物流 API 凭证
- 需要保证演示稳定性
- 重点是展示 Agent 设计能力，而不是依赖在线模型能力

后续如果接入真实 LLM，只需要替换 Planner 层，不需要重写 Workflow 与工具层。

---

## 7. 安装与运行

### 环境要求

- Python `3.12.x`
- Node.js `18+`

### 后端安装

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .\apps\agent-server[dev]
```

### 启动后端

```powershell
cd .\apps\agent-server
..\..\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir src --host 127.0.0.1 --port 8011 --reload
```

### 前端安装

```powershell
cd .\apps\web
npm install
```

### 启动前端

```powershell
cd .\apps\web
npm run dev
```

### 运行测试

后端：

```powershell
cd .\apps\agent-server
..\..\.venv\Scripts\python.exe -m pytest -q
```

前端：

```powershell
cd .\apps\web
npm run build
```

---

## 8. 关键接口

### `POST /api/chat`

请求示例：

```json
{
  "sessionId": "optional",
  "message": "查询订单 #12345 的运输状态",
  "mode": "offline-demo"
}
```

响应包括：

- `sessionId`
- `reply`
- `traceSteps`
- `cards`
- `pendingAction`
- `sessionState`

### `GET /api/sessions/{sessionId}/trace`

返回当前会话最新的：

- `traceSteps`
- `sessionState`

---

## 9. 当前已实现能力

- 查轨迹
- 单号解析
- 报价试算
- 最近订单查询
- 建单
- 多轮补槽
- 确认 / 取消
- Trace 面板
- 工作编排流
- AI 思考流摘要

---

## 10. 后续可扩展方向

- 接入真实物流 API
- 接入真实 LLM planner
- 引入数据库持久化
- 增加权限 / 策略 / 审计层
- 补更多物流 API 能力

---

## 11. 相关文件

后端核心：

- [root_agent.py](./apps/agent-server/src/app/agents/root_agent.py)
- [workflows.py](./apps/agent-server/src/app/agents/workflows.py)
- [planner.py](./apps/agent-server/src/app/services/planner.py)
- [models.py](./apps/agent-server/src/app/domain/models.py)
- [logistics_tools.py](./apps/agent-server/src/app/tools/logistics_tools.py)
- [catalog.py](./apps/agent-server/src/app/mock_gateway/catalog.py)

前端核心：

- [App.tsx](./apps/web/src/App.tsx)
- [useChatSession.ts](./apps/web/src/hooks/useChatSession.ts)
- [CardRenderer.tsx](./apps/web/src/components/cards/CardRenderer.tsx)
- [ActionListCard.tsx](./apps/web/src/components/cards/ActionListCard.tsx)
- [RecentOrdersCard.tsx](./apps/web/src/components/cards/RecentOrdersCard.tsx)
- [TraceTimeline.tsx](./apps/web/src/components/trace/TraceTimeline.tsx)
- [OrchestrationFlow.tsx](./apps/web/src/components/workbench/OrchestrationFlow.tsx)

---

## 12. 结论

这个项目的重点不是“做一个能聊天的页面”，而是：

- 用 Google ADK 正确组织智能体和工具系统
- 用清晰的分层方式实现业务编排
- 让错误处理、补槽、确认、轨迹输出都结构化
- 让前端成为真正的工作台，而不是被动文本容器

这也是我对这个任务的理解：**交付的是一个有产品逻辑、有工程边界、有可扩展性的 AI Agent 系统。**
