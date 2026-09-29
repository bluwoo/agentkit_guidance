import { useState } from 'react';
import {
  Alert, Button, Input, Message, Popconfirm, Select, Table, Tag,
} from '@arco-design/web-react';
import { IconDelete, IconExperiment, IconPlus, IconSave } from '@arco-design/web-react/icon';
import { api } from '@/api/client';
import { useWizardStore } from '@/store/wizardStore';
import type { AcceptanceCase, EvaluationRun, JudgmentType } from '@/types';

const JUDGMENT_OPTIONS: Array<{ value: JudgmentType; label: string; color: string }> = [
  { value: 'artifact', label: '产物检查', color: 'blue' },
  { value: 'external_state', label: '外部状态', color: 'green' },
  { value: 'llm_judge', label: 'LLM Judge', color: 'purple' },
  { value: 'rule', label: '确定性规则', color: 'orange' },
];

export default function Step2Evaluation() {
  const { cases, setCases, evalDatasetsConnected, markCompleted } = useWizardStore();
  const [runtimeId, setRuntimeId] = useState((import.meta.env.VITE_TARGET_RUNTIME_ID as string | undefined) ?? '');
  const [run, setRun] = useState<EvaluationRun | null>(null);
  const [busy, setBusy] = useState(false);

  const addCase = () => setCases([...cases, {
    eval_id: `case-${Date.now()}`, description: '', input_sample: '', expected: '',
    judgment_type: 'rule', judgment_detail: { operator: 'contains' },
    pass_threshold: '', boundary_case: '', baseline_locked: true,
  }]);
  const removeCase = (id: string) => setCases(cases.filter((item) => item.eval_id !== id));
  const updateCase = (id: string, patch: Partial<AcceptanceCase>) =>
    setCases(cases.map((item) => (item.eval_id === id ? { ...item, ...patch } : item)));

  const save = async () => {
    await api.saveCases(cases);
    Message.success('验收用例已保存');
  };

  const runCases = async () => {
    if (!runtimeId.trim()) return Message.warning('请先填写目标 Agent runtime_id');
    if (!cases.length) return Message.warning('请至少添加一条用例');
    setBusy(true);
    try {
      await api.saveCases(cases);
      const result = await api.runEvaluation(runtimeId.trim(), cases);
      setRun(result);
      if (result.failed) Message.warning(`完成：${result.passed} 通过，${result.failed} 未通过`);
      else Message.success(`全部 ${result.passed} 条用例通过`);
    } catch (cause) {
      Message.error(cause instanceof Error ? cause.message : '评测运行失败');
    } finally { setBusy(false); }
  };

  const columns = [
    { title: '场景', dataIndex: 'description', render: (_: string, item: AcceptanceCase) => <Input value={item.description} onChange={(value) => updateCase(item.eval_id, { description: value })} placeholder="例如：识别发票类工单" size="small" /> },
    { title: '真实输入', dataIndex: 'input_sample', render: (_: string, item: AcceptanceCase) => <Input value={item.input_sample} onChange={(value) => updateCase(item.eval_id, { input_sample: value })} placeholder="发送给目标 Agent 的输入" size="small" /> },
    { title: '预期结果', dataIndex: 'expected', render: (_: string, item: AcceptanceCase) => <Input value={item.expected} onChange={(value) => updateCase(item.eval_id, { expected: value })} placeholder="结果中必须包含的内容" size="small" /> },
    { title: '判断方式', dataIndex: 'judgment_type', width: 138, render: (_: JudgmentType, item: AcceptanceCase) => <Select value={item.judgment_type} onChange={(value) => updateCase(item.eval_id, { judgment_type: value as JudgmentType })} size="small" style={{ width: 126 }}>{JUDGMENT_OPTIONS.map((option) => <Select.Option key={option.value} value={option.value}><Tag color={option.color} size="small">{option.label}</Tag></Select.Option>)}</Select> },
    { title: '', dataIndex: 'actions', width: 42, render: (_: unknown, item: AcceptanceCase) => <Popconfirm title="删除此用例？" onOk={() => removeCase(item.eval_id)}><Button size="mini" type="text" icon={<IconDelete />} /></Popconfirm> },
  ];

  return (
    <div style={{ padding: 4, display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Alert type="info" style={{ marginBottom: 14 }} content="判断真实输出与外部状态，不采信 Agent 的完成声明。未配置的判断器会明确标记未通过。" />
      <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end', marginBottom: 12 }}>
        <div style={{ flex: 1 }}><div className="panel-title">目标 Agent runtime_id</div><Input value={runtimeId} onChange={setRuntimeId} placeholder="输入独立目标 Agent 的 runtime_id" /></div>
        <Button icon={<IconPlus />} onClick={addCase}>添加用例</Button>
        <Button icon={<IconSave />} onClick={() => void save()}>保存</Button>
        <Button type="primary" icon={<IconExperiment />} loading={busy} onClick={() => void runCases()}>运行并判分</Button>
      </div>
      <div style={{ marginBottom: 10 }}>
        {evalDatasetsConnected ? <Tag color="green">已连接评测服务</Tag> : <Tag color="gray">本地验收用例</Tag>}
        <span style={{ marginLeft: 8, color: 'var(--wizard-text-muted)', fontSize: 11 }}>baseline_locked 用例不会被自进化流程自动改写</span>
      </div>
      <Table rowKey="eval_id" columns={columns} data={cases} pagination={false} size="small" style={{ flex: 1 }} />
      {run && (
        <div style={{ marginTop: 12 }}>
          <div className="panel-title">最新评测结果 · {run.passed} 通过 / {run.failed} 未通过</div>
          <div className="artifact-pre">{run.results.map((item) => `${item.passed ? 'PASS' : 'FAIL'}  ${item.eval_id}\n${item.reason}\n实际输出：${item.actual_output || '—'}\n证据：${JSON.stringify(item.evidence)}\n`).join('\n')}</div>
        </div>
      )}
      <div style={{ marginTop: 14, display: 'flex', justifyContent: 'flex-end' }}>
        <Button type="primary" disabled={!run || run.failed > 0} onClick={() => { markCompleted(2); useWizardStore.getState().setStep(3); }}>下一步：架构设计</Button>
      </div>
    </div>
  );
}
