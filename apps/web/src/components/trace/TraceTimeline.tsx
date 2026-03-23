import { Card } from 'tdesign-react';
import type { PendingAction, TraceStep, WorkspaceSessionState } from '../../types/contracts';
import { buildMissingSlotsCopy, formatWorkflowLabel } from '../../utils/display';
import { TraceStepCard } from './TraceStepCard';

interface TraceTimelineProps {
  traceSteps: TraceStep[];
  sessionState: WorkspaceSessionState | null;
  pendingAction?: PendingAction | null;
}

function formatConfidence(value?: number) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '未提供';
  }

  return `${Math.round(value * 100)}%`;
}

export function TraceTimeline({ traceSteps, sessionState, pendingAction }: TraceTimelineProps) {
  const latestStepId = traceSteps[traceSteps.length - 1]?.step_id;
  const plan = sessionState?.last_plan;
  const missingSlots = plan?.missing_slots ?? [];
  const missingSlotsCopy = buildMissingSlotsCopy(missingSlots);

  const pipelineCards = [
    {
      title: '意图',
      value: formatWorkflowLabel(plan?.intent),
      meta: plan?.user_message ? '已识别' : '等待输入',
    },
    {
      title: '工作流',
      value: formatWorkflowLabel(plan?.selected_workflow),
      meta: `置信度 ${formatConfidence(plan?.confidence)}`,
    },
    {
      title: '参数',
      value: missingSlotsCopy.value,
      meta: missingSlotsCopy.meta,
    },
    {
      title: '确认',
      value: pendingAction ? '待人工确认' : '无需确认',
      meta: pendingAction?.summary ?? '当前没有阻塞动作',
    },
  ];

  return (
    <>
      <section className="trace-pipeline">
        {pipelineCards.map((card) => (
          <article key={card.title} className="trace-pipeline-card">
            <div className="trace-pipeline-card__top">
              <strong>{card.title}</strong>
            </div>
            <h3>{card.value}</h3>
            <p>{card.meta}</p>
          </article>
        ))}
      </section>

      <div className="trace-list">
        {traceSteps.length === 0 ? (
          <Card className="panel-card trace-empty-card">
            <div className="empty-inline">
              <p>发起查询或建单后，这里会按顺序展示规划、校验和工具调用步骤。</p>
            </div>
          </Card>
        ) : (
          traceSteps.map((step, index) => (
            <TraceStepCard
              key={step.step_id}
              step={step}
              emphasized={step.step_id === latestStepId}
              index={index + 1}
            />
          ))
        )}
      </div>
    </>
  );
}
