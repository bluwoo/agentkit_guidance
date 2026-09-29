import { useCallback, useEffect, useMemo, useState } from 'react';
import ReactFlow, {
  Background, Controls, MiniMap, useNodesState, useEdgesState, MarkerType,
} from 'reactflow';
import {
  Button, Input, Switch, Tag, Drawer, Descriptions, Empty, Alert, Message, Statistic,
} from '@arco-design/web-react';
import { api } from '@/api/client';
import { useWizardStore } from '@/store/wizardStore';
import CustomNode from '@/components/graph/CustomNode';
import type { EdgeType, TraceOverlay } from '@/types';

const nodeTypes = { custom: CustomNode };

const EDGE_STYLE: Record<EdgeType, { strokeDasharray?: string; animated?: boolean }> = {
  sync: {},
  stream: { animated: true },
  data_flow: { strokeDasharray: '5 3' },
  config: { strokeDasharray: '2 4' },
};

export default function Step4DiagramTest() {
  const {
    topology, testState, setTestState,
    testPrompt, setTestPrompt, userId, setUserId, sessionId, setSessionId,
    testOutput, appendTestOutput, resetTestOutput,
    activeTraceId, setActiveTraceId, traceOverlay, setTraceOverlay,
    traceOverlayEnabled, setTraceOverlayEnabled,
    aggregate, setAggregate, testError, setTestError,
    setSelectedNode,
  } = useWizardStore();

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [streamMode, setStreamMode] = useState(true);
  const [drawerNode, setDrawerNode] = useState<string | null>(null);
  const [targetRuntimeId, setTargetRuntimeId] = useState(
    (import.meta.env.VITE_TARGET_RUNTIME_ID as string | undefined) ?? '',
  );

  // Hydrate topology into React Flow
  useEffect(() => {
    const ns = topology.nodes.map((n) => ({
      id: n.component_id,
      type: 'custom',
      position: { x: n.x ?? 0, y: n.y ?? 0 },
      data: {
        kind: n.kind,
        label: n.label,
        missingConfig: false,
        config: n.config,
      },
    }));
    const es = topology.edges.map((e) => ({
      id: e.edge_id,
      source: e.source,
      target: e.target,
      animated: EDGE_STYLE[e.type].animated,
      style: { strokeDasharray: EDGE_STYLE[e.type].strokeDasharray },
      markerEnd: { type: MarkerType.ArrowClosed },
    }));
    setNodes(ns);
    setEdges(es);
  }, [topology, setNodes, setEdges]);

  // Apply trace overlay coloring when overlay is enabled
  useEffect(() => {
    if (!traceOverlayEnabled || !traceOverlay) {
      // Reset to design-time neutral colors
      setNodes((ns) =>
        ns.map((n) => ({
          ...n,
          data: { ...n.data, overlayState: undefined, overlayDuration: undefined },
        })),
      );
      setEdges((es) => es.map((e) => ({ ...e, label: undefined })));
      return;
    }
    const or = traceOverlay.node_runtime;
    const er = traceOverlay.edge_runtime;
    setNodes((ns) =>
      ns.map((n) => {
        const rt = or[n.id];
        if (!rt) {
          return { ...n, data: { ...n.data, overlayState: 'no_span' as const, overlayDuration: undefined } };
        }
        const overlayState = rt.state === 'error'
          ? ('error' as const)
          : rt.state === 'invoked'
            ? ('invoked' as const)
            : ('no_span' as const);
        return {
          ...n,
          data: {
            ...n.data,
            overlayState,
            overlayDuration: rt.duration_ms,
          },
        };
      }),
    );
    setEdges((es) =>
      es.map((e) => {
        const key = `${e.source}->${e.target}`;
        const rt = er[key];
        if (!rt) return { ...e, label: undefined };
        const errTag = rt.error_rate > 0 ? ` (${(rt.error_rate * 100).toFixed(0)}% err)` : '';
        return {
          ...e,
          label: `${rt.count}x · ${rt.duration_ms.toFixed(0)}ms${errTag}`,
          labelStyle: { fontSize: 10 },
          labelBgStyle: { fill: rt.error_rate > 0 ? '#ffece8' : '#fff' },
        };
      }),
    );
  }, [traceOverlayEnabled, traceOverlay, setNodes, setEdges]);

  // Fetch aggregate panel (independent — never attached to a single trace)
  useEffect(() => {
    const runtimeId = targetRuntimeId.trim();
    if (!runtimeId) return;
    void api.getAggregate(runtimeId, '6h').then((a) => setAggregate(a));
  }, [targetRuntimeId, setAggregate]);

  // --- Test invocation (S0 -> S1 -> S2/S3/S4) ---
  const sendInvoke = useCallback(async () => {
    if (!testPrompt.trim()) {
      Message.warning('请输入测试 prompt');
      return;
    }
    resetTestOutput();
    setTestState('S1');
    setTraceOverlayEnabled(false);
    const runtimeId = (targetRuntimeId || '').trim();
    if (!runtimeId) { Message.warning('请在下方填写目标 Agent runtime_id'); return; }

    try {
      let traceId: string | null = null;
      if (streamMode) {
        const r = await api.invokeRuntimeStream(
          { runtime_id: runtimeId, input: testPrompt, user_id: userId, session_id: sessionId || `sess-${Date.now()}` },
          (delta) => appendTestOutput(delta),
        );
        traceId = r.trace_id;
      } else {
        const r = await api.invokeRuntime({
          runtime_id: runtimeId, input: testPrompt, user_id: userId,
          session_id: sessionId || `sess-${Date.now()}`, stream: false,
        });
        if (r.error) throw new Error(r.error);
        appendTestOutput(r.output);
        traceId = r.trace_id;
      }

      setActiveTraceId(traceId);

      // Poll for trace (finite retries per 03 §4.5)
      if (traceId) {
        let overlay: TraceOverlay | null = null;
        for (let attempt = 0; attempt < 10; attempt++) {
          await new Promise((r) => setTimeout(r, 800));
          const o = await api.getTrace(runtimeId, traceId);
          if (o.status === 'ok') {
            overlay = o;
            break;
          }
          if (o.status === 'not_configured' || o.status === 'auth_error' || o.status === 'error') {
            overlay = o;
            break;
          }
          // empty → keep polling (async ingestion delay)
        }
        if (overlay && overlay.status === 'ok') {
          setTraceOverlay(overlay);
          setTestState('S2');
          setTraceOverlayEnabled(true);
          Message.success('测试完成，已获取 trace 覆盖层');
        } else if (overlay) {
          setTraceOverlay(overlay);
          setTestState('S3');
          Message.info('测试完成但无观测数据（不代表未调用）');
        } else {
          setTestState('S3');
        }
      } else {
        setTestState('S3');
      }
    } catch (e) {
      setTestError(e instanceof Error ? e.message : String(e));
      setTestState('S4');
    }
  }, [testPrompt, streamMode, targetRuntimeId, userId, sessionId, appendTestOutput, resetTestOutput, setTestState, setActiveTraceId, setTraceOverlay, setTraceOverlayEnabled, setTestError]);

  // --- Node detail drawer data ---
  const drawerNodeData = useMemo(() => {
    if (!drawerNode || !traceOverlay) return null;
    const designNode = topology.nodes.find((n) => n.component_id === drawerNode);
    const runtime = traceOverlay.node_runtime[drawerNode];
    const spanIds = new Set(runtime?.span_ids ?? []);
    const spans = traceOverlay.spans.filter((span) => spanIds.has(span.span_id));
    return { designNode, spans };
  }, [drawerNode, traceOverlay, topology]);

  const overlayToggleDisabled = testState === 'S0' || testState === 'S1' || testState === 'S4';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Status banner per state machine */}
      {testState === 'S4' && (
        <Alert type="error" style={{ margin: 12 }} content={`测试失败：${testError ?? '未知错误'}`} />
      )}
      {testState === 'S3' && (
        <Alert
          type="warning"
          style={{ margin: 12 }}
          content="无观测数据（观测服务未配置或暂无 trace）。节点保持设计中性色；trace 缺失 ≠ 未调用。"
        />
      )}

      <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        {/* Left: topology + overlay */}
        <div style={{ flex: 1, position: 'relative' }}>
          {/* Toolbar: overlay toggle + legend */}
          <div style={{ position: 'absolute', top: 8, left: 8, zIndex: 10, display: 'flex', gap: 12, alignItems: 'center', background: '#fff', padding: '4px 12px', borderRadius: 4, border: '1px solid #e5e6eb' }}>
            <span style={{ fontSize: 12 }}>Trace 覆盖层</span>
            <Switch
              checked={traceOverlayEnabled}
              onChange={setTraceOverlayEnabled}
              disabled={overlayToggleDisabled}
              size="small"
            />
            <span style={{ fontSize: 11, color: '#86909c' }}>
              <span style={{ color: '#00b42a' }}>●</span> 成功
              {' '}<span style={{ color: '#f53f3f' }}>●</span> 失败
              {' '}<span style={{ color: '#c9cdd4' }}>●</span> 未命中
            </span>
          </div>
          {traceOverlayEnabled && traceOverlay && (
            <div style={{ position: 'absolute', bottom: 8, left: 8, zIndex: 10, background: '#fff', padding: '4px 12px', borderRadius: 4, border: '1px solid #e5e6eb', fontSize: 11 }}>
              trace_id: <span className="mono">{traceOverlay.trace_id}</span>
              {' · '}spans: {traceOverlay.summary.span_nums}
              {traceOverlay.summary.error_span_ids.length > 0 && (
                <Tag color="red" size="small" style={{ marginLeft: 4 }}>
                  {traceOverlay.summary.error_span_ids.length} error
                </Tag>
              )}
            </div>
          )}
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            onNodeClick={(_, node) => {
              setSelectedNode(node.id);
              setDrawerNode(node.id);
            }}
            fitView
            nodesDraggable={false}
            nodesConnectable={false}
          >
            <Background />
            <Controls />
            <MiniMap />
          </ReactFlow>
        </div>

        {/* Right: test panel */}
        <div style={{ width: 320, borderLeft: '1px solid #e5e6eb', padding: 12, overflowY: 'auto' }}>
          <div className="panel-title">测试面板</div>
          <div style={{ marginBottom: 8, fontSize: 12, color: '#86909c' }}>
            目标：{targetRuntimeId.trim() || '尚未选择独立目标 Agent'}
          </div>

          <div style={{ marginBottom: 8 }}>
            <div className="panel-title">测试 prompt</div>
            <Input.TextArea
              value={testPrompt}
              onChange={setTestPrompt}
              rows={3}
              placeholder="输入测试输入…"
            />
          </div>
          <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
            <div style={{ flex: 1 }}>
              <div className="panel-title">目标 Agent runtime_id</div>
              <Input value={targetRuntimeId} onChange={setTargetRuntimeId} size="small" placeholder="如 runtime:hermes" />
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
            <div style={{ flex: 1 }}>
              <div className="panel-title">user_id</div>
              <Input value={userId} onChange={setUserId} size="small" />
            </div>
            <div style={{ flex: 1 }}>
              <div className="panel-title">session_id</div>
              <Input value={sessionId} onChange={setSessionId} size="small" placeholder="留空自动生成" />
            </div>
          </div>
          <div style={{ marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 12 }}>流式 SSE</span>
            <Switch checked={streamMode} onChange={setStreamMode} size="small" />
          </div>
          <Button
            type="primary"
            long
            loading={testState === 'S1'}
            onClick={sendInvoke}
          >
            发送 /invoke
          </Button>

          {testOutput && (
            <div style={{ marginTop: 12 }}>
              <div className="panel-title">响应流</div>
              <div className="artifact-pre" style={{ maxHeight: 200 }}>{testOutput}</div>
              {activeTraceId && (
                <div className="mono" style={{ marginTop: 8, fontSize: 11 }}>
                  trace_id: {activeTraceId}
                </div>
              )}
            </div>
          )}

          {/* observed-unmapped */}
          {traceOverlayEnabled && traceOverlay && traceOverlay.observed_unmapped.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <div className="panel-title" style={{ color: '#f53f3f' }}>
                观测到但未在设计中 ({traceOverlay.observed_unmapped.length})
              </div>
              {traceOverlay.observed_unmapped.map((u, i) => (
                <div key={i} style={{ fontSize: 12, padding: 4, background: '#ffece8', borderRadius: 3, marginBottom: 4 }}>
                  {u.name}
                  <div style={{ fontSize: 10, color: '#86909c' }}>{u.service_name} · {u.operation_name}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Bottom: independent aggregate panel */}
      {aggregate && (
        <div style={{ borderTop: '1px solid #e5e6eb', padding: '8px 16px', background: '#fafbfc' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
            <div className="panel-title" style={{ margin: 0 }}>近 {aggregate.time_window} 聚合</div>
            <span style={{ fontSize: 11, color: '#86909c' }}>{aggregate.note}</span>
            <div style={{ flex: 1 }} />
            {aggregate.connected ? (
              <>
                <Statistic title="P50 时延" value={aggregate.p50_latency_ms ?? '—'} suffix="ms" groupSeparator={false} />
                <Statistic title="P95 时延" value={aggregate.p95_latency_ms ?? '—'} suffix="ms" groupSeparator={false} />
                <Statistic title="QPS" value={aggregate.qps ?? '—'} groupSeparator={false} />
                <Statistic title="错误率" value={aggregate.error_rate != null ? (aggregate.error_rate * 100).toFixed(1) : '—'} suffix="%" groupSeparator={false} />
                <Statistic title="总调用" value={aggregate.total_calls ?? '—'} groupSeparator={false} />
              </>
            ) : (
              <span style={{ fontSize: 12, color: '#86909c' }}>聚合观测服务未连接</span>
            )}
          </div>
        </div>
      )}

      {/* Node detail drawer */}
      <Drawer
        visible={!!drawerNode}
        title={drawerNodeData?.designNode?.label ?? '节点详情'}
        onCancel={() => setDrawerNode(null)}
        width={480}
      >
        {drawerNodeData?.designNode && (
          <Descriptions
            column={1}
            size="small"
            data={[
              { label: 'component_id', value: drawerNodeData.designNode.component_id },
              { label: '类型', value: drawerNodeData.designNode.kind },
              ...Object.entries(drawerNodeData.designNode.config).map(([k, v]) => ({
                label: k,
                value: typeof v === 'object' ? JSON.stringify(v) : String(v),
              })),
            ]}
          />
        )}
        {drawerNodeData && drawerNodeData.spans.length > 0 && (
          <>
            <div className="panel-title" style={{ marginTop: 16 }}>本次调用详情</div>
            {drawerNodeData.spans.map((s) => (
              <div key={s.span_id} className="artifact-pre" style={{ marginBottom: 8 }}>
                <div>{s.name} — {s.duration_ms.toFixed(0)}ms [{s.status.code}]</div>
                {s.status.error_message && (
                  <div style={{ color: '#f53f3f' }}>错误: {s.status.error_message}</div>
                )}
                {s.total_tokens != null && (
                  <div>tokens: {s.total_tokens}</div>
                )}
              </div>
            ))}
          </>
        )}
        {drawerNodeData && drawerNodeData.spans.length === 0 && (
          <Empty description="本次 trace 中无此节点 span" />
        )}
      </Drawer>
    </div>
  );
}
