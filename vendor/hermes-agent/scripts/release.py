#!/usr/bin/env python3
"""Hermes Agent Release Script

Generates changelogs and creates GitHub releases with CalVer tags.

Usage:
    # Preview changelog (dry run)
    python scripts/release.py

    # Preview with semver bump
    python scripts/release.py --bump minor

    # Create the release
    python scripts/release.py --bump minor --publish

    # First release (no previous tag)
    python scripts/release.py --bump minor --publish --first-release

    # Override CalVer date (e.g. for a belated release)
    python scripts/release.py --bump minor --publish --date 2026.3.15
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = REPO_ROOT / "hermes_cli" / "__init__.py"
PYPROJECT_FILE = REPO_ROOT / "pyproject.toml"

# ──────────────────────────────────────────────────────────────────────
# Git email → GitHub username mapping
# ──────────────────────────────────────────────────────────────────────

# FROZEN legacy mappings — do NOT add new entries here. New contributor
# mappings live as one-file-per-email entries under contributors/emails/
# (see contributors/README.md), which merge-conflict-free by construction.
# This dict is kept only so existing history keeps resolving; the effective
# AUTHOR_MAP below merges it with the directory (directory wins).
LEGACY_AUTHOR_MAP = {
    "user@example.com": "cat-thats-fat",  # PR #60489 (desktop: first-run remote connection option)
    "user@example.com": "cat-thats-fat",  # PR #60489 (desktop: first-run remote connection option; historical merge email)
    "user@example.com": "ragingbulld",  # PR #65606 salvage (non-finite API wait deadlines; #65746)
    "user@example.com": "shady2k",  # PR #60104 salvage of #66143 (MCP loop-owned shutdown drain)
    "user@example.com": "zzpigpinggai",  # PR #66017 salvage of #63617 (OpenRouter explicit-provider picker visibility)
    "user@example.com": "StellarisW",  # PR #66222 salvage (Discord WebSocket liveness + systemd watchdog; #26656 follow-up)
    "user@example.com": "wxy-nlp",  # PR #66222 salvage (systemd event-loop watchdog co-author)
    "user@example.com": "sam7894604",  # PR #55803 salvage (discord: /reasoning slash choices)
    "user@example.com": "hydraxman",  # PR #62028 salvage (copilot xhigh) — regression-test commit authored under a bare-noreply local git identity; PR author is @hydraxman
    "user@example.com": "antydizajn",  # PR #36043 salvage (auxiliary: route custom:<name> through named-provider arm + Palantir Bearer auth)
    "user@example.com": "briandevans",  # PR #64951 salvage (lmstudio: clamp max/ultra reasoning effort)
    "user@example.com": "karfly",  # PR #64012 salvage (gateway: surface extended reasoning efforts)
    "user@example.com": "enzo-adami",  # PR #66637 salvage (compression: preserve human intent and durable handoffs)
    "user@example.com": "rlaehddus302",  # PR #61985 salvage (gateway: secondary-adapter auth callback profile)
    "user@example.com": "bautrey",  # PR #66479 salvage (gateway reliability hardening: Bedrock liveness, supervised watchers, launchd respawn throttle)
    "user@example.com": "aguung",  # PR #64461 salvage (gateway: multiplex secret_scope for authz/Slack/webhooks)
    "user@example.com": "jtstothard",  # PR #63256 salvage (gateway: multiplex secondary adapter config validation)
    "user@example.com": "fjlaowan1983",  # PR #11256 salvage (honcho: reject whitespace-only reasoning queries)
    "user@example.com": "RainbowAndSun",  # PR #62982 salvage (honcho: observer target in prefetch context)
    "user@example.com": "Elektrofussel",  # PR #61675 salvage (honcho: defaultHost + private-range local URL detection)
    "user@example.com": "SAMBAS123",  # PR #64986 salvage (gateway: multiplex primary bot token scope)
    "user@example.com": "MaartenDMT",  # PR #65637 salvage (gateway: retry failed transcript appends and rebuild corrupted FTS)
    "user@example.com": "kocaemre",  # PR #36051 salvage (docs: audit round 3 code/doc reconciliation)
    "user@example.com": "m1qaweb",  # PR #29290 salvage (gateway: strip /queue prefix when idle)
    "user@example.com": "otsune",  # PR #36019 salvage (kanban: attachment toolset + CLI)
    "user@example.com": "wesleion",  # PR #36049 salvage (telegram: per-topic free-response allowlist)
    "user@example.com": "evefromwayback",  # PR #64611 salvage (agent: never load install-tree AGENTS.md as project context)
    "user@example.com": "Rival",  # PR #64935/#64936 salvage (state: restore-boundary alternation repair; agent: turn-overlap tripwire)
    "user@example.com": "embwl0x",  # PR #65105 salvage (gateway: preserve external supervisor ownership)
    "user@example.com": "2751738943",  # PR #54785 salvage (tui: post-turn completion ownership routing)
    "user@example.com": "Burgunthy",  # PR #20096 salvage (gateway: profile-based routing for inbound messages)
    "user@example.com": "BB-light",  # PR #76015 salvage (caching: honor cache_ttl disable; #33555)
    "user@example.com": "webtecnica",  # PR #63360 salvage (nous: restore inference-api base_url)
    "user@example.com": "webtecnica",  # PR #70888 salvage
    "user@example.com": "webtecnica",  # PR #75838 salvage (aux: free-only fallback guard; #75803)
    "user@example.com": "ckaznocha",  # PR #71543 salvage (matrix: crypto store reset + pickle migration)
    "user@example.com": "Epoxidex",  # PR #29820 salvage (ollama: top-level reasoning_effort=none; #25758)
    "user@example.com": "JiaDe-Wu",  # PR #34742 salvage (bedrock: bearer routing + streaming fallback + image decode; #28156)
    "user@example.com": "minchang",  # PR #42231 salvage (providers: add Upstage Solar)
    "user@example.com": "neo-claw-bot",  # PR #58465 salvage (moa: drop empty user turns from advisory view)
    "user@example.com": "pixel4039",  # PR #64420 salvage (streaming: retry zero-chunk streams)
    "user@example.com": "marcelohildebrand",  # PR #42346 salvage (lmstudio: JIT load mode)
    "user@example.com": "Soju06",  # agent turn-latency perf PRs
    "user@example.com": "mguttmann",  # PR #63738 salvage (Anthropic setup-token pool auth normalization)
    "user@example.com": "flyingdoubleG",  # PR #18166 salvage (memory-provider tools honor disabled_toolsets in initial and MCP-refresh injection)
    "user@example.com": "VrtxOmega",  # PR #43809 salvage (desktop: WSL folder-picker path bridge)
    "user@example.com": "SemonCat",  # PR #56786 salvage (Slack Agent View manifests and Assistant APIs)
    "user@example.com": "KCAYAAI",  # PR #62248 partial salvage (resume typing after clarify reply)
    "user@example.com": "jakelongvu-bot",  # PR #36683 partial salvage (approval: honor canonical approvals.timeout in gateway waits)
    "user@example.com": "Tortugasaur",  # PR #43205 salvage (desktop: profile-aware three-way approval mode statusbar control)
    "user@example.com": "kavioavio",  # Issue #46544 / PR #47705 evolution (smart DENY exact-operation owner override)
    "user@example.com": "ansel-f",  # PR #62388 salvage (approval: allow exact verifier temp cleanup without broadening rm safety boundary)
    "user@example.com": "Hopfensaft",  # PR #31933 salvage (dashboard: align approvals.mode dropdown with canonical engine values)
    "user@example.com": "professorpalmer",  # PR #48591 salvage (sessions: CLI workspace filter + restore-cwd-on-resume)
    "user@example.com": "Supersynergy",  # PR #59241 salvage (desktop: workspace path status-bar action)
    "user@example.com": "roryford",  # PR #63132 salvage (compression: fail closed for errors from a resolved lock API, preserving lineage)
    "user@example.com": "esthonjr",  # PR #61950 salvage (desktop: legacy non-git workspace grouping + Windows path identity)
    "user@example.com": "Drexuxux",  # PR #36042 salvage (gateway: /footer reachable mid-run via safe-toggle set)
    "user@example.com": "IgorGanapolsky",  # PR #62125 salvage (compaction anti-thrash threshold verification)
    "user@example.com": "aeyeopsdev",  # PRs #36035/#36068 salvage (google-chat: http inbound without pubsub; clarify cards)
    "user@example.com": "TheTom",  # PR #62696 salvage (gateway: expand @ context references under runtime/session model resolution)
    "user@example.com": "ljy-2000",  # PR #62204 adopted in #62290
    "user@example.com": "vizi0uz",  # PR #59795 adopted in #62290
    "user@example.com": "WilsonKinyua",  # PR #62052 (tui: persist unflushed conversations on disconnect/restart)
    "user@example.com": "HumphreySun98",  # PR #61142 salvage (web: null web/backend config value guards)
    "user@example.com": "light-merlin-dark",  # PR #7821 salvage (zai: parallel endpoint detection probes)
    "user@example.com": "frizikk",  # PR #63389 salvage (session-search: fields projection skips unused context enrichment)
    "user@example.com": "EndeavorYen",  # PR #33971 salvage (image: parallel image_generate batches + FileSyncManager transaction lock)
    "user@example.com": "17324393074",  # PR #53196 salvage (tools_config: known_plugin_toolsets null guard; commit under unlinked local identity)
    "user@example.com": "lemonwan",  # PR #59430 sibling salvage (adapter reconnect contract guard)
    "user@example.com": "luxuguang-leo",  # PR #52966 + #52908 salvage (QQBot reconnect + Feishu Channel signaling)
    "user@example.com": "evelynburger",  # PR #57544 salvage (gateway: webhook payload filters + route scripts; commit under unlinked identity)
    "user@example.com": "SiteupAgencia",  # PR #57435 salvage (tui_gateway: back off notification poller when session is busy; #55578)
    "user@example.com": "rainbowgore",  # PR #59405 salvage (mcp: bound stdio initialize handshake to stop subprocess/FD leak; #59349)
    "user@example.com": "thestudionorth",  # PR #60015 salvage (mcp: parent-death watchdog for stdio children; commit under unlinked local identity)
    "user@example.com": "vampyren",  # PR #59830 salvage (kanban: grab-to-pan board scrolling; original commit under unlinked local identity)
    "user@example.com": "spiky02plateau",  # PR #32824 salvage (usage: fetch Codex account limits from the credential pool in pool-only setups; superseded by #60028)
    "user@example.com": "hwrdprkns",  # PR #36896 salvage (secrets: 1Password op:// secret source + shared _cache substrate, adapted onto the SecretSource interface)
    "user@example.com": "isheng-eqi",  # PR #59428 salvage (cron: reject past one-shot timestamps in update_job fallback + resume_job; #59395). Also PR #59446 salvage (cron: advance one-shot next_run_at before dispatch so concurrent gateway+desktop schedulers can't double-execute; #59229).
    "user@example.com": "derek2000139",  # PR #57838 salvage (desktop/windows: pre-write update marker before quit dwell so the renderer's waitForUpdateToFinish gate parks instead of respawning a backend that re-locks venv .pyd files mid-update)
    "user@example.com": "AndreasHiltner",  # PR #56854 salvage (gateway: route multiplex profile responses through the profile's own adapter — 53-site _adapter_for_source sweep)
    "user@example.com": "AlexFucuson9",  # PR #61347 salvage (agent: reapply provider headers after model switch; #61099)
    "user@example.com": "allenliang2022",  # PR #56932 test coverage folded into #56909 salvage (408 → retryable timeout)
    "user@example.com": "ManniBr",  # PR #57417 partial salvage (gateway: fail-closed adapter resolution for unregistered secondary profiles)
    "user@example.com": "Umi4Life",  # PR #47377 salvage (agent: emit one-shot fallback switch notice on successful fallback so gateway users see model/provider change; #35419)
    "user@example.com": "austinlaw076",  # PR #57563 partial salvage (auth: lazy per-profile Anthropic OAuth file; gateway: whatsapp_cloud/line added to port-binding platform set)
    "user@example.com": "liuhao1024",  # PR #56993 salvage (gateway: process-level HERMES_HOME for pid/lock/status identity files; #56986)
    "user@example.com": "Roseyco-management",  # PR #63581 salvage (telegram: require getUpdates progress before polling is healthy; #63243, #63766)
    "user@example.com": "nima20002000",  # PR #36022/#36025 salvage (code-exec truncation metadata; achievements hover loop)
    "user@example.com": "gauravsaxena1997",  # PR #59868 partial salvage (agent: guard response.text against httpx.ResponseNotRead in _summarize_api_error; #59769)
    "user@example.com": "irresi",  # PR #59048 salvage (gateway: scope reset banners' session info to the serving profile; #59003)
    "user@example.com": "s905060",  # PR #57943 salvage (photon: auto-reinstall stale sidecar node_modules when lockfile is newer than npm's install marker; #59169)
    "user@example.com": "l0h1nth",  # PR #32210 salvage (mattermost: accept leading-space slash commands from mobile clients; #25184)
    "user@example.com": "arnispiekus",  # PR #63581 salvage (telegram: require getUpdates progress before polling is healthy; #63243)
    "user@example.com": "devatnull",  # PR #58704 salvage (whatsapp: native Baileys polls, clarify-as-poll, location pins, structured quoted replies, PTT/audio split, bridge_helpers extraction)
    "user@example.com": "tjp2021",  # PR #4097 salvage (copilot: per-turn x-initiator header so user prompts bill as premium requests; #3040)
    "user@example.com": "falkoro",  # PRs #58519/#58520 salvage (config: env-ref-aware load_config cache invalidation; auxiliary: honor auxiliary.<task>.base_url/api_key with explicit provider arg)
    "user@example.com": "kevinrajaram",  # PR #3850 salvage (gateway: add POSIX system dirs to PATH so launchctl/systemctl resolve under UV's minimal-PATH bundled Python; #3849)
    "user@example.com": "lord-dubious",  # PR #58453 salvage (preserve static custom provider models declared as dict rows)
    "user@example.com": "williamumu",  # PR #31041 salvage (pairing: merge split legacy/new pairing store dirs at PairingStore init so approved users aren't re-prompted to pair)
    "user@example.com": "JAlmanzarMint",  # PR #52688 salvage (vision: rasterize SVG / re-encode unsupported raster formats to PNG before embedding), folded into #57890
    "user@example.com": "alex-fireworks",  # PR #61182 salvage (Fireworks AI model-provider integration)
    "user@example.com": "ooiuuii",  # PR #58466/#58377 salvage (redact: fireworks fw-/fpk_ prefixes; telegram: redact bot tokens out of transport error strings). Also PR #58433 salvage (codex: accept recorded final_text when app-server omits turn/completed) and PR #58472 salvage (gateway: cap proxy SSE line buffer at 16MiB).
    "user@example.com": "Jigoooo",  # PR #58474 salvage (auxiliary: fall back to token resolver when anthropic pool has no usable entry)
    "user@example.com": "ostravajih",  # PR #58374 salvage (poolside: coerce integer finish_reason and tool_call id to strings)
    "user@example.com": "sahil-shubham",  # PR #58448 salvage (whatsapp_cloud: honor documented WHATSAPP_CLOUD_ALLOWED_USERS / ALLOW_ALL_USERS in the DM intake gate)
    "user@example.com": "Ahmett101",  # PR #58445 salvage (profiles: allowlist default-export roots + preserve symlinks)
    "user@example.com": "IpastorSan",  # PR #63690 salvage (codex: rescue reasoning-only turns that die after 3 continuation attempts)
    "user@example.com": "Ahmett101",  # PR #59455 salvage (background-review: guard summarize against list-shaped tool responses; #59437)
    "user@example.com": "wyuebei-cloud",  # PR #56640 salvage (hermes journey: replace GNU-only %-d strftime with dt.day for Windows)
    "user@example.com": "msh01",  # PR #58250 salvage (telegram: wall-clock init timeout via daemon-thread deadline + abandon the shielded initialize task on timeout so the retry ladder advances instead of hanging on attempt 1/8 under s6 supervision; #58236). Also covers PR #58276 salvage (compression: preserve a real user turn after compaction; #55677).
    "user@example.com": "danilofalcao",  # PR #56674 salvage (update: skip unsupported platform.matrix lazy refresh on native Windows — python-olm has no Windows wheel)
    "user@example.com": "huanshan5195",  # PR #57601 salvage (custom-provider: emit reasoning_effort at the live CustomProfile path so GLM-5.2/ARK/vLLM/Ollama endpoints receive it; + "max" reasoning level)
    "user@example.com": "infinitycrew39",  # PR #56431 salvage (honor live vLLM context limits on local endpoints)
    "user@example.com": "CocaKova",  # PR #57692 salvage (cron: run jobs under the profile secret scope so get_secret does not fail-close with UnscopedSecretError under profile isolation)
    "user@example.com": "trismegistus-wanderer",  # PR #31856 salvage (gateway: defer idle-TTL agent-cache eviction until the session store says the session actually expired, so the expiry watcher can still fire MemoryProvider.on_session_end with the live transcript; #11205)
    "user@example.com": "Mibayy",  # PR #3243 salvage (/compact alias + preview/aggressive flags for /compress)
    "user@example.com": "Mibayy",  # PR #3176 salvage (api-server: per-client model routing via model_routes)
    "user@example.com": "jneeee",  # PR #3526 salvage (extra HTTP headers for LLM API calls via config.yaml)
    "user@example.com": "CrazyBoyM",  # PR #55828 salvage (image_gen openai-codex: wire image-to-image / reference-image editing via Codex Responses input_image parts; magic-byte + read-guard + 25MB-cap + clamp-to-16 hardening)
    "user@example.com": "r0gersm1th",  # PR #3219 salvage (whatsapp bridge: resolve LID sender IDs to phone numbers in the message payload so phone-based allowlists match; commit authored by collaborator r0gersm1th, PR by @ajmeese7)
    "user@example.com": "Mibayy",  # PR #3296 salvage (status: provider label honors config.yaml model.base_url, not just OPENAI_BASE_URL env)
    "user@example.com": "keslerm",  # PR #3459 salvage (gateway: 'log' tool_progress mode — silent in chat, tool calls appended to ~/.hermes/logs/tool_calls.log via rotating handler; duplicate of #3458 by @dlkakbs who submitted 4 min earlier — both credited)
    "user@example.com": "Git-on-my-level",  # PR #3659 salvage (gateway: persist per-session /model overrides across gateway restarts)
    "user@example.com": "tarunravi",  # PR #2696 salvage (api-server: inline MEDIA:<path> image tags as base64 data URLs in final responses so remote OpenAI-compatible frontends can render server-local screenshots; the PR's tool-progress-streaming and SSE-sentinel pieces were independently superseded on main)
    "user@example.com": "VolodymyrBg",  # PR #2861 salvage (webhook: drop the unused full request payload from retained _delivery_info entries — up to ~1MB dead weight per delivery for the 1h idempotency TTL)
    "user@example.com": "CharmingGroot",  # PR #2794 salvage (email: guard msg_data[0][1] against malformed IMAP fetch structures so one bad response can't abort the batch and permanently lose seen-marked messages; Message-ID domain falls back to localhost when EMAIL_ADDRESS lacks '@')
    "user@example.com": "sahibzada-allahyar",  # PR #39227 salvage (desktop: configured terminal.cwd overrides a stale remembered workspace-cwd localStorage value when no session is active; #38855)
    "user@example.com": "rarf",  # PR #56966 salvage (desktop chat model picker: hide implicitly discovered providers unless explicitly configured)
    "user@example.com": "plcunha",  # PR #55300 salvage (gateway: record child gateway peer metadata after a compression session-id rotation and repoint stale sessions.json compression-parent entries to the recovered live child; consolidated in the compression-routing-integrity salvage)
    "user@example.com": "jakepresent",  # PR #55721 salvage (gateway: identity-guard stale in-flight compression splits — a late run may publish its compressed child only if its run generation is still current and the session key still points at the run's original parent, so an old run can't overwrite a newer /new or moved binding)
    "user@example.com": "gumclaw",  # PR #57322 salvage (gateway: close per-delivery webhook sessions on completion so prune_sessions can reap them — fixes unbounded state.db growth from unprunable ended_at=NULL webhook rows)
    "user@example.com": "zmlgit",  # PR #54872 salvage (multiplex-profile kanban: route task notifications via the owning profile's adapter + wake the creator agent with a synthetic internal MessageEvent on terminal events)
    "user@example.com": "nankingjing",  # PR #56404 salvage (gateway: while a state.db compression lock is held for the session, demote busy_input_mode 'interrupt' to 'queue' so a rapid message burst can't interrupt and fork orphaned compression siblings off a stale parent; #56391)
    "user@example.com": "udatny",  # PR #29433 salvage (subdirectory_hints: catch RuntimeError from Path.expanduser()/Path.home() so a literal ~ in tool-call args — e.g. LLM "~500-700" or ~unknownuser — can't escape the hint walker and crash the conversation loop)
    "user@example.com": "brett539",  # PR #49369 salvage (cap Telegram initialize() with asyncio.wait_for(HERMES_TELEGRAM_INIT_TIMEOUT, default 30s) per attempt so an unreachable fallback-IP connect chain can't block gateway startup indefinitely; add WARNING progress logs before DoH discovery and each connect attempt)
    "user@example.com": "randomuser2026x",  # PR #50204 salvage (gateway /restart under systemd: probe both system + --user scope for MainPID instead of hardcoding --user; always exit 75 so RestartForceExitStatus=75 revives the unit under Restart=on-failure too, not just Restart=always)
    "user@example.com": "valenteff",  # PR #53277 salvage (macOS launchd reload: retry bootstrap via _launchctl_bootstrap until launchctl-list confirms registration or the restart-drain window elapses; retry TimeoutExpired not just CalledProcessError; log persistent orphans)
    "user@example.com": "slawt",  # PR #8427 salvage (Google Vertex AI provider for Gemini: OAuth2 token minting via service-account JSON / ADC on the OpenAI-compat endpoint, rewired as a provider profile with per-turn 401 token refresh)
    "user@example.com": "bitcryptic-gw",  # PR #53997 salvage (Matrix E2EE: resolve device_id via query_keys({mxid: []}) when whoami returns none; guard verification call sites so query_keys is never sent [null]; reset _device_id_unverified at connect() start; disconnect before reconnect)
    "user@example.com": "Gromykoss",  # PR #56372 salvage (context_compressor merge-into-tail: place END MARKER last, wrap prior tail content in [PRIOR CONTEXT]...[END OF PRIOR CONTEXT] delimiters so the model doesn't read it as a fresh message)
    "user@example.com": "HODLCLONE",  # PR #49351 salvage (Nous Portal token resilience: rotate refresh tokens write-through to the source auth store in profile mode, skip Nous fallback when no local token, sync gateway session model after fallback)
    "user@example.com": "abchiaravalle",  # PR #46997 salvage (recover resume_pending sessions: dual freshness signal + empty-turn safety net so restart auto-resume never sends a blank user turn)
    "user@example.com": "swissly",  # PR #47167 salvage (wrap cron delivery thread-pool fallback in its own try/except so a per-target failure can't escape the except-RuntimeError block and crash the multi-target delivery loop; #47163)
    "user@example.com": "shawchanshek",  # PR #44126 salvage (strip <think>...</think> reasoning blocks from title-generator LLM output via the canonical strip_think_blocks scrubber so reasoning-model output can't leak into session titles)
    "user@example.com": "YLChen-007",  # PR #27289 salvage (case-insensitive streaming reasoning-tag filter in cli.py _stream_delta + gateway stream_consumer so mixed-case variants like <Think>/<ThInK> are suppressed, not just the hardcoded case literals)
    "user@example.com": "kangsoo-bit",  # PR #47508 salvage (keep Telegram gateway alive on transient bootstrap network errors: best-effort deleteWebhook + resilient start_polling degrade to background recovery instead of failing startup)
    "user@example.com": "testingbuddies24",  # PR #43192 salvage (strip orphan think-tag close tags in progressive gateway stream so a bare </think> whose open was dropped upstream can't leak to the user)
    "user@example.com": "Lazymonter",  # PR #42914 salvage (retry launchd bootstrap after bootout on EIO for install/start instead of degrading to detached)
    "user@example.com": "WXBR",  # PR #46183 salvage (persist recovered final_response at the finalize_turn chokepoint so recovery-path breaks don't drop the delivered assistant row)
    "user@example.com": "dmabry",  # PR #63862 salvage (output-cap retry: use provider available_tokens + request estimate; exempt parseable vLLM/LM Studio errors from compression-disabled guard)
    "user@example.com": "SahilRakhaiya05",  # PR #44073 salvage (fail-closed gateway/external-surface hardening: own-policy defaults, open-policy startup guard, profile-aware multiplex authz, API-server auth, execute_code per-session RPC token)
    "user@example.com": "itenev",  # PR #22753 salvage (asyncify model-context resolution in gateway message path so blocking requests.get can't starve Discord heartbeats)
    "user@example.com": "arthurzhang",  # PR #34718 salvage (redact Slack App-Level xapp- tokens in agent/redact.py + gateway/run.py)
    "user@example.com": "rrevenanttt",  # PR #40773 salvage (close hardline rm bypass via quoted paths and ${HOME} brace form)
    "user@example.com": "Vesna-9",  # PR #41274 salvage (collapse shell line continuations before dangerous/hardline pattern matching so `rm -rf \<newline>/` can't bypass the yolo-proof hardline floor)
    "user@example.com": "kernel-t1",  # PR #41349 salvage (.env sanitizer: only split when line starts with a known KEY= and preceding values are plain tokens; keep URL/query/whitespace secrets verbatim)
    "user@example.com": "sasquatch9818",  # PR #41198 salvage (defang untrusted-tool-result delimiter against tag injection; drop forgeable startswith fast-path)
    "user@example.com": "jnibarger01",  # PR #35130 salvage (ReDoS-bound threat-pattern filler + FTS5 query cap + V4A Move-File approval/traversal targets)
    "user@example.com": "yong2bba",  # PR #49830 salvage (harden browser tool safety boundaries: config-gated risky-eval blocklist, force-redact browser/CDP/supervisor output, session-ownership tracking, credential-query denylist)
    "user@example.com": "djimit",  # PR #48034 salvage (recover from truncated gateway responses: 4 continuation retries + exponential token headroom + normalize empty partials)
    "user@example.com": "lubosxyz",  # PR #49225 salvage (persist codex app-server turns to session DB via agent_persisted=False so session_search/distill see gateway conversations)
    "user@example.com": "petrichor-op",  # PR #41281 salvage (never persist ephemeral empty-response recovery scaffolding to the SQLite session store / JSON log; filter by flag not position)
    "user@example.com": "redactdeveloper",  # PR #36897 salvage (route /sessions & /history through prompt_toolkit-safe print; filter doctor missing-key summary to CLI-enabled toolsets)
    "user@example.com": "charleneleong-ai",  # PR #11736 salvage (classify Anthropic "out of extra usage" 400 as billing)
    "user@example.com": "janrenz",  # PR #35862 salvage (prompt_caching.enabled escape hatch for strict providers)
    "user@example.com": "syahidfrd",  # PR #17059 salvage (tag unverified senders in Slack thread context to mitigate indirect prompt injection)
    "user@example.com": "H2KFORGIVEN",  # PR #22523 salvage (turn-pair preservation: never orphan the last user ask at head_end during compaction)
    "user@example.com": "sgabel",  # PR #13139 salvage (redact secrets in user-facing approval prompts)
    "user@example.com": "CRWuTJ",  # PR #17082 salvage (cancel delayed Telegram deliveries on disconnect so buffered flushes don't dispatch into a torn-down session)
    "user@example.com": "cyb3rwr3n",  # PR #11333 salvage (sanitize FTS5 queries for natural-language recall in holographic memory)
    "user@example.com": "codexGW",  # PR #12302 salvage (Discord raw <@!ID> mention detection + drop bare mention-only pings)
    "user@example.com": "jackroofan",  # PR #54609 salvage (add anthropic to MoA _slot_runtime name-preserve set; OAuth sk-ant-oat* needs Bearer + anthropic-beta header)
    "user@example.com": "iizotov",  # PR #54912 salvage (add bedrock to MoA _slot_runtime name-preserve set; SigV4-signed client, placeholder aws-sdk api_key)
    "user@example.com": "JustinOhms",  # PR #24469 salvage (route native-SDK delegation providers through runtime resolver; fail on '(empty)' sentinel instead of accepting it as success)
    "user@example.com": "lEWFkRAD",  # PR #53848 salvage (stream the MoA aggregator response to the user)
    "user@example.com": "jimmyjohansson84",  # PR #27123 salvage (Kanban unknown-skill warn-instead-of-crash; #27136)
    "user@example.com": "Jeffgithub0029",  # PR #28558 salvage (chunk Telegram text *after* MarkdownV2/HTML formatting so escaping inflation can't push a send over the 4096 UTF-16 limit; #28557)
    "user@example.com": "fayenix",  # PR #28846 salvage (normalize _cfg_model in gateway fallback-eviction so vendor-prefixed config matches stripped agent.model on native providers)
    "user@example.com": "theAgenticBuilder",  # PR #14180 salvage (route delegate_task progress lines through _safe_print so ACP stdio JSON-RPC frames stay clean)
    "user@example.com": "huangxudong663-sys",  # PR #15157 salvage (isinstance(dict) guard on tool-call model_extra; NVIDIA NIM non-dict crash)
    "user@example.com": "jasonQin6",  # PR #15093 salvage (session staleness guard on stream consumer run() loop; #11016 follow-up)
    "user@example.com": "znding04",  # PR #15487 salvage (distinguish OpenRouter upstream 429 from account 429; upstream_rate_limit failover reason)
    "user@example.com": "nnnet",  # PR #25142 salvage (stop STT-failure chatter poisoning the LLM prompt; drop hardcoded English notice)
    "user@example.com": "nnnet",  # PR #36024 salvage (dashboard: inline critical-CSS bootstrap for user themes)
    "user@example.com": "londo161",  # PR #15795 salvage (redact status --all API keys; tolerate dict/str compression message shape)
    "user@example.com": "neo-2026",  # PR #14026 salvage (clear input-blocking overlays on interrupt so the CLI doesn't freeze; #13618)
    "user@example.com": "Nickperillo",  # PR #8008 salvage (Discord channel-name matching + flush pending sends on shutdown)
    "user@example.com": "MarioYounger",  # PR #9028 salvage (bash/sh heredoc approval, NFKC homograph fold, execute_code CREDS/BEARER/APIKEY env filter)
    "user@example.com": "peetwan",  # PR #51841 salvage (loopback ws-ping tuning + token-frame coalescing + loop heartbeat; #48445/#50005)
    "user@example.com": "Peterskaronis",  # PR #63889 salvage (mcp-oauth: WAF-safe redirect_host for loopback callback URIs)
    "user@example.com": "Zyxxx-xxxyZ",  # PR #54287 salvage (route frontend-polled inline RPCs to _LONG_HANDLERS; #48445/#50005)
    "user@example.com": "DataAdvisory",  # PR #9562 salvage (flatten multi-part user_message in codex intermediate-ack detector so vision turns don't crash)
    "user@example.com": "huangsen365",  # PR #42334 (CVE dependency pins + pin-drift guard)
    "user@example.com": "telos-oc",  # PR #14353 salvage (propagate custom_providers key_env into ProviderDef.api_key_env_vars; named + bare-custom self-heal paths)
    "user@example.com": "Kolektori",  # PR #6436 salvage (require approval for host-bound Docker commands; container guard fast-path)
    "user@example.com": "LIC99",  # PR #4682 salvage (warn + default to manual on unknown approvals.mode; #4261)
    "user@example.com": "cmcejas",  # PR #41188 salvage (early Telegram auth gate before event build/observe; #40863)
    "user@example.com": "oreoluwa",  # PR #49845 salvage (skip preflight content-type probe for OAuth MCP servers so OAuth discovery runs; Akiflow/Hospitable)
    "user@example.com": "PRATHAMESH75",  # PR #37550 salvage (ExecStopPost cgroup-orphan reaper to unblock systemd restart; #37454)
    "user@example.com": "konsisumer",  # PR #19608 salvage (read-modify-write merge in write_credential_pool to preserve concurrently-added credentials; #19566)
    "user@example.com": "linyubin",  # PR #50228 salvage (eager fallback on persistent transport timeout/overloaded; #22277)
    "user@example.com": "bradhallett",  # PR #46948 salvage (force app exit after update/uninstall handoff on macOS; #46948)
    "user@example.com": "coygeek",  # PR #37951 salvage (fail closed when provider env blocklist import fails; #37950)
    "user@example.com": "djstunami",  # PR #5316 salvage / co-author (suppress transient check_fn flakes so subagents keep file/terminal tools; #21658 / #5304)
    "user@example.com": "jmmaloney4",  # PR #25206 salvage (re-select credential pool on primary runtime restore; #25205)
    "user@example.com": "hmirin",
    "user@example.com": "dalenguyen",  # PR #53678 salvage (strip VIRTUAL_ENV/CONDA_PREFIX from terminal subprocess env; #23473)
    "user@example.com": "prashantjain25",  # PR #80740 salvage (custom-endpoint /v1/models disk cache; #72762)
    "user@example.com": "HexLab98",  # PR #53863 salvage (env-only proxy policy for auxiliary OpenAI clients on macOS; #53702)
    "user@example.com": "fangliquanflq",  # PR #99265 (linear lowercase env-assignment redaction; #99255) - merged directly by maintainer
    "user@example.com": "sycamoregroupltd",  # PR #97779 salvage (estop fleet-root sentinel for profile gateways)
    "user@example.com": "Blaryxoff",  # PR #32602 salvage (deep-merge PUT /api/config to preserve unrelated sections; #13396)
    "user@example.com": "DiamondEyesFox",  # PR #53351 salvage (rebaseline in-place compression flushes to prevent duplicate compacted rows; #9096)
    "user@example.com": "rlaope",  # PR #35075 salvage (align cron invisible-unicode set with install-time scanner; #35075)
    "user@example.com": "bykim0119",  # PR #22335 salvage (honor "*" wildcard in DISCORD_ALLOWED_USERS; #22334)
    "user@example.com": "rebel0789",  # PR #47308 salvage (redact browser_type typed text across display surfaces; #47197)
    "user@example.com": "agt-user",  # PR #48496 salvage (telegram CLOSE-WAIT polling heartbeat, #48495)
    "user@example.com": "DavidMetcalfe",  # PR #52272 salvage (route reasoning-model thinking-timeouts to timeout not context_overflow + reasoning-specific guidance; #52271)
    "user@example.com": "Tranquil-Flow",  # PR #52623 salvage (auxiliary Anthropic base_url host validation; #52608)
    "user@example.com": "nikshepsvn",  # PR #27426 salvage (two-layer guard against hallucinated acp_command crashing the gateway on hosts with no ACP CLI)
    "user@example.com": "coygeek",  # PR #37735 salvage (redact provider error text at api-server HTTP boundary; #37733)
    "user@example.com": "Tranquil-Flow",  # PR #52623 salvage (auxiliary Anthropic base_url host validation; #52608)
    "user@example.com": "isair",  # PR #50124 salvage (periodic FTS5 segment merge to curb write-lock contention; #54752)
    "user@example.com": "Dr1985",  # PR #42567 salvage (launchd supervision detection + status reporting; #42524)
    "user@example.com": "herbalizer404",  # PR #49076 + #51835 salvage (auxiliary compression fallback: 403/session-usage payment errors + honor fallback chain when aux provider auth unavailable)
    "user@example.com": "pyxl-dev",  # PR #52230 salvage (include rate-limit in auxiliary capacity-error fallback gate; #52228)
    "user@example.com": "yashiels",  # PR #53284 salvage (discord markdown table-to-bullet conversion; #21168)
    "user@example.com": "yungchentang",  # PR #53622 salvage (drain Telegram general send pool on pool timeout before retry; #53524)
    "user@example.com": "595650661",  # PR #37851 salvage (classify MiniMax new_sensitive content filter → content_policy_blocked; #32421)
    "user@example.com": "qWaitCrypto",  # PR #52534 salvage (preserve assistant tool_use cache_control marker in Anthropic conversion so cache breakpoints aren't dropped from the wire)
    "user@example.com": "benbenlijie",  # PR #47205 salvage (named custom-provider extra_body + Z.AI Coding overload adaptive backoff; #50663)
    "user@example.com": "Danamove",  # PR #46726 salvage (kill venv-resident pythonw gateway before recreating venv on Windows; #47036/#47557/#47910)
    "user@example.com": "rc-int",  # PR #9126 salvage / co-author (cap subagent summary size vs parent context overflow)
    "user@example.com": "wgu9",  # PR #51468 salvage (WSL/no-systemd orphan gateway tracking, #51325)
    "user@example.com": "uperLu",  # PR #50958 salvage (rename plugins/cron → plugins/cron_providers; #50872)
    "user@example.com": "yusekiotacode",  # PR #48706 salvage (anthropic OAuth login token endpoint → platform.claude.com; #45250/#49821)
    "user@example.com": "s010mn",  # PR #29221 salvage (ollama-cloud reasoning_effort xhigh→max)
    "user@example.com": "chriswesley4",  # PR #53185 salvage (re-enable titleBarOverlay on plain Linux; missing min/max/close regression)
    "user@example.com": "RafaelMiMi",  # PR #42229 salvage (no-sandbox fallback for AppArmor-restricted Linux desktop launch)
    "user@example.com": "jeeves-assistant",  # PR #50771 (computer-use CuaDriver vision capture routing)
    "user@example.com": "ScotterMonk",  # PR #50145 salvage (cron output truncation: adapter-aware chunking, #50126)
    "user@example.com": "TutkuEroglu",  # PR #50481 salvage (AGENTS.md stale token-lock adapter path)
    "user@example.com": "f-trycua",  # PR #50507 salvage (cross-platform computer_use; supersedes #44221/#30660)
    "user@example.com": "flewe",  # PR #47755 salvage (mcp-oauth: configurable redirect_uri for proxied callbacks, e.g. Tailscale Funnel)
    "user@example.com": "pmos69",  # PR #29474 salvage (native Antigravity OAuth provider; Gemini CLI sunset #29294/#49701)
    "user@example.com": "orbisai0security",  # PR #9560 salvage (session.py path-traversal guard, V-009)
    "user@example.com": "panghuer023",  # PR #37994 salvage (interrupt unblocks pending gateway approval; #8697)
    "user@example.com": "natehale",  # PR #48678 salvage (typing indicator lingers after final reply)
    "user@example.com": "kn8-codes",  # PR #48422 salvage (rich messages opt-in default off)
    "user@example.com": "de1tydev",  # PR #10158 salvage (poll read-only for notify_on_complete watcher; #10156)
    "user@example.com": "skabartem",  # PR #32867 salvage (atomic check-and-replace in _ensure_primary_openai_client; #32846)
    "user@example.com": "szzhoujiarui-sketch",  # cron model.default salvage co-author (#45550)
    "user@example.com": "rayjun",  # cron model.default salvage co-author (#43952)
    "user@example.com": "sweetcornna",  # cron ticker-liveness salvage co-author (#33849)
    "user@example.com": "izumi0uu",  # PR #49544 salvage (native rich reply echo; #49534)
    "user@example.com": "yingliang-zhang",  # PR #56084 (setup RPC pool routing; #57335)
    "user@example.com": "texhy",  # PR #27435 salvage (few-but-huge preflight compression gate; #27405)
    "user@example.com": "qdaszx",  # PR #29190 salvage (non-blocking OSV malware preflight; #29184)
    "user@example.com": "w31rdm4ch1nZ",
    "user@example.com": "x7peeps",
    "user@example.com": "ahmadashfq",
    "user@example.com": "yinkev",  # scratch artifact preservation salvage
    "user@example.com": "rratmansky",
    "user@example.com": "lkz-de",
    "user@example.com": "salesondemandio",
    "user@example.com": "IamSanchoPanza",
    "user@example.com": "victor-kyriazakos",
    "user@example.com": "JoaoMarcos44",
    "user@example.com": "JoaoMarcos44",
    "user@example.com": "neoguyverx",  # PR #60526 salvage (fail-closed write syntax gate; #60525)
    "user@example.com": "srojk34",
    "user@example.com": "srojk34",  # legacy prefix-less noreply (PR #50098 salvage; #38763)
    "user@example.com": "PINKIIILQWQ",  # PR #45035 salvage (resume-to-tip; #38763)
    "user@example.com": "PINKIIILQWQ",  # PR #45035 local git identity (resume-to-tip; #38763)
    "user@example.com": "ailang323",  # PR #48682 salvage (compression-tip predicate; #38763)
    "user@example.com": "sitkarev",
    "user@example.com": "omegazheng",
    "user@example.com": "james47kjv",
    "user@example.com": "1960697431",
    "user@example.com": "XVVH",
    "user@example.com": "definitelynotguru",
    "user@example.com": "ChasLui",
    "user@example.com": "rio-jeong",
    "user@example.com": "Cdddo",
    "user@example.com": "Cdddo",
    "user@example.com": "ArcanePivot",
    "user@example.com": "benegessarit",
    "user@example.com": "MrDiamondBallz",
    "user@example.com": "claudlos",  # PR #52351 salvage (cron base_url exfil guard; #<salvagePR>)
    "user@example.com": "Adolanium",
    "user@example.com": "Kenmege",
    "user@example.com": "xtymac",
    "user@example.com": "Diyoncrz18",
    "user@example.com": "ali-nld",
    "user@example.com": "necoweb3",
    "user@example.com": "DNAlec",  # PR #61743 salvage (honor reset policy in #54878 stale-heal recovery)
    "user@example.com": "joelbrilliant",  # PR #58486 salvage (session-expiry cleanup must not end row as agent_close)
    "user@example.com": "hydracoco7",  # PR #61382 salvage (id-less cron job freeze)
    "user@example.com": "AlexFucuson9",  # PR #61209 salvage (hygiene compression data loss)
    "user@example.com": "shauneccles",  # PR #95433 salvage (compression stall-fallback retry on fallback_chain; #78981)
    "user@example.com": "fedosis",  # PR #94996 salvage (compression rotation dedupe current-turn rows)
    "user@example.com": "adambiggs",  # PR #43819 salvage (holographic shared SQLite connection)
    "user@example.com": "kohoj",  # PR #61667 salvage (nonce-CSP HTML session export)
    "user@example.com": "cypctlinux",  # PR #52403 salvage (Slack bot/workflow auth before no-user-id guard)
    "user@example.com": "YLChen-007",  # PR #26965 (approval remote command substitution)
    "user@example.com": "egilewski",  # co-author, PR #40663
    "user@example.com": "pinguarmy",
    "user@example.com": "joerj123",
    "user@example.com": "AIalliAI",
    "user@example.com": "AIalliAI",
    "user@example.com": "iamlukethedev",
    "user@example.com": "HaozheZhang6",
    "user@example.com": "barronlroth",
    "user@example.com": "OndrejDrapalik",
    "user@example.com": "tomekpanek",
    "user@example.com": "PhilipAD",
    "user@example.com": "underthestars-zhy",
    "user@example.com": "yanxue06",
    "user@example.com": "ARegalado1",
    "user@example.com": "AlchemistChaos",  # co-author only
    "user@example.com": "giladbau",
    "user@example.com": "Dusk1e",
    "user@example.com": "LaPhilosophie",
    "user@example.com": "maxtrigify",
    "user@example.com": "ccook1963",
    "user@example.com": "libre-7",
    "user@example.com": "kristianvast",
    "user@example.com": "RyTsYdUp",
    "user@example.com": "ProgramCaiCai",
    "user@example.com": "bmoore210",
    "user@example.com": "deaneeth",
    "user@example.com": "psionic73",
    "user@example.com": "manishbyatroy",
    "user@example.com": "manus-use",  # PR #51129 salvage (Discord thread-starter dedup, #51057)
    "user@example.com": "TheGardenGallery",
    "user@example.com": "randomsnowflake",
    "user@example.com": "zakame",
    "user@example.com": "jiangkoumo",
    "user@example.com": "qin-ctx",
    "user@example.com": "ViewWay",
    "user@example.com": "m4dni5",
    "user@example.com": "harjothkhara",
    "user@example.com": "HeLLGURD",
    "user@example.com": "synapsesx",
    "user@example.com": "itsflownium",
    "user@example.com": "dirtyren",
    "user@example.com": "juniperbevensee",
    "user@example.com": "krowd3v",
    "user@example.com": "dfein38347g",
    "user@example.com": "thegoodguysla",
    "user@example.com": "s96919",
    "user@example.com": "rasitakyol",
    "user@example.com": "Thatgfsj",
    "user@example.com": "seagpt",
    "user@example.com": "davidrobertson",
    "user@example.com": "HaiderSultanArc",
    "user@example.com": "jjadeo-oss",
    "user@example.com": "juanfradb",
    "user@example.com": "100yenadmin",
    "user@example.com": "doxe0x",
    "user@example.com": "Code-suphub",
    "user@example.com": "Code-suphub",
    "user@example.com": "shuangxinniao",
    "user@example.com": "brendandebeasi",
    "user@example.com": "dorokuma",
    "user@example.com": "liuwei666888",
    "user@example.com": "liuwei666888",
    "user@example.com": "justinschille",
    "user@example.com": "unsupportedpastels",
    "user@example.com": "John-Lussier",
    "user@example.com": "bytesnail",  # PR #60360 salvage (--yolo startup ordering; #60328)
    "user@example.com": "nullptr0807",  # PR #60956 salvage (gateway hygiene in-place compaction; #60947)
    "user@example.com": "embwl0x",  # PR #60810 salvage (channel directory offload)
    "user@example.com": "doncazper",
    "user@example.com": "alex107ivanov",
    "user@example.com": "rungmc357",
    "user@example.com": "flo1t",
    "user@example.com": "fanyangCS",
    "user@example.com": "bigstar0920",
    "user@example.com": "tanmayxchoudhary",
    "user@example.com": "AIalliAI",
    "user@example.com": "waseemshahwan",
    "user@example.com": "hellno",
    "user@example.com": "devatnull",
    "user@example.com": "Marxb85",
    "user@example.com": "yy<PROJECT_NAME>uwu",  # PR #47567 salvage (Matrix: register inbound handlers with wait_sync=True so _dispatch_sync's gather awaits them; without it mautrix fire-and-forgets and inbound intake has no completion point)
    "user@example.com": "jearnest11",  # PR #48700 salvage (multi-profile gateway flap: use node symlink's own parent, not .resolve() target, when building systemd/launchd service PATH so one profile's node path can't leak into every unit and force a perpetual daemon-reload restart loop)
    "user@example.com": "tgmerritt",  # PR #43553 salvage (parse vLLM's token-based output-cap error format so over-cap max_tokens 400s reduce the output cap instead of death-looping into compression)
    "user@example.com": "justin-cyhuang",
    "user@example.com": "Tranquil-Flow",
    "jason@hermes-jc": "jcjc81",
    "user@example.com": "friendshipisover",
    "user@example.com": "MattKotsenas",
    "user@example.com": "ypwcharles",
    "user@example.com": "marco0158",
    "user@example.com": "lkevincc0",
    "user@example.com": "Cossackx",  # PR #52528 salvage (Windows hermes-shim resolution + prefer --update on recovery; #52378)
    "user@example.com": "Icather",  # PR #45554 salvage (self-lock guard breaks Windows update-recovery infinite loop; #52378 / #45542)
    "--email": "user@example.com",
    "user@example.com": "francescomucio",
    "user@example.com": "thestral123",
    "user@example.com": "tkwong",
    "user@example.com": "buihongduc132",
    "user@example.com": "EtherAura",  # PR #45205 salvage (Linux in-app update relaunch / GUI-skew terminal state)
    "user@example.com": "valentt",
    "user@example.com": "devorun",
    "user@example.com": "x7peeps",
    "user@example.com": "andressommerhoff",
    "user@example.com": "x7peeps",
    "user@example.com": "skyc1e",
    "user@example.com": "namredips",
    "user@example.com": "whoislikemiha",
    "user@example.com": "m24927605",
    "user@example.com": "gdeyoung",
    "user@example.com": "GauravPatil2515",
    "user@example.com": "Sworntech-dev",
    "user@example.com": "jvradahellys24-art",
    "user@example.com": "bbopen",
    "user@example.com": "BBCrypto-web",
    "user@example.com": "asimons81",
    "user@example.com": "HwangJohn",
    "user@example.com": "anderskev",
    "user@example.com": "alloevil",
    "user@example.com": "aieng-abdullah",
    "user@example.com": "loes5050",
    "user@example.com": "Tortugasaur",
    "user@example.com": "DrZM007",
    "user@example.com": "yapsrubricsz0",
    "user@example.com": "Railway9784",
    "user@example.com": "graphanov",
    "user@example.com": "Antimatter543",
    "user@example.com": "mkslzk",
    "user@example.com": "baolingao",
    "user@example.com": "hakanpak",
    "user@example.com": "lgalabru",
    "user@example.com": "johnjacobkenny",
    "user@example.com": "channkim",
    "user@example.com": "xxchan",
    "user@example.com": "x1erra",
    "user@example.com": "zimigit2020",
    "user@example.com": "ft-ioxcs",
    "user@example.com": "0xneobyte",
    "user@example.com": "Veritas-7",
    "user@example.com": "kmccammon",
    "user@example.com": "CiarasClaws",
    "user@example.com": "WolframRavenwolf",
    "user@example.com": "WolframRavenwolf",
    "user@example.com": "895252509",
    "user@example.com": "zxcasongs",
    "user@example.com": "alfred-smith-0",
    "user@example.com": "tangtaizong666",
    "user@example.com": "aldoeliacim",
    "user@example.com": "MaxFreedomPollard",
    "user@example.com": "achaljhawar",
    "user@example.com": "claytonchew",
    "user@example.com": "hbentel",
    "user@example.com": "justinbao19",
    "user@example.com": "kdunn926",
    "user@example.com": "mvanhorn",
    "user@example.com": "youjunxiaji",
    "user@example.com": "NormallyGaussian",
    "user@example.com": "mollusk",
    "user@example.com": "temalo",
    "user@example.com": "alarcritty",
    "user@example.com": "islam666",
    "user@example.com": "mnajafian-nv",
    "user@example.com": "lsaether",
    "user@example.com": "JimStenstrom",
    "user@example.com": "rodboev",
    "user@example.com": "dangelo352",
    "user@example.com": "zhaoleibd",
    "user@example.com": "jeffrobodie-glitch",
    "user@example.com": "kyssta-exe",
    "user@example.com": "kyssta-exe",  # PR #55657 salvage (read-before-write invariant for background-review skill patches; #55647)
    "user@example.com": "ITheEqualizer",
    "user@example.com": "stremtec",
    "user@example.com": "solaitken",
    "user@example.com": "worlldz",
    "user@example.com": "vladkvlchk",
    "user@example.com": "ThyFriendlyFox",
    "user@example.com": "truenorth-lj",
    "user@example.com": "nepenth",
    "user@example.com": "benfrank241",
    "user@example.com": "SaguaroDev",
    "user@example.com": "Subway2023",
    "user@example.com": "tmchow",
    "user@example.com": "a1245582339",
    "user@example.com": "mathijsvandenhurk",
    "user@example.com": "davidgut1982",
    "user@example.com": "SeaXen",
    "user@example.com": "LengR",
    "user@example.com": "Kewe63",
    "user@example.com": "Kewe63",
    "user@example.com": "CharZhou",
    "user@example.com": "HashClawAI",
    "user@example.com": "TonyPepeBear",
    "user@example.com": "nielskaspers",
    "user@example.com": "bpasquini",
    "user@example.com": "kurobaryo",
    "user@example.com": "scubamount",
    "user@example.com": "youngstar-eth",
    "user@example.com": "alelpoan",
    "user@example.com": "alelpoan",
    "user@example.com": "Aman113114-IITD",
    "user@example.com": "octavioturra",
    "user@example.com": "ryo-solo",
    "user@example.com": "Twanislas",
    "user@example.com": "adam91holt",
    "user@example.com": "kchuang1015",
    "user@example.com": "MaheshtheDev",
    "user@example.com": "kyssta-exe",
    "user@example.com": "ashishpatel26",
    "user@example.com": "fujinice",
    "user@example.com": "carltonawong",
    "user@example.com": "EvilHumphrey",
    "user@example.com": "superearn-fisher",
    "user@example.com": "kpadilha",
    "user@example.com": "chaconne67",
    "user@example.com": "Pluviobyte",
    "user@example.com": "sanghyuk-seo-nexcube",
    "user@example.com": "Brixyy",
    "user@example.com": "wangpuv",
    "user@example.com": "ticketclosed-wontfix",
    "user@example.com": "victorGPT",
    "user@example.com": "xiaoxinova",
    "user@example.com": "wenchengxucool",
    "user@example.com": "Frowtek",
    "user@example.com": "julio-cloudvisor",
    "user@example.com": "kweiner",
    "user@example.com": "kweiner",
    "user@example.com": "faisfamilytravel",
    "user@example.com": "baofuen",
    "user@example.com": "Interstellar-code",
    "user@example.com": "Interstellar-code",
    "user@example.com": "tillfalko",
    "user@example.com": "fesalfayed",
    "user@example.com": "maxcz79",
    # teknium (multiple emails)
    "user@example.com": "teknium1",
    "user@example.com": "kenyonxu",
    "user@example.com": "CipherFrame",
    "user@example.com": "donovan-yohan",
    "user@example.com": "jacevys",
    "user@example.com": "CNSeniorious000",
    "user@example.com": "YarrowQiao",
    "user@example.com": "erhnysr",
    "user@example.com": "0xdany",  # PR #26124 salvage (chat argv off event loop)
    "user@example.com": "WorldWriter",
    "user@example.com": "WorldWriter",
    "user@example.com": "Strontvod",
    "user@example.com": "someaka",
    "user@example.com": "Jaggia",
    "user@example.com": "steveonjava",
    "user@example.com": "steveonjava",
    "user@example.com": "MoonRay305",
    "user@example.com": "annguyenNous",
    "user@example.com": "simpolism",
    "user@example.com": "simpolism",
    "user@example.com": "simpolism",
    "user@example.com": "vKongv",
    "user@example.com": "devatnull",
    "user@example.com": "discodirector",
    "user@example.com": "TruaShamu",
    "user@example.com": "Stark-X",
    "user@example.com": "nthrow",
    "user@example.com": "mikeyobrien",
    "user@example.com": "falasi",
    "user@example.com": "chdlc",
    "user@example.com": "nycomar",
    "user@example.com": "qiyin-code",
    "user@example.com": "aashizpoudel",
    "user@example.com": "AdityaRajeshGadgil",
    "user@example.com": "shaun0927",
    "user@example.com": "Soju06",
    "user@example.com": "Soju06",
    "user@example.com": "Bihruze",
    "user@example.com": "Lempkey",
    "user@example.com": "m0n3r0",
    "user@example.com": "leeseoki0",
    "user@example.com": "kronexoi",
    "user@example.com": "vgocoder",
    "user@example.com": "Schrotti77",
    "user@example.com": "devwdave",
    "user@example.com": "devwdave",
    "user@example.com": "zapabob",
    "user@example.com": "zapabob",
    "user@example.com": "jfuenmayor",
    "user@example.com": "Jiahui-Gu",
    "user@example.com": "YLChen-007",
    "user@example.com": "xzessmedia",
    "user@example.com": "AdamPlatin123",
    "user@example.com": "waefrebeorn",
    "user@example.com": "dusterbloom",
    "user@example.com": "basilalshukaili",
    "user@example.com": "basilalshukaili",
    "user@example.com": "liuhao1024",
    "user@example.com": "Rivuza",
    "user@example.com": "annguyenNous",
    "user@example.com": "annguyenNous",
    "user@example.com": "devatnull",
    "user@example.com": "kylekahraman",
    "user@example.com": "kylekahraman",
    "user@example.com": "seppegadeyne",
    "user@example.com": "seppegadeyne",
    "user@example.com": "blackpilledsoftware-prog",
    "user@example.com": "blackpilledsoftware-prog",
    "user@example.com": "dsr-restyn",
    "user@example.com": "WuKongAI-CMU",
    "user@example.com": "codeblackhole1024",
    "user@example.com": "Lempkey",
    "user@example.com": "nidhi-singh02",
    "user@example.com": "aashizpoudel",
    "user@example.com": "olisikh",
    "user@example.com": "JithendraNara",
    "user@example.com": "islam666",
    "user@example.com": "islam666",
    "user@example.com": "outdoorsea",
    "user@example.com": "thedavidmurray",
    "user@example.com": "leoneparise",
    "user@example.com": "mrshu",
    "user@example.com": "am423",
    "user@example.com": "ygd58",
    "user@example.com": "buntingszn",
    "user@example.com": "Alex-yang00",
    "user@example.com": "yangguangjin",
    "user@example.com": "teknium1",
    "user@example.com": "Glucksberg",
    "user@example.com": "Glucksberg",
    "user@example.com": "thelumiereguy",
    "user@example.com": "pnascimento9596",
    "user@example.com": "dskwe",
    "user@example.com": "wuli666",
    "user@example.com": "tw2818",
    "user@example.com": "counterposition",
    "user@example.com": "Korkyzer",
    "user@example.com": "zhengyn0001",
    "user@example.com": "littlewwwhite",
    "user@example.com": "db-aeon",
    "user@example.com": "ahmedbadr3",
    "user@example.com": "CoinTheHat",
    "user@example.com": "curiouscleo",
    "user@example.com": "hrkzogw",
    "user@example.com": "dandacompany",
    "user@example.com": "TreyDong",
    "user@example.com": "explainanalyze",
    "user@example.com": "pkyanam",
    "user@example.com": "1000Delta",
    "user@example.com": "1000Delta",
    "user@example.com": "szymonclawd",
    "user@example.com": "szymonclawd",
    "user@example.com": "worlldz",
    "user@example.com": "luoyuctl",
    "user@example.com": "luoyuctl",
    "user@example.com": "teknium1",
    "user@example.com": "InB4DevOps",
    "user@example.com": "InB4DevOps",
    "user@example.com": "AhmetArif0",
    "user@example.com": "purzbeats",
    "user@example.com": "Hugo-SEQUIER",
    "user@example.com": "Kylejeong2",
    "user@example.com": "Gutslabs",
    "user@example.com": "nocturnum91",
    "user@example.com": "gianfrancopiana",
    "user@example.com": "Abd0r",
    "user@example.com": "HuangYuChuh",
    "user@example.com": "hrygo",
    "user@example.com": "hrygo",
    "user@example.com": "eren-karakus0",
    "user@example.com": "Freeman-Consulting",
    "user@example.com": "rahimsais",
    "user@example.com": "rahimsais",
    "user@example.com": "NivOO5",
    "user@example.com": "NivOO5",
    "user@example.com": "kjames2001",
    "user@example.com": "kjames2001",
    "user@example.com": "wilsen0",
    "user@example.com": "Abd0r",
    "user@example.com": "oswaldb22",
    "user@example.com": "AJV20",
    "user@example.com": "masonjames",
    "user@example.com": "amethystani",
    "user@example.com": "liquidchen",
    "user@example.com": "subtract0",
    "user@example.com": "ReqX",
    "user@example.com": "qWaitCrypto",
    "user@example.com": "kidonng",
    "user@example.com": "ayushere",
    "user@example.com": "DanielLSM",
    "user@example.com": "v1b3coder",
    "user@example.com": "ming1523",
    "user@example.com": "Qwinty",
    "user@example.com": "Que0x",
    "user@example.com": "CalmProton",
    "user@example.com": "mbac",
    "user@example.com": "nicoechaniz",
    "user@example.com": "Ninso112",
    "user@example.com": "wesleysimplicio",
    "user@example.com": "SiliconID",
    "user@example.com": "xieNniu",
    "user@example.com": "wali-reheman",
    "user@example.com": "uzunkuyruk",
    "user@example.com": "Zhekinmaksim",
    "user@example.com": "KvnGz",
    "user@example.com": "MottledShadow",
    "user@example.com": "adamludwin",
    "user@example.com": "NikolayGusev-astra",
    "user@example.com": "liuguangyong93",
    "user@example.com": "exiao",
    "user@example.com": "nik1t7n",
    "user@example.com": "ggnnggez",
    "user@example.com": "ehz0ah",
    "user@example.com": "eloklam",
    "user@example.com": "kyan12",
    "user@example.com": "rylena",
    "user@example.com": "jatingodnani",
    "user@example.com": "adybag14-cyber",
    "user@example.com": "tmimmanuel",
    "user@example.com": "donramon77",
    "user@example.com": "IMHaoyan",
    "user@example.com": "revaraver",
    "user@example.com": "dengtaoyuan450-a11y",
    "user@example.com": "Junass1",
    "user@example.com": "Bartok9",
    "user@example.com": "Bartok9",
    "user@example.com": "erhnysr",  # PR #25198 salvage (tool-progress flood-control)
    "user@example.com": "CryptoByz",  # PR #25630 salvage (polling conflict Stage 1+2)
    "user@example.com": "fabiosiqueira",  # PR #27212 salvage (bg-process notif anchor)
    "user@example.com": "falconexe",  # PR #24511 salvage (sticky-IP reset)
    "user@example.com": "fonhal",  # PR #27865/#27861 salvage (mention entities / typing fallback)
    "user@example.com": "Zyrixtrex",  # PR #26754 salvage (avoid duplicate text after auto-TTS)
    "user@example.com": "nftpoetrist",  # PR #25856 salvage (escape slash-confirm preview)
    "user@example.com": "samahn0601",  # PR #27887 salvage (retry wrapped connect timeouts)
    "user@example.com": "aqilaziz",  # PR #26406 salvage (preserve native audio outside Telegram)
    "user@example.com": "karthikeyann",  # PR #26609 salvage (DM-topic routing pin)
    "user@example.com": "kunci115",  # PR #27098 salvage (thread-not-found retry)
    "user@example.com": "hayka-pacha",  # PR #25270 salvage (registry-aware mcp_ prefix strip)
    "user@example.com": "chromalinx",  # PR #27014 salvage (commands for groups+DM)
    "user@example.com": "chromalinx",  # PR #37026 salvage (SSL CA guard)
    "user@example.com": "booker1207",  # PR #25132 salvage (gate profile bots by allowed topics)
    "user@example.com": "kiranvk-2011",  # PR #24815 salvage (image documents → vision)
    "user@example.com": "rak135",  # PR #25960 salvage (Windows /restart)
    "user@example.com": "B0Tch1",  # PR #27634 salvage (disable_topic_auto_rename)
    "user@example.com": "jackjin1997",  # PR #27239 salvage (restore DM topic thread_id after split)
    "user@example.com": "soynchux",  # PR #27806 salvage (chat-scoped auth without user_id)
    "user@example.com": "el-analista",  # PR #25368 salvage (cron topic fallback report)
    "user@example.com": "khungate",  # PR #25829 salvage (gmail-triage gt: callbacks)
    "user@example.com": "stevehq26-bot",  # PR #28015 salvage (quick-command-only menus)
    "user@example.com": "brndnsvr",  # PR #25327 salvage (channel post updates)
    "user@example.com": "houenyang-momo",  # PR #24014 salvage (quiet noisy errors)
    "user@example.com": "OCWC22",  # PR #24581 salvage (multi-bot exclusive mentions)
    "user@example.com": "ai-hana-ai",  # PR #23928 salvage (ignore_root_dm)
    "user@example.com": "indigokarasu",  # PR #26636 salvage (pin user message)
    "user@example.com": "alber70g",  # PR #25280 salvage (skip-STT + 2GB cap)
    "user@example.com": "eliteworkstation94-ai",  # PR #28157 salvage (group reply session splits)
    "user@example.com": "hllqkb",
    "user@example.com": "Bongulielmi",
    "user@example.com": "JTroyerOvermatch",
    "user@example.com": "tt-a1i",  # PR #48933 (SSE-only Anthropic stream aggregation, #48923)
    "user@example.com": "hharry11",
    "user@example.com": "wysie",
    "user@example.com": "RonHillDev",  # PR #29523 salvage (machine-local commit email)
    "user@example.com": "Moikapy",  # PR #31527 salvage
    "user@example.com": "gbarany",  # PR #27907 salvage (xAI sanitizer deepcopy)
    "user@example.com": "Nami4D",  # PR #28490 salvage
    "user@example.com": "jkausel-ai",
    "user@example.com": "Es1la",
    "user@example.com": "stephen0110",
    "user@example.com": "sonic-netizen",
    "user@example.com": "mwnickerson",
    "user@example.com": "SandroHub013",
    "user@example.com": "maciekczech",
    "user@example.com": "LeonSGP43",
    "user@example.com": "LeonSGP43",
    "user@example.com": "cyb0rgk1tty",
    "user@example.com": "cyb0rgk1tty",
    "user@example.com": "chimpera",
    "user@example.com": "cmullins70",
    "user@example.com": "zeejaytan",
    "user@example.com": "Aslaaen",
    "user@example.com": "Tkander1715",
    "user@example.com": "beardthelion",
    "user@example.com": "orcool",
    "user@example.com": "tangyuanjc",
    "user@example.com": "agentlinker",
    "user@example.com": "npmisantosh",
    "user@example.com": "luarss",
    "user@example.com": "zccyman",
    "user@example.com": "zccyman",  # PR #26998 (auxiliary fallback chain)
    "user@example.com": "Osraka",
    "user@example.com": "Osraka",
    "user@example.com": "ryptotalent",
    "user@example.com": "hookinglau",
    "user@example.com": "AllynSheep",
    "user@example.com": "AllynSheep",
    "user@example.com": "aqilaziz",
    "user@example.com": "aqilaziz",
    "user@example.com": "laoli-no1",
    "user@example.com": "laoli-no1",
    "user@example.com": "NorethSea",
    "user@example.com": "NorethSea",
    "user@example.com": "JamesX88",
    "user@example.com": "JamesX88",
    "user@example.com": "novax635",
    "user@example.com": "Krionex",
    "user@example.com": "rxdxxxx",
    "user@example.com": "MaHaoHao-ch",
    "user@example.com": "xydigit-zt",
    "user@example.com": "revaraver",
    "user@example.com": "TheEpTic",
    "user@example.com": "wmagev",
    "user@example.com": "ashermorse",
    "user@example.com": "happy5318",
    "user@example.com": "wabrent",
    "user@example.com": "CashWilliams",
    "user@example.com": "chengoak",
    "user@example.com": "qxxaa",
    "user@example.com": "guillaumemeyer",
    "user@example.com": "EmelyanenkoK",
    "user@example.com": "manateelazycat",
    "user@example.com": "Beandon13",
    "user@example.com": "asimons81",
    "user@example.com": "jethac",
    "user@example.com": "vishal-dharm",
    "user@example.com": "deep-name",
    # LINE messaging plugin (synthesis PR)
    "user@example.com": "leepoweii",
    "user@example.com": "liyoungc",
    "user@example.com": "perng",
    "user@example.com": "soichiyo",
    "user@example.com": "David-0x221Eight",
    "user@example.com": "David-0x221Eight",
    "user@example.com": "yuga-hashimoto",
    "user@example.com": "CES4751",
    "user@example.com": "counterposition",
    "user@example.com": "nidhi-singh02",
    "user@example.com": "Fearvox",
    "user@example.com": "Fearvox",
    "user@example.com": "Hypnus-Yuan",
    "user@example.com": "xsfX20",
    "user@example.com": "binhnt92",
    "user@example.com": "Alix-007",  # PR #54620 salvage (sms: bound Twilio webhook body reads)
    "user@example.com": "acesjohnny",
    "user@example.com": "liu-collab",
    "user@example.com": "haidao1919",
    "user@example.com": "zhanggttry",
    "user@example.com": "formulahendry",
    "user@example.com": "bogerman1",
    "user@example.com": "rob-maron",
    # Matrix parity salvage batch (April 2026)
    "sr@samirusani": "samrusani",
    "user@example.com": "angel12",
    "user@example.com": "charles-brooks",
    # DeepSeek v4 + Kimi thinking-mode reasoning_content salvage (April 2026)
    "user@example.com": "lsdsjy",
    "user@example.com": "season179",
    "user@example.com": "heathley",
    "user@example.com": "heathley",
    "user@example.com": "dandaka",
    "user@example.com": "cyclingwithelephants",
    # Temporary tool-progress cleanup salvage (May 2026)
    "user@example.com": "mrcharlesiv",
    "user@example.com": "liizfq",
    "user@example.com": "dhabibi",
    "user@example.com": "JayGwod",
    "user@example.com": "0xKingBack",
    "user@example.com": "SimbaKingjoe",
    "user@example.com": "MaxyMoos",
    "user@example.com": "leprincep35700",
    # OpenViking viking_read salvage (April 2026)
    "user@example.com": "htsh",
    "user@example.com": "pty819",
    "user@example.com": "pty819",
    "user@example.com": "pty819",
    "user@example.com": "chennest",
    # Curator fixes (Apr 30 2026)
    "user@example.com": "y0shua1ee",
    "user@example.com": "0xDevNinja",
    "user@example.com": "steezkelly",
    "user@example.com": "btorresgil",
    "user@example.com": "momowind",
    "user@example.com": "misery-hl",
    "user@example.com": "misery-hl",
    "user@example.com": "nik1t7n",
    "user@example.com": "nik1t7n",
    "user@example.com": "suncokret12",
    "user@example.com": "WompaJango",
    "user@example.com": "mioimotoai-lgtm",
    "user@example.com": "heyitsaamir",
    "user@example.com": "johnncenae",
    "user@example.com": "ThomassJonax",
    "user@example.com": "yes999zc",
    "user@example.com": "rmoen",
    "user@example.com": "thirstycrow",  # PR #23630 salvage (config-aware memory status labels)
    # Slack ephemeral slash-ack salvage (May 2026)
    "user@example.com": "probepark",
    # Slack batch salvage (May 2026)
    "user@example.com": "priveperfumes",
    "user@example.com": "amroessam",
    "user@example.com": "Hinotoi-agent",
    "user@example.com": "valda",
    "user@example.com": "0z1-ghb",
    "user@example.com": "yes999zc",
    "user@example.com": "DrStrangerUJN",
    "user@example.com": "hejuntt1014",
    "user@example.com": "dlkakbs",
    "user@example.com": "BeliefanX",
    "user@example.com": "changchun989",
    "user@example.com": "Mind-Dragon",
    "user@example.com": "Nanako0129",
    "user@example.com": "westers",
    "user@example.com": "yeyitech",
    "user@example.com": "beenherebefore",
    "user@example.com": "txbxxx",
    "user@example.com": "liuhao1024",
    "user@example.com": "devorun",
    "user@example.com": "iaji",
    "user@example.com": "beesrsj2500",
    "user@example.com": "beesrsj2500",
    "user@example.com": "Mind-Dragon",
    "user@example.com": "JustinUssuri",
    "user@example.com": "ma-pony",
    "user@example.com": "Sonoyunchu",
    "user@example.com": "yatesjalex",
    "user@example.com": "say8hi",
    "user@example.com": "Mirac1eSky",
    "user@example.com": "web3blind",
    "user@example.com": "web3blind",
    # Sessions export format cluster (July 2026): HTML + prompt-only salvages
    "user@example.com": "simplast",
    "user@example.com": "catbearlove1-lang",
    "user@example.com": "alexg0bot",
    "user@example.com": "scheidti",
    # Moonshot schema anyOf+enum salvage (May 2026)
    "user@example.com": "hendrixfreire",
    "user@example.com": "benjaminsehl",
    "user@example.com": "Nerijusas",
    # Compaction salvage batch (May 2026)
    "user@example.com": "MacroAnarchy",
    "user@example.com": "Ito-69",
    "user@example.com": "georgeglessner",
    "user@example.com": "maxims-oss",
    # Codex Spark restoration salvage (May 2026)
    "user@example.com": "nederev",
    "user@example.com": "askclaw-vesper",
    "user@example.com": "nazirulhafiy",
    "user@example.com": "BadTechBandit",
    "user@example.com": "Yoimex",
    "user@example.com": "romanornr",
    "user@example.com": "foxion37",
    "user@example.com": "bloodcarter",
    "user@example.com": "scotttrinh",
    "user@example.com": "quocanh261997",
    "user@example.com": "savanne-kham",  # PR #28958 salvage (strip tool_name for strict providers)
    # contributors (from noreply pattern)
    "user@example.com": "davidvv",
    "user@example.com": "xiaoqiang243",
    "user@example.com": "snreynolds",
    "user@example.com": "0xbyt4",
    "user@example.com": "MassiveMassimo",
    "user@example.com": "MassiveMassimo",
    "user@example.com": "kshitijk4poor",
    "user@example.com": "keifergu",
    "user@example.com": "kshitijk4poor",
    "user@example.com": "kshitijk4poor",
    "user@example.com": "SHL0MS",
    "user@example.com": "Abnertheforeman",
    "user@example.com": "amanning3390",
    "user@example.com": "tochukwuada",
    "user@example.com": "zicochaos",
    "user@example.com": "hharry11",
    "user@example.com": "kshitijk4poor",
    "user@example.com": "Tosko4",
    "user@example.com": "keiravoss94",
    "user@example.com": "veradim",  # PR #41201 salvage (Z.AI endpoint persist)
    "user@example.com": "stablegenius49",
    "user@example.com": "EKKOLearnAI",
    "user@example.com": "octo-patch",
    "user@example.com": "math0r-be",
    "user@example.com": "simbam99",
    "user@example.com": "irispillars",
    "user@example.com": "stablegenius49",
    "user@example.com": "batuhankocyigit",
    "user@example.com": "ismell0992-afk",
    "user@example.com": "iRonin",
    "user@example.com": "jvcl",
    "user@example.com": "aj-nt",
    "user@example.com": "UgwujaGeorge",
    "user@example.com": "francip",
    "user@example.com": "omnissiah-comelse",
    "user@example.com": "mavrickdeveloper",
    "user@example.com": "vilkasdev",
    "user@example.com": "cutepawss",
    "user@example.com": "memosr",
    "user@example.com": "memosr",
    "user@example.com": "milkoor",
    "user@example.com": "Fatty911",
    "user@example.com": "SHL0MS",
    "user@example.com": "raulvidis",
    "user@example.com": "Aum08Desai",
    "user@example.com": "kshitij-eliza",
    "user@example.com": "Jason2031",
    "user@example.com": "shitcoinsherpa",
    "user@example.com": "Sertug17",
    "user@example.com": "caentzminger",
    "user@example.com": "voidborne-d",
    "user@example.com": "ddupont808",
    "user@example.com": "voidborne-d",
    "user@example.com": "Readon",
    "user@example.com": "sirEven",
    "user@example.com": "sirEven",
    "user@example.com": "insecurejezza",
    "user@example.com": "JezzaHehn",
    "user@example.com": "JezzaHehn",
    "user@example.com": "dodo-reach",
    "user@example.com": "EdderTalmor",  # PR #41575 salvage (prompt-size: pass platform-resolved enabled_toolsets + agent.disabled_toolsets into the inspection agent; #41445)
    "user@example.com": "Bartok9",
    "user@example.com": "banditburai",
    "user@example.com": "Kyzcreig",
    "user@example.com": "Kyzcreig",
    "user@example.com": "crayfish-ai",
    "user@example.com": "MestreY0d4-Uninter",
    "user@example.com": "Roy-oss1",
    "user@example.com": "nosleepcassette",
    "user@example.com": "MestreY0d4-Uninter",
    "user@example.com": "davetist",
    "user@example.com": "yyq4193",
    "user@example.com": "Asunfly",
    "user@example.com": "honghua",
    "user@example.com": "jplew",
    "user@example.com": "nish3451",
    "user@example.com": "Mibayy",
    "user@example.com": "Mibayy",
    "user@example.com": "Mibayy",
    "user@example.com": "Mibayy",
    "user@example.com": "sgaofen",
    "user@example.com": "zhiyanliu",
    "user@example.com": "hhhonzik",
    "user@example.com": "hhuang91",
    "user@example.com": "Satoshi-agi",
    "user@example.com": "kunlabs",
    "user@example.com": "Wang-tianhao",
    "user@example.com": "ghostmfr",
    "user@example.com": "mewwts",
    "user@example.com": "haru398801",
    "user@example.com": "badgerbees",
    "user@example.com": "xnbi",
    "user@example.com": "xiahu88988",
    "user@example.com": "nocoo",
    "user@example.com": "n-WN",
    "user@example.com": "hiddenpuppy",
    "user@example.com": "ygd58",
    "user@example.com": "HiddenPuppy",
    "user@example.com": "jerome-benoit",
    "user@example.com": "Wysie",
    "user@example.com": "keyuyuan",
    "user@example.com": "Only-Code-A",
    "user@example.com": "TroyMitchell911",
    "user@example.com": "zhongyueming1121",
    "user@example.com": "hansnow",
    "user@example.com": "UNLINEARITY",
    "user@example.com": "burtenshaw",
    "user@example.com": "rnijhara",
    "user@example.com": "j0sephz",
    # contributors (manual mapping from git names)
    "user@example.com": "asheriif",
    "user@example.com": "dyxushuai",
    "user@example.com": "etcircle",
    "user@example.com": "liujinkun2025",
    "user@example.com": "dmahan93",
    "user@example.com": "ifrederico",
    "user@example.com": "cdanis",
    "user@example.com": "samherring99",
    "user@example.com": "crazywriter1",
    "user@example.com": "Aum08Desai",
    "user@example.com": "shannonsands",
    "user@example.com": "shannonsands",
    "user@example.com": "AxDSan",
    "user@example.com": "Erosika",
    "user@example.com": "hjc-puro",
    "user@example.com": "aydnOktay",
    "user@example.com": "Farukest",
    "user@example.com": "rovle",
    "user@example.com": "mengjian-github",
    "user@example.com": "kevinskysunny",
    "user@example.com": "yule975",
    "user@example.com": "meng93",
    "user@example.com": "teyrebaz33",
    "user@example.com": "Linux2010",
    "user@example.com": "elmatadorgh",
    "user@example.com": "elmatadorgh",
    "user@example.com": "alexzhu0",
    "user@example.com": "Swift42",
    "user@example.com": "Ruzzgar",
    "user@example.com": "Yukipukii1",
    "user@example.com": "alireza78a",
    "user@example.com": "OutThisLife",
    "user@example.com": "StefanIsMe",
    "user@example.com": "helix4u",
    "user@example.com": "SidUParis",
    "user@example.com": "Ifkellx",
    "user@example.com": "counterposition",
    "user@example.com": "BrennerSpear",
    "user@example.com": "akhater",
    "user@example.com": "akhater",
    "user@example.com": "handsdiff",
    "user@example.com": "etherman-os",
    "user@example.com": "mark-ramsell",
    "user@example.com": "taeng0204",
    "user@example.com": "gpickett00",
    "user@example.com": "wakamex",
    "user@example.com": "clawdia-nash",
    "user@example.com": "austinpickett",
    "user@example.com": "dieutx",
    "user@example.com": "jaisup",
    "user@example.com": "PercyDikec",
    "user@example.com": "HenkDz",
    # Azure Foundry salvage (PRs #9029, #4599, #10086, #8766)
    "user@example.com": "TechPrototyper",
    "user@example.com": "HangGlidersRule",
    "user@example.com": "pein892",
    "user@example.com": "deankerr",
    "user@example.com": "socrates1024",
    "user@example.com": "Salt-555",
    "user@example.com": "satelerd",
    "user@example.com": "danklynn",
    "user@example.com": "MattMaximo",
    "user@example.com": "mrhwick",
    "user@example.com": "j3ffffff",
    "user@example.com": "A-FdL-Prog",
    "user@example.com": "l0hde",
    "user@example.com": "difujia",
    "user@example.com": "trevorgordon981",  # PR #50590 co-author (prefer endpoints.api for Copilot base URL + empty-base-URL guard; #50252)
    "user@example.com": "vominh1919",
    "user@example.com": "YueLich",
    "user@example.com": "andyylin",
    "user@example.com": "jakubkrcmar",
    "user@example.com": "prasadus92",
    "user@example.com": "mssteuer",
    "user@example.com": "konsisumer",
    "user@example.com": "amanuel2",
    "user@example.com": "alexzhu0",
    "user@example.com": "AntAISecurityLab",
    "user@example.com": "briandevans",
    "user@example.com": "tcconnally",
    "user@example.com": "mijanx",
    "user@example.com": "inchargeautomation-lab",
    "user@example.com": "Bartok9",
    "user@example.com": "kuangmi-bit",
    "user@example.com": "sweetcornna",
    "user@example.com": "briancl2",
    "user@example.com": "CruxExperts",
    "user@example.com": "LeonSGP43",
    "user@example.com": "Kailigithub",
    "user@example.com": "vlwkaos",
    "user@example.com": "Oxidane-bot",
    "user@example.com": "Tranquil-Flow",
    "user@example.com": "Tranquil-Flow",
    "user@example.com": "mcndjxlefnd",
    "user@example.com": "Wangshengyang2004",
    "user@example.com": "H-Ali13381",
    "user@example.com": "XieNBi",
    "user@example.com": "maymuneth",
    "user@example.com": "nightq",
    "user@example.com": "5park1e",
    "user@example.com": "5park1e",
    "user@example.com": "innocarpe",
    "user@example.com": "qike-ms",
    "user@example.com": "AndreKurait",
    "user@example.com": "bsgdigital",
    "user@example.com": "nummanali",
    "user@example.com": "whitehatjr1001",
    "user@example.com": "0xNyk",
    "user@example.com": "0xNyk",
    "user@example.com": "buray",
    "user@example.com": "joshmartinelle",
    "user@example.com": "tekelala",
    "user@example.com": "vincentcharlebois",
    "user@example.com": "aryansingh",
    "user@example.com": "voteblake",
    "user@example.com": "pedh",
    "user@example.com": "haileymarshall",
    "user@example.com": "BennetYrWang",
    "user@example.com": "g-guthrie",
    "user@example.com": "bobashopcashier",
    "user@example.com": "bobashopcashier",
    "user@example.com": "megastary",  # PR #18325
    "user@example.com": "areu01or00",
    "user@example.com": "bryanyoung",
    "user@example.com": "christomitov",
    "user@example.com": "NousResearch",
    "user@example.com": "ReginaldasR",
    "user@example.com": "0xharryriddle",
    "user@example.com": "ericnicolaides",
    "user@example.com": "georgex8001",
    "user@example.com": "dimitrovi",
    "user@example.com": "benbarclay",
    "user@example.com": "ChimingLiu",
    "user@example.com": "AllardQuek",
    "user@example.com": "openclaw",
    "user@example.com": "Himess",
    "user@example.com": "erenkarakus",
    "user@example.com": "adavyas",
    "user@example.com": "aayushchaudhary",
    "user@example.com": "jasonoutland",
    "user@example.com": "Magaav",
    "user@example.com": "SPANISHFLU",
    "user@example.com": "mormio",
    "user@example.com": "cesareth",
    "user@example.com": "fuleinist",
    "user@example.com": "JackTheGit",
    "user@example.com": "0xjackyang",
    "user@example.com": "Jr-kenny",
    "user@example.com": "mbierling",
    "user@example.com": "alt-glitch",
    "user@example.com": "alt-glitch",
    "user@example.com": "oluwadareab12",
    "user@example.com": "simon-marcus",
    "user@example.com": "Xowiek",
    "user@example.com": "Gutslabs",
    "user@example.com": "zons-zhaozhy",
    "user@example.com": "Es1la",
    "user@example.com": "stephen0110",
    "user@example.com": "sonic-netizen",
    "user@example.com": "mwnickerson",
    "user@example.com": "SandroHub013",
    "user@example.com": "maciekczech",
    "user@example.com": "CoreyNoDream",
    "user@example.com": "franksong2702",
    "user@example.com": "ambition0802",
    "user@example.com": "beibi9966",
    # ── bulk addition: 75 emails resolved via API, PR salvage bodies, noreply
    #    crossref, and GH contributor list matching (April 2026 audit) ──
    "user@example.com": "aaronlab",
    "user@example.com": "hqhq1025",
    "user@example.com": "luyao618",
    "user@example.com": "houziershi",
    "user@example.com": "PStarH",
    "user@example.com": "Sanjays2402",
    "user@example.com": "Andy283",
    "user@example.com": "bingo906",
    "user@example.com": "AaronWong1999",
    "user@example.com": "DeployFaith",
    "user@example.com": "angelos",
    "user@example.com": "cokemine",
    "user@example.com": "ethernet8023",
    "user@example.com": "benbarclay",
    "user@example.com": "yyovil",
    "user@example.com": "nicoloboschi",
    "user@example.com": "cherifya",
    "user@example.com": "BongSuCHOI",
    "user@example.com": "Cafexss",
    "user@example.com": "dalianmao000",
    "user@example.com": "konsisumer",
    "user@example.com": "DomGrieco",
    "user@example.com": "spideystreet",
    "user@example.com": "dippwho",
    "user@example.com": "donrhmexe",
    "user@example.com": "dorukardahan",
    "user@example.com": "dsocolobsky",
    "user@example.com": "dsocolobsky",
    "user@example.com": "IAvecilla",
    "user@example.com": "duerzy",
    "user@example.com": "emozilla",
    "user@example.com": "fancydirty",
    "user@example.com": "farion1231",
    "user@example.com": "flobo3",
    "user@example.com": "pefontana",
    "user@example.com": "fxfitz",
    "user@example.com": "Helmi",
    "user@example.com": "gaixianggeng",
    "user@example.com": "geoffwellman",
    "user@example.com": "jamesarch",
    "user@example.com": "LongOddCode",
    "user@example.com": "glennc",
    "user@example.com": "hata1234",
    "user@example.com": "Hmbown",
    "user@example.com": "m0n5t3r",
    "user@example.com": "m0n5t3r",
    "user@example.com": "JiayuuWang",
    "user@example.com": "sjh9714",
    "user@example.com": "yoniebans",
    "user@example.com": "simpolism",
    "user@example.com": "jjovalle99",
    "user@example.com": "Julientalbot",
    "user@example.com": "kagura-agent",
    "user@example.com": "youngDoo",
    "user@example.com": "kamil-gwozdz",
    "user@example.com": "bugkill3r",
    "user@example.com": "MustafaKara7",
    "user@example.com": "kira-ariaki",
    "user@example.com": "KiraKatana",
    "user@example.com": "knopki",
    "user@example.com": "limars874",
    "user@example.com": "lesterli",
    "user@example.com": "MagicRay1217",
    "user@example.com": "GenKoKo",
    "user@example.com": "iacker",
    "user@example.com": "sontianye",
    "user@example.com": "jackjin1997",
    "user@example.com": "jackjin1997",
    "user@example.com": "danieldoderlein",
    "user@example.com": "lrawnsley",
    "user@example.com": "taeuk178",
    "user@example.com": "ogzerber",
    "user@example.com": "cola-runner",
    "user@example.com": "ygd58",
    "user@example.com": "warabe1122",
    "user@example.com": "willy-scr",
    "user@example.com": "vominh1919",
    "user@example.com": "iamagenius00",
    "user@example.com": "cresslank",
    "user@example.com": "trevthefoolish",
    "user@example.com": "ATran28",  # PR #77270 whatsapp bridge reconnect wedge fix
    "user@example.com": "ziliangpeng",
    "user@example.com": "ziliangpeng",
    "user@example.com": "centripetal-star",
    "user@example.com": "LeonSGP43",
    "user@example.com": "LeonSGP43",
    "user@example.com": "LeonSGP43",
    "user@example.com": "Lubrsy706",
    "user@example.com": "spniyant",
    "user@example.com": "nicha16",  # PR #54139 partial salvage (re-register tools after park revival)
    "user@example.com": "olafthiele",
    "user@example.com": "sprmn24",
    "user@example.com": "olafthiele",
    "user@example.com": "r266-tech",
    "user@example.com": "r266-tech",  # PR #55780 salvage (dead-target not_found blast radius)
    "user@example.com": "BlackishGreen33",
    "user@example.com": "gnodet",  # PR #37598 salvage (MCP preflight POST probe fallback)
    "user@example.com": "kaishi00",  # PR #55203 salvage (skip_preflight opt-out)
    "user@example.com": "setclock",  # PR #27052 salvage (MCP session-expired retry waits for a distinct fresh session)
    "user@example.com": "sberan",  # PR #54494 salvage (--connect-timeout flag on hermes mcp add)
    "user@example.com": "labsobsidian",  # PR #56699 salvage (MCP OAuth login connect_timeout floor)
    "user@example.com": "SaulJWu",
    "user@example.com": "hcshen0111",
    "user@example.com": "Cygra",
    "user@example.com": "Sertug17",
    "user@example.com": "stephenschoettler",
    "user@example.com": "yyovil",
    "user@example.com": "taosiyuan163",
    "user@example.com": "tesseracttars-creator",
    "user@example.com": "xingkongliang",
    "user@example.com": "Oxidane-bot",
    "user@example.com": "Tranquil-Flow",
    "user@example.com": "mcndjxlefnd",
    "user@example.com": "Unayung",
    "user@example.com": "WorldInnovationsDepartment",
    "user@example.com": "win4r",
    "user@example.com": "KUSH42",
    "user@example.com": "SeeYangZhi",
    "user@example.com": "yongtenglei",
    "user@example.com": "YoungYang963",
    "user@example.com": "Junass1",
    "user@example.com": "WAXLYY",
    "user@example.com": "Dusk1e",
    "user@example.com": "zhouboli",
    "user@example.com": "tomqiaozc",
    "user@example.com": "xinbenlv",
    "user@example.com": "ZaynJarvis",
    "user@example.com": "ZaynJarvis",
    "user@example.com": "loongfay",
    "user@example.com": "lrt4836",
    "user@example.com": "beforeload",
    "user@example.com": "libo1106",
    "user@example.com": "295367131",
    "user@example.com": "IxAres",
    "user@example.com": "danieldliu",
    "user@example.com": "loongzhao",
    "user@example.com": "Bartok9",
    "user@example.com": "LeonSGP43",
    "user@example.com": "kshitijk4poor",
    "user@example.com": "malaiwah",
    "user@example.com": "malaiwah",
    "user@example.com": "gnanam1990",
    "user@example.com": "0xyg3n",
    "user@example.com": "Spaceman-Spiffy",  # PR #35586 (renamed account)
    "user@example.com": "ianculling",  # PR #36087
    "user@example.com": "0xyg3n",
    "user@example.com": "nftpoetrist",  # PR #18982
    "user@example.com": "millerc79",  # PR #19033
    "user@example.com": "shellybotmoyer",  # PR #18915 (bot-committed)
    "user@example.com": "exxmen",  # PR #19555
    "user@example.com": "Hypn0sis",
    "user@example.com": "OwenYWT",
    "user@example.com": "v1k22",
    "user@example.com": "RucchiZ",
    "user@example.com": "tannerfokkens-maker",
    "user@example.com": "LehaoLin",
    "user@example.com": "imink",
    "user@example.com": "hedgeho9X",
    "user@example.com": "bernylinville",
    "user@example.com": "briandevans",
    "user@example.com": "LLQWQ",
    "user@example.com": "memosr",
    "user@example.com": "perlowja",
    "user@example.com": "web-dev0521",
    "user@example.com": "bjianhang",
    "user@example.com": "tangyuanjc",
    "user@example.com": "harryplusplus",
    "user@example.com": "anthhub",
    "user@example.com": "phuongvm",
    "user@example.com": "AllardQuek",
    "user@example.com": "shenuu",
    "user@example.com": "xiayh0107",
    "user@example.com": "opriz",
    "user@example.com": "xxxigm",
    "user@example.com": "ElSnacko",
    "user@example.com": "x9x9x9x9x9x91",
    "user@example.com": "NickLarcombe",
    "user@example.com": "xxxigm",
    "user@example.com": "anniesurla",
    "user@example.com": "nv-kasikritc",
    "user@example.com": "bbednarski9",
    "user@example.com": "WideLee",
    "user@example.com": "AviArora02-commits",
    "user@example.com": "draix",
    "user@example.com": "draix",
    "user@example.com": "JimLiu",
    "user@example.com": "jooray",
    "user@example.com": "maxchernin",
    "user@example.com": "LVT382009",
    "user@example.com": "heykb",
    "user@example.com": "StefanIsMe",
    "user@example.com": "lumenradley",
    "user@example.com": "sjz-ks",
    "user@example.com": "haileymarshall",
    "user@example.com": "aniruddhaadak80",
    "user@example.com": "jerilynzheng",
    "user@example.com": "Aslaaen",
    "user@example.com": "pinion05",
    "user@example.com": "VTRiot",
    "user@example.com": "iamagenius00",
    "user@example.com": "Feranmi10",
    "user@example.com": "Feranmi10",
    "user@example.com": "simon-gtcl",
    "user@example.com": "houko",
    "user@example.com": "cgarwood82",
    "user@example.com": "anna-oake",
    "user@example.com": "jaffarkeikei",
    "user@example.com": "hxp-plus",
    "user@example.com": "Tianworld",
    "user@example.com": "wujhsu",
    "user@example.com": "niyoh120",
    "user@example.com": "vrinek",
    "user@example.com": "xandersbell",
    "user@example.com": "Somme4096",
    "user@example.com": "brianclemens",
    "user@example.com": "yudaiyan",
    "user@example.com": "ycbai",
    "user@example.com": "longsizhuo",
    "user@example.com": "ms-alan",
    "user@example.com": "johnisag",
    "user@example.com": "explainanalyze",
    "user@example.com": "WuTianyi123",
    "user@example.com": "li0near",
    "user@example.com": "li0near",
    "user@example.com": "tymrtn",
    "user@example.com": "kallidean",
    "user@example.com": "baocin",
    "user@example.com": "princepal9120",
    "user@example.com": "guglielmofonda",
    "user@example.com": "yehuosi",
    "user@example.com": "yehuosi",
    "user@example.com": "jelrod27",
    "user@example.com": "konsisumer",
    "user@example.com": "sicnuyudidi",
    "user@example.com": "haimu0x",
    "user@example.com": "NIDNASSER-Abdelmajid",
    "user@example.com": "projectadmin-dev",
    "user@example.com": "Dev-Mriganka",
    "user@example.com": "shushuzn",
    "user@example.com": "iborazzi",
    "user@example.com": "A-afflatus",
    "user@example.com": "huangke19",
    "user@example.com": "10ishq",
    "user@example.com": "christopherwoodall",
    "user@example.com": "zhang9w0v5",
    "user@example.com": "fuleinist",
    "user@example.com": "Llugaes",
    "user@example.com": "Llugaes",
    "user@example.com": "fengtianyu88",
    "user@example.com": "lmoncany",
    "user@example.com": "fatinghenji",
    "user@example.com": "xinpengdr",
    "user@example.com": "mikewaters",
    "user@example.com": "WadydX",
    "user@example.com": "isaachuangGMICLOUD",
    "user@example.com": "isaachuangGMICLOUD",
    "user@example.com": "hsy5571616",
    "user@example.com": "Nan93",
    "user@example.com": "zhouxiaoya12",
    "user@example.com": "roytian1217",
    "user@example.com": "minorgod",
    "user@example.com": "wenhao7",
    "user@example.com": "yzx9",
    "user@example.com": "lvnilesh",
    "user@example.com": "azhengbot",
    "user@example.com": "sharziki",
    "user@example.com": "RyanLee-Dev",
    "user@example.com": "TaroballzChen",
    "user@example.com": "Lind3ey",
    "user@example.com": "phpoh",
    "user@example.com": "vivganes",
    "user@example.com": "MikeFac",
    "user@example.com": "GuyCui",
    "user@example.com": "maelrx",
    "user@example.com": "ats3v",
    # v0.11.0 additions
    "user@example.com": "benbarclay",
    "user@example.com": "Jiawen-lee",
    "user@example.com": "kovyrin",
    "user@example.com": "kovyrin",
    "user@example.com": "liftaris",
    "user@example.com": "arihantsethia",
    "user@example.com": "coekfung",
    "user@example.com": "teknium1",
    "user@example.com": "cuyua9",
    "user@example.com": "Disaster-Terminator",
    "user@example.com": "LeonSGP43",
    "user@example.com": "grimmjoww578",  # PR #52142 co-author (direct CUA window targeting)
    "user@example.com": "Zyproth",
    "user@example.com": "amitgaur",
    "user@example.com": "mrbob-git",
    "user@example.com": "kiala9",
    "user@example.com": "alanxchen85",
    "user@example.com": "John-tip",
    "user@example.com": "konsisumer",
    "user@example.com": "CIRWEL",
    "user@example.com": "molvikar",
    "user@example.com": "nftpoetrist",
    "user@example.com": "colorcross",
    "user@example.com": "zhao0112",
    "user@example.com": "EthanGuo-coder",
    "user@example.com": "tmdgusya",
    "user@example.com": "leavrcn",
    "user@example.com": "wanazhar",
    "user@example.com": "cixuuz",
    "user@example.com": "pasevin",
    "user@example.com": "pasevin",
    "user@example.com": "holynn-q",
    "user@example.com": "holynn-q",
    "user@example.com": "jacdevos",
    "user@example.com": "liuhao1024",
    "user@example.com": "suninrain086",  # PR #57651 salvage of #50685 (vision custom-endpoint creds)
    "user@example.com": "mohamedorigami-jpg",  # PR #32117 (cron storage root anchor; #32091)
    "user@example.com": "sherman-yang",  # PR #32788 (cron per-job MCP merge; #23997)
    "user@example.com": "rbrtbn",
    "user@example.com": "VinciZhu",
    "user@example.com": "rodrigoeqnit",
    "user@example.com": "sgtworkman",
    "user@example.com": "keepcalmqqf",
    "user@example.com": "ai-ag2026",
    "user@example.com": "YanzhongSu",
    "user@example.com": "WanderWang",
    "user@example.com": "yuehei",
    "user@example.com": "Emidomenge",
    "user@example.com": "BlackJulySnow",
    "user@example.com": "helix4u",
    "user@example.com": "flobo3",
    "user@example.com": "dpaluy",
    "user@example.com": "el-analista",
    "user@example.com": "ms-alan",
    "user@example.com": "johnisag",
    "user@example.com": "explainanalyze",
    "user@example.com": "hex-clawd",
    "user@example.com": "LeonSGP43",
    "user@example.com": "barteqpl",
    "user@example.com": "pama0227",
    "user@example.com": "ee-blog",
    "user@example.com": "simplenamebox-ops",
    "user@example.com": "alt-glitch",
    "user@example.com": "foreverxdord",
    "user@example.com": "QifengKuang",
    "user@example.com": "jjjojoj",
    "user@example.com": "valda",
    "user@example.com": "M3RCUR2Y",
    "user@example.com": "ygd58",
    "user@example.com": "ideathinklab01-source",
    "user@example.com": "zng8418",
    "user@example.com": "DaniuXie",
    "user@example.com": "ChanlerDev",
    "user@example.com": "briandevans",
    "user@example.com": "tcconnally",
    "user@example.com": "mijanx",
    "user@example.com": "h0tp-ftw",
    "user@example.com": "chinadbo",
    "user@example.com": "kshitijk4poor",
    "user@example.com": "xyiy001",
    "user@example.com": "CharlieKerfoot",
    "user@example.com": "Grey0202",
    "user@example.com": "vominh1919",
    "user@example.com": "giwaov",
    "user@example.com": "Yoimex",
    "user@example.com": "atongrun",
    "user@example.com": "MichaelWDanko",
    "user@example.com": "YX234",
    "user@example.com": "julysir",
    "user@example.com": "JanCong",
    "user@example.com": "e-shizz",
    "user@example.com": "VinVC",
    "user@example.com": "zons-zhaozhy",
    "user@example.com": "JayGwod",
    "user@example.com": "swithek",
    "user@example.com": "PratikRai0101",
    "user@example.com": "sasha-id",
    "user@example.com": "chenyunbo411",
    "openclaw@local": "Asce66",
    "user@example.com": "0xsir0000",
    "user@example.com": "lisanhu",
    "user@example.com": "chenyunbo411",
    "user@example.com": "stevenchanin",
    "user@example.com": "halmisen",
    "user@example.com": "yuqianma",
    "user@example.com": "yuqianma",
    "user@example.com": "bassings",
    "user@example.com": "highland0971",
    "user@example.com": "lewislulu",
    "user@example.com": "Gaurav23V",
    "user@example.com": "Tranquil-Flow",
    "user@example.com": "albert748",
    "user@example.com": "0xharryriddle",
    "user@example.com": "lhysdl",
    "user@example.com": "SherlockShemol",
    "user@example.com": "eloklam",
    "user@example.com": "eloklam",
    "user@example.com": "fmercurio",
    "user@example.com": "Ricardo-M-L",
    "user@example.com": "leozeli",
    "user@example.com": "LehaoLin",
    "user@example.com": "I3eg1nner",
    "user@example.com": "PeterBerthelsen",
    "user@example.com": "lengxii",
    "user@example.com": "priveperfumes",
    "user@example.com": "sjz-ks",
    "user@example.com": "topcheer",
    "user@example.com": "walli",
    "user@example.com": "Zhuofeng-Wang",
    "user@example.com": "Contentment003111",
    # April 2026 salvage-PR batch (#14920, #14986, #14966)
    "user@example.com": "mrunmayee17",
    "user@example.com": "camaragon",
    "user@example.com": "shamork",
    # April 2026 Discord Copilot /model salvage (#15030)
    "user@example.com": "Nicecsh",
    # no-github-match — keep as display names
    "user@example.com": "Sisyphus",
    "user@example.com": "Marco Rutsch",
    "user@example.com": "Paul Bergeron",
    "user@example.com": "zhangxicen",
    "user@example.com": "teknium1",
    "user@example.com": "teknium1",
    "user@example.com": "chen1749144759",
    "user@example.com": "MorAlekss",
    "user@example.com": "ztexydt-cqh",
    # v0.16.0 additions
    "user@example.com": "teknium1",
    "user@example.com": "alaamohanad169-ship-it",
    "user@example.com": "Archerouyang",  # display name 欧阳
    "user@example.com": "Sarbai",  # git email for PR #33438 author (display: Брагарник Дмитро)
    "user@example.com": "aminvakil",
    "user@example.com": "polnikale",
    "user@example.com": "sarvesh1327",  # salvaged via #38655
    "user@example.com": "wysie",
    "user@example.com": "bedirhancode",
    "user@example.com": "ash",
    "user@example.com": "andrewhosf",
    # April 2026 Honcho bug-fix consolidation (#15381)
    "user@example.com": "HiddenPuppy",
    "user@example.com": "sasha-id",
    "user@example.com": "dontcallmejames",
    "user@example.com": "hekaru-agent",
    "user@example.com": "twozle",
    "user@example.com": "rfilgueiras",
    "user@example.com": "Leihb",
    # ACP streaming fix salvage (PR #9428 + #16273)
    "user@example.com": "ningfangbin",
    "user@example.com": "Joseph19820124",
    "user@example.com": "rugvedS07",
    "user@example.com": "Heltman",
    # v0.12.0 additions
    "user@example.com": "ching-kaching",
    "user@example.com": "Zjianru",  # salvage chain: code by codez, PR #15749 author @Zjianru
    "user@example.com": "Siddharth Balyan",  # co-author only
    "user@example.com": "zkl2333",
    "user@example.com": "isaachuangGMICLOUD",
    "user@example.com": "isaachuangGMICLOUD",  # salvage of PR #11955 → #16663
    "user@example.com": "Octopus",  # co-author only
    "user@example.com": "Versun",  # co-author only
    "user@example.com": "kevin-ho",  # salvage: PR #15488 author @kevin-ho
    "user@example.com": "Paperclip",  # co-author only
    "teknium@hermes-agent": "teknium1",
    "user@example.com": "web3blind",
    "user@example.com": "chengoak",  # PR #17467
    "user@example.com": "zwcf5200",  # PR #38661 (SSH remote cwd fix)
    "user@example.com": "YuShu",  # co-author only
    "user@example.com": "CharlieKerfoot",  # PR #18951
    # Debug share upload-time redaction (May 2026)
    "user@example.com": "GodsBoy",  # PR #19318
    "user@example.com": "ruangraung",  # PR #42308
    "user@example.com": "mrcoferland",  # PR #19023
    "user@example.com": "noOne-list",  # PR #19050
    "user@example.com": "likejudy",  # PR #19052
    "user@example.com": "leon7609",  # PR #19069
    "user@example.com": "nouseman666",  # PR #19088
    "user@example.com": "GinWU05",  # PR #19093
    "user@example.com": "shashwatgokhe",  # PR #19196
    "user@example.com": "cypres0099",  # PR #25935 salvage (mixed-attachment image routing)
    "user@example.com": "stevenchouai",  # PR #19221
    "user@example.com": "agilejava",  # PR #19346
    "user@example.com": "acc001k",  # PR #19358
    "user@example.com": "kowenhaoai",  # PR #19376
    "user@example.com": "hedirman",  # PR #19410
    "user@example.com": "LucianoSP",  # PR #19412
    "user@example.com": "paul-tian",  # PR #19423
    "user@example.com": "glesperance",  # PR #19443
    "user@example.com": "EvilDrag0n",  # PR #20651
    # v0.13.0 additions
    "user@example.com": "jackey8616",  # via PR salvage
    "user@example.com": "jrusso1020",  # via PR salvage
    "user@example.com": "LeonSGP43",  # PR #18739 salvage of #14570
    "user@example.com": "Foolafroos",  # PR #20329 French locale
    "user@example.com": "Montbra",  # PR #20897 salvage of #16189 (TUI voice PTT)
    "user@example.com": "paulb26",  # PR #24135 salvage (pty-bridge killpg)
    "user@example.com": "firefly",  # PR #18123 salvage of #16660 (ContextVars)
    "user@example.com": "WuTianyi123",  # PR #20275 salvage of #13723 (feishu markdown)
    "user@example.com": "hanzckernel",  # PR #20311 (api-server approval events)
    "user@example.com": "oferlaor",  # PR #22356 salvage (cron origin sender identity)
    "user@example.com": "leehack",  # PR #22053 salvage (telegram DM topic reply fallback)
    "user@example.com": "caojiguang",  # PR #35117 carries #31853 (weixin _api_post/_api_get wait_for)
    "user@example.com": "goku94123",  # PR #46609 salvage (MiniMax reasoning extra_body)
    # pander: empty email, salvaged via PR #19665 from #16126 by @ms-alan
    "user@example.com": "chaithanyak42",  # PR #15624
    "user@example.com": "kartik-mem0",  # PR #15624
    "user@example.com": "A-kamal",  # PR #18678 (xAI image resolution fix)
    # Kanban bug-fix batch salvage (May 2026)
    "user@example.com": "Frowtek",  # salvage of #23206 (gateway --board auto-subscribe)
    "user@example.com": "Sylw3ster",  # salvage of #23252 (HERMES_KANBAN_BOARD restore)
    "user@example.com": "dmnkhorvath",  # salvage of #23358 (kanban worker send_message)
    "user@example.com": "smwbev",  # salvage of #23659 (aria-label colLabel)
    "user@example.com": "TurgutKural",  # salvage of #23356 (HERMES_HOME inject)
    "user@example.com": "29206394",  # PR #22194 salvage (sudo -S brute-force guard, #9590)
    "user@example.com": "fr33d3m0n",  # PR #21128 salvage (sudo stdin/askpass DANGEROUS, #17873 cat 4)
    "user@example.com": "VinceZcrikl",  # PR #23647 salvage (npm UTF-8 decode on GBK Windows)
    "user@example.com": "JabberELF",  # PR #20238 seed (session_search dual-mode, evolved into single-shape)
    "user@example.com": "ZeterMordio",  # PR #11754 salvage (zsh completion compdef + _arguments syntax)
    "user@example.com": "iuyup",  # PR #6155 salvage (shell=True hardening)
    "user@example.com": "1RB",  # PR #25462 salvage (discord forwarded messages)
    "user@example.com": "ayushere",  # PR #25342 salvage (memory teardown leak)
    "user@example.com": "domtriola",  # PR #25424 salvage (docs tirith link)
    "user@example.com": "tuancookiez-hub",  # PR #34865 salvage (LSP Windows .cmd shim spawn, #34864)
    "user@example.com": "ephron-ren",  # PR #25358 salvage (MiMo reasoning echo-back)
    "user@example.com": "freqyfreqy",  # PR #25423 salvage (docs LSP worktree -> repo)
    "user@example.com": "fu576",  # PR #25369 salvage (api_mode not inherited cross-provider)
    "user@example.com": "kfa-ai",  # PR #25398 salvage (whatsapp quoted reply metadata)
    "user@example.com": "magic524",  # PR #25361 salvage (QQBot reconnect loop)
    "user@example.com": "PaTTeeL",  # PR #25359 salvage (custom_providers in compression length)
    "user@example.com": "pearjelly",  # PR #25388 salvage (feishu ws connect override sync)
    "user@example.com": "raymaylee",  # PR #25394 salvage (context compaction status)
    "user@example.com": "Tianyu199509",  # PR #25421 salvage (gateway PID Windows)
    "user@example.com": "HxT9",  # PR #25760 salvage (web sync-assets cross-platform)
    "user@example.com": "evgyur",  # PR #25651 salvage (docs media session context)
    "user@example.com": "AsoTora",  # PR #25624 salvage (MCP auth no-retry)
    "user@example.com": "oxngon",  # PR #25603 salvage (forward image attachments to bg tasks)
    "user@example.com": "yifengingit",  # PR #25589 salvage (AUTOINCREMENT id ordering)
    "user@example.com": "vanthinh6886",  # PR #25562 salvage (.env 0600 perms)
    "user@example.com": "Arkmusn",  # PR #25559 salvage (approvals.timeout from config)
    "user@example.com": "nidhi-singh02",  # PR #2752 salvage (slack whitespace-only IndexError guard)
    "user@example.com": "nidhi-singh02",
    "user@example.com": "Jaaneek",  # PR #26457 (xAI Grok OAuth provider)
    # v0.14.0 additions
    "user@example.com": "wuwuzhijing",  # PR #21063 salvage (gateway docs mention Weixin)
    "user@example.com": "nightcityblade",  # PR #24138 (docs voice/tts table)
    "user@example.com": "polkn",  # PR #6136 salvage (skill_view collision refusal)
    "user@example.com": "rewbs",
    # batch salvage (May 2026 LHF run)
    "user@example.com": "Saurav0989",  # PR #27071 (docs: hermes-eval community link)
    "user@example.com": "Saurav0989",
    "user@example.com": "avifenesh",  # PR #25902 (docs: computer-use-linux MCP)
    "user@example.com": "avifenesh",
    "user@example.com": "BROCCOLO1D",  # PR #26796 (docs: spotify + HA)
    "user@example.com": "matthewlai",  # PR #25293 (feat: gemma 4 reasoning allowlist)
    "user@example.com": "matthewlai",
    "user@example.com": "0xchainer",  # PR #27154/27138/27147 salvage
    "user@example.com": "kronexoi",  # PR #27167 salvage (Teams port fallback)
    "user@example.com": "EloquentBrush0x",  # PR #26642 salvage (post_setup parity)
    # batch salvage (May 2026 LHF run, group 2)
    "user@example.com": "shellybotmoyer",  # PR #26661 (kanban --severity >=)
    "user@example.com": "shellybotmoyer",  # PR #25576 (credential_pool ISO rehydrate)
    "user@example.com": "shellybotmoyer",
    "user@example.com": "ether-btc",  # PR #26632 (memory provider whitespace guard)
    "user@example.com": "LifeJiggy",  # PR #26516 (paste collapse logging)
    "user@example.com": "LifeJiggy",
    "user@example.com": "LifeJiggy",  # stale salvage commit alias (PR #28315)
    "user@example.com": "nekwo",  # PR #26481 (PS5.1 UTF-8 BOM)
    "user@example.com": "nekwo",
    "user@example.com": "stepanov1975",  # PR #22074 (setup config picker writes)
    "user@example.com": "devsart95",  # PR #23249 (cron Telegram DM topic delivery)
    "user@example.com": "flooryyyy",  # PR #26374 (tool_trace error detection)
    "user@example.com": "dgians",  # PR #26034 (.ts/.py/.sh docs types)
    "user@example.com": "dgians",  # PR #26034 (bot-committed by zealy-tzco under dgians' PR)
    "user@example.com": "flanny7",  # PR #27030 (setup_open_webui python var)
    "user@example.com": "flanny7",
    "user@example.com": "hermesagent26",  # PR #26438 (kimi model-name reasoning pad)
    "user@example.com": "hermesagent26",
    "user@example.com": "kriscolab",  # PR #26926 (deepseek default_aux_model)
    # batch salvage (May 2026 LHF run, group 3)
    "user@example.com": "darvsum",  # PR #26766 (preserve discover_models in normalize)
    "user@example.com": "hueilau",  # PR #26498 (strip image parts for non-vision)
    "user@example.com": "hueilau",
    "user@example.com": "Timur00Kh",  # PR #27114 (telegram DM topic for synthetic events)
    "user@example.com": "Grogger",  # PR #27061 (windows console flash suppress)
    "user@example.com": "Grogger",
    "user@example.com": "Grogger",  # stale salvage commit alias (PR #28330)
    "user@example.com": "lemassykoi",  # PR #27042 (model-switch probe keyless providers)
    "user@example.com": "lemassykoi",
    "user@example.com": "draplater",  # PR #26707 (goal judge current time)
    "user@example.com": "draplater",
    "user@example.com": "pr7426",  # PR #27048 (cron parallel job loss)
    "user@example.com": "therahul-yo",  # PR #26215 (mock keychain in tests)
    "user@example.com": "flamiinngo",  # PR #27205 (UnicodeEncodeError footgun checker)
    # batch salvage (May 2026 LHF run, group 4)
    "user@example.com": "EloquentBrush0x",  # PR #26657 (trust_env aiohttp)
    "user@example.com": "subtract0",  # PR #25658 (zsh $status -> $rc)
    "user@example.com": "zwolniony",  # PR #26961 (gemini x-goog-api-key)
    "user@example.com": "zwolniony",
    "user@example.com": "that-ambuj",  # PR #26582 (preserve underscores)
    "user@example.com": "zccyman",  # PR #25294 (custom provider api_key_env alias)
    # xAI cluster batch salvage (May 2026)
    "user@example.com": "Fewmanism",  # PR #27420 (threaded xAI OAuth callback)
    "user@example.com": "Slimydog21",  # PR #28021 (strip slash enums xAI Responses)
    "user@example.com": "Slimydog21",  # PR #28021 salvage (noreply form)
    "user@example.com": "lidge-jun",  # PR #26814 (api server browser security headers)
    "user@example.com": "phoenixshen",  # PR #26768 (respect user-configured vision model)
    "user@example.com": "phoenixshen",
    "user@example.com": "AhmetArif0",  # PR #26635 (line proxy env vars)
    # batch salvage (May 2026 LHF run, group 5)
    "user@example.com": "haran2001",  # PR #27070 (i18n catalog test)
    "user@example.com": "haran2001",  # PR #27068 (qwen3.6-plus 1M context)
    "user@example.com": "haran2001",
    "user@example.com": "ms-alan",  # PR #26443 (reload-skills tab completion)
    "user@example.com": "godlin-gh",  # PR #26118 (ACP polished tools)
    "user@example.com": "wesleysimplicio",  # PR #25777 (xterm.js native selection)
    "user@example.com": "wesleysimplicio",
    "user@example.com": "Carry00",  # PR #26851 (doctor SSH env vars)
    "user@example.com": "alaamohanad169-ship-it",  # PR #26036 (telegram typing after send)
    "vigo@hermes": "hawknewton",  # PR #26294 (bedrock boto3 lazy_deps)
    "user@example.com": "hawknewton",
    "user@example.com": "QuenVix",  # PR #26761/26772 salvage
    "user@example.com": "QuenVix",
    "user@example.com": "Mind-Dragon",  # PR #26966 salvage
    "user@example.com": "soynchux",  # PR #27060 salvage
    "user@example.com": "soynchux",
    # batch salvage (May 2026 LHF run, group 6 — final)
    "user@example.com": "bird",  # PR #25219 (gateway docker exit-75 restart)
    "user@example.com": "davidcampbelldc",  # PR #26834 (web_server proxy_headers=False)
    "user@example.com": "davidcampbelldc",
    "user@example.com": "chazmaniandinkle",  # PR #43888 (launchd /restart detection)
    "user@example.com": "nodejun",  # PR #21112 (anthropic keychain/file credential desync)
    "user@example.com": "hehehe0803",  # PR #26212 salvage (codex kanban writable root)
    "user@example.com": "hehehe0803",
    "user@example.com": "kasunvinod",  # PR #24126 salvage (codex timeout propagation)
    "user@example.com": "kasunvinod",
    "user@example.com": "vaddisrinivas",  # PR #26394 salvage (Docker messaging extra)
    # batch salvage (May 2026 LHF run, group 7)
    "user@example.com": "02356abc",  # PR #28286 salvage (wecom CLOSING)
    "user@example.com": "burjorjee",  # PR #28201 salvage (inline-shell timeout guard)
    "user@example.com": "burjorjee",
    "user@example.com": "oseftg",  # PR #28168 salvage (natural ending emoji/caret)
    "user@example.com": "oseftg",
    "user@example.com": "rudi193-cmd",  # PR #28241 salvage (empty credential pool)
    "user@example.com": "rudi193-cmd",
    "user@example.com": "sadiksaifi",  # PR #27982 salvage (kanban horiz scroll)
    "user@example.com": "sadiksaifi",
    "user@example.com": "vynxevainglory-ai",  # PR #29233 salvage (kanban scrollbar + body overflow)
    "user@example.com": "vynxevainglory-ai",
    # batch salvage (May 2026 LHF run, group 8)
    "user@example.com": "AceWattGit",  # PR #28159 salvage (_pool_may_recover NameError)
    "user@example.com": "YuanHanzhong",  # PR #28032 salvage (x.com status link-like)
    "user@example.com": "colin-chang",  # PR #28245/#28249/#28251 salvage
    "user@example.com": "colin-chang",
    "user@example.com": "felix-windsor",  # PR #28019 salvage (cron asterisks)
    "user@example.com": "felix-windsor",
    "user@example.com": "houenyang-momo",  # PR #28205 salvage (charizard contrast)
    "user@example.com": "sir-ad",  # PR #31941 salvage (compaction noise)
    "user@example.com": "sir-ad",
    "user@example.com": "rdasilva1016-ui",  # PR #31098 salvage (Telegram /start ping)
    "user@example.com": "rdasilva1016-ui",
    "user@example.com": "iqdoctor",  # PR #28095 salvage (windows installer docs)
    "user@example.com": "joe102084",  # PR #28151 salvage (whitespace cron responses)
    "user@example.com": "joe102084",
    "user@example.com": "jvinals",  # PR #27936 salvage (Slack U-IDs)
    "user@example.com": "maxmilian",  # PR #28267 salvage (Change Model portal)
    "user@example.com": "maxmilian",
    "user@example.com": "samggggflynn",  # PR #27952 salvage (dingtalk pre_start)
    "user@example.com": "samggggflynn",
    "user@example.com": "yannsunn",  # PR #28064 salvage (xai proxy upstream)
    "user@example.com": "yannsunn",
    "user@example.com": "asdlem",  # PR #27852 salvage (clarify full text in body)
    # batch salvage (May 2026 LHF run, group 9)
    "user@example.com": "jdelmerico",  # PR #28278 salvage (signal require_mention)
    "user@example.com": "justemu",  # PR #27996 salvage (matrix thread_require_mention)
    "user@example.com": "justemu",
    "user@example.com": "YuanHanzhong",  # PR #28029 salvage (dashboard scrollback)
    "user@example.com": "YuanHanzhong",
    "user@example.com": "noctilust",  # PR #28080 salvage (stale TUI resume env)
    "user@example.com": "noctilust",
    "user@example.com": "MoonJuhan",  # PR #28288 salvage (unreadable JSONL transcripts)
    "user@example.com": "MoonJuhan",
    "user@example.com": "outsourc-e",  # PR #28164 salvage (cron emoji ZWJ)
    "user@example.com": "outsourc-e",  # PR #28177 salvage (Teams recording path traversal)
    "user@example.com": "Zyrixtrex",  # PR #28275 salvage (Google OAuth timeout)
    "user@example.com": "Zyrixtrex",
    "user@example.com": "ooovenenoso",  # PR #28256 salvage (tool loop recovery hints)
    "user@example.com": "ooovenenoso",
    "user@example.com": "vanthinh6886",  # PR #28018 salvage (yaml/flock/atomic write guards)
    "user@example.com": "erikengervall",  # PR #28774 (firecrawl integration tag)
    "user@example.com": "egilewski",  # PR #30432 (MEDIA path traversal fix, GHSA-jmf9-9729-7pp8)
    "user@example.com": "andrewhomeyer",  # PR #20056 (snapshot owner-only perms, co-author on #57386 salvage)
    "user@example.com": "McClean-Edison",  # PR #29817 (register_auxiliary_task plugin API)
    "user@example.com": "OYLFLMH",  # PR #48312 salvage (cli_refresh_interval config, #48309)
    "user@example.com": "SamuelZ12",  # PR #7480 (show recap after in-session resume)
    "user@example.com": "daizhonggeng",  # PR #9020 (numbered /resume selection)
    "user@example.com": "wanwan2qq",  # PR #10215 (strip brackets/quotes from /resume; gateway session-ID lookup)
    "user@example.com": "SimoKiihamaki",  # PR #30773 (Windows /reset+/new freeze; stdin fallback for modal)
    "user@example.com": "Tranquil-Flow",  # PR #27518 (bracketed-paste timeout)
    "user@example.com": "riyas22",  # PR #43687 salvage (strip cronjob toolset from delegated children, #43466)
    "user@example.com": "8bit64k",  # PR #14681 (TUI /q alias from quit to queue)
    "user@example.com": "hclsys",  # PR #31985 (TUI /q alias regression test)
    "dearmayo@localhost": "ffr31mr",  # PR #32103 (SubdirectoryHintTracker workspace boundary)
    "user@example.com": "TheOnlyMika",  # PR #32155 (dashboard XSS + defusedxml)
    "user@example.com": "krislidimo",  # PR #29775 (tighten Telegram table row-group spacing; drop redundant first bullet)
    "user@example.com": "Codename-11",  # PR #29302 (API server session controls — sessions/chat/fork/stream)
    "user@example.com": "Schwartz10",  # PR #29302 sub-PR (multimodal media in session chat API)
    "user@example.com": "JohnC1009",  # PR #32020 salvage (auth: global auth.json fallback in _load_provider_state)
    "user@example.com": "bisko",  # PR #33784 salvage (re-pad reasoning_content on cross-provider fallback to require-side providers)
    # v0.15.0 additions
    "user@example.com": "sgtworkman",
    "user@example.com": "jfuenmayor",
    "user@example.com": "joshuadow",  # PR #43004 salvage (desktop WS session rebind)
    "user@example.com": "emonty",
    "user@example.com": "rodrigoeqnit",
    "user@example.com": "jonpol01",
    "user@example.com": "yu-xin-c",  # PR #51875 salvage (protect external_dirs skills from curator)
    "user@example.com": "BaxBit",  # PR #30200 (Svix webhook signature validation)
    "user@example.com": "duyua9",  # PR #10949 (render object config values structurally)
    "ethie@nous": "ethernet8023",  # PR #29342 (TUI clipboard copy on linux/wayland)
    "user@example.com": "Jiahui-Gu",  # PR #29276 (guard pickle.loads in darwinian-evolver)
    "user@example.com": "justincc",  # PR #28914 (set tool_name on tool-result messages)
    "user@example.com": "slowtokki0409",  # PR #29025 (ignore local Hermes runtime files)
    "user@example.com": "WuKongAI-CMU",  # PR #10082 (reject symlinked audio inputs)
    "user@example.com": "Sunil123135",  # PR #31031 (Windows Docker Desktop compose)
    "user@example.com": "ChyuWei",  # PR #30987 (TUI TTS env var on voice off)
    # batch salvage PR #35758 (perf micro-fixes)
    "user@example.com": "amathxbt",  # PR #22155 (cache tool_output_limits)
    "user@example.com": "ErnestHysa",  # PRs #32636/#32708 (MCP asyncio.sleep + O(n^2) watcher drain)
    "user@example.com": "alastraz",  # PR #41383 salvage (cua EAGAIN CLI-transport fallback)
    "user@example.com": "SiTaggart",  # PR #35583 (docker_forward_env empty-secret .env fallback)
    "user@example.com": "x1am1",  # PR #35098 (chown root-owned top-level HERMES_HOME state files)
    "user@example.com": "polnikale",  # PR #35717 (discover Playwright headless_shell browser)
    "user@example.com": "whyhkzk",  # PR #32407 (sandbox-mirror inner-container guard; commits authored as whyhkzk + zhukun)
    "user@example.com": "leonardsellem",  # PR #37405 (desktop WS origin guard on remote/Tailscale binds)
    "user@example.com": "ohMyJason",  # PR #29810 (discover_models in custom_providers section 4)
    "user@example.com": "sanidhyasin",  # PR #40403 salvage (model.default_headers for custom OpenAI-compatible providers, #40033)
    "user@example.com": "JoelJJohnson",  # PR #39913 salvage (Windows ConPTY dashboard chat bridge)
    "user@example.com": "Nea74",  # PR #40022 co-author credit (same Windows ConPTY bridge design)
    "user@example.com": "joel611",  # PR #33958 salvage (DISCORD_ALLOWED_ROLES role_authorized gateway flag)
    "user@example.com": "dschnurbusch",  # PR #42373 salvage (archive compressed conversation lineages)
    "user@example.com": "bcsmith528",  # PR #20589 salvage (register_slack_action_handler plugin API)
    "user@example.com": "liuhao1024",  # PR #45494 salvage (claim session slot before auto-resume task; #45456)
    "user@example.com": "capt-marbles",  # PR #38440 salvage (resolve xAI OAuth credentials across profiles; #43589)
    "user@example.com": "infinitycrew39",  # PR #47945 salvage (scope langfuse trace state by turn/request ids; #48292)
    "user@example.com": "huangxun375-stack",  # PR #37251 / #48894 structured OpenViking sync
    "user@example.com": "koshaji",  # PR #49832 salvage (OpenViking runtime autostart shutdown drain)
    "user@example.com": "wgd753",  # PR #59454 salvage (OpenViking trusted-mode retry matching)
    "user@example.com": "Sahil-SS9",  # PR #48466/#44919/#44909/#42209 salvage (cron/checkpoint/kanban/skill)
    "user@example.com": "max-chen",  # PR #51194 salvage (single-pass list_profiles alias map + skill-count cache; #54751)
    # v0.17.0 additions
    "user@example.com": "pengyuyanITYU",  # PR #43618 (harden local file tree paths)
    "user@example.com": "AIalliAI",  # PR #44159 (desktop hover-reveal inset)
    "user@example.com": "ameobius",  # PR #44383 co-author (discord gateway task recovery)
    "user@example.com": "mollusk",  # PR #44493 (desktop assistant-ui recovery)
    "user@example.com": "bionicbutterfly13",  # direct email match
    "user@example.com": "enesilhaydin",  # direct email match
    "user@example.com": "Evisolpxe",  # direct email match
    "user@example.com": "fyzanshaik",  # direct email match
    "user@example.com": "AMIK-coorporations",  # PR #40578 (Urdu README) co-author
    "user@example.com": "AMIK-coorporations",  # PR #40578 (Urdu README)
    "user@example.com": "kyssta-exe",  # PR #44282 (Windows dashboard re-exec)
    "user@example.com": "Elshayib",  # PR #48351 (custom-provider misattribution guard; #48305)
    "user@example.com": "loongfay",  # PR #43508 (Yuanbao wechat forward msg)
    "user@example.com": "BROCCOLO1D",  # PR #42733 (lazy-parse docker env config)
    "user@example.com": "underthestars-zhy",  # PR #46907 co-author (Photon Spectrum project ids)
    "user@example.com": "OmarB97",  # PR #43977 (desktop session model metadata)
    "user@example.com": "OmarB97",  # PR #43977 (desktop session model metadata)
    "user@example.com": "szafranski",  # PR #36020 (Telegram voice/audio duration)
    "user@example.com": "PhilipAD",  # direct email match
    "user@example.com": "qingshan89",  # PR #46895 co-author (desktop remote artifact download)
    "user@example.com": "AJ",  # PR #44510 co-author (desktop named-profile boot loop)
    "user@example.com": "steveonjava",  # PR #29669 (redact secrets in kanban tool payloads)
    "user@example.com": "Afnath-max",  # PR #49129 salvage (opencode-zen catalog refresh + uncapped/live-first picker)
    "user@example.com": "ipriyaaanshu",  # PR #51488 salvage (clear stale base_url on gateway model switches; #25107)
    "user@example.com": "mrparker0980",  # @file context-ref expansion anchored to canonical read deny-list
    # v0.18.0 additions
    "user@example.com": "AetherAgents",  # direct email match
    "user@example.com": "lEWFkRAD",  # PR #45610 (Windows scheduled task reboot survival)
    "user@example.com": "p-andhika",  # PR #53312 co-author (setup guide button)
    "user@example.com": "annguyenNous",  # PR #52844 co-author
    "user@example.com": "talmax1124",  # direct email match
    "user@example.com": "chrispersico",  # commit 135f2351 PR author
    "user@example.com": "KeyArgo",  # co-author
    "user@example.com": "spjoes",  # direct email match
    "user@example.com": "KeyArgo",  # PR #45638 author
    "user@example.com": "Lucas Nicolas",  # PR #54210 co-author (display name)
    "user@example.com": "maxpetrusenko",  # PR #54128 co-author
    "user@example.com": "wnuuee1",  # commit 9fd2b2cb PR author
    "user@example.com": "Eji4h",  # direct email match
    "user@example.com": "designnotdrum",  # PR #56480 salvage (toolset static-inference fix)
    "user@example.com": "LavyaTandel",  # PR #57893 salvage local git identity (envelope-layout cache markers on tool/empty-assistant messages; #57845)
    "user@example.com": "SquabbyZ",  # PR #59682 salvage (in-container dashboard WS loopback host; #58993)
    "user@example.com": "0disoft",  # PR #53511 salvage (gateway PID probe TTL cache)
    "user@example.com": "0-CYBERDYNE-SYSTEMS-0",  # PR #53966 salvage (session DB reads off event loop)
    "user@example.com": "sebastianlutycz",  # PR #39140 salvage (descendant CTE); bare noreply (no NNN+ prefix) needs explicit mapping
    "user@example.com": "BobClawblaw",  # PR #77870 salvage (output-cap compression on retry path; #55546)
    "user@example.com": "mahdiwafy",  # PR #60347 salvage (session messages pagination)
    "user@example.com": "CodeForgeNet",  # PR #47437 salvage (compact_rows blob skip)
    "user@example.com": "dexhunter",  # PR #60339 salvage (skills snapshot manifest speedup)
    "user@example.com": "uzaylisak",  # PR #29988 salvage (detect_local_server_type process-lifetime cache)
    "user@example.com": "8294",  # PR #50572 salvage (honor config context_length on banner)
    "user@example.com": "ya-nsh",  # PR #26790 salvage (normalize local terminal relative cwd; #26783)
}


# ──────────────────────────────────────────────────────────────────────
# Directory-based mappings: contributors/emails/<email> → login
# ──────────────────────────────────────────────────────────────────────
CONTRIBUTORS_EMAILS_DIR = REPO_ROOT / "contributors" / "emails"


def _load_contributor_dir(directory: "Path | None" = None) -> dict:
    """Load one-file-per-email mappings from contributors/emails/.

    Filename = commit-author email, first non-comment line = GitHub login.
    Additions never merge-conflict (each mapping is a distinct file), which
    is why new entries go here instead of the frozen LEGACY_AUTHOR_MAP.
    """
    directory = directory or CONTRIBUTORS_EMAILS_DIR
    mapping = {}
    if not directory.is_dir():
        return mapping
    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.name.startswith("."):
            continue
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    mapping[path.name] = line.lstrip("@")
                    break
        except OSError:
            continue
    return mapping


# Effective map: frozen legacy dict + directory entries (directory wins).
AUTHOR_MAP = {**LEGACY_AUTHOR_MAP, **_load_contributor_dir()}


def git(*args, cwd=None):
    """Run a git command and return stdout."""
    result = subprocess.run(
        ["git"] + list(args),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=cwd or str(REPO_ROOT),
    )
    if result.returncode != 0:
        print(f"git {' '.join(args)} failed: {result.stderr}", file=sys.stderr)
        return ""
    return result.stdout.strip()


def git_result(*args, cwd=None):
    """Run a git command and return the full CompletedProcess."""
    return subprocess.run(
        ["git"] + list(args),
        capture_output=True,
        text=True, encoding="utf-8", errors="replace",
        cwd=cwd or str(REPO_ROOT),
    )


def get_last_tag():
    """Get the most recent CalVer tag."""
    tags = git("tag", "--list", "v20*", "--sort=-v:refname")
    if tags:
        return tags.split("\n")[0]
    return None


def next_available_tag(base_tag: str) -> tuple[str, str]:
    """Return a tag/calver pair, suffixing same-day releases when needed."""
    if not git("tag", "--list", base_tag):
        return base_tag, base_tag.removeprefix("v")

    suffix = 2
    while git("tag", "--list", f"{base_tag}.{suffix}"):
        suffix += 1
    tag_name = f"{base_tag}.{suffix}"
    return tag_name, tag_name.removeprefix("v")


def get_current_version():
    """Read current semver from __init__.py."""
    content = VERSION_FILE.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
    return match.group(1) if match else "0.0.0"


def bump_version(current: str, part: str) -> str:
    """Bump a semver version string."""
    parts = current.split(".")
    if len(parts) != 3:
        parts = ["0", "0", "0"]
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "patch":
        patch += 1
    else:
        raise ValueError(f"Unknown bump part: {part}")

    return f"{major}.{minor}.{patch}"


def update_version_files(semver: str, calver_date: str):
    """Update version strings in source files."""
    # Update __init__.py
    content = VERSION_FILE.read_text(encoding="utf-8")
    content = re.sub(
        r'__version__\s*=\s*"[^"]+"',
        f'__version__ = "{semver}"',
        content,
    )
    content = re.sub(
        r'__release_date__\s*=\s*"[^"]+"',
        f'__release_date__ = "{calver_date}"',
        content,
    )
    VERSION_FILE.write_text(content, encoding="utf-8")

    # Update pyproject.toml
    pyproject = PYPROJECT_FILE.read_text(encoding="utf-8")
    pyproject = re.sub(
        r'^version\s*=\s*"[^"]+"',
        f'version = "{semver}"',
        pyproject,
        # Turn-end file-mutation verifier footer appended by run_agent.py
        # (``_format_file_mutation_failure_footer``). It's a UI affordance — reading "warning file mutation
        # verifier, 2 files were NOT modified..." aloud is noise (#40772). The footer is a ``⚠️
        # File-mutation verifier:`` header line followed by indented ``•`` bullet lines; strip the whole
        # block.
        flags=re.MULTILINE,
    )
    PYPROJECT_FILE.write_text(pyproject, encoding="utf-8")

    # Keep the desktop Electron app's package.json version in lockstep with the
    # Python package version. The desktop About panel reads the live Hermes
    # version at runtime, but app.getVersion()/packaging metadata still come
    # from this field, so it must track pyproject to avoid drift.
    desktop_pkg = REPO_ROOT / "apps" / "desktop" / "package.json"
    if desktop_pkg.exists():
        pkg_text = desktop_pkg.read_text(encoding="utf-8")
        pkg_text = re.sub(
            r'("version"\s*:\s*)"[^"]+"',
            rf'\g<1>"{semver}"',
            pkg_text,
            count=1,
        )
        desktop_pkg.write_text(pkg_text, encoding="utf-8")

    # Keep the bootstrap installer (Hermes-Setup.dmg CFBundleShortVersionString)
    # in lockstep with the Python package version. Tauri reads `version` from
    # package.json + tauri.conf.json; a hardcoded 0.0.1 ships in the DMG.
    installer_pkg = REPO_ROOT / "apps" / "bootstrap-installer" / "package.json"
    if installer_pkg.exists():
        pkg_text = installer_pkg.read_text(encoding="utf-8")
        pkg_text = re.sub(
            r'("version"\s*:\s*)"[^"]+"',
            rf'\g<1>"{semver}"',
            pkg_text,
            count=1,
        )
        installer_pkg.write_text(pkg_text, encoding="utf-8")

    installer_tauri = (
        REPO_ROOT / "apps" / "bootstrap-installer" / "src-tauri" / "tauri.conf.json"
    )
    if installer_tauri.exists():
        pkg_text = installer_tauri.read_text(encoding="utf-8")
        pkg_text = re.sub(
            r'("version"\s*:\s*)"[^"]+"',
            rf'\g<1>"{semver}"',
            pkg_text,
            count=1,
        )
        installer_tauri.write_text(pkg_text, encoding="utf-8")

    installer_cargo = (
        REPO_ROOT / "apps" / "bootstrap-installer" / "src-tauri" / "Cargo.toml"
    )
    if installer_cargo.exists():
        cargo_text = installer_cargo.read_text(encoding="utf-8")
        cargo_text = re.sub(
            r'^version\s*=\s*"[^"]+"',
            f'version = "{semver}"',
            cargo_text,
            count=1,
            flags=re.MULTILINE,
        )
        installer_cargo.write_text(cargo_text, encoding="utf-8")


def version_files_to_stage() -> list[str]:
    """Return version-bearing files that exist and should be `git add`ed after a bump."""
    candidates = [
        VERSION_FILE,
        PYPROJECT_FILE,
        REPO_ROOT / "apps" / "desktop" / "package.json",
        REPO_ROOT / "apps" / "bootstrap-installer" / "package.json",
        REPO_ROOT / "apps" / "bootstrap-installer" / "src-tauri" / "tauri.conf.json",
        REPO_ROOT / "apps" / "bootstrap-installer" / "src-tauri" / "Cargo.toml",
    ]
    return [str(path) for path in candidates if path.exists()]


def resolve_author(name: str, email: str) -> str:
    """Resolve a git author to a GitHub @mention."""
    # Try email lookup first
    gh_user = AUTHOR_MAP.get(email)
    if gh_user:
        return f"@{gh_user}"

    # Try noreply pattern
    noreply_match = re.match(r"(\d+)\+(.+)@users\.noreply\.github\.com", email)
    if noreply_match:
        return f"@{noreply_match.group(2)}"

    # Try user@example.com
    noreply_match2 = re.match(r"(.+)@users\.noreply\.github\.com", email)
    if noreply_match2:
        return f"@{noreply_match2.group(1)}"

    # Fallback to git name
    return name


def categorize_commit(subject: str) -> str:
    """Categorize a commit by its conventional commit prefix."""
    subject_lower = subject.lower()

    # Match conventional commit patterns
    patterns = {
        "breaking": [r"^breaking[\s:(]", r"^!:", r"BREAKING CHANGE"],
        "features": [r"^feat[\s:(]", r"^feature[\s:(]", r"^add[\s:(]"],
        "fixes": [r"^fix[\s:(]", r"^bugfix[\s:(]", r"^bug[\s:(]", r"^hotfix[\s:(]"],
        "improvements": [r"^improve[\s:(]", r"^perf[\s:(]", r"^enhance[\s:(]",
                         r"^refactor[\s:(]", r"^cleanup[\s:(]", r"^clean[\s:(]",
                         r"^update[\s:(]", r"^optimize[\s:(]"],
        "docs": [r"^doc[\s:(]", r"^docs[\s:(]"],
        "tests": [r"^test[\s:(]", r"^tests[\s:(]"],
        "chore": [r"^chore[\s:(]", r"^ci[\s:(]", r"^build[\s:(]",
                  r"^deps[\s:(]", r"^bump[\s:(]"],
    }

    for category, regexes in patterns.items():
        for regex in regexes:
            if re.match(regex, subject_lower):
                return category

    # Heuristic fallbacks
    if any(w in subject_lower for w in ["add ", "new ", "implement", "support "]):
        return "features"
    if any(w in subject_lower for w in ["fix ", "fixed ", "resolve", "patch "]):
        return "fixes"
    if any(w in subject_lower for w in ["refactor", "cleanup", "improve", "update "]):
        return "improvements"

    return "other"


def clean_subject(subject: str) -> str:
    """Clean up a commit subject for display."""
    # Remove conventional commit prefix
    cleaned = re.sub(r"^(feat|fix|docs|chore|refactor|test|perf|ci|build|improve|add|update|cleanup|hotfix|breaking|enhance|optimize|bugfix|bug|feature|tests|deps|bump)[\s:(!]+\s*", "", subject, flags=re.IGNORECASE)
    # Remove trailing issue refs that are redundant with PR links
    cleaned = cleaned.strip()
    # Capitalize first letter
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned


def parse_coauthors(body: str) -> list:
    """Extract Co-authored-by trailers from a commit message body.

    Returns a list of {'name': ..., 'email': ...} dicts.
    Filters out AI assistants and bots (Claude, Copilot, Cursor, etc.).
    """
    if not body:
        return []
    # AI/bot emails to ignore in co-author trailers
    _ignored_emails = {"user@example.com", "user@example.com",
                       "user@example.com", "user@example.com"}
    _ignored_names = re.compile(r"^(Claude|Copilot|Cursor Agent|GitHub Actions?|dependabot|renovate)", re.IGNORECASE)
    pattern = re.compile(r"Co-authored-by:\s*(.+?)\s*<([^>]+)>", re.IGNORECASE)
    results = []
    for m in pattern.finditer(body):
        name, email = m.group(1).strip(), m.group(2).strip()
        if email in _ignored_emails or _ignored_names.match(name):
            continue
        results.append({"name": name, "email": email})
    return results


def get_commits(since_tag=None):
    """Get commits since a tag (or all commits if None)."""
    if since_tag:
        range_spec = f"{since_tag}..HEAD"
    else:
        range_spec = "HEAD"

    # Format: hash<US>author_name<US>author_email<US>subject\0body
    # Using %x1f (unit separator) to avoid conflict with | in author names
    log = git(
        "log", range_spec,
        "--format=%H%x1f%an%x1f%ae%x1f%s%x00%b%x00",
        "--no-merges",
    )

    if not log:
        return []

    commits = []
    # Split on double-null to get each commit entry, since body ends with \0
    # and format ends with \0, each record ends with \0\0 between entries
    for entry in log.split("\0\0"):
        entry = entry.strip()
        if not entry:
            continue
        # Split on first null to separate "hash<US>name<US>email<US>subject" from "body"
        if "\0" in entry:
            header, body = entry.split("\0", 1)
            body = body.strip()
        else:
            header = entry
            body = ""
        parts = header.split("\x1f", 3)
        if len(parts) != 4:
            continue
        sha, name, email, subject = parts
        coauthor_info = parse_coauthors(body)
        coauthors = [resolve_author(ca["name"], ca["email"]) for ca in coauthor_info]
        commits.append({
            "sha": sha,
            "short_sha": sha[:8],
            "author_name": name,
            "author_email": email,
            "subject": subject,
            "category": categorize_commit(subject),
            "github_author": resolve_author(name, email),
            "coauthors": coauthors,
        })

    return commits


def get_pr_number(subject: str) -> str | None:
    """Extract PR number from commit subject if present."""
    match = re.search(r"#(\d+)", subject)
    if match:
        return match.group(1)
    return None


def generate_changelog(commits, tag_name, semver, repo_url="https://github.com/NousResearch/hermes-agent",
                       prev_tag=None, first_release=False):
    """Generate markdown changelog from categorized commits."""
    lines = []

    # Header
    now = datetime.now()
    date_str = now.strftime("%B %d, %Y")
    lines.append(f"# Hermes Agent v{semver} ({tag_name})")
    lines.append("")
    lines.append(f"**Release Date:** {date_str}")
    lines.append("")

    if first_release:
        lines.append("> 🎉 **First official release!** This marks the beginning of regular weekly releases")
        lines.append("> for Hermes Agent. See below for everything included in this initial release.")
        lines.append("")

    # Group commits by category
    categories = defaultdict(list)
    all_authors = set()
    teknium_aliases = {"@teknium1"}

    for commit in commits:
        categories[commit["category"]].append(commit)
        author = commit["github_author"]
        if author not in teknium_aliases:
            all_authors.add(author)
        for coauthor in commit.get("coauthors", []):
            if coauthor not in teknium_aliases:
                all_authors.add(coauthor)

    # Category display order and emoji
    category_order = [
        ("breaking", "⚠️ Breaking Changes"),
        ("features", "✨ Features"),
        ("improvements", "🔧 Improvements"),
        ("fixes", "🐛 Bug Fixes"),
        ("docs", "📚 Documentation"),
        ("tests", "🧪 Tests"),
        ("chore", "🏗️ Infrastructure"),
        ("other", "📦 Other Changes"),
    ]

    for cat_key, cat_title in category_order:
        cat_commits = categories.get(cat_key, [])
        if not cat_commits:
            continue

        lines.append(f"## {cat_title}")
        lines.append("")

        for commit in cat_commits:
            subject = clean_subject(commit["subject"])
            pr_num = get_pr_number(commit["subject"])
            author = commit["github_author"]

            # Build the line
            parts = [f"- {subject}"]
            if pr_num:
                parts.append(f"([#{pr_num}]({repo_url}/pull/{pr_num}))")
            else:
                parts.append(f"([`{commit['short_sha']}`]({repo_url}/commit/{commit['sha']}))")

            if author not in teknium_aliases:
                parts.append(f"— {author}")

            lines.append(" ".join(parts))

        lines.append("")

    # Contributors section
    if all_authors:
        # Sort contributors by commit count
        author_counts = defaultdict(int)
        for commit in commits:
            author = commit["github_author"]
            if author not in teknium_aliases:
                author_counts[author] += 1
            for coauthor in commit.get("coauthors", []):
                if coauthor not in teknium_aliases:
                    author_counts[coauthor] += 1

        sorted_authors = sorted(author_counts.items(), key=lambda x: -x[1])

        lines.append("## 👥 Contributors")
        lines.append("")
        lines.append("Thank you to everyone who contributed to this release!")
        lines.append("")
        for author, count in sorted_authors:
            commit_word = "commit" if count == 1 else "commits"
            lines.append(f"- {author} ({count} {commit_word})")
        lines.append("")

    # Full changelog link
    if prev_tag:
        lines.append(f"**Full Changelog**: [{prev_tag}...{tag_name}]({repo_url}/compare/{prev_tag}...{tag_name})")
    else:
        lines.append(f"**Full Changelog**: [{tag_name}]({repo_url}/commits/{tag_name})")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Hermes Agent Release Tool")
    parser.add_argument("--bump", choices=["major", "minor", "patch"],
                        help="Which semver component to bump")
    parser.add_argument("--publish", action="store_true",
                        help="Actually create the tag and GitHub release (otherwise dry run)")
    parser.add_argument("--date", type=str,
                        help="Override CalVer date (format: YYYY.M.D)")
    parser.add_argument("--first-release", action="store_true",
                        help="Mark as first release (no previous tag expected)")
    parser.add_argument("--output", type=str,
                        help="Write changelog to file instead of stdout")
    args = parser.parse_args()

    # Determine CalVer date
    if args.date:
        calver_date = args.date
    else:
        now = datetime.now()
        calver_date = f"{now.year}.{now.month}.{now.day}"

    base_tag = f"v{calver_date}"
    tag_name, calver_date = next_available_tag(base_tag)
    if tag_name != base_tag:
        print(f"Note: Tag {base_tag} already exists, using {tag_name}")

    # Determine semver
    current_version = get_current_version()
    if args.bump:
        new_version = bump_version(current_version, args.bump)
    else:
        new_version = current_version

    # Get previous tag
    prev_tag = get_last_tag()
    if not prev_tag and not args.first_release:
        print("No previous tags found. Use --first-release for the initial release.")
        print(f"Would create tag: {tag_name}")
        print(f"Would set version: {new_version}")
        return

    # Get commits
    commits = get_commits(since_tag=prev_tag)
    if not commits:
        print("No new commits since last tag.")
        if not args.first_release:
            return

    print(f"{'='*60}")
    print("  Hermes Agent Release Preview")
    print(f"{'='*60}")
    print(f"  CalVer tag:      {tag_name}")
    print(f"  SemVer:          v{current_version} → v{new_version}")
    print(f"  Previous tag:    {prev_tag or '(none — first release)'}")
    print(f"  Commits:         {len(commits)}")
    print(f"  Unique authors:  {len({c['github_author'] for c in commits})}")
    print(f"  Mode:            {'PUBLISH' if args.publish else 'DRY RUN'}")
    print(f"{'='*60}")
    print()

    # Generate changelog
    changelog = generate_changelog(
        commits, tag_name, new_version,
        prev_tag=prev_tag,
        first_release=args.first_release,
    )

    if args.output:
        Path(args.output).write_text(changelog, encoding="utf-8")
        print(f"Changelog written to {args.output}")
    else:
        print(changelog)

    if args.publish:
        print(f"\n{'='*60}")
        print("  Publishing release...")
        print(f"{'='*60}")

        # Update version files
        if args.bump:
            update_version_files(new_version, calver_date)
            print(f"  ✓ Updated version files to v{new_version} ({calver_date})")

            # Commit version bump
            add_files = version_files_to_stage()
            add_result = git_result("add", *add_files)
            if add_result.returncode != 0:
                print(f"  ✗ Failed to stage version files: {add_result.stderr.strip()}")
                return

            commit_result = git_result(
                "commit", "-m", f"chore: bump version to v{new_version} ({calver_date})"
            )
            if commit_result.returncode != 0:
                print(f"  ✗ Failed to commit version bump: {commit_result.stderr.strip()}")
                return
            print("  ✓ Committed version bump")

        # Create annotated tag
        tag_result = git_result(
            "tag", "-a", tag_name, "-m",
            f"Hermes Agent v{new_version} ({calver_date})\n\nWeekly release"
        )
        if tag_result.returncode != 0:
            print(f"  ✗ Failed to create tag {tag_name}: {tag_result.stderr.strip()}")
            return
        print(f"  ✓ Created tag {tag_name}")

        # Push
        push_result = git_result("push", "origin", "HEAD", "--tags")
        if push_result.returncode == 0:
            print("  ✓ Pushed to origin")
        else:
            print(f"  ✗ Failed to push to origin: {push_result.stderr.strip()}")
            print("    Continue manually after fixing access:")
            print("    git push origin HEAD --tags")

        # Create GitHub release
        changelog_file = REPO_ROOT / ".release_notes.md"
        changelog_file.write_text(changelog, encoding="utf-8")

        gh_cmd = [
            "gh", "release", "create", tag_name,
            "--title", f"Hermes Agent v{new_version} ({calver_date})",
            "--notes-file", str(changelog_file),
        ]

        gh_bin = shutil.which("gh")
        if gh_bin:
            result = subprocess.run(
                gh_cmd,
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                cwd=str(REPO_ROOT),
            )
        else:
            result = None

        if result and result.returncode == 0:
            changelog_file.unlink(missing_ok=True)
            print(f"  ✓ GitHub release created: {result.stdout.strip()}")
            print(f"\n  🎉 Release v{new_version} ({tag_name}) published!")
        else:
            if result is None:
                print("  ✗ GitHub release skipped: `gh` CLI not found.")
            else:
                print(f"  ✗ GitHub release failed: {result.stderr.strip()}")
            print(f"    Release notes kept at: {changelog_file}")
            print("    Tag was created locally. Create the release manually:")
            print(
                f"    gh release create {tag_name} --title 'Hermes Agent v{new_version} ({calver_date})' "
                f"--notes-file .release_notes.md"
            )
            print(f"\n  ✓ Release v{new_version} ({tag_name}) prepared for manual publish.")
    else:
        print(f"\n{'='*60}")
        print("  Dry run complete. To publish, add --publish")
        print("  Example: python scripts/release.py --bump minor --publish")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
