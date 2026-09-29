import { useMemo, useState } from 'react';
import { Button, Message, Tag } from '@arco-design/web-react';
import { IconCopy, IconEye, IconEyeInvisible } from '@arco-design/web-react/icon';

interface ArtifactPanelProps {
  title: string;
  children: React.ReactNode;
  onExport?: () => void;
  onCopy?: () => void;
}

export default function ArtifactPanel({ title, children, onExport, onCopy }: ArtifactPanelProps) {
  const [collapsed, setCollapsed] = useState(false);
  const badge = useMemo(() => (collapsed ? 'PAUSED' : 'LIVE'), [collapsed]);

  const handleCopy = async () => {
    if (onCopy) onCopy();
    else Message.info('请在产物区选择需要复制的内容');
  };

  return (
    <aside className="artifact-stack">
      <div className="artifact-head">
        <div>
          <div className="section-eyebrow">LIVE ARTIFACT</div>
          <h3>{title}</h3>
        </div>
        <Tag className={`live-tag ${collapsed ? 'is-muted' : ''}`}><i /> {badge}</Tag>
      </div>
      <div className="artifact-toolbar">
        <Button size="mini" className="ghost-button" icon={collapsed ? <IconEye /> : <IconEyeInvisible />} onClick={() => setCollapsed(!collapsed)}>
          {collapsed ? '展开' : '收起'}
        </Button>
        <Button size="mini" className="ghost-button" icon={<IconCopy />} onClick={() => void handleCopy()}>复制</Button>
        {onExport && <Button size="mini" className="ghost-button" onClick={onExport}>导出</Button>}
      </div>
      {!collapsed && <div className="artifact-body">{children}</div>}
      <div className="artifact-foot">
        <span className="status-dot" /> 所有产物随当前项目保存
      </div>
    </aside>
  );
}
