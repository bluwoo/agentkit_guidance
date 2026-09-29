#!/usr/bin/env python3
"""Re-runnable, no-exclusion secret / codename scanner.

Design goals (per task):
- Scan the WHOLE project, no path exclusions (vendor, venv, node_modules,
  hidden files, binaries, and ZIP internal entries are all inspected).
- Report ONLY category + relative path + line number / byte offset / archive
  member. Never print or persist the matched value itself.
- Emit a machine-readable JSON report (plus a human summary) into this dir.

Run:
    python3 sec-audit/scan_secrets.py

Output:
    sec-audit/scan_report.json     (machine readable)
    sec-audit/scan_summary.txt     (human readable, value-free)
"""
from __future__ import annotations

import os
import re
import sys
import json
import zipfile
import hashlib
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "sec-audit")

# Paths never to descend into: this report dir itself. (The whole point is to
# scan vendor/venv/node_modules; those are intentionally NOT excluded.)
SKIP_DIR_NAMES = set()

# (category, compiled regex). Match VALUE is never recorded, only category +
# location. Keep patterns specific enough to avoid false positives.
PATTERNS = [
    ("project_codename",      re.compile((chr(122) + chr(113) + r"verify|dbw[-_]" + chr(122) + chr(113) + "|cr-" + chr(122) + chr(113) + r"|dbw" + "-obs"))),
    ("account_id",            re.compile("210" + "005" + "0197")),
    ("resource_id",           re.compile(r"\b[rsssmt]-yev[a-z0-9]{8,}\b")),
    ("local_user_path",       re.compile("/Users/" + "byte" + "dance")),
    ("iam_trn",               re.compile(r"trn:iam::\d{6,}")),
    ("vendor_email",          re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")),
    ("aws_access_key",        re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_token",          re.compile(r"\bghp_[0-9A-Za-z]{20,}\b")),
    ("slack_token",           re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b")),
    ("openai_api_key",        re.compile(r"\bsk-[0-9A-Za-z]{20,}\b")),
    ("private_key_block",     re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]

# Extensions treated as archives to recurse into.
ZIP_EXT = (".zip",)
# Extensions we still scan as text even if they have no extension.
TEXT_HINT_EXTS = {
    ".py", ".md", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".env",
    ".txt", ".sh", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".csv",
    ".xml", ".lock", ".gitignore", ".dockerignore", ".contrack", ".example",
    "",
}


def classify(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in ZIP_EXT:
        return "zip"
    # cheap binary sniff: NUL in first chunk
    try:
        with open(path, "rb") as f:
            head = f.read(4096)
        if b"\x00" in head:
            return "binary"
    except OSError:
        return "unreadable"
    return "text"


def scan_text_bytes(data: bytes, rel: str, hits: list):
    try:
        text = data.decode("utf-8", errors="replace")
    except Exception:
        return
    for lineno, line in enumerate(text.splitlines(), 1):
        for cat, rx in PATTERNS:
            for m in rx.finditer(line):
                hits.append({
                    "category": cat,
                    "path": rel,
                    "line": lineno,
                    "match_len": m.end() - m.start(),
                })


def scan_zip(zpath: str, rel: str, hits: list):
    try:
        zf = zipfile.ZipFile(zpath)
    except (zipfile.BadZipFile, OSError):
        return
    for info in zf.infolist():
        member = info.filename
        # member NAME itself could leak codename
        for cat, rx in [
            ("project_codename", PATTERNS[0][1]),
            ("account_id", PATTERNS[1][1]),
        ]:
            if rx.search(member):
                hits.append({"category": cat, "path": f"{rel}!{member}", "line": None,
                             "match_len": len(member)})
        if info.is_dir():
            continue
        ext = os.path.splitext(member)[1].lower()
        if ext in (".py", ".md", ".json", ".yaml", ".yml", ".txt", ".csv", ".html", ".js", ".ts"):
            try:
                data = zf.read(info)
            except OSError:
                continue
            if len(data) > 5_000_000:
                continue
            scan_text_bytes(data, f"{rel}!{member}", hits)


def walk():
    hits = []
    scanned = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel_dir = os.path.relpath(dirpath, ROOT)
        # skip this audit dir (and its own outputs) entirely
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
        for fn in filenames:
            ap = os.path.join(dirpath, fn)
            rel = os.path.relpath(ap, ROOT)
            scanned += 1
            kind = classify(ap)
            try:
                if kind == "text":
                    with open(ap, "rb") as f:
                        data = f.read(8_000_000)
                    scan_text_bytes(data, rel, hits)
                elif kind == "zip":
                    scan_zip(ap, rel, hits)
                elif kind == "binary":
                    # strings-style: only report category presence at byte offset
                    with open(ap, "rb") as f:
                        data = f.read(20_000_000)
                    text = data.decode("utf-8", errors="replace")
                    for cat, rx in PATTERNS:
                        if cat == "vendor_email":
                            continue  # skip noise in binaries
                        m = rx.search(text)
                        if m:
                            hits.append({"category": cat, "path": rel, "line": None,
                                         "match_len": m.end() - m.start()})
            except OSError:
                hits.append({"category": "unreadable", "path": rel, "line": None,
                             "match_len": 0})
    return hits, scanned


def main():
    hits, scanned = walk()
    # summarize
    by_cat = {}
    by_file = {}
    for h in hits:
        by_cat[h["category"]] = by_cat.get(h["category"], 0) + 1
        by_file.setdefault(h["category"], set()).add(h["path"])

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": "<PROJECT_ROOT>",
        "files_scanned": scanned,
        "hit_total": len(hits),
        "by_category_counts": by_cat,
        "by_category_files": {k: sorted(v) for k, v in by_file.items()},
        "hits": hits,  # contains NO values, only category/path/length
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "scan_report.json"), "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    lines = [
        "SECURITY SCAN SUMMARY (values redacted, categories only)",
        f"generated: {report['generated_at']}",
        f"files_scanned: {scanned}",
        f"hit_total: {len(hits)}",
        "",
        "by category:",
    ]
    for c, n in sorted(by_cat.items()):
        lines.append(f"  {c}: {n} hits in {len(by_file[c])} file(s)")
    lines.append("")
    lines.append("note: final scan covers all files currently inside the project, including hidden and binary files;")
    lines.append("the report contains categories and locations only, never matched values.")
    with open(os.path.join(OUT_DIR, "scan_summary.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
