#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_read_status.py (证据驱动版)
从 [SHARD-1]~5-results.md + reading_evidence.jsonl 提取每页读取证据，合并到 read_status.json。
不重新抓取任何页面，不使用 URL 白名单。只有 read_complete=true 的证据才升级为 read_full。
"""
import json, re, os, sys
from urllib.parse import urlparse
from collections import Counter, defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# 1. 分片结果解析（保留原有 offset/total_length 提取逻辑）
# ---------------------------------------------------------------------------
URL_RE = re.compile(r'https?://[^\s\)`"\]<>，。）]+')

def norm_url(u):
    u = u.strip().rstrip('.,;')
    p = urlparse(u)
    host = p.netloc.lower()
    path = p.path.lower().rstrip('/')
    return f"{p.scheme.lower()}://{host}{path}"

def parse_shard(path):
    text = open(path, encoding='utf-8').read()
    lines = text.split('\n')
    pages = []
    cur = None
    header_re = re.compile(r'^(#{2,3})\s+(.*)$')
    for ln in lines:
        m = header_re.match(ln)
        if m:
            if cur and cur.get('url'):
                pages.append(cur)
            title = m.group(2).strip()
            inline = URL_RE.search(title)
            cur = {'title': re.sub(r'\s*\(https?://.*$', '', title).strip(),
                   'url': inline.group(0).rstrip(')').rstrip('.,;') if inline else None,
                   'range_raw': '', 'reached_bottom': None, 'anomaly': '', 'body': []}
            continue
        if cur is None:
            continue
        s = ln.strip()
        if s.startswith('- **URL**') or s.startswith('- **URL**:'):
            um = URL_RE.search(ln)
            if um and not cur['url']:
                cur['url'] = um.group(0).rstrip('.,;)')
            continue
        if s.startswith('- **读取范围**') or s.startswith('- 读取范围'):
            cur['range_raw'] = s
            continue
        if s.startswith('- **是否到底**') or s.startswith('- 是否到底'):
            v = s.split(':', 1)[-1].split('：', 1)[-1].strip()
            cur['reached_bottom'] = v
            continue
        if s.startswith('- **异常**') or s.startswith('- 异常'):
            cur['anomaly'] = s
            continue
        if s.startswith('- **读取状态**') or s.startswith('- 读取状态'):
            cur['read_state'] = s
            continue
        cur['body'].append(ln)
    if cur and cur.get('url'):
        pages.append(cur)
    return pages

def classify(pg):
    rng = pg['range_raw']
    rb = pg['reached_bottom'] or ''
    an = pg['anomaly'] or ''
    rs = pg.get('read_state', '')
    text = ' '.join([rng, rb, an, rs, pg['title']])

    range_empty_kw = ['空壳', '空页', '存根', '占位', '仅导航', '通用占位', '通用文档中心页面',
                     '文档中心占位']
    fail_done_kw = ['重定向到文档中心首页', '重定向到文档中心落地页', '重定向到"新功能',
                    '重定向到"新功能', 'SPA 拦截', 'URL 被重定向', '两次均得到相同重定向',
                    '已重定向到', '拦截页', '欢迎来到文档中心', '落地页', '外部阻塞',
                    '仍失败', '原文档已下线', '原文档已迁移', 'link dead']
    empty_kw = ['空壳', '空页', '存根', '占位', '仅导航', '正文为空', '无正文', '无实质内容',
                '通用文档中心', '文档中心占位', '未渲染实际内容', '仅标题', '页面为空',
                '尚未发布', '敬请期待', '正文为跳转指针', '无独立', '仅有导航']
    is_partial = (rb.startswith('否') or
                  any(k in rng for k in ['部分', '未读完', '总计']) or
                  ('tokens' in rng and '未读完' in rng) or
                  re.search(r'（总[\d]+', rng) is not None)

    if any(k in rng for k in range_empty_kw):
        return 'empty_shell', an or rng
    if any(k in text for k in fail_done_kw):
        return 'failed', an or rng
    if any(k in text for k in empty_kw):
        return 'empty_shell', an or rng
    if is_partial:
        return 'read_partial', rng
    return 'read_full', rng

def parse_offsets(rng_raw):
    s = rng_raw
    total = None
    m_tot = re.search(r'total_length\s*=\s*(\d+)', s)
    if m_tot:
        total = int(m_tot.group(1))
    m_part = re.search(r'总计\s*(\d+)', s) or re.search(r'总\s*(\d+)', s) or re.search(r'/\s*(\d+)', s)
    if m_part and total is None:
        total = int(m_part.group(1))
    big = re.findall(r'\d+', s)
    start = end = None
    if big:
        start = 0
        if len(big) >= 2:
            end = int(big[1])
        elif total is not None:
            end = total
    if '全文读完' in s or '完整读取' in s or '分页读取完成' in s:
        if total is None and end is not None:
            total = end
    return start, end, total

# ---------------------------------------------------------------------------
# 2. 加载 reading_evidence.jsonl（权威浏览器/DOM 证据）
# ---------------------------------------------------------------------------
def load_evidence():
    """返回 {norm_url: evidence_record}"""
    ev = {}
    epath = os.path.join(BASE, 'reading_evidence.jsonl')
    if not os.path.exists(epath):
        print('警告: reading_evidence.jsonl 不存在，浏览器证据为空')
        return ev
    with open(epath, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            nu = norm_url(rec['exact_url'])
            # 如果同 URL 有多条记录，取 read_complete 优先级高的
            if nu in ev:
                prev = ev[nu]
                rank = {True: 3, False: 2, None: 1}
                if rank.get(rec['read_complete'], 1) > rank.get(prev['read_complete'], 1):
                    ev[nu] = rec
            else:
                ev[nu] = rec
    return ev

# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main():
    # 分片解析
    all_pages = []
    for i in range(1, 6):
        fp = os.path.join(BASE, f'shard{i}-results.md')
        ps = parse_shard(fp)
        for p in ps:
            p['shard'] = i
        all_pages.extend(ps)
        print(f'shard{i}: 解析到 {len(ps)} 页')
    print(f'分片合计段落数: {len(all_pages)}')

    for p in all_pages:
        p['status'], p['detail'] = classify(p)
        p['start_offset'], p['end_offset'], p['total_length'] = parse_offsets(p['range_raw'])
        p['norm'] = norm_url(p['url']) if p['url'] else None

    by_norm = defaultdict(list)
    for p in all_pages:
        if p['norm']:
            by_norm[p['norm']].append(p)

    rank = {'read_full': 4, 'empty_shell': 3, 'read_partial': 2, 'failed': 1, 'unread': 0}
    merged = {}
    for n, plist in by_norm.items():
        best = max(plist, key=lambda x: rank.get(x['status'], 0))
        aliases = sorted({p['url'] for p in plist if p['url']})
        merged[n] = {
            'norm': n,
            'status': best['status'],
            'title': best['title'],
            'read_urls': aliases,
            'start_offset': best['start_offset'],
            'end_offset': best['end_offset'],
            'total_length': best['total_length'],
            'shard': best['shard'],
            'detail': best['detail'],
            'occurrences': len(plist),
        }
    print(f'规范化后唯一 URL 数: {len(merged)}')
    print('分片证据状态分布:', dict(Counter(p['status'] for p in all_pages)))

    # 加载证据
    evidence = load_evidence()
    print(f'reading_evidence.jsonl 加载: {len(evidence)} 条证据')

    # 载入 url_map_raw.json
    um = json.load(open(os.path.join(BASE, 'url_map_raw.json'), encoding='utf-8'))
    base_urls = {}
    for path, title in um.items():
        full = 'https://<INTERNAL_HOST>.com' + path
        base_urls[full] = {'title': title, 'norm': norm_url(full)}
    print(f'url_map_raw 基准 URL 数: {len(base_urls)}')

    # 旧 read_status（保留历史页）
    old_rs = json.load(open(os.path.join(BASE, 'read_status.json'), encoding='utf-8'))

    # 从 00-directory.md 重建初始精读集合
    initial_read = set()
    try:
        dtext = open(os.path.join(BASE, '00-directory.md'), encoding='utf-8').read()
        for m in re.finditer(r'^\- \[x\]\s*\[.*?\]\((https?://[^)]+)\)', dtext, re.M):
            initial_read.add(norm_url(m.group(1)))
    except FileNotFoundError:
        pass
    print(f'00-directory.md [x] 初始精读 URL 数: {len(initial_read)}')

    # ------------------------------------------------------------------
    # 合并：以 url_map 为基准
    # ------------------------------------------------------------------
    new_rs = {}
    stat = Counter()
    evidence_upgraded = 0
    evidence_empty_confirmed = 0

    for full, meta in base_urls.items():
        n = meta['norm']
        ev = merged.get(n)
        ev_record = evidence.get(n)

        # 确定最终状态
        if ev:
            base_status = ev['status']
            entry = {
                'title': meta['title'],
                'status': base_status,
                'read_url': ev['read_urls'][0] if ev['read_urls'] else full,
                'aliases': ev['read_urls'],
                'start_offset': ev['start_offset'],
                'end_offset': ev['end_offset'],
                'total_length': ev['total_length'],
                'source_shard': ev['shard'],
                'evidence': ev['detail'],
            }
        elif n in initial_read:
            # 初始 [x] 精读：有读取标记但无 offset/total_length 证据
            # 按证据驱动原则：无法证明完整阅读 → read_partial（待核验）
            entry = {'title': meta['title'],
                     'status': 'read_partial',
                     'read_url': full, 'aliases': [],
                     'start_offset': None, 'end_offset': None, 'total_length': None,
                     'source_shard': 'initial',
                     'evidence': '00-directory.md [x] 初始精读标记，无offset/total_length证据，无法证明完整阅读（待核验）'}
            base_status = 'read_partial'
        else:
            entry = {'title': meta['title'], 'status': 'unread',
                     'read_url': None, 'aliases': [],
                     'start_offset': None, 'end_offset': None, 'total_length': None,
                     'source_shard': None,
                     'evidence': '分片结果与初始精读均无此页证据'}
            base_status = 'unread'

        # ------------------------------------------------------------------
        # 证据驱动状态升级（不使用白名单）
        # ------------------------------------------------------------------
        if ev_record is not None:
            rc = ev_record['read_complete']
            old_status = entry['status']

            if rc is True:
                # 浏览器/DOM 证据确认有完整正文
                if old_status != 'read_full':
                    entry['status'] = 'read_full'
                    # 保留 shard 的 offset/total_length，不清空
                    # 记录 alias（如有 redirect）
                    actual = ev_record.get('actual_url', '')
                    if actual and norm_url(actual) != n:
                        if actual not in entry['aliases']:
                            entry['aliases'].append(actual)
                        entry['evidence'] = (
                            f"{entry.get('evidence','')} | "
                            f"浏览器DOM核验: read_complete=true (actual_url={actual})"
                        )
                    else:
                        entry['evidence'] = (
                            f"{entry.get('evidence','')} | "
                            f"浏览器DOM核验: read_complete=true"
                        )
                    evidence_upgraded += 1

            elif rc is False:
                # 浏览器确认空壳（如 manage-user-information, templates-and-specifications）
                if old_status == 'read_partial':
                    entry['status'] = 'empty_shell'
                    entry['evidence'] = (
                        f"{entry.get('evidence','')} | "
                        f"浏览器DOM核验: read_complete=false（页面存在但无正文body）"
                    )
                    evidence_empty_confirmed += 1

            # rc is None: 保持原状态不变

        new_rs[full] = entry
        stat[entry['status']] += 1

    # 追加旧 read_status 中存在但 url_map 没有的历史页
    extra = []
    for u in old_rs:
        if u not in base_urls:
            n = norm_url(u)
            ev = merged.get(n)
            ev_record = evidence.get(n)

            if ev:
                new_rs[u] = {
                    'title': ev['title'],
                    'status': ev['status'],
                    'read_url': ev['read_urls'][0],
                    'aliases': ev['read_urls'],
                    'start_offset': ev['start_offset'],
                    'end_offset': ev['end_offset'],
                    'total_length': ev['total_length'],
                    'source_shard': ev['shard'],
                    'evidence': ev['detail'],
                }
            else:
                new_rs[u] = {'title': '(历史重试页)', 'status': 'failed',
                             'read_url': u, 'aliases': [],
                             'start_offset': None, 'end_offset': None, 'total_length': None,
                             'source_shard': None,
                             'evidence': '历史失败重试页，分片未提供新证据，维持 failed'}

            # 证据升级
            if ev_record and ev_record['read_complete'] is True:
                if new_rs[u]['status'] != 'read_full':
                    new_rs[u]['status'] = 'read_full'
                    new_rs[u]['evidence'] += ' | 浏览器DOM核验: read_complete=true'
                    evidence_upgraded += 1

            stat[new_rs[u]['status']] += 1
            extra.append(u)

    print(f'新增(不在url_map的历史页): {len(extra)}')
    print(f'证据驱动升级 read_full: {evidence_upgraded} 页')
    print(f'浏览器确认空壳（partial→empty_shell）: {evidence_empty_confirmed} 页')

    # ------------------------------------------------------------------
    # 三个口径统计
    # ------------------------------------------------------------------
    # 口径1: 实体正文页数（read_status.json 中去重后的唯一文档 URL 数）
    entity_pages = len(new_rs)

    # 口径2: 索引别名数（redirect 证据产生的别名 actual_url != exact_url）
    alias_count = 0
    for nu, rec in evidence.items():
        actual = rec.get('actual_url', '')
        if actual and norm_url(actual) != nu:
            alias_count += 1

    # 口径3: 外部页数（DeliveryAI 子产品 + APMPlus + adk.dev + [BASE-ADK].github.io）
    # DeliveryAI 子产品页数（从 00-directory.md 统计）
    deliveryai_pages = 0
    try:
        dtext = open(os.path.join(BASE, '00-directory.md'), encoding='utf-8').read()
        in_deliveryai = False
        for ln in dtext.split('\n'):
            if 'DeliveryAI' in ln and ('##' in ln or '子产品' in ln):
                in_deliveryai = True
            if in_deliveryai and ln.strip().startswith('- ['):
                deliveryai_pages += 1
    except FileNotFoundError:
        pass
    # 外部主机页（adk.dev, [BASE-ADK].github.io, ObservabilityPlatform）
    external_host_pages = 0
    for nu, rec in evidence.items():
        pu = urlparse(rec['exact_url'])
        if pu.netloc not in ['<INTERNAL_HOST>.com']:
            external_host_pages += 1
        elif '/docs/ObservabilityPlatform/' in rec['exact_url']:
            external_host_pages += 1
    external_pages = deliveryai_pages + external_host_pages

    print(f'\n=== 三个口径 ===')
    print(f'  实体正文页数: {entity_pages}')
    print(f'  索引别名数: {alias_count}')
    print(f'  外部页数: {external_pages} (DeliveryAI {deliveryai_pages} + 外部主机 {external_host_pages})')

    # 写出
    out = os.path.join(BASE, 'read_status.json')
    json.dump(new_rs, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f'\n=== 合并完成 ===')
    print(f'read_status.json 总条目: {len(new_rs)}')
    for k in ['read_full', 'read_partial', 'empty_shell', 'failed', 'unread']:
        print(f'  {k}: {stat[k]}')

    # 保存中间产物
    dump = {
        'shard_pages': [{k: v for k, v in p.items() if k != 'body'} for p in all_pages],
        'merged_by_norm': merged,
        'base_urls': base_urls,
        'stat': dict(stat),
        'extra_urls': extra,
        'three_metrics': {
            'entity_pages': entity_pages,
            'alias_count': alias_count,
            'external_pages': external_pages,
            'deliveryai_pages': deliveryai_pages,
            'external_host_pages': external_host_pages,
        },
        'evidence_upgraded': evidence_upgraded,
        'evidence_empty_confirmed': evidence_empty_confirmed,
    }
    json.dump(dump, open(os.path.join(BASE, '_merge_debug.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)
    print('中间产物: _merge_debug.json')

if __name__ == '__main__':
    main()
