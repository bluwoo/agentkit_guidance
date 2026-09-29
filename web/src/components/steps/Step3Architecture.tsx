import { useCallback, useEffect, useMemo, useState } from 'react';
import ReactFlow, {
  Background, Controls, MiniMap, addEdge, useNodesState, useEdgesState,
  type Connection, type Edge, type Node, MarkerType,
} from 'reactflow';
import dagre from 'dagre';
import { Button, Input, Select, Tag, Empty, Tooltip } from '@arco-design/web-react';
import { IconUndo, IconRedo, IconDelete } from '@arco-design/web-react/icon';
import { api } from '@/api/client';
import { useWizardStore } from '@/store/wizardStore';
import { COMPONENT_CATALOG, COMPONENT_GROUPS } from '@/data/componentCatalog';
import { DEFAULT_TOPOLOGY } from '@/data/defaultTopology';
import type { ComponentDef } from '@/data/componentCatalog';
import CustomNode from '@/components/graph/CustomNode';
import type { EdgeType, NodeKind, TopologyEdge, TopologyNode } from '@/types';

const nodeTypes = { custom: CustomNode };

const EDGE_STYLE: Record<EdgeType, { strokeDasharray?: string; animated?: boolean }> = {
  sync: {},
  stream: { animated: true },
  data_flow: { strokeDasharray: '5 3' },
  config: { strokeDasharray: '2 4' },
};

let idCounter = 100;
function nextId(kind: string) {
  idCounter += 1;
  return `${kind}:n${idCounter}`;
}

/** Run dagre layered layout and return positioned nodes. */
function autoLayout(nodes: Node[], edges: Edge[]): Node[] {
  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir: 'TB', nodesep: 60, ranksep: 80 });
  g.setDefaultEdgeLabel(() => ({}));
  nodes.forEach((n) => g.setNode(n.id, { width: 160, height: 60 }));
  edges.forEach((e) => g.setEdge(e.source, e.target));
  dagre.layout(g);
  return nodes.map((n) => {
    const pos = g.node(n.id);
    return { ...n, position: { x: pos.x - 80, y: pos.y - 30 } };
  });
}

export default function Step3Architecture() {
  const {
    topology, setTopology, selectedNodeId, setSelectedNode,
    validationIssues, setValidationIssues, recommendations, setRecommendations,
    markCompleted,
  } = useWizardStore();

  const [nodes, setNodes, onNodesChange] = useNodesState<Record<string, unknown>>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Record<string, unknown>>([]);
  const [redoStack, setRedoStack] = useState<Array<{ nodes: Node[]; edges: Edge[] }>>([]);
  const [history, setHistory] = useState<Array<{ nodes: Node[]; edges: Edge[] }>>([]);

  // Hydrate from store topology on mount, or fallback to default topology template
  useEffect(() => {
    let baseTopo = topology;
    if (baseTopo.nodes.length === 0) {
      baseTopo = DEFAULT_TOPOLOGY;
      setTopology(baseTopo);
      void api.saveTopology(baseTopo);
    }
    const ns: Node[] = baseTopo.nodes.map((n) => ({
      id: n.component_id,
      type: 'custom',
      position: { x: n.x ?? 0, y: n.y ?? 0 },
      data: {
        kind: n.kind,
        label: n.label,
        missingConfig: !isNodeConfigured(n),
        config: n.config,
      },
    }));
    const es: Edge[] = baseTopo.edges.map((e) => ({
      id: e.edge_id,
      source: e.source,
      target: e.target,
      type: 'default',
      animated: EDGE_STYLE[e.type].animated,
      style: { strokeDasharray: EDGE_STYLE[e.type].strokeDasharray },
      markerEnd: { type: MarkerType.ArrowClosed },
    }));
    setNodes(ns);
    setEdges(es);
    void runValidation(ns, es);
    void loadRecommendations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const pushHistory = useCallback(
    (ns: Node[], es: Edge[]) => {
      setHistory((h) => [...h.slice(-20), { nodes: ns, edges: es }]);
      setRedoStack([]);
    },
    [],
  );

  const onConnect = useCallback(
    (conn: Connection) => {
      setEdges((eds) => addEdge({ ...conn, markerEnd: { type: MarkerType.ArrowClosed } }, eds));
    },
    [setEdges],
  );

  const undo = () => {
    setHistory((h) => {
      if (h.length === 0) return h;
      const prev = h[h.length - 1];
      setRedoStack((r) => [...r, { nodes, edges }]);
      setNodes(prev.nodes);
      setEdges(prev.edges);
      return h.slice(0, -1);
    });
  };

  const redo = () => {
    setRedoStack((r) => {
      if (r.length === 0) return r;
      const next = r[r.length - 1];
      setHistory((h) => [...h, { nodes, edges }]);
      setNodes(next.nodes);
      setEdges(next.edges);
      return r.slice(0, -1);
    });
  };

  const clearCanvas = () => {
    pushHistory(nodes, edges);
    setNodes([]);
    setEdges([]);
  };

  const doAutoLayout = () => {
    const laid = autoLayout(nodes, edges);
    pushHistory(nodes, edges);
    setNodes(laid);
  };

  // Drag from component library
  const onDragStart = (e: React.DragEvent, def: ComponentDef) => {
    e.dataTransfer.setData('application/component', JSON.stringify(def));
    e.dataTransfer.effectAllowed = 'move';
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const raw = e.dataTransfer.getData('application/component');
    if (!raw) return;
    const def = JSON.parse(raw) as ComponentDef;
    const id = nextId(def.kind);
    const bounds = (e.currentTarget as HTMLElement).getBoundingClientRect();
    const newNode: Node = {
      id,
      type: 'custom',
      position: { x: e.clientX - bounds.left - 80, y: e.clientY - bounds.top - 30 },
      data: {
        kind: def.kind as NodeKind,
        label: def.label,
        missingConfig: true,
        config: {},
      },
    };
    pushHistory(nodes, edges);
    setNodes((nds) => nds.concat(newNode));
    setSelectedNode(id);
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const toTopology = (currentNodes: Node[] = nodes, currentEdges: Edge[] = edges) => ({
    nodes: currentNodes.map((n) => ({
      component_id: n.id,
      kind: n.data.kind as NodeKind,
      label: n.data.label as string,
      config: (n.data.config as Record<string, unknown>) ?? {},
      skill_ref: null,
      x: n.position.x,
      y: n.position.y,
    } as TopologyNode)),
    edges: currentEdges.map((e) => ({
      edge_id: e.id,
      source: e.source,
      target: e.target,
      type: (e.data?.type as EdgeType) ?? 'sync',
    } as TopologyEdge)),
  });

  // Validation
  const runValidation = async (ns: Node[] = nodes, es: Edge[] = edges) => {
    const draft = toTopology(ns, es);
    const issues = await api.validateTopology(draft);
    setValidationIssues(issues);
    return issues;
  };

  const loadRecommendations = async () => {
    const r = await api.recommendComponents();
    setRecommendations(r.component_ids);
  };

  // Selected node config editing
  const selectedNode = nodes.find((n) => n.id === selectedNodeId);
  const selectedDef = useMemo(() => {
    if (!selectedNode) return null;
    return COMPONENT_CATALOG.find((c) => c.kind === (selectedNode.data.kind as NodeKind));
  }, [selectedNode]);

  const updateNodeConfig = (key: string, value: string) => {
    if (!selectedNode) return;
    setNodes((nds) =>
      nds.map((n) =>
        n.id === selectedNode.id
          ? {
              ...n,
              data: {
                ...n.data,
                config: { ...(n.data.config as Record<string, unknown>), [key]: value },
              },
            }
          : n,
      ),
    );
  };

  const issues = validationIssues;
  const hasErrors = issues.some((i) => i.severity === 'error');
  const allPass = issues.length === 0;

  const syncToStore = async () => {
    const draft = toTopology();
    setTopology(draft);
    await api.saveTopology(draft);
    const currentIssues = await runValidation(nodes, edges);
    return currentIssues;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Validation bar */}
      <div className={`validation-bar ${allPass ? 'ok' : 'has-issues'}`}>
        {allPass ? (
          <span>✓ 架构校验通过</span>
        ) : (
          <div>
            {issues.map((i, idx) => (
              <div key={idx} style={{ cursor: 'pointer' }} onClick={() => i.component_id && setSelectedNode(i.component_id)}>
                <Tag color={i.severity === 'error' ? 'red' : 'orange'} size="small">{i.code}</Tag>
                {' '}{i.message}
              </div>
            ))}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        {/* Left: component library */}
        <div style={{ width: 220, borderRight: '1px solid #e5e6eb', overflowY: 'auto', padding: 12 }}>
          <div className="panel-title">智能推荐</div>
          {recommendations.length === 0 ? (
            <Empty
              style={{ margin: '12px 0' }}
              description="暂无足够信息，请先补全业务目标"
            />
          ) : (
            <div>推荐组件：{recommendations.join(', ')}</div>
          )}

          <div className="panel-title" style={{ marginTop: 16 }}>组件卡片库</div>
          {COMPONENT_GROUPS.map((group) => {
            const defs = COMPONENT_CATALOG.filter((c) => c.group === group);
            if (defs.length === 0) return null;
            return (
              <div key={group} style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 11, color: '#86909c', marginBottom: 4 }}>{group}</div>
                {defs.map((d) => (
                  <Tooltip key={d.kind} content={`前置：${d.prerequisites.join('、') || '无'} | 权限：${d.permissions.join('、') || '无'}`}>
                    <div
                      draggable
                      onDragStart={(e) => onDragStart(e, d)}
                      style={{
                        padding: '6px 8px',
                        border: '1px solid #e5e6eb',
                        borderRadius: 4,
                        marginBottom: 4,
                        cursor: 'grab',
                        background: '#fff',
                        fontSize: 12,
                      }}
                    >
                      {d.label}
                      <div style={{ fontSize: 10, color: '#86909c' }}>{d.purpose}</div>
                    </div>
                  </Tooltip>
                ))}
              </div>
            );
          })}
        </div>

        {/* Middle: canvas */}
        <div style={{ flex: 1, position: 'relative' }}>
          {/* Toolbar */}
          <div style={{ position: 'absolute', top: 8, left: 8, zIndex: 10, display: 'flex', gap: 4 }}>
            <Button size="small" icon={<IconUndo />} onClick={undo} disabled={history.length === 0} />
            <Button size="small" icon={<IconRedo />} onClick={redo} disabled={redoStack.length === 0} />
            <Button size="small" onClick={doAutoLayout}>自动布局</Button>
            <Button size="small" icon={<IconDelete />} onClick={clearCanvas} />
            <Button size="small" onClick={() => void syncToStore()}>保存草稿</Button>
          </div>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={(ch) => {
              onNodesChange(ch);
            }}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onNodeClick={(_, node) => setSelectedNode(node.id)}
            fitView
          >
            <Background />
            <Controls />
            <MiniMap />
          </ReactFlow>
        </div>

        {/* Right: config panel */}
        <div style={{ width: 260, borderLeft: '1px solid #e5e6eb', overflowY: 'auto', padding: 12 }}>
          {!selectedNode || !selectedDef ? (
            <div className="empty-placeholder">点击画布节点查看配置</div>
          ) : (
            <div>
              <div className="panel-title">{selectedNode.data.label as string}</div>
              {selectedDef.configSchema.map((f) => {
                const val = (selectedNode.data.config as Record<string, unknown>)?.[f.key] as string ?? '';
                const missing = f.required && !val;
                return (
                  <div key={f.key} style={{ marginBottom: 10 }}>
                    <div style={{ fontSize: 12, marginBottom: 4 }}>
                      {f.label}
                      {f.required && <Tag color="orange" size="small" style={{ marginLeft: 4 }}>必填</Tag>}
                      {missing && <Tag color="red" size="small" style={{ marginLeft: 4 }}>缺失</Tag>}
                    </div>
                    {f.type === 'select' ? (
                      <Select
                        value={val || undefined}
                        onChange={(v) => updateNodeConfig(f.key, v as string)}
                        size="small"
                        style={{ width: '100%' }}
                      >
                        {f.options?.map((o) => <Select.Option key={o} value={o}>{o}</Select.Option>)}
                      </Select>
                    ) : f.type === 'textarea' ? (
                      <Input.TextArea value={val} onChange={(v) => updateNodeConfig(f.key, v)} rows={2} />
                    ) : (
                      <Input value={val} onChange={(v) => updateNodeConfig(f.key, v)} placeholder={f.placeholder} size="small" />
                    )}
                  </div>
                );
              })}
              {selectedNode.data.kind === 'wizard_core' && (
                <div className="mono" style={{ marginTop: 8, color: '#86909c' }}>
                  {WIZARD_BASE_NOTE}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div style={{ padding: 12, borderTop: '1px solid #e5e6eb', display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          type="primary"
          disabled={hasErrors || nodes.length === 0}
          onClick={() => {
            void (async () => {
              const currentIssues = await syncToStore();
              if (currentIssues.some((issue) => issue.severity === 'error')) return;
              markCompleted(3);
              useWizardStore.getState().setStep(4);
            })();
          }}
        >
          下一步：架构图 + 测试
        </Button>
      </div>
    </div>
  );
}

const WIZARD_BASE_NOTE =
  '底座 = Hermes Agent (AIAgent.run_conversation) + FastAPI Shim，非 veADK Agent。';

function isNodeConfigured(n: TopologyNode): boolean {
  // A node is "configured" if all required fields are filled.
  const def = COMPONENT_CATALOG.find((c) => c.kind === n.kind);
  if (!def) return true;
  return def.configSchema
    .filter((f) => f.required)
    .every((f) => Boolean(n.config[f.key]));
}
