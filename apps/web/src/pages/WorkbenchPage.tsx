import { Card, Tag } from 'tdesign-react';
import { ChatThread } from '../components/chat/ChatThread';
import { Composer } from '../components/chat/Composer';
import { ConfirmationCard } from '../components/cards/ConfirmationCard';
import { TraceTimeline } from '../components/trace/TraceTimeline';
import { QuickPromptList } from '../components/workbench/QuickPromptList';
import { SidebarSessions } from '../components/workbench/SidebarSessions';
import { StatsCard } from '../components/workbench/StatsCard';
import { WorkbenchShell } from '../components/workbench/WorkbenchShell';
import { useChatSession } from '../hooks/useChatSession';

const QUICK_PROMPTS = [
  '查询订单 #12345 的运输状态',
  '创建从深圳到洛杉矶的新货运单',
  '先查一下美国报价',
];

export function WorkbenchPage() {
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

  return (
    <main className="workbench-page">
      <WorkbenchShell
        sidebar={
          <>
            <div className="panel-header">
              <div>
                <p className="eyebrow">ADK Logistics</p>
                <h1>Agent Workbench</h1>
              </div>
              <Tag theme="primary" variant="light">
                Offline Demo
              </Tag>
            </div>

            <SidebarSessions
              sessions={recentSessions}
              activeSessionId={sessionId}
              onSelect={(session) => void openSession(session)}
              onNewSession={startNewSession}
            />
            <QuickPromptList prompts={QUICK_PROMPTS} onPromptClick={(prompt) => void submitMessage(prompt)} />
            <StatsCard stats={stats} />
          </>
        }
        center={
          <>
            <div className="panel-header">
              <div>
                <p className="eyebrow">三栏工作台</p>
                <h2>聊天主区</h2>
              </div>
              <Card className="toolbar-card">
                <div className="toolbar-card__content">
                  <span>当前会话</span>
                  <strong>{sessionId ? sessionId.slice(0, 12) : '未开始'}</strong>
                </div>
              </Card>
            </div>

            {error ? (
              <Card className="panel-card result-card result-card--error">
                <p>{error}</p>
              </Card>
            ) : null}

            {pendingAction ? (
              <ConfirmationCard
                sticky
                title="待确认建单摘要"
                data={{
                  summary: pendingAction.summary,
                  draft: pendingAction.payload,
                  actionId: pendingAction.action_id,
                }}
                pendingAction={pendingAction}
                loading={loading}
                onConfirm={() => void confirmPendingAction()}
                onCancel={() => void cancelPendingAction()}
              />
            ) : null}

            <ChatThread
              messages={messages}
              pendingAction={pendingAction}
              loading={loading}
              onConfirm={() => void confirmPendingAction()}
              onCancel={() => void cancelPendingAction()}
            />
            <Composer onSend={(message) => submitMessage(message)} loading={loading} />
          </>
        }
        trace={<TraceTimeline traceSteps={traceSteps} sessionState={sessionState} pendingAction={pendingAction} />}
      />
    </main>
  );
}
