import { Button, Tooltip } from '@arco-design/web-react';
import {
  IconApps,
  IconArrowRight,
  IconCheckCircle,
  IconExport,
  IconRobot,
} from '@arco-design/web-react/icon';
import { useWizardStore } from '@/store/wizardStore';
import type { StepId } from '@/types';

const STEP_META: Record<StepId, { title: string; kicker: string }> = {
  1: { title: '业务目标', kicker: 'DISCOVER' },
  2: { title: '验收与评测', kicker: 'DEFINE' },
  3: { title: '架构设计', kicker: 'ASSEMBLE' },
  4: { title: '测试与追踪', kicker: 'VERIFY' },
};

export default function Stepper() {
  const { currentStep, steps, setStep, markNeedsReview, setAuthenticated } = useWizardStore();

  const handleClick = (step: StepId) => {
    if (steps[step].completed || step === currentStep - 1 || step < currentStep) {
      setStep(step);
      if (step < currentStep) {
        for (let cursor = (step + 1) as StepId; cursor <= 4; cursor = (cursor + 1) as StepId) {
          if (useWizardStore.getState().steps[cursor].completed) markNeedsReview(cursor);
        }
      }
    }
  };

  const logout = async () => {
    await fetch('/api/auth/logout', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    });
    setAuthenticated(false);
  };

  return (
    <header className="top-shell">
      <div className="brand-block">
        <div className="brand-mark"><IconRobot /></div>
        <div>
          <div className="brand-kicker">AGENTKIT LAB</div>
          <div className="brand-title">Agent Builder</div>
        </div>
      </div>

      <nav className="stage-rail" aria-label="Agent 开发步骤">
        {([1, 2, 3, 4] as StepId[]).map((step, index) => {
          const active = step === currentStep;
          const complete = steps[step].completed;
          const enabled = complete || step <= currentStep;
          return (
            <div className="stage-fragment" key={step}>
              <button
                type="button"
                className={`stage-button ${active ? 'is-active' : ''} ${complete ? 'is-complete' : ''}`}
                onClick={() => handleClick(step)}
                disabled={!enabled}
              >
                <span className="stage-number">{complete ? <IconCheckCircle /> : String(step).padStart(2, '0')}</span>
                <span className="stage-copy">
                  <span>{STEP_META[step].kicker}</span>
                  <strong>{STEP_META[step].title}</strong>
                </span>
                {steps[step].needsReview && (
                  <Tooltip content="上游信息已变更，需要重新检查">
                    <i className="review-dot" />
                  </Tooltip>
                )}
              </button>
              {index < 3 && <IconArrowRight className="stage-arrow" />}
            </div>
          );
        })}
      </nav>

      <div className="top-actions">
        <span className="runtime-pill"><i /> HERMES CORE</span>
        <Button className="ghost-button" size="small" icon={<IconApps />}>组件</Button>
        <Button className="ghost-button" size="small" icon={<IconExport />} onClick={() => void logout()}>退出</Button>
      </div>
    </header>
  );
}
