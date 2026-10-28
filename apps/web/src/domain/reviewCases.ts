import type { ReviewMoney } from '@casepilot/contracts';

export const labels: Record<string, string> = {
  target: '目标赔案', related: '关联赔案', insured: '本车', third_party: '第三方',
  paid_closed: '赔付结案', refused_closed: '拒赔结案', zero_closed: '零赔付结案', other_closed: '其他结案',
  settled: '已完成支付', partial: '部分支付', pending: '待处理', failed: '失败', not_applicable: '不适用', unknown: '未知',
  no_injury_reported: '原档案记录未报人伤', injury_reported: '原档案记录有人伤', conflicting_information: '信息冲突',
  not_started: '未启动', running: '执行中', pending_review: '待人工复核', pending_verification: '待核实',
  vehicle_review_completed: '车损审查完成', awaiting_recovery: '待恢复',
  ctpl: '交强险', commercial: '商业险', available: '已取得', not_obtained: '未取得', not_insured: '已确认未投保', unidentified: '无法识别',
  insured_status: '已承保', OWN_DAMAGE: '机动车损失保险', THIRD_PARTY: '机动车第三者责任保险', CTPL: '交强险',
  own_vehicle: '本车车辆损失', third_party_vehicle: '第三方车辆损失', other_property: '其他财产损失', injury: '人伤',
  calculation: '赔款计算', approval: '核赔审批', payment: '支付记录', succeeded: '成功', cancelled: '已取消', approved: '审批通过', rejected: '审批拒绝', final: '有效最终记录', superseded: '已被替代',
  ctpl_policy: '交强险保单', commercial_policy: '商业险保单', endorsement: '批单或特别约定', claim_notification: '报案或申请记录', accident_proof: '事故证明', survey: '查勘记录', vehicle_driver_summary: '车辆驾驶人摘要', assessment: '定损核损明细', repair_cost: '维修及费用证明', transaction: '支付退款冲销记录', closure: '结案记录', adjustment: '调整或损失确认',
  case_document: '案件材料', shared_document: '共享资料', structured_record: '结构化记录',
};

export function label(value: string | null | undefined): string {
  if (!value) return '未提供';
  if (value === 'insured') return '本车';
  return labels[value] ?? value;
}

export function formatMoney(value: ReviewMoney | null | undefined): string {
  if (!value || value.status === 'unknown') return value?.reason ? `未知（${value.reason}）` : '未知';
  if (value.status === 'not_applicable') return value.reason ? `不适用（${value.reason}）` : '不适用';
  return new Intl.NumberFormat('zh-CN', { style: 'currency', currency: value.currency ?? 'CNY' }).format((value.amountFen ?? 0) / 100);
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '未提供';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(parsed);
}
