import type { TraceKind, TraceStatus } from '../types/contracts';

const TRACE_STATUS_LABELS: Record<TraceStatus, string> = {
  completed: '已完成',
  running: '执行中',
  warning: '需补充',
  failed: '失败',
};

const TRACE_KIND_LABELS: Record<TraceKind, string> = {
  decision: '决策',
  tool: '工具',
  validation: '校验',
  summary: '汇总',
};

const WORKFLOW_LABELS: Record<string, string> = {
  TrackShipmentWorkflow: '轨迹查询',
  CreateShipmentWorkflow: '建单编排',
  QuoteWorkflow: '报价试算',
  OrderLookupWorkflow: '订单浏览',
  ReferenceResolutionWorkflow: '单号解析',
  UnknownWorkflow: '待路由',
  greeting: '欢迎引导',
  track_shipment: '轨迹查询',
  create_shipment: '建单编排',
  quote_shipment: '报价试算',
  order_lookup: '订单浏览',
  confirm_action: '确认动作',
  provide_missing: '补充信息',
  unknown: '待识别',
};

export function getTraceStatusTheme(status: TraceStatus) {
  switch (status) {
    case 'completed':
      return 'success';
    case 'running':
      return 'primary';
    case 'warning':
      return 'warning';
    case 'failed':
      return 'danger';
    default:
      return 'default';
  }
}

export function formatTraceStatus(status: TraceStatus) {
  return TRACE_STATUS_LABELS[status] ?? status;
}

export function formatTraceKind(kind: TraceKind) {
  return TRACE_KIND_LABELS[kind] ?? kind;
}

export function formatWorkflowLabel(value?: string | null) {
  if (!value || value === 'none') {
    return '未激活';
  }

  if (value in WORKFLOW_LABELS) {
    return WORKFLOW_LABELS[value];
  }

  return value
    .replace(/Workflow$/, '')
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .trim();
}

export function buildMissingSlotsCopy(missingSlots: string[]) {
  if (!missingSlots.length) {
    return {
      value: '参数完整',
      meta: '已具备进入下一步的条件',
    };
  }

  const [firstSlot, ...restSlots] = missingSlots;
  return {
    value: '需要补充信息',
    meta: restSlots.length
      ? `我会逐项引导，当前优先补 ${firstSlot}，后续再补 ${restSlots.length} 项。`
      : `我会一步一步引导，当前优先补 ${firstSlot}。`,
  };
}
