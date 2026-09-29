import { Routes, Navigate, Route } from 'react-router-dom';
import Stepper from '@/components/Stepper';
import Login from '@/components/Login';
import ContextPanel from '@/components/layout/ContextPanel';
import ArtifactPanel from '@/components/layout/ArtifactPanel';
import Step1BizGoal from '@/components/steps/Step1BizGoal';
import Step2Evaluation from '@/components/steps/Step2Evaluation';
import Step3Architecture from '@/components/steps/Step3Architecture';
import Step4DiagramTest from '@/components/steps/Step4DiagramTest';
import { useWizardStore } from '@/store/wizardStore';
import { useEffect, useState } from 'react';
import { api } from '@/api/client';

const ARTIFACT_TITLES: Record<number, string> = {
  1: '业务目标草稿',
  2: '验收用例表',
  3: '架构拓扑 JSON',
  4: '本次 Trace 详情',
};

const STEP_HEADERS: Record<number, { eyebrow: string; title: string; description: string }> = {
  1: { eyebrow: '01 / DISCOVER', title: '先把业务目标说清楚', description: '快速生成适合简单任务；深度访谈适合高风险、多人协作或边界复杂的 Agent。' },
  2: { eyebrow: '02 / DEFINE', title: '把成功定义成可验证结果', description: '为每条用例选择判断方式，并用真实输出或外部状态完成判分。' },
  3: { eyebrow: '03 / ASSEMBLE', title: '用 AgentKit 组件组装运行架构', description: '拖入需要的能力，补齐权限与配置，再保存为可测试拓扑。' },
  4: { eyebrow: '04 / VERIFY', title: '运行目标 Agent，并用 Trace 还原事实', description: '设计图与运行时证据分层展示；没有 Span 的组件保持未知。' },
};

export default function App() {
  const { currentStep, setStep, authenticated, setAuthenticated } = useWizardStore();
  const [booted, setBooted] = useState(false);

  useEffect(() => {
    void (async () => {
      try {
        const r = await fetch('/api/auth/status', { credentials: 'include' });
        const j = await r.json();
        if (j.authenticated) setAuthenticated(true);
      } catch { /* stay logged out */ }
      setBooted(true);
    })();
  }, [setAuthenticated]);

  useEffect(() => {
    if (!authenticated) return;
    void (async () => {
      try {
        const [goal, points, cases, topo, datasets] = await Promise.all([
          api.getGoal(),
          api.getPoints(),
          api.getCases(),
          api.getTopology(),
          api.getDatasets(),
        ]);
        const s = useWizardStore.getState();
        s.setGoal(goal);
        s.setPoints(points);
        s.setCases(cases);
        s.setTopology(topo);
        s.setDatasetsConnected(datasets.connected);
      } catch (e) {
        console.error('initial load failed', e);
      }
    })();
  }, [authenticated]);

  if (!booted) return <p style={{ margin: 40 }}>加载中…</p>;
  if (!authenticated) return <Login />;

  const renderMain = () => {
    switch (currentStep) {
      case 1:
        return <Step1BizGoal />;
      case 2:
        return <Step2Evaluation />;
      case 3:
        return <Step3Architecture />;
      case 4:
        return <Step4DiagramTest />;
      default:
        return <Navigate to="/wizard/biz-goal" />;
    }
  };

  const renderArtifact = () => {
    switch (currentStep) {
      case 1:
        return <Step1Artifact />;
      case 2:
        return <Step2Artifact />;
      case 3:
        return <Step3Artifact />;
      case 4:
        return <Step4Artifact />;
      default:
        return null;
    }
  };

  return (
    <div className="app-shell">
      <Stepper />
      <div className="workspace">
        <div className="workspace-col workspace-col-left">
          <ContextPanel />
        </div>
        <div className="workspace-col workspace-col-main">
          <div className="step-heading">
            <div>
              <div className="section-eyebrow">{STEP_HEADERS[currentStep].eyebrow}</div>
              <h1>{STEP_HEADERS[currentStep].title}</h1>
              <p>{STEP_HEADERS[currentStep].description}</p>
            </div>
            <div className="step-status-card">
              <span>阶段状态</span>
              <strong>{useWizardStore.getState().steps[currentStep].completed ? '已确认' : '编辑中'}</strong>
            </div>
          </div>
          <div className="step-surface">{renderMain()}</div>
        </div>
        <div className="workspace-col workspace-col-right">
          <ArtifactPanel title={ARTIFACT_TITLES[currentStep] ?? ''}>
            {renderArtifact()}
          </ArtifactPanel>
        </div>
      </div>
      {/* Routes preserve step in URL */}
      <Routes>
        <Route path="/wizard/biz-goal" element={<RouteSync step={1} setStep={setStep} />} />
        <Route path="/wizard/evaluation" element={<RouteSync step={2} setStep={setStep} />} />
        <Route path="/wizard/architecture" element={<RouteSync step={3} setStep={setStep} />} />
        <Route path="/wizard/diagram-test" element={<RouteSync step={4} setStep={setStep} />} />
        <Route path="*" element={<Navigate to="/wizard/biz-goal" />} />
      </Routes>
    </div>
  );
}

function RouteSync({ step, setStep }: { step: number; setStep: (s: 1|2|3|4) => void }) {
  useEffect(() => {
    setStep(step as 1|2|3|4);
  }, [step, setStep]);
  return null;
}

// --- Artifact previews per step ---
function Step1Artifact() {
  const { goal, adrMarkdown, glossaryMarkdown } = useWizardStore();
  return (
    <div>
      <div className="artifact-pre">{JSON.stringify(goal, null, 2)}</div>
      {adrMarkdown && (
        <>
          <div className="panel-title" style={{ marginTop: 12 }}>ADR</div>
          <div className="artifact-pre">{adrMarkdown}</div>
        </>
      )}
      {glossaryMarkdown && (
        <>
          <div className="panel-title" style={{ marginTop: 12 }}>术语表</div>
          <div className="artifact-pre">{glossaryMarkdown}</div>
        </>
      )}
    </div>
  );
}

function Step2Artifact() {
  const { cases } = useWizardStore();
  return <div className="artifact-pre">{JSON.stringify(cases, null, 2)}</div>;
}

function Step3Artifact() {
  const { topology } = useWizardStore();
  return <div className="artifact-pre">{JSON.stringify(topology, null, 2)}</div>;
}

function Step4Artifact() {
  const { traceOverlay, activeTraceId } = useWizardStore();
  if (!traceOverlay || !activeTraceId) {
    return <div className="empty-placeholder">发送测试后此处显示 trace 详情</div>;
  }
  return (
    <div>
      <div className="mono" style={{ marginBottom: 8 }}>trace_id: {activeTraceId}</div>
      <div className="artifact-pre">{JSON.stringify(traceOverlay, null, 2)}</div>
    </div>
  );
}
