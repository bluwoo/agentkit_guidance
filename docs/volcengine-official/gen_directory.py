#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate 00-directory.md with reading status tracking."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_directory import TREE, EXTRA, by_title, BASE

STATUS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "read_status.json")

def get_url(title, idx=0):
    paths = by_title.get(title)
    if not paths or idx >= len(paths):
        return None
    return BASE + paths[idx]

if __name__ == "__main__":
    # load existing status
    try:
        status = json.load(open(STATUS_FILE, encoding="utf-8"))
    except Exception:
        status = {}

    lines = []
    lines.append("# [PRODUCT] 官方文档目录与阅读记录")
    lines.append("")
    lines.append("- 入口: https://<INTERNAL_HOST>.com/docs/[PRODUCT]?lang=zh")
    lines.append("- 生成时间: 2026-09-18")
    lines.append("- 说明: 状态标记为 [未读] / [已读] / [失败] / [需登录]")
    lines.append("")
    total = 0
    done = 0
    for fn, sec, pages in TREE:
        lines.append(f"## {sec}  →  `{fn}`")
        lines.append("")
        for item in pages:
            title, idx = item if isinstance(item, tuple) else (item, None)
            idx = idx or 0
            url = get_url(title, idx)
            total += 1
            key = url or title
            st = status.get(key, "未读")
            if st == "已读":
                done += 1
            badge = {"未读":"[ ]","已读":"[x]","失败":"[!]","需登录":"[L]"}.get(st, "[ ]")
            lines.append(f"- {badge} [{title}]({url})")
        lines.append("")
    lines.append(f"## 附录：DeliveryAI 子产品页面（同 docs/[PRODUCT] 路径下，独立子产品）")
    lines.append("")
    for item in EXTRA:
        title, idx = item if isinstance(item, tuple) else (item, None)
        idx = idx or 0
        url = get_url(title, idx)
        total += 1
        key = url or title
        st = status.get(key, "未读")
        if st == "已读":
            done += 1
        badge = {"未读":"[ ]","已读":"[x]","失败":"[!]","需登录":"[L]"}.get(st, "[ ]")
        lines.append(f"- {badge} [{title}]({url})")
    lines.append("")
    lines.append("---")
    lines.append(f"**总计 {total} 页，已读 {done} 页。**")
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "00-directory.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"total={total} done={done}")
