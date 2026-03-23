import {
  AddIcon,
  AppIcon,
  ChatIcon,
  ChartLineDataIcon,
  SearchIcon,
  TimeIcon,
} from 'tdesign-icons-react';
import { Tag } from 'tdesign-react';
import { ChatThread } from './components/chat/ChatThread';
import { Composer } from './components/chat/Composer';
import { TraceTimeline } from './components/trace/TraceTimeline';
import { OrchestrationFlow } from './components/workbench/OrchestrationFlow';
import { QuickPromptList } from './components/workbench/QuickPromptList';
import { SidebarSessions } from './components/workbench/SidebarSessions';
import { StatsCard } from './components/workbench/StatsCard';
import { WorkbenchShell } from './components/workbench/WorkbenchShell';
import { useChatSession } from './hooks/useChatSession';

const quickPrompts = [
  '查询订单 #12345 的运输状态',
  '先查一下美国报价 3kg 1件',
  '创建从深圳到洛杉矶的新货运单',
  '查询最近订单',
];

const welcomePrompts = [
  '查询订单 #12345 的运输状态',
  '创建从深圳到洛杉矶的新货运单',
  '先查一下美国报价 3kg 1件',
  '查看渠道列表',
  '查询最近订单',
  '帮我梳理这票货接下来要做什么',
];

const sidebarMenuItems = [
  { icon: AddIcon, label: '新对话', active: true, action: 'new' },
  { icon: SearchIcon, label: '订单浏览', action: 'orders' },
  { icon: ChartLineDataIcon, label: '报价分析', action: 'quotes' },
  { icon: AppIcon, label: '更多工具' },
];

export default function App() {
  const {
    sessionId,
    messages,
    traceSteps,
    sessionState,
    pendingAction,
    loading,
    error,
    recentSessions,
    stats,
    submitMessage,
    startNewSession,
    openSession,
    confirmPendingAction,
    cancelPendingAction,
  } = useChatSession();

  const sidebar = (
    <div className="panel-scroll">
      <div className="brand-block">
        <div className="brand-head">
          <div className="brand-avatar">物</div>
          <div className="brand-block__text">
            <p className="eyebrow">Logistics AI</p>
            <h1>物流智能体</h1>
            <span>企业级工具编排工作台</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {sidebarMenuItems.map((item) => {
            const Icon = item.icon;
            const handleClick = () => {
              if (item.action === 'new') startNewSession();
              else if (item.action === 'orders') submitMessage('查询最近订单');
              else if (item.action === 'quotes') submitMessage('查看报价分析');
            };
            return (
              <button
                key={item.label}
                type="button"
                className={`sidebar-nav__item${item.active ? ' is-active' : ''}`}
                onClick={item.action ? handleClick : undefined}
              >
                <span className="sidebar-nav__icon">
                  <Icon size={18} />
                </span>
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

      </div>

      <SidebarSessions
        sessions={recentSessions}
        activeSessionId={sessionId}
        onSelect={openSession}
      />
      <QuickPromptList prompts={quickPrompts} onPromptClick={(prompt) => void submitMessage(prompt)} />
      <StatsCard stats={stats} />
    </div>
  );

  const center = (
    <>
      <header className="center-topbar">
        <div>
          <p className="eyebrow">智能体工作台</p>
          <h2>有什么我能帮你的吗？</h2>
        </div>
      </header>

      <OrchestrationFlow traceSteps={traceSteps} sessionState={sessionState} pendingAction={pendingAction} />

      <section className="chat-shell">
        {messages.length > 0 ? (
          <div className="chat-shell__header">
            <div className="chat-shell__meta">
              <span>会话 {sessionId ? sessionId.slice(0, 8) : '新建中'}</span>
              <span>已连接</span>
            </div>
            <div className="chat-shell__stats">
              <div className="chat-shell__stat">
                <span>消息数</span>
                <strong>{stats.totalMessages}</strong>
              </div>
              <div className="chat-shell__stat">
                <span>轨迹查询</span>
                <strong>{stats.trackingQueries}</strong>
              </div>
              <div className="chat-shell__stat">
                <span>报价次数</span>
                <strong>{stats.quoteQueries}</strong>
              </div>
            </div>
          </div>
        ) : null}

        <div className="chat-stage">
          <ChatThread
            messages={messages}
            pendingAction={pendingAction}
            loading={loading}
            onConfirm={() => void confirmPendingAction()}
            onCancel={() => void cancelPendingAction()}
            suggestions={welcomePrompts}
            onSelectSuggestion={(value) => void submitMessage(value)}
            onSelectAction={(value) => void submitMessage(value)}
          />
        </div>

        <Composer loading={loading} onSend={submitMessage} />
        {error ? <div className="error-inline">{error}</div> : null}
      </section>
    </>
  );

  const trace = (
    <>
      <div className="trace-topbar">
        <div>
          <p className="eyebrow">执行观察</p>
          <h2>执行过程</h2>
        </div>
        <Tag theme="primary" variant="light">
          <TimeIcon size={14} />
          实时
        </Tag>
      </div>
      <TraceTimeline traceSteps={traceSteps} sessionState={sessionState} pendingAction={pendingAction} />
    </>
  );

  return (
    <main className="workbench-page">
      <WorkbenchShell sidebar={sidebar} center={center} trace={trace} />
    </main>
  );
}
