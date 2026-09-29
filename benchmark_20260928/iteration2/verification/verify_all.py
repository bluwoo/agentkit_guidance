#!/usr/bin/env python3
"""Unified verification entry point for the AgentKit Benchmark (iteration2, slice B).

Runs, in one process, and emits a single machine-readable JSON report:

  1. ``skill_structure``   — the 14 formal Skills have SKILL.md + YAML frontmatter
                             (name / description), name matches directory.
  2. ``code_blocks``        — fenced Markdown/Python/Bash/YAML code blocks pass a
                             basic sanity check (fence balance; python compiles;
                             yaml parses when PyYAML is available).
  3. ``pytest``             — three suites via the project venv: Benchmark ``tests/``,
                             ``iteration2/evaluation/tests``,
                             ``iteration2/cold_start/test_cold_start.py``; each records
                             passed/failed/duration; ALL must pass.
  4. ``secret_scan``        — pattern scan of *repository file text only*; reports
                             file:line + pattern name, NEVER the matched value.
  5. ``duplicate_skills``   — duplicate Skill names / identical SKILL.md content in
                             formal directories; backup dirs and .venv are excluded.
  6. ``reference_links``    — relative Markdown links in formal Skills (incl. the
                             shared ``../references/runner-entrypoint.md``) must
                             resolve to existing files.

Rules honored:
  * Only repository file *text* is inspected. Shell profiles / live secret stores
    (~/.aws, ~/.ssh, ~/.zshrc ...) are never opened or read.
  * The project venv (``benchmark_20260928/.venv``) may be invoked for pytest.
  * Duplicate detection excludes backup directories, ``.venv``, caches and zips.

Usage:
    python verify_all.py            # prints JSON to stdout, writes verify_report.json
    python verify_all.py --json-only
Exit code 0 iff every check passes; 1 otherwise.
"""
from __future__ import annotations

import json
import os
import py_compile
import re
import subprocess
import sys
import datetime
from pathlib import Path

# --------------------------------------------------------------------- paths --
SCRIPT_DIR = Path(__file__).resolve().parent          # iteration2/verification
BENCH = SCRIPT_DIR.parents[1]                          # benchmark_20260928
REPO = BENCH.parent                                     # agentkit_dev_skills
FORMAL_SKILLS_DIR = REPO / "skills"

EXPECTED_SKILLS = [
    "adk-workflow", "agentkit-a2a-registry", "agentkit-evaluation",
    "agentkit-gateway-mcp", "agentkit-guardrails", "agentkit-identity-permission",
    "agentkit-knowledge-base", "agentkit-observability", "agentkit-runtime",
    "agentkit-sandbox", "agentkit-sdk", "agentkit-session-memory",
    "agentkit-skills", "veadk",
]

# Directories never scanned for duplication / secrets.
EXCLUDE_DIR_PARTS = {
    ".venv", ".git", ".pytest_cache", "__pycache__", "node_modules",
    "backup_skills", "_backup", ".ruff_cache",
}
SCAN_SUFFIXES = {".md", ".py", ".sh", ".bash", ".toml", ".yaml", ".yml",
                 ".json", ".txt", ".cfg", ".ini"}

SECRET_PATTERNS = {
    "aws_access_key_id": re.compile(r"AKIA[0-9A-Z]{16}"),
    "private_key_block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    "slack_token": re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    "openai_api_key": re.compile(r"sk-[A-Za-z0-9]{24,}"),
    "aws_secret_key_assign": re.compile(r"(?i)aws_secret_access_key\s*[=:]\s*\S{8,}"),
}


# ------------------------------------------------------------- check helpers --
def _parse_frontmatter(text: str) -> dict:
    """Minimal YAML-frontmatter parser (name/description only; stdlib only)."""
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}
    meta: dict = {}
    for line in lines[1:end]:
        m = re.match(r"^(name|description)\s*:\s*(.*)$", line)
        if m:
            meta[m.group(1)] = m.group(2).strip()
    return meta


def check_skill_structure() -> dict:
    skills = {}
    all_ok = True
    for name in EXPECTED_SKILLS:
        d = FORMAL_SKILLS_DIR / name
        md = d / "SKILL.md"
        entry = {"dir_exists": d.is_dir(), "skill_md_exists": md.is_file(),
                 "frontmatter_name": None, "name_matches": False, "has_description": False}
        if md.is_file():
            meta = _parse_frontmatter(md.read_text(encoding="utf-8"))
            entry["frontmatter_name"] = meta.get("name")
            entry["name_matches"] = meta.get("name") == name
            entry["has_description"] = bool(meta.get("description"))
        ok = (entry["dir_exists"] and entry["skill_md_exists"]
              and entry["name_matches"] and entry["has_description"])
        entry["ok"] = ok
        all_ok = all_ok and ok
        skills[name] = entry
    return {"ok": all_ok, "formal_dir": str(FORMAL_SKILLS_DIR),
            "expected_count": len(EXPECTED_SKILLS), "skills": skills}


def _iter_markdown_files() -> list[Path]:
    roots = [FORMAL_SKILLS_DIR, BENCH]
    out = []
    for root in roots:
        for p in root.rglob("*.md"):
            if any(part in EXCLUDE_DIR_PARTS for part in p.parts):
                continue
            out.append(p)
    return sorted(set(out))


def check_code_blocks() -> dict:
    failures = []
    n_files = 0
    n_blocks = 0
    n_skipped_placeholders = 0
    try:
        import yaml  # optional
    except Exception:
        yaml = None  # noqa: N806

    # Angle-bracket placeholders inside a python fence (e.g. tools=[<本组件特有工具>])
    # are documented skeletons, not runnable code — skip compile, don't fail on them.
    PLACEHOLDER_RE = re.compile(r"<[^<>\n]{1,40}>")

    for md in _iter_markdown_files():
        n_files += 1
        text = md.read_text(encoding="utf-8")
        if text.count("```") % 2 != 0:
            failures.append({"file": str(md.relative_to(REPO)), "error": "unbalanced fences"})
        lines = text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            m = re.match(r"^```(\w+)", line.strip())
            if not m:
                i += 1
                continue
            lang = m.group(1).lower()
            block = []
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("```"):
                block.append(lines[j])
                j += 1
            i = j + 1
            src = "\n".join(block)
            n_blocks += 1
            rel = str(md.relative_to(REPO))
            if lang in ("python", "py"):
                if md.name == "SKILL-TEMPLATE.md" or PLACEHOLDER_RE.search(src):
                    n_skipped_placeholders += 1
                    continue
                try:
                    compile(src, f"{rel}:{i}", "exec")
                except SyntaxError as e:
                    failures.append({"file": rel, "lang": lang,
                                     "error": f"SyntaxError: {e.msg} (line {e.lineno})"})
            elif lang in ("yaml", "yml"):
                if yaml is not None:
                    try:
                        yaml.safe_load(src)
                    except Exception as e:  # noqa: BLE001
                        failures.append({"file": rel, "lang": lang, "error": str(e)[:120]})
            # bash/sh: fence balance already checked; no shell execution here.
    return {"ok": not failures, "files_scanned": n_files, "fenced_blocks": n_blocks,
            "skipped_placeholder_blocks": n_skipped_placeholders,
            "yaml_available": yaml is not None, "failures": failures}


# pytest suites: (name, cwd, pytest args). KB/local-import suites are slow; tolerated.
PYTEST_SUITES = [
    {"name": "benchmark_tests", "cwd": BENCH, "args": ["tests", "-q"]},
    {"name": "iteration2_evaluation", "cwd": BENCH,
     "args": ["iteration2/evaluation/tests", "-q"]},
    {"name": "iteration2_cold_start", "cwd": BENCH / "iteration2" / "cold_start",
     "args": ["test_cold_start.py", "-q"]},
]


def check_pytest() -> dict:
    py = BENCH / ".venv" / "bin" / "python"
    if not py.exists():
        py = Path(sys.executable)
    suites = []
    for s in PYTEST_SUITES:
        t0 = datetime.datetime.now()
        try:
            proc = subprocess.run(
                [str(py), "-m", "pytest", *s["args"]], cwd=s["cwd"],
                capture_output=True, text=True, timeout=900)
            rc = proc.returncode
            out = (proc.stdout or "") + (proc.stderr or "")
        except subprocess.TimeoutExpired as e:
            rc = 124
            out = "" if e.stdout is None else str(e.stdout)
        dur = (datetime.datetime.now() - t0).total_seconds()
        m = re.search(r"(\d+) passed", out)
        f = re.search(r"(\d+) failed", out)
        suites.append({
            "name": s["name"], "rc": rc,
            "passed": int(m.group(1)) if m else 0,
            "failed": int(f.group(1)) if f else 0,
            "duration_s": round(dur, 1),
            "tail": out.strip().splitlines()[-3:],
        })
    ok = all(x["rc"] == 0 and x["failed"] == 0 for x in suites)
    return {"ok": ok, "python": str(py), "suites": suites}


_MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)\s]+)(?:\s+[^\)]*)?\)")


def check_reference_links() -> dict:
    """Relative Markdown links in formal Skills must resolve to existing files.

    Covers the shared reference (``skills/references/runner-entrypoint.md``) that
    every component SKILL.md points to via ``../references/...``. External
    (http/https/mailto) and anchor-only links are skipped. Broken links are
    reported with file + link target; no file contents are printed.
    """
    broken = []
    checked = 0
    for md in sorted(FORMAL_SKILLS_DIR.rglob("*.md")):
        if any(part in EXCLUDE_DIR_PARTS for part in md.parts):
            continue
        text = md.read_text(encoding="utf-8")
        for target in _MD_LINK_RE.findall(text):
            if re.match(r"^(https?:|mailto:)", target) or target.startswith("#"):
                continue
            checked += 1
            rel = target.split("#", 1)[0].split("§", 1)[0].strip()
            if not rel:
                continue
            resolved = (md.parent / rel).resolve()
            if not resolved.exists():
                broken.append({"file": str(md.relative_to(REPO)), "link": target,
                               "resolved_missing": str(resolved)})
    return {"ok": not broken, "links_checked": checked, "broken": broken}


def check_secret_scan() -> dict:
    findings = []
    for root in (FORMAL_SKILLS_DIR, BENCH):
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if any(part in EXCLUDE_DIR_PARTS for part in p.parts):
                continue
            if p.suffix.lower() not in SCAN_SUFFIXES:
                continue
            if p.name == "verify_report.json":
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                for pat_name, pat in SECRET_PATTERNS.items():
                    if pat.search(line):
                        # Report location + pattern ONLY; never the value.
                        findings.append({"file": str(p.relative_to(REPO)),
                                         "line": lineno, "pattern": pat_name})
    return {"ok": not findings, "findings": findings, "patterns_checked": list(SECRET_PATTERNS)}


def check_duplicate_skills() -> dict:
    seen_names: dict[str, list[str]] = {}
    seen_hashes: dict[str, list[str]] = {}
    for md in FORMAL_SKILLS_DIR.rglob("SKILL.md"):
        if any(part in EXCLUDE_DIR_PARTS for part in md.parts):
            continue
        rel = str(md.relative_to(REPO))
        text = md.read_text(encoding="utf-8")
        meta = _parse_frontmatter(text)
        if meta.get("name"):
            seen_names.setdefault(meta["name"], []).append(rel)
        import hashlib
        h = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        seen_hashes.setdefault(h, []).append(rel)
    dup_names = {k: v for k, v in seen_names.items() if len(v) > 1}
    dup_content = {k: v for k, v in seen_hashes.items() if len(v) > 1}
    return {"ok": not dup_names and not dup_content,
            "skill_dirs_scanned": sum(len(v) for v in seen_names.values()),
            "duplicate_names": dup_names, "duplicate_content": dup_content}


# -------------------------------------------------------------------- main ---
def _sanitize_report_paths(value):
    """Replace machine-specific paths before persisting or printing reports."""
    if isinstance(value, dict):
        return {key: _sanitize_report_paths(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_report_paths(item) for item in value]
    if isinstance(value, str):
        replacements = (
            (str(REPO), "<PROJECT_ROOT>"),
            (str(BENCH), "<BENCHMARK_ROOT>"),
            (str(Path(sys.executable).resolve()), "<PYTHON>"),
        )
        for source, target in replacements:
            value = value.replace(source, target)
        return value
    return value


def main() -> int:
    checks = {
        "skill_structure": check_skill_structure(),
        "code_blocks": check_code_blocks(),
        "pytest": check_pytest(),
        "secret_scan": check_secret_scan(),
        "duplicate_skills": check_duplicate_skills(),
        "reference_links": check_reference_links(),
    }
    report = {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "repo": str(REPO),
        "benchmark": str(BENCH),
        "ok": all(c["ok"] for c in checks.values()),
        "checks": checks,
    }
    report = _sanitize_report_paths(report)
    out = json.dumps(report, ensure_ascii=False, indent=2)
    (SCRIPT_DIR / "verify_report.json").write_text(out + "\n", encoding="utf-8")
    print(out)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
