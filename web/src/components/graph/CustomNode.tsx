import { Handle, Position, type NodeProps } from 'reactflow';
import type { NodeKind } from '@/types';
import { getNodeVisual, WIZARD_BASE_ANNOTATION, SELF_EVOLUTION_ANNOTATION } from '@/utils/nodeStyles';

interface CustomNodeData {
  kind: NodeKind;
  label: string;
  missingConfig: boolean;
  // Optional trace overlay state (only set when overlay is on)
  overlayState?: 'invoked' | 'error' | 'no_span';
  overlayDuration?: number;
  [key: string]: unknown;
}

/**
 * React Flow custom node. Encodes node kind via color/label per 02 §1.
 * Wizard internal nodes get an "内部" badge; missing required config → dashed orange.
 * Trace overlay (when Step4 overlay is enabled) recolors border green/red/grey.
 */
export default function CustomNode({ data, selected }: NodeProps<CustomNodeData>) {
  const visual = getNodeVisual(data.kind);
  const cls = ['react-flow__node-custom'];

  if (data.missingConfig) cls.push('missing-config');
  if (selected) cls.push('selected');
  if (data.overlayState === 'invoked') cls.push('node-overlay-green');
  if (data.overlayState === 'error') cls.push('node-overlay-red');
  if (data.overlayState === 'no_span') cls.push('node-overlay-grey');

  const annotation =
    data.kind === 'wizard_core'
      ? WIZARD_BASE_ANNOTATION
      : data.kind === 'self_evolution'
        ? SELF_EVOLUTION_ANNOTATION
        : null;

  return (
    <div
      className={cls.join(' ')}
      style={{
        borderColor: visual.color,
        background: visual.background,
      }}
    >
      {visual.internal && <div className="internal-badge">内部</div>}
      <Handle type="target" position={Position.Top} />
      <div className="node-kind-badge">{visual.shapeHint}</div>
      <div style={{ fontWeight: 600 }}>{data.label}</div>
      {annotation && (
        <div style={{ fontSize: 9, color: '#86909c', marginTop: 2, maxWidth: 200 }}>
          {annotation}
        </div>
      )}
      {data.overlayDuration !== undefined && (
        <div style={{ fontSize: 10, marginTop: 2, color: '#4e5969' }}>
          {data.overlayDuration.toFixed(0)} ms
        </div>
      )}
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
