# Prompt material provenance

The files in this directory are **verbatim copies of third-party skill prompt
material**, copied here verbatim (with their original frontmatter) so the
Wizard adapter can load them as system-prompt context. They are NOT original
work of this repository.

| File | Source path | Notes |
|---|---|---|
| `grilling.SKILL.md` | `~/.agents/skills/grilling/SKILL.md` | design-tree frontier interview prompts |
| `domain-modeling.SKILL.md` | `~/.agents/skills/domain-modeling/SKILL.md` | glossary + ADR discipline |
| `CONTEXT-FORMAT.md` | `~/.agents/skills/domain-modeling/CONTEXT-FORMAT.md` | glossary format reference |
| `ADR-FORMAT.md` | `~/.agents/skills/domain-modeling/ADR-FORMAT.md` | ADR format reference |

## Why they live here

`grill-with-docs/SKILL.md` (`~/.agents/skills/grill-with-docs/SKILL.md`) carries
`disable-model-invocation: true` and instructs the *host*:

> Call the Skill tool twice, for "grilling" and "domain-modeling".

That instruction targets a Claude/Codex-style host that exposes a "Skill tool".
The Hermes process this shim drives has no such tool. The Wizard adapter
(`server/wizard/grill/adapter.py`) **translates** "call the Skill tool twice"
into two in-process sub-flows within one conversation turn:

1. **grilling** — design-tree frontier: ask a numbered round `Q1/Q2...` each with
   a recommended answer, then recompute the frontier after the user answers.
2. **domain-modeling** — maintain a CONTEXT.md glossary and propose ADRs only
   when all three conditions hold (hard to reverse / surprising without context
   / real trade-off).

These prompt files are the material injected for those two sub-flows; the
state machine around them is our adapter.

## License

These are generic prompt/process skills (interview method, glossary/ADR
discipline), not vendored binary dependencies. They retain their original
copyright and terms; this repository records provenance and does not claim
authorship. If you redistribute, preserve the upstream attribution.
