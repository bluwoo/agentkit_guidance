import { useState } from 'react';
import {
  Button, Input, Checkbox, Modal, Message, Radio, Empty,
} from '@arco-design/web-react';
import { IconDelete } from '@arco-design/web-react/icon';
import { api } from '@/api/client';
import { useWizardStore } from '@/store/wizardStore';

const { TextArea } = Input;

export default function Step1BizGoal() {
  const [mode, setMode] = useState<'grill' | 'quick'>('grill');
  const {
    chatMessages, appendChatMessage, points, removePoint, togglePoint,
    interviewStarted, setInterviewStarted, setAdr, setGlossary,
    setGoal, goal, markCompleted,
  } = useWizardStore();

  // Quick-mode form state
  const [qName, setQName] = useState(goal.name);
  const [qDesc, setQDesc] = useState(goal.task);
  const [qUser, setQUser] = useState(goal.target_user);
  const [qLang, setQLang] = useState('中文');
  const [qDraft, setQDraft] = useState('');
  const [quickLoading, setQuickLoading] = useState(false);

  // Chat state
  const [input, setInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  const startInterview = async () => {
    setInterviewStarted(true);
    setChatLoading(true);
    try {
      await api.chatStream('sess-step1', '', (delta) => {
        appendChatMessage({ id: `w${Date.now()}-${Math.random()}`, role: 'wizard', text: delta });
      });
    } catch {
      Message.error('无法启动访谈');
    } finally {
      setChatLoading(false);
    }
  };

  const sendChat = async () => {
    if (!input.trim() || chatLoading) return;
    const text = input.trim();
    appendChatMessage({ id: `u${Date.now()}`, role: 'user', text });
    setInput('');
    setChatLoading(true);
    const replyId = `w${Date.now()}`;
    appendChatMessage({ id: replyId, role: 'wizard', text: '' });
    try {
      const { points: newPoints } = await api.chatStream('sess-step1', text, (delta) => {
        const s = useWizardStore.getState();
        const updated = s.chatMessages.map((m) =>
          m.id === replyId ? { ...m, text: m.text + delta } : m,
        );
        s.setChatMessages(updated);
      });
      const s = useWizardStore.getState();
      if (newPoints.length > 0) {
        s.appendChatMessage({
          id: `p${Date.now()}`,
          role: 'wizard',
          text: `我抽取到以下要点，请确认：\n${newPoints.map((p) => `• ${p}`).join('\n')}`,
        });
        newPoints.forEach((p) => s.addPoint(p));
      }
    } catch {
      Message.error('访谈请求失败');
    } finally {
      setChatLoading(false);
    }
  };

  const generateQuick = async () => {
    setQuickLoading(true);
    try {
      const g = await api.generateQuickGoal({
        name: qName,
        description: qDesc,
        target_user: qUser,
        language: qLang,
        external_systems: [],
      });
      setGoal(g);
      setQDraft(JSON.stringify(g, null, 2));
      Message.success('已生成业务目标草稿');
    } finally {
      setQuickLoading(false);
    }
  };

  const genADR = async () => {
    const md = await api.generateADR();
    setAdr(md);
    Message.success('ADR 草稿已生成');
  };
  const genGlossary = async () => {
    const md = await api.generateGlossary();
    setGlossary(md);
    Message.success('术语表草稿已生成');
  };

  const goNext = async () => {
    await api.saveGoal(goal);
    markCompleted(1);
    useWizardStore.getState().setStep(2);
  };

  return (
    <div style={{ padding: 20, display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Radio.Group
        type="button"
        value={mode}
        onChange={(v) => {
          if (chatMessages.length > 0 && v !== mode) {
            Modal.info({
              title: '切换模式',
              content: '切换模式将保留已确认要点但重置当前输入。',
              onOk: () => setMode(v as 'grill' | 'quick'),
            });
          } else {
            setMode(v as 'grill' | 'quick');
          }
        }}
        style={{ marginBottom: 16, alignSelf: 'flex-start' }}
      >
        <Radio value="grill">深度访谈 grill-with-docs</Radio>
        <Radio value="quick">快速生成表单</Radio>
      </Radio.Group>

      {mode === 'grill' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 260px', gap: 16, flex: 1, minHeight: 0 }}>
          {/* Chat area */}
          <div style={{ display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            {!interviewStarted ? (
              <div className="empty-placeholder" style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <div style={{ marginBottom: 16 }}>
                  grill-with-docs 是显式触发的流程型 skill（不会自动启动）。
                </div>
                <Button type="primary" size="large" onClick={startInterview}>
                  开始访谈
                </Button>
              </div>
            ) : (
              <>
                <div className="chat-scroll">
                  {chatMessages.map((m) => (
                    <div key={m.id} className={`chat-bubble ${m.role}`}>
                      {m.text.split('\n').map((line, i) => (
                        <div key={i}>{line || '\u00a0'}</div>
                      ))}
                    </div>
                  ))}
                  {chatLoading && <div className="chat-bubble wizard">正在输入…</div>}
                </div>
                <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                  <Input
                    value={input}
                    onChange={(v) => setInput(v)}
                    onPressEnter={sendChat}
                    placeholder="回答 Wizard 的追问…"
                  />
                  <Button type="primary" onClick={sendChat} loading={chatLoading}>
                    发送
                  </Button>
                </div>
              </>
            )}
          </div>

          {/* Confirmed points */}
          <div style={{ borderLeft: '1px solid #e5e6eb', paddingLeft: 16 }}>
            <div className="panel-title">已确认要点</div>
            {points.length === 0 ? (
              <Empty description="暂无确认要点" style={{ margin: '12px 0' }} />
            ) : (
              <div>
                {points.map((p) => (
                  <div key={p.id} className="point-item">
                    <Checkbox checked={p.confirmed} onChange={() => togglePoint(p.id)} />
                    <span style={{ flex: 1 }}>{p.text}</span>
                    <Button
                      size="mini"
                      type="text"
                      icon={<IconDelete />}
                      onClick={() => removePoint(p.id)}
                    />
                  </div>
                ))}
              </div>
            )}
            <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
              <Button size="small" onClick={genADR} disabled={points.length === 0}>
                生成 ADR
              </Button>
              <Button size="small" onClick={genGlossary} disabled={points.length === 0}>
                术语表
              </Button>
            </div>
          </div>
        </div>
      )}

      {mode === 'quick' && (
        <div style={{ maxWidth: 640 }}>
          <div style={{ marginBottom: 12 }}>
            <div className="panel-title">Agent 名称</div>
            <Input value={qName} onChange={(v) => setQName(v)} placeholder="e.g. 工单分类助手" />
          </div>
          <div style={{ marginBottom: 12 }}>
            <div className="panel-title">一句话描述这个 Agent 要做什么</div>
            <TextArea
              value={qDesc}
              onChange={(v) => setQDesc(v)}
              placeholder="帮企业客服对工单进行意图分类…"
              rows={3}
            />
          </div>
          <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
            <div style={{ flex: 1 }}>
              <div className="panel-title">服务对象</div>
              <Input value={qUser} onChange={(v) => setQUser(v)} placeholder="企业客服团队" />
            </div>
            <div style={{ flex: 1 }}>
              <div className="panel-title">主要语言</div>
              <Input value={qLang} onChange={(v) => setQLang(v)} />
            </div>
          </div>
          <Button type="primary" onClick={generateQuick} loading={quickLoading}>
            生成业务目标草稿
          </Button>
          {qDraft && (
            <>
              <div className="panel-title" style={{ marginTop: 16 }}>可编辑草稿</div>
              <TextArea value={qDraft} onChange={(v) => setQDraft(v)} rows={10} />
              <div style={{ marginTop: 8 }}>
                <Button size="small" type="primary" onClick={() => {
                  try {
                    setGoal(JSON.parse(qDraft));
                    markCompleted(1);
                    Message.success('已采纳为正式产物');
                  } catch {
                    Message.error('草稿不是合法 JSON');
                  }
                }}>采纳为正式产物</Button>
                <Button size="small" style={{ marginLeft: 8 }} onClick={generateQuick}>重新生成</Button>
              </div>
            </>
          )}
        </div>
      )}

      <div style={{ marginTop: 16, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          type="primary"
          disabled={points.length === 0 && !goal.name}
          onClick={() => void goNext()}
        >
          下一步：定义验收标准
        </Button>
      </div>
    </div>
  );
}
