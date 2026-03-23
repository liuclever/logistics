import { ChevronDownIcon, ChevronUpIcon, FlashlightIcon } from 'tdesign-icons-react';
import { useState } from 'react';
import { Button, Card, Tag } from 'tdesign-react';
import type { ActionListCardData } from '../../types/contracts';

interface ActionListCardProps {
  title: string;
  data: ActionListCardData;
  onSelectAction?: (prompt: string) => void;
}

function modeLabel(mode?: string) {
  switch (mode) {
    case 'auto':
      return '自动执行';
    case 'input_required':
      return '需要输入';
    case 'confirm_required':
      return '需要确认';
    case 'navigation':
      return '建议跳转';
    default:
      return '待处理';
  }
}

export function ActionListCard({ title, data, onSelectAction }: ActionListCardProps) {
  const [expanded, setExpanded] = useState(false);
  const actions = data.actions ?? [];
  const primaryAction = actions[0];
  const remainingActions = actions.slice(1);
  const reasoningSteps = data.thinkingFlow ?? [];

  return (
    <Card className="result-card action-card" title={title}>
      <div className="action-card__hero">
        <div>
          <p className="action-card__summary">{data.summary ?? '已整理下一步动作。'}</p>
          {primaryAction ? (
            <div className="action-card__primary">
              <div className="action-card__primary-top">
                <strong>{primaryAction.label}</strong>
                <Tag size="small" variant="light" theme="primary">
                  {modeLabel(primaryAction.mode)}
                </Tag>
              </div>
              <p>{primaryAction.description}</p>
              <div className="action-card__meta">
                <span>{primaryAction.tool ? `工具: ${primaryAction.tool}` : '工具: 对话输入'}</span>
                {primaryAction.prompt ? <code>{primaryAction.prompt}</code> : null}
              </div>
              <div className="action-card__pulse-line" />
              {primaryAction.prompt ? (
                <div className="action-card__bubble-row">
                  <button
                    type="button"
                    className="action-bubble action-bubble--primary"
                    onClick={() => onSelectAction?.(primaryAction.prompt ?? '')}
                  >
                    {primaryAction.label}
                  </button>
                </div>
              ) : null}
            </div>
          ) : null}
        </div>

        <Button
          className="action-card__toggle"
          variant="text"
          theme="default"
          onClick={() => setExpanded((current) => !current)}
        >
          <FlashlightIcon size={14} />
          {expanded ? '隐藏 AI 思考流' : '查看 AI 思考流'}
          {expanded ? <ChevronUpIcon size={14} /> : <ChevronDownIcon size={14} />}
        </Button>
      </div>

      {expanded ? (
        <section className="thinking-flow">
          <div className="thinking-flow__header">
            <span>模拟推理路径</span>
            <p>只展示产品化决策摘要，不暴露原始链路推理。</p>
          </div>

          <div className="thinking-flow__steps">
            {reasoningSteps.map((step, index) => (
              <article key={step.step_id} className="thinking-step">
                <div className="thinking-step__dot">{`0${index + 1}`.slice(-2)}</div>
                <div className="thinking-step__content">
                  <span>{step.label}</span>
                  <strong>{step.title}</strong>
                  <p>{step.content}</p>
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {remainingActions.length ? (
        <div className="action-list action-list--compact">
          <div className="action-list__bubble-wrap">
            {remainingActions.map((action) => (
              <button
                key={`${action.action_id}-bubble`}
                type="button"
                className={`action-bubble${action.prompt ? '' : ' is-disabled'}`}
                onClick={() => (action.prompt ? onSelectAction?.(action.prompt) : undefined)}
                disabled={!action.prompt}
              >
                <span>{action.label}</span>
                <small>{modeLabel(action.mode)}</small>
              </button>
            ))}
          </div>
        </div>
      ) : null}
    </Card>
  );
}
