<!-- codex-workflow:project-conventions:start -->
## Agent skills

### Issue tracker

Local Markdown issues are stored under `.scratch/<feature>/issues/`. Publication policy is `explicit`. See `docs/agents/issue-tracker.md`.

### Domain docs

Use the `single` domain layout. See `docs/agents/domain.md`.
<!-- codex-workflow:project-conventions:end -->

## Project confirmation gates

- Vue 3, FastAPI, SQLite and the configured workflow conventions are approved.
- Before implementing EACH requirement, present its technical choices, tradeoffs, acceptance criteria, and public test boundaries; wait for explicit user confirmation.
- Approval of one ticket never approves later tickets. Record confirmation in decisions.md and the matching workflow plan. Do not mark grilling confirmed prematurely.
- Use vertical TDD: one failing behavior test, minimal implementation, passing check, then the next test. Tests must use approved public seams.
- Keep root spec.md canonical. tasks.md is the roadmap; local issues live under .scratch/certificate-admin/issues/. Workflow packets store execution evidence and scoped specs, referring to the canonical specification.
- Confine changes to this independent repository. Preserve unrelated files and use native Codex worktree behavior. Do not modify ComfyUI or global dependencies.
- Do not commit, publish, deploy, or send messages without the corresponding user authorization.
- Preserve original AI interaction evidence; summaries are not original exports. Never fabricate completion, test results, or approval records.
