import { Tag } from '@arco-design/web-react';
import {
  IconBook,
  IconBranch,
  IconBulb,
  IconCheckCircle,
  IconExperiment,
  IconFile,
} from '@arco-design/web-react/icon';
import { useWizardStore } from '@/store/wizardStore';

const GUIDE = [
  { icon: <IconBulb />, title: '先说清目标', text: '定义谁使用、解决什么问题、输出什么结果。' },
  { icon: <IconExperiment />, title: '再写验收方式', text: '检查真实产物或外部状态，而非 Agent 自述。' },
  { icon: <IconBranch />, title: '按证据组装架构', text: '优先选择 AgentKit 组件，缺口明确标注。' },
];

export default function ContextPanel() {
  const { points, goal, cases, currentStep } = useWizardStore();
  const confirmed = points.filter((point) => point.confirmed);

  return (
    <aside className="context-stack">
      <section className="context-hero">
        <div className="section-eyebrow">BUILD CONTEXT</div>
        <h2>把想法压成<br />可验收的 Agent</h2>
        <p>每一步都生成可复用产物，并为下一阶段提供明确输入。</p>
      </section>

      <section className="context-card guide-card">
        <div className="panel-heading"><IconBook /> 当前路径</div>
        <div className="guide-list">
          {GUIDE.map((item, index) => (
            <div className={`guide-row ${index + 1 === currentStep ? 'is-current' : ''}`} key={item.title}>
              <span className="guide-icon">{item.icon}</span>
              <div><strong>{item.title}</strong><p>{item.text}</p></div>
            </div>
          ))}
        </div>
      </section>

      <section className="context-card">
        <div className="panel-heading"><IconFile /> 业务目标</div>
        {goal.name ? (
          <div className="goal-summary">
            <strong>{goal.name}</strong>
            <p>{goal.task || '尚未补充任务描述'}</p>
            {goal.classification && <Tag color="arcoblue">{goal.classification}</Tag>}
          </div>
        ) : <div className="empty-copy">尚未生成业务目标</div>}
      </section>

      <section className="context-card compact-card">
        <div className="panel-heading"><IconCheckCircle /> 已确认要点 <span>{confirmed.length}</span></div>
        {confirmed.length ? (
          <ul>{confirmed.slice(0, 4).map((point) => <li key={point.id}>{point.text}</li>)}</ul>
        ) : <div className="empty-copy">访谈或快速生成后显示</div>}
      </section>

      <section className="context-card compact-card">
        <div className="panel-heading"><IconExperiment /> 验收用例 <span>{cases.length}</span></div>
        {cases.length ? (
          <ul>{cases.slice(0, 4).map((item) => <li key={item.eval_id}>{item.description || item.eval_id}</li>)}</ul>
        ) : <div className="empty-copy">尚未添加验收用例</div>}
      </section>
    </aside>
  );
}
