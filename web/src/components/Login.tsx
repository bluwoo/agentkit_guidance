import { useEffect, useState } from 'react';
import { Button, Input, Message } from '@arco-design/web-react';
import { IconLock, IconRobot } from '@arco-design/web-react/icon';
import { useWizardStore } from '@/store/wizardStore';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [needsSetup, setNeedsSetup] = useState(false);
  const [error, setError] = useState('');
  const setAuthenticated = useWizardStore((state) => state.setAuthenticated);

  useEffect(() => {
    void (async () => {
      try {
        const response = await fetch('/api/auth/status', { credentials: 'include' });
        const result = await response.json();
        setNeedsSetup(Boolean(result.needs_setup));
        if (result.authenticated) setAuthenticated(true);
      } catch {
        setError('无法连接登录服务');
      }
    })();
  }, [setAuthenticated]);

  const submit = async () => {
    if (!username.trim() || !password) {
      setError('请输入用户名和密码');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: username.trim(), password }),
      });
      if (!response.ok) {
        const result = await response.json().catch(() => ({}));
        throw new Error(result.detail || `登录失败 (${response.status})`);
      }
      setAuthenticated(true);
      Message.success('登录成功');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : '登录失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="login-shell">
      <section className="login-manifesto">
        <div>
          <div className="brand-block">
            <div className="brand-mark"><IconRobot /></div>
            <div><div className="brand-kicker">AGENTKIT LAB</div><div className="brand-title">Agent Builder</div></div>
          </div>
          <h1>从目标<br />到可运行<br />Agent</h1>
          <p>以 Eval-driven Development 组织需求、验收、架构和测试。设计图表达意图，Trace 只表达真实发生的调用。</p>
        </div>
        <div className="login-signal">
          <span>HERMES CORE</span><span>AGENTKIT RUNTIME</span><span>TRACE VERIFIED</span>
        </div>
      </section>

      <section className="login-panel">
        <div className="login-card">
          <div className="section-eyebrow">SECURE WORKSPACE</div>
          <h2>进入构建工作台</h2>
          <p>仅限已授权账号。浏览器不会保存或接触 Runtime、MCP 与模型服务的机器凭据。</p>
          {needsSetup && <p style={{ color: 'var(--wizard-warning)' }}>Owner 尚未由管理员完成受控初始化。</p>}
          <div className="login-field">
            <label className="login-label" htmlFor="wizard-username">用户名</label>
            <Input id="wizard-username" aria-label="用户名" prefix={<IconRobot />} placeholder="输入用户名" value={username} onChange={setUsername} />
          </div>
          <div className="login-field">
            <label className="login-label" htmlFor="wizard-password">密码</label>
            <Input.Password id="wizard-password" aria-label="密码" prefix={<IconLock />} placeholder="输入密码" value={password} onChange={setPassword} onPressEnter={() => void submit()} />
          </div>
          <Button type="primary" long loading={loading} onClick={() => void submit()} style={{ marginTop: 18, height: 40 }}>
            登录并继续
          </Button>
          {error && <p style={{ color: 'var(--wizard-danger)', marginTop: 12 }}>{error}</p>}
          <div className="artifact-foot"><span className="status-dot" /> SESSION PROTECTED · HTTPONLY COOKIE</div>
        </div>
      </section>
    </main>
  );
}
