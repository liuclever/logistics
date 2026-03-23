import { Card, Tag } from 'tdesign-react';
import type { PendingAction, TraceStep, WorkspaceSessionState } from '../../types/contracts';
import { TraceStepCard } from './TraceStepCard';

interface TraceTimelineProps {
  traceSteps: TraceStep[];
  sessionState: WorkspaceSessionState | null;
  pendingAction?: PendingAction | null;
}

export function TraceTimeline({ traceSteps, sessionState, pendingAction }: TraceTimelineProps) {
  const latestStepId = traceSteps[0]?.step_id;

  return (
    <>
      <div className="panel-header">
        <div>
          <p className="eyebrow">Execution Trace</p>
          <h2>执行侧栏</h2>
        </div>
      </div>

      <Card className="panel-card" title="当前工作流">
        <div className="workflow-summary">
          <div>
            <span>Intent</span>
            <strong>{sessionState?.last_plan?.intent ?? '--'}</strong>
          </div>
          <div>
            <span>Workflow</span>
            <strong>{sessionState?.last_plan?.selected_workflow ?? '--'}</strong>
          </div>
          <div>
            <span>Pending</span>
            <strong>{pendingAction?.kind ?? 'none'}</strong>
          </div>
        </div>
        {pendingAction ? (
          <Tag theme="warning" variant="light">
            {pendingAction.summary}
          </Tag>
        ) : null}
      </Card>

      <div className="trace-list">
        {traceSteps.length === 0 ? (
          <Card className="panel-card">
            <div className="empty-inline">
              <p>这里会显示决策、校验、工具调用和摘要步骤。</p>
            </div>
          </Card>
        ) : (
          traceSteps.map((step) => (
            <TraceStepCard key={step.step_id} step={step} emphasized={step.step_id === latestStepId} />
          ))
        )}
      </div>
    </>
  );
}
