#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_evidence.py
从真实证据源生成 reading_evidence.jsonl：
1. _merge_debug.json 中的 shard web.fetch 原始证据（offset/total_length）
2. s_0001lffBKE7 trajectory.jsonl 中的浏览器 DOM 读取结果
3. browser-gap-results.md 中的浏览器补读记录

原则：无法证明完整阅读的 read_complete=null，不默认 true。
"""
import json, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
TRAJ = "/home/user/Library/Application Support/DoubaoWork/Default/.doubaowork/agent_mode/workspace/.sessions/38442086078415874/agents/s_0001lffBKE7/system/trajectory.jsonl"

# ---------------------------------------------------------------------------
# 1. 加载 shard web.fetch 证据
# ---------------------------------------------------------------------------
dump = json.load(open(os.path.join(BASE, '_merge_debug.json'), encoding='utf-8'))
shard_pages = dump['shard_pages']

# 按 URL 索引 shard 证据
shard_by_url = {}
for p in shard_pages:
    url = p.get('url')
    if url:
        shard_by_url[url] = p

# ---------------------------------------------------------------------------
# 2. 解析 trajectory.jsonl 提取浏览器 DOM 结果
# ---------------------------------------------------------------------------
# 手动从 trajectory 7 行中提取的真实浏览器结果
# （trajectory 只有 7 行，3 批浏览器调用，无 web.fetch 续读）

# Batch 1: 7 partial pages (trajectory line 3)
browser_batch1 = {
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/manage-user-information?lang=zh": {
        "dom_len": 402, "has_content": False,
        "note": "浏览器DOM仅402字符，全为导航/页脚chrome，无正文body（标题'管理用户信息'+更新时间但无操作步骤）",
        "traj_line": 3,
    },
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/create-space?lang=zh": {
        "dom_len": 3981, "has_content": True,
        "note": "浏览器DOM 3981字符，含'前提条件''空间创建方式说明'等正文",
        "traj_line": 3,
    },
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/demand-center?lang=zh": {
        "dom_len": 3658, "has_content": True,
        "note": "浏览器DOM 3658字符，含'本文介绍''操作场景'等正文",
        "traj_line": 3,
    },
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/templates-and-specifications?lang=zh": {
        "dom_len": 3373, "has_content": False,
        "note": "浏览器DOM 3373字符但全为页脚（关于我们/为什么选火山/版权信息），无正文body",
        "traj_line": 3,
    },
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/custom-tasks?lang=zh": {
        "dom_len": 4079, "has_content": True,
        "note": "浏览器DOM 4079字符，含'本文介绍''注意''自定义任务运行'等正文",
        "traj_line": 3,
    },
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/manage-mcp?lang=zh": {
        "dom_len": 3170, "has_content": True,
        "note": "浏览器DOM 3170字符，含'本文面向''前提条件'等正文",
        "traj_line": 3,
    },
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/handling-deliveryai-requirements?lang=zh": {
        "dom_len": 3971, "has_content": True,
        "note": "浏览器DOM 3971字符，含'前提条件''步骤一：创建需求'等正文",
        "traj_line": 3,
    },
}

# Batch 2: 21 empty_shell pages (trajectory line 5)
browser_batch2 = {
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/UpdatingA2Aspaces?lang=zh": {
        "dom_len": 839, "has_content": True, "note": "含'更新A2A空间''本文介绍''操作步骤'", "traj_line": 5},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Deletingtoolinstances?lang=zh": {
        "dom_len": 1083, "has_content": True, "note": "含'删除沙箱实例''注意事项''操作步骤'", "traj_line": 5},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/mcp-service-access-gateway-instance-via-private-domain?lang=zh": {
        "dom_len": 0, "has_content": False, "note": "首次加载len=0（未渲染完成）", "traj_line": 5},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/create-a-gateway-instance?lang=zh": {
        "dom_len": 4186, "has_content": True, "note": "含'创建网关实例''前提条件''计费'", "traj_line": 5},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/manage-gateway-instances?lang=zh": {
        "dom_len": 2007, "has_content": True, "note": "含'管理网关实例''前提条件''操作步骤'", "traj_line": 5},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/AddingMCPtools?lang=zh": {
        "dom_len": 2313, "has_content": True, "note": "含'添加MCP工具''注意''背景信息'", "traj_line": 5},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/view-mcp-service-network-info?lang=zh": {
        "dom_len": 1906, "has_content": True, "note": "含'前提条件''操作步骤''基本信息'", "traj_line": 5},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/DeletingMCPservices?lang=zh": {
        "dom_len": 1950, "has_content": True, "note": "含'删除MCP服务''应用场景''警告'", "traj_line": 5},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Updatinginboundidentityauthentication-1?lang=zh": {
        "dom_len": 2203, "has_content": True, "note": "含'更新入站身份认证''应用场景''注意'", "traj_line": 5},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Viewgatewayinstancemonitoringdata?lang=zh": {
        "dom_len": 2609, "has_content": True, "note": "含'前提条件''查看说明''查询限制'", "traj_line": 5},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Signaturealgorithm?lang=zh": {
        "dom_len": 624, "has_content": True, "note": "含'签名机制''哈希值计算''加密'", "traj_line": 5},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/APIresponse-6?lang=zh": {
        "dom_len": 2474, "has_content": True, "note": "len=2474，has_content=True（无snippet输出但标记有内容）", "traj_line": 5},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListTools-Batchqueriestooldetails?lang=zh": {
        "dom_len": 7872, "has_content": True, "note": "含'请求参数''Action''Version'等API字段", "traj_line": 5},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListSkills-BatchqueriesdetailsofmultipleSkills?lang=zh": {
        "dom_len": 3933, "has_content": True, "note": "含'请求参数''Action ListSkills''Version'", "traj_line": 5},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListSharingSkills-BatchqueriessharedSkilldetails?lang=zh": {
        "dom_len": 3908, "has_content": True, "note": "含'请求参数''Action ListSharingSkills'", "traj_line": 5},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetKnowledgeConnectionInfo-Queriesknowledgedetails?lang=zh": {
        "dom_len": 3609, "has_content": True, "note": "含'查询知识库详情''请求参数''Action GetKnowledgeConnectionInfo'", "traj_line": 5},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/service-overview?lang=zh": {
        "dom_len": 3052, "has_content": True, "note": "含'服务总览''本文介绍''操作场景'", "traj_line": 5},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/import-user-information?lang=zh": {
        "dom_len": 0, "has_content": False, "note": "首次加载len=0（未渲染完成）", "traj_line": 5},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/management-agent-template?lang=zh": {
        "dom_len": 4054, "has_content": True, "note": "含'管理Agent模板''本文面向''Agent配置页'", "traj_line": 5},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/process-management?lang=zh": {
        "dom_len": 3431, "has_content": True, "note": "含'流程管理''本文面向''节点类型''绑定Agent模板'", "traj_line": 5},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/manage-personal-settings?lang=zh": {
        "dom_len": 0, "has_content": False, "note": "首次加载len=0（未渲染完成）", "traj_line": 5},
}

# Batch 3: 4 failed + 3 retry (trajectory line 7)
browser_batch3 = {
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Creatingtools?lang=zh": {
        "dom_len": 11102, "has_content": True, "note": "含'创建沙箱模板''前提条件''TOS''AK/SK'", "traj_line": 7},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Updatingtooltypes?lang=zh": {
        "dom_len": 1649, "has_content": True, "note": "含'更新模板类型''支持的工具''操作步骤'", "traj_line": 7},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/UpdatingAgentCardaddressesofA2Aagents?lang=zh": {
        "dom_len": 1835, "has_content": True, "note": "含'更新智能体AgentCard地址''背景信息''AgentCard'", "traj_line": 7},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/RuntimeFAQ?lang=zh": {
        "dom_len": 1305, "has_content": True, "note": "含'运行时FAQ''网络访问模式''私网/公网'", "traj_line": 7},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/mcp-service-access-gateway-instance-via-private-domain?lang=zh": {
        "dom_len": 11567, "has_content": True, "note": "重试(+2s等待)后11567字符，含'前提条件''VPC互通''DNS'", "traj_line": 7},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/import-user-information?lang=zh": {
        "dom_len": 1993, "has_content": True, "note": "重试(+2s等待)后1993字符，含'导入用户信息''前提条件''CSV/XLSX模板'", "traj_line": 7},
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/manage-personal-settings?lang=zh": {
        "dom_len": 3592, "has_content": True, "note": "重试(+2s等待)后3592字符，含'管理个人设置''前提条件''个人接入'", "traj_line": 7},
}

# 合并所有浏览器证据
browser_evidence = {}
for url, ev in {**browser_batch1, **browser_batch2, **browser_batch3}.items():
    if url in browser_evidence:
        # 有多次尝试（如batch2 len=0 + batch3 retry成功）
        prev = browser_evidence[url]
        ev['attempts_prev'] = prev
    browser_evidence[url] = ev

# ---------------------------------------------------------------------------
# 3. browser-gap-results.md 证据
# ---------------------------------------------------------------------------
gap_results_evidence = {
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetSessionStore-Queriessessionresourcedetails?lang=zh": {
        "method": "browser_dom",
        "read_complete": True,
        "note": "browser-gap-results.md §3.1: 浏览器完整读取成功，含Status枚举/ProviderType/请求示例",
        "source": "browser-gap-results.md:3.1",
    },
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/SampleA2AagentJSONfile?lang=zh": {
        "method": "browser_dom",
        "read_complete": True,
        "note": "browser-gap-results.md §3.2: 别名URL，浏览器完整读取成功，含A2A 0.3.0 AgentCard全字段",
        "source": "browser-gap-results.md:3.2",
    },
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/MCPserviceAPIfilespecificationsandexamples?lang=zh": {
        "method": "browser_dom",
        "read_complete": True,
        "note": "browser-gap-results.md §3.3: 别名URL，浏览器完整读取成功，含Swagger 2.0/OpenAPI 3.0.1",
        "source": "browser-gap-results.md:3.3",
    },
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Trackingfieldsandmetricsdescription?lang=zh": {
        "method": "browser_dom",
        "read_complete": True,
        "note": "browser-gap-results.md §1.1: 纯导航概述页，含两套埋点方案说明",
        "source": "browser-gap-results.md:1.1",
    },
}

# ---------------------------------------------------------------------------
# 4. 构建 reading_evidence.jsonl
# ---------------------------------------------------------------------------
records = []

# 4a. 对每个 shard 中的非 full 页构建证据记录
for url, sp in shard_by_url.items():
    slug = url.split('/')[-1].split('?')[0]
    status = sp['status']
    end_off = sp.get('end_offset')
    total_len = sp.get('total_length')

    rec = {
        "exact_url": url,
        "actual_url": url,
        "method": "web_fetch",
        "captured_text_path": f"shard{sp['shard']}-results.md",
        "read_complete": None,
        "end_offset": end_off,
        "total_length": total_len,
        "learned_points": sp.get('title', ''),
        "attempts": [],
        "source_trajectory": f"shard{sp['shard']}-results.md (web.fetch原始读取)",
    }

    # web.fetch attempt
    rec['attempts'].append({
        "method": "web_fetch",
        "result": status,
        "error": sp.get('anomaly', ''),
        "range": sp.get('range_raw', ''),
    })

    # shard 自身是否已完整读取
    if status == 'read_full':
        rec['read_complete'] = True
    elif status == 'read_partial':
        # web.fetch 未读完，需要后续证据
        rec['read_complete'] = None  # 待浏览器/续读证据
    elif status == 'empty_shell':
        # web.fetch 抓到空壳，需要浏览器证据判断是否真空
        rec['read_complete'] = None
    elif status == 'failed':
        # web.fetch 重定向失败，需要浏览器证据
        rec['read_complete'] = None

    # 浏览器 DOM 证据
    if url in browser_evidence:
        bv = browser_evidence[url]
        rec['method'] = "browser_dom"
        rec['actual_url'] = url  # 无 redirect
        rec['captured_text_path'] = f"trajectory line {bv['traj_line']}"
        rec['attempts'].append({
            "method": "browser_dom",
            "result": "HAS_CONTENT" if bv['has_content'] else "EMPTY",
            "error": bv['note'],
            "dom_length": bv['dom_len'],
        })
        if bv['has_content']:
            rec['read_complete'] = True
            rec['learned_points'] = bv['note']
        else:
            # 浏览器也确认无正文
            rec['read_complete'] = False
            rec['learned_points'] = bv['note']

    # browser-gap-results.md 证据
    if url in gap_results_evidence:
        ge = gap_results_evidence[url]
        rec['attempts'].append({
            "method": ge['method'],
            "result": "confirmed",
            "error": ge['note'],
        })
        rec['read_complete'] = True
        rec['learned_points'] = ge['note']
        rec['source_trajectory'] = ge['source']

    # [SHARD-2] GetSessionStore 已有 web.fetch 完整读取（990字节到底）
    if slug == 'GetSessionStore-Queriessessionresourcedetails' and sp['shard'] == 2:
        rec['read_complete'] = True
        rec['learned_points'] = "[SHARD-2] web.fetch 0-990/990 已到底，含会话资源详情API"

    records.append(rec)

# 4b. 修正 redirect 别名页：原URL重定向到发布记录，但别名URL有正文
# A2AAgentJSONfileexample → 别名 SampleA2AagentJSONfile（browser-gap-results.md §3.2 确认）
# MCPServiceAPIfile-specificationandexamples → 别名 MCPserviceAPIfilespecificationsandexamples（§3.3 确认）
alias_map = {
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/A2AAgentJSONfileexample?lang=zh": {
        "alias_url": "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/SampleA2AagentJSONfile?lang=zh",
        "note": "原URL重定向到新功能发布记录页；别名URL SampleA2AagentJSONfile 浏览器完整读取成功（A2A 0.3.0 AgentCard全字段）",
        "source": "browser-gap-results.md:3.2",
    },
    "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/MCPServiceAPIfile-specificationandexamples?lang=zh": {
        "alias_url": "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/MCPserviceAPIfilespecificationsandexamples?lang=zh",
        "note": "原URL重定向到新功能发布记录页；别名URL MCPserviceAPIfilespecificationsandexamples 浏览器完整读取成功（Swagger 2.0/OpenAPI 3.0.1）",
        "source": "browser-gap-results.md:3.3",
    },
}
for rec in records:
    if rec['exact_url'] in alias_map:
        am = alias_map[rec['exact_url']]
        rec['actual_url'] = am['alias_url']
        rec['read_complete'] = True
        rec['learned_points'] = am['note']
        rec['attempts'].append({
            "method": "browser_dom", "result": "via_alias",
            "error": am['note'], "alias_url": am['alias_url'],
        })
        rec['source_trajectory'] = am['source']

# 4c. browser-gap-results.md 中的外部页（不在 shard 中的）
external_pages = [
    ("https://<INTERNAL_HOST>.com/docs/ObservabilityPlatform/[PRODUCT]trackingfieldsandmetricsdescription?lang=zh",
     "[PRODUCT]埋点字段与指标说明", True, "browser-gap-results.md:1.2"),
    ("https://volcengine.github.io/[BASE-ADK]-python/cn/docs/framework/span-attributes/",
     "[BASE-ADK]埋点字段说明", True, "browser-gap-results.md:1.3"),
    ("https://adk.dev/workflows/", "ADK Workflows总览", True, "browser-gap-results.md:2.1"),
    ("https://adk.dev/graphs/", "Graph-based Workflows", True, "browser-gap-results.md:2.2"),
    ("https://adk.dev/graphs/dynamic/", "Dynamic Workflows", True, "browser-gap-results.md:2.3"),
    ("https://adk.dev/workflows/collaboration/", "Collaborative Workflows", True, "browser-gap-results.md:2.4"),
    ("https://adk.dev/agents/workflow-agents/sequential-agents/", "SequentialAgent", True, "browser-gap-results.md:2.5.1"),
    ("https://adk.dev/agents/workflow-agents/loop-agents/", "LoopAgent", True, "browser-gap-results.md:2.5.2"),
    ("https://adk.dev/agents/workflow-agents/parallel-agents/", "ParallelAgent", True, "browser-gap-results.md:2.5.3"),
    ("https://adk.dev/agents/routing/", "Agent Routing", True, "browser-gap-results.md:2.6"),
    ("https://adk.dev/workflows/patterns/", "Workflow Patterns", True, "browser-gap-results.md:2.7"),
]
for url, title, complete, source in external_pages:
    records.append({
        "exact_url": url,
        "actual_url": url,
        "method": "browser_dom",
        "captured_text_path": source,
        "read_complete": complete,
        "end_offset": None,
        "total_length": None,
        "learned_points": title,
        "attempts": [{"method": "browser_dom", "result": "confirmed", "error": source}],
        "source_trajectory": source,
    })

# 4d. management-skills（唯一 unread 页，trajectory 中无任何读取记录）
records.append({
    "exact_url": "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/management-skills?lang=zh",
    "actual_url": "https://<INTERNAL_HOST>.com/docs/[PRODUCT]/management-skills?lang=zh",
    "method": None,
    "captured_text_path": None,
    "read_complete": None,
    "end_offset": None,
    "total_length": None,
    "learned_points": "DeliveryAI管理Skill页",
    "attempts": [{"method": None, "result": "no_evidence", "error": "无法从轨迹恢复原始返回：trajectory中无此页的web.fetch或浏览器调用记录"}],
    "source_trajectory": "trajectory.jsonl中无此页调用",
})

# 4e. 初始精读 [x] 页（47页）：有读取标记但无 offset/total_length 证据
# 这些页在 00-directory.md 中标记 [x]，但无 web.fetch 分页证据记录
# 按用户要求：无法证明完整阅读的保持 partial，不默认 full
import re as _re
dtext = open(os.path.join(BASE, '00-directory.md'), encoding='utf-8').read()
existing_urls = {r['exact_url'] for r in records}
for m in _re.finditer(r'^\- \[x\]\s*\[.*?\]\((https?://[^)]+)\)', dtext, _re.M):
    u = m.group(1)
    if u not in existing_urls:
        records.append({
            "exact_url": u,
            "actual_url": u,
            "method": "web_fetch",
            "captured_text_path": "00-directory.md [x]标记",
            "read_complete": None,
            "end_offset": None,
            "total_length": None,
            "learned_points": "初始精读标记，无offset/total_length证据，无法证明完整阅读",
            "attempts": [{
                "method": "web_fetch", "result": "initial_read_unverified",
                "error": "目录[x]标记表示已读，但无分页证据记录读取深度；早期页面可能仅读前8000字符",
            }],
            "source_trajectory": "00-directory.md [x]标记",
        })

# ---------------------------------------------------------------------------
# 5. 写入 reading_evidence.jsonl
# ---------------------------------------------------------------------------
out_path = os.path.join(BASE, 'reading_evidence.jsonl')
with open(out_path, 'w', encoding='utf-8') as f:
    for rec in records:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')

# 统计
from collections import Counter
c = Counter()
for r in records:
    if r['read_complete'] is True:
        c['true'] += 1
    elif r['read_complete'] is False:
        c['false'] += 1
    else:
        c['null'] += 1

print(f'reading_evidence.jsonl 已生成: {len(records)} 条记录')
print(f'  read_complete=true:  {c["true"]}')
print(f'  read_complete=false: {c["false"]}')
print(f'  read_complete=null:  {c["null"]}')
