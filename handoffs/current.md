# Current handoff — Part 3.2 completion

Read README.md, AGENTS.md, and the final Part 3.2 sections in the design and
verification notes. Part 3.1 report.md and its existing local edit are preserved.
The Part 3.2 submission file is docs/part-3-2/report.md.

Branch: codex/part-3-2, based on ada0f9ba06cbcf37961db7c4daae3757a2b91eb9.
A checked implementation checkpoint is being published; do not claim its hash
until Git confirms it. main remains the original Part 3.1 branch.

Working app: http://127.0.0.1:8000/ . FastAPI serves the built Vue interface.
The Vite development server is stopped. See README to rebuild or restart.
Implemented: fixed 60-second 4–6 pacing, pause/resume/Stop, text-only cues,
interruption recovery, independent static support, SQLite session/conversation
history, optional cue preferences/Forget, strict-schema live model planning and
answer generation through bounded read-only SQL retrieval, and honest failures.
Original Figma frames are unchanged.

The student supplied a key locally and approved up to four provider API attempts.
The allowance is exhausted: one generation attempt rejected HTTP400, one read-only
model-access check, then two successful generation stages. Do not make additional
provider calls without a new budget. Local .env now selects openai/gpt-5.4-mini;
never print or overwrite the key. It and app.sqlite3 are ignored by Git.

Actual live request af4f6a8e-1602-441f-9352-3a70c65682d0 produced saved assistant
message 792a4540-9672-4e2d-913a-8cf8204581c3 in conversation
57fc339b-7644-4fdd-8cef-28cdfe33de0f. It correctly cited completed session
9c6fc7e0-e900-4f05-ab77-f77e07fd076a (60.1077 server seconds).
The first failed live question remains failed without a fabricated reply.
health.live_verified is true only after a live answer is saved in the current
server run and resets on restart; historic evidence is in verification notes.

Checks: 18 backend tests, 7 frontend tests, production build; real guided duration
60.0138 seconds, API/SQLite/browser IDs and content agreement, refresh/restart
persistence, support with backend offline, model/database failures, preference
save/forget, 320px layout and keyboard support access. A later outcome shows
separate setup timing (0.1 seconds in a fast automated walkthrough, not a human
setup estimate). Screenshots in docs/evidence are fictional records only.

Next: verify the published checkpoint and final report links. The student must
review and upload the Part 3.2 report to the course page; no course submission,
main merge, external deployment, or video recording is authorized/performed.
Remaining product limits: single-user/single-tab, no full accessibility audit or
automatic retention controls, no clinical-effectiveness claim. Preserve all local
records, unfinished work, and the Part 3.1 files.
