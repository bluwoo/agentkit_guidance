#!/usr/bin/env python3
"""从阅读状态表生成审阅缺口，不推断文档是否发布，不修改状态。"""
from pathlib import Path
import json
from collections import Counter

base = Path(__file__).resolve().parent
records = json.loads((base / 'read_status.json').read_text(encoding='utf-8'))
counts = Counter(v['status'] for v in records.values())
lines = [
    '# 文档阅读证据与未完成项',
    '',
    '> 本表依据 read_status.json 生成，展示记录状态，不构成全部来源已独立复核的保证。',
    '> URL 记录包含补录与历史别名，不等于独立正文篇数；返回空白、落地页或其他产品标题不能证明文档未发布。',
    '',
    f'- URL 记录总数：{len(records)}',
]
for key in ('read_full','read_partial','empty_shell','failed','unread'):
    lines.append(f'- {key}：{counts[key]}')
lines += [
    '',
    '**当前未完成“全部官方文档完整阅读”的要求。**',
    '',
    '## 需补核验的原始链接',
    '',
    '| 状态 | 标题 | 原始 URL | 需要完成的核验 |',
    '|---|---|---|---|',
]
for url, record in records.items():
    state = record['status']
    if state == 'read_full':
        continue
    note = ('补齐全文/分页读取证据，不能以摘要替代全文' if state == 'read_partial'
            else '核对真实导航、重定向及正文；本轮未取得匹配有效正文')
    title = str(record.get('title','')).replace('|','/').replace('\n',' ')
    lines.append(f'| {state} | {title} | {url} | {note} |')
lines += [
    '',
    '## 本阶段验证边界',
    '',
    '- reading_evidence.jsonl 与分片笔记保留阅读来源；旧尝试失败不代表当前原站不可访问。',
    '- 缺失的读取证据应补核验，不应通过预设 URL 白名单修改成 read_full。',
    '- 已有设计和 Skills 可供审阅，但仍需要真实资源与业务运行验证。',
    '- 本阶段未实现 [BASE-AGENT] shim/前端，未创建云资源，未执行云端测试；凭据可用性尚未核验。',
]
(base / '99-gaps.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
print(json.dumps({'records':len(records),'counts':dict(counts)}, ensure_ascii=False))
