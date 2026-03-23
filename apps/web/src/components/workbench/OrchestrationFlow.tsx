import { useState } from 'react';
import type { PendingAction, TraceStatus, TraceStep, WorkspaceSessionState } from '../../types/contracts';
import { buildMissingSlotsCopy, formatTraceStatus, formatWorkflowLabel } from '../../utils/display';

interface OrchestrationFlowProps {
  traceSteps: TraceStep[];
  sessionState: WorkspaceSessionState | null;
  pendingAction?: PendingAction | null;
}

type FlowStageStatus = 'idle' | 'active' | TraceStatus;

interface FlowStage {
  id: string;
  label: string;
  value: string;
  meta: string;
  status: FlowStageStatus;
}

function getStageStatus(kindSteps: TraceStep[], latestStepId?: string): FlowStageStatus {
  if (!kindSteps.length) {
    return 'idle';
  }

  if (kindSteps.some((step) => step.step_id === latestStepId)) {
    return 'active';
  }

  return kindSteps[kindSteps.length - 1]?.status ?? 'idle';
}

function formatStageStatus(status: FlowStageStatus) {
  if (status === 'idle') {
    return '待命';
  }

  if (status === 'active') {
    return '进行中';
  }

  return formatTraceStatus(status);
}

export function OrchestrationFlow({ traceSteps, sessionState, pendingAction }: OrchestrationFlowProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const plan = sessionState?.last_plan;
  const latestStepId = traceSteps[traceSteps.length - 1]?.step_id;
  const decisionSteps = traceSteps.filter((step) => step.kind === 'decision');
  const validationSteps = traceSteps.filter((step) => step.kind === 'validation');
  const toolSteps = traceSteps.filter((step) => step.kind === 'tool');
  const summarySteps = traceSteps.filter((step) => step.kind === 'summary');
  const missingSlotsCopy = buildMissingSlotsCopy(plan?.missing_slots ?? []);

  const stages: FlowStage[] = [
    {
      id: 'intent',
      label: '01 意图',
      value: formatWorkflowLabel(plan?.intent),
      meta: plan?.user_message ? '识别用户目标' : '等待输入消息',
      status: getStageStatus(decisionSteps.slice(0, 1), latestStepId),
    },
    {
      id: 'workflow',
      label: '02 编排',
      value: formatWorkflowLabel(plan?.selected_workflow),
      meta: typeof plan?.confidence === 'number' ? `置信度 ${Math.round(plan.confidence * 100)}%` : '等待编排',
      status: getStageStatus(decisionSteps.slice(1), latestStepId),
    },
    {
      id: 'validation',
      label: '03 校验',
      value: missingSlotsCopy.value,
      meta: missingSlotsCopy.meta,
      status: getStageStatus(validationSteps, latestStepId),
    },
    {
      id: 'tool',
      label: '04 工具',
      value: toolSteps.length ? toolSteps[toolSteps.length - 1]?.title ?? '执行工具' : '待执行',
      meta: toolSteps.length ? `${toolSteps.length} 次工具调用` : '尚未调用工具',
      status: getStageStatus(toolSteps, latestStepId),
    },
    {
      id: 'result',
      label: '05 输出',
      value: pendingAction ? '等待确认' : summarySteps.length ? '生成结果' : '待输出',
      meta: pendingAction?.summary ?? (summarySteps.length ? '已整理为工作台结果' : '执行结束后展示'),
      status: pendingAction ? 'active' : getStageStatus(summarySteps, latestStepId),
    },
  ];

  return (
    <section className={`orchestration-flow ${isCollapsed ? 'is-collapsed' : ''}`}>
      <div className="orchestration-flow__header">
        <div>
          <p className="eyebrow">工作编排流</p>
          <h3>Agent Workflow</h3>
        </div>
        <button
          className="orchestration-flow__toggle"
          onClick={() => setIsCollapsed(!isCollapsed)}
          aria-label={isCollapsed ? '展开' : '收起'}
        >
          {isCollapsed ? '展开' : '收起'}
        </button>
      </div>

      {!isCollapsed && <div className="orchestration-flow__track">
        {stages.map((stage, index) => (
          <div key={stage.id} className={`orchestration-node orchestration-node--${stage.status}`}>
            <div className="orchestration-node__top">
              <span className="orchestration-node__label">{stage.label}</span>
              <span className="orchestration-node__status">{formatStageStatus(stage.status)}</span>
            </div>
            <strong>{stage.value}</strong>
            <p>{stage.meta}</p>
            {index < stages.length - 1 ? <span className="orchestration-node__line" /> : null}
          </div>
        ))}
      </div>}
    </section>
  );
}
