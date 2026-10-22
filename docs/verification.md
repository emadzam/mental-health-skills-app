# Part 3.1 verification and limitations (archived)

This file records design/document checks only. It is not an application test report.

The report's wording was revised into first-person student language on request.
The revision retains the research codes, design tradeoffs, AI-use disclosure,
and explicit limits on completed work. No new implementation claims were added.

Repository preparation: the student authorized upload. `git ls-remote --symref`
completed successfully and returned no refs for the supplied repository. The
existing Git identity is configured. The design commit
`d17d873649c44990a07063d799e9d0561820ca2a` was pushed to main and verified with
`git ls-remote origin refs/heads/main`. Report links now use that fixed commit.
Remote access does not establish instructor access to Figma.

| Check | Observed result |
| --- | --- |
| Workspace inspected on October 15, 2026 | Initially six empty base directories plus README.md and AGENTS.md |
| Existing instructions reviewed | README.md and AGENTS.md read before changes; no prior design/handoff existed |
| Research source | Student-provided assignment screenshots and complete R1–R4/D1–D6 table |
| Timing calculation | 6 × (4 + 6) = 60 seconds; no measured runtime exists |
| Existing sketch review | Student described the sketch as good and selected Circle cue in the preview |
| Figma connection | whoami returned eqz5094@psu.edu, Starter plan, View seat, admin role |
| Figma file creation | Created https://www.figma.com/design/Ec255iH4NSnqPSmo5N6WQ6 |
| Figma construction | Eight static editable screen frames created after recovery from initial failed calls |
| Editability | Storyboard inspection returned 79 TEXT, 44 FRAME, 21 INSTANCE, and 2 ELLIPSE descendants; no image-filled nodes; text uses Inter |
| Visual review | Initial screenshot exposed clipped/overlapping text. Auto-height repaired; second composition screenshot showed readable, separated content and persistent support/coursework labels |
| Figma baseline | [Storyboard frame 1:391](https://www.figma.com/design/Ec255iH4NSnqPSmo5N6WQ6?node-id=1-391); original screens retained |
| Access limits | Connected-account read/write succeeded; independent instructor access and sharing permissions not checked |

Screen IDs: entry 3:142; inhale 3:182; exhale 3:207; completed 3:232;
stopped 3:263; text-only 3:293; history 3:323; support 3:348. These are editable
design evidence, not a running or wired prototype. Imported Simple Design System
buttons provide reusable instances. Inter replaces unavailable Arial from the
conversation sketch. Temporary screenshot URLs are not submission evidence links;
use the stable Figma frame link.

## Later checks, not performed

- Measure actual guided duration, entry/setup time, and pause/support exclusions.
- Operate Stop, restart, support, cue switching, focus order, and reduced-motion mode.
- Check layout at 320px, text contrast, screen-reader announcements, and touch targets.
- Compare fictional session/message IDs across SQLite, API, and UI after refresh,
  retry, and service restart; ensure save failures are honest and retries do not duplicate.
- Test model timeouts, missing configuration, rejected retrieval SQL, empty records,
  and provider failures, distinguishing mocks from live paid calls.
- Verify support resources and user access to the submitted repository/design links.

No dependencies were installed, no database or credentials were created, and no
model API call was made. There is no app to smoke-test at Part 3.1. Planned checks
are not reported as passing. No clinical outcomes were evaluated.

## Part 3.2 actual checks — October 22, 2026

This section supersedes the earlier no-app status. All records/scenarios were
fictional. Checks establish software behavior, not clinical effectiveness.

| Check | Observed evidence |
| --- | --- |
| Setup | Python 3.12.14, Node 24.19.0, pnpm 11.25.0; project-local dependencies imported successfully; backend requirements.lock.txt and frontend pnpm-lock.yaml record versions |
| First round trip | Temporary SQLite session created through FastAPI, returned by history; Vue displayed connected mock status through the real API proxy |
| Backend tests | `backend/.venv/Scripts/python.exe -m pytest backend/tests -q --tb=short`: 15 passed, one upstream Starlette HTTPX deprecation warning |
| Frontend tests | `pnpm --dir frontend test`: 7 passed; timing/pauses/interruption/restart and meaningful proxy/database errors |
| Build | `pnpm --dir frontend build`: passed after final UI/code changes |
| Built app | Opened http://127.0.0.1:8000 in the browser and confirmed the full Vue interface connects to the API; development Vite server subsequently stopped |
| Real duration | Completed session 9c6fc7e0-e900-4f05-ab77-f77e07fd076a; start 18:03:32.310579 UTC, end 18:04:32.418287 UTC; 60.1077075 server seconds, 60.0138 browser seconds, six full cycles, no pause |
| Support/Stop | Session 26a304b1-69b7-4f45-b616-8909099ab12e paused on support access, did not resume on return, then saved stopped; 0.4052 active and 10.0462 paused seconds |
| Grounded mock response | Conversation d8bfa0ca-4d13-4963-970c-658b31fbd9c6; user message 84496751-e7a7-4b24-8edc-781cba97b6f2, actual mock reply bd14f8ec-98f1-4d95-97c0-5818804e2b03 citing stopped session 26a304b1-69b7-4f45-b616-8909099ab12e |
| Provider failure | Failed user message 2f24be1b-89ec-45e8-92be-820fb1b3003c; no assistant reply invented; support still opened |
| Persistence | Same two sessions/three messages survived browser refresh and actual backend stop/start without duplicates; later mobile check added a third stopped session |
| SQLite/API comparison | inspect_db.py opened URI mode=ro for schema/relationships/rows; `python -m backend.verify_records` returned “SQLite and API agree” before/after restart and after mobile walkthrough; browser IDs/content/order also matched |
| Retrieval safety | Tests covered empty retrieval, denied direct base/system tables, writes/multiple statements, extension loading, and cross-conversation access |
| Idempotency/save failures | Repeated start/event/question IDs did not duplicate rows; assistant-insert failure rolled back request success; no fabricated reply |
| Missing live config | Live-mode test without key/model returned failed status with only the submitted question; no secret values exposed |
| Support offline | With FastAPI stopped, bundled support dialog still opened; no contact links activated |
| 320px layout | document scrollWidth 305px; support y=14–66 and Stop y=465–536 in a 740px viewport during text-only guidance |
| Preferences | Text-only opt-in saved and survived refresh; Forget removed it; circle cue restored for entry |
| Keyboard | Tab focused support with a solid visible outline; Enter opened the modal; Escape closed it |
| Ignore rules | git check-ignore confirmed backend/.env, backend/.venv, frontend/node_modules, data/app.sqlite3 are ignored |

### Browser evidence

- [Entry](evidence/part-3-2-entry.png)
- [Completed real session](evidence/part-3-2-completed.png)
- [Support pauses exercise](evidence/part-3-2-support.png)
- [Session history and record IDs](evidence/part-3-2-session-history.png)
- [Mock answer and retrieved context](evidence/part-3-2-grounded-history.png)
- [Failed model request](evidence/part-3-2-model-failure.png)
- [Support with API offline](evidence/part-3-2-support-api-offline.png)
- [320px text-only exercise](evidence/part-3-2-mobile-text-cue.png)

### Limits before claiming Part 3.2 complete

The student selected mock-first development. The live adapter has not been
configured/verified with an actual model or paid call, and mock evidence does not
establish a live-model contribution. Model and paid-call budget still need selection.
No credentials were entered. Setup time was not measured. Full screen-reader,
contrast, and OS reduced-motion testing were not performed. Single-tab fictional
demo only; no authentication or multi-user isolation claim. Abrupt-close recovery
cannot establish measured guided time. Real contact calls/texts were not made.
No recording, Part 3.2 commit/push, or course submission has occurred. The original
report.md and its pre-existing local edit were preserved.

## Final live-model check and submission checkpoint

This section supersedes the earlier “live adapter unverified” limit. With the
student's local key and four-attempt allowance, one request was rejected (HTTP400),
a read-only model-access check passed, and the corrected two-stage request passed.
No more provider attempts were made. Strict JSON schemas are used for both stages.
The API key was neither printed nor included in source, evidence, or Git.

- Model: gpt-5.4-mini, verified through the actual OpenAI Responses endpoint.
- Conversation: 57fc339b-7644-4fdd-8cef-28cdfe33de0f.
- Successful request: af4f6a8e-1602-441f-9352-3a70c65682d0.
- Submitted user message: 7f9a489f-cc69-48a8-8191-6421f13cb700.
- Actual assistant message: 792a4540-9672-4e2d-913a-8cf8204581c3.
- Supporting session: 9c6fc7e0-e900-4f05-ab77-f77e07fd076a, completed,
  60.107707500457764 server active seconds (60.0138 browser guided seconds).
- Saved reply: “Latest completed breathing session: 60.107707500457764 seconds,
  status completed, record ID 9c6fc7e0-e900-4f05-ab77-f77e07fd076a.”
- GET /api/health returned model_mode=openai, provider_configured=true, and
  live_verified=true after that reply was saved in this server run.
- The live failed question f4de128c-a766-4270-a7b8-3a97d664267d has failed status
  and no assistant reply; previous mock failure evidence remains labeled mock.
- `python -m backend.verify_records` confirmed all API/SQLite records agree.
- Backend checks now total 18 passing tests; frontend checks total 7. Mocked HTTP
  tests are identified as mocks, not additional live-model checks.
- [Actual live reply and retrieved record](evidence/part-3-2-live-model.png).

The app remains a single-tab fictional classroom prototype. Full screen-reader,
contrast and operating-system reduced-motion testing, long-term retention/deletion,
and broad Part 3.3 evaluation are still outside this milestone. No clinical claims,
real distress tests, or contact calls/texts were made. Screenshots provide the
milestone evidence; no video recording or course-site submission has been made.

Entry/setup timing is now displayed separately on the outcome screen for the
current visit, measured from entry-view initialization to the first pacing cue.
A fast automated reload/start/stop walkthrough displayed 0.1 seconds of setup;
this is not an estimate of a person's reading or decision time. Guided time in
that stopped walkthrough was 0.3 seconds. Screenshot:
[Separate setup timing](evidence/part-3-2-setup-time.png). Initial recovery finishes
before Start is enabled, preventing a new session from racing startup recovery.

Publication: implementation checkpoint 93796ae7b23e90885ce64e014124771974dcca04
was pushed to origin/codex/part-3-2 and the hash verified with git ls-remote.
main remains ada0f9ba06cbcf37961db7c4daae3757a2b91eb9. All 44 staged files were
scanned against the local private key before committing; it was absent, and neither
backend/.env nor app.sqlite3 was included. The Part 3.1 report's existing local edit
was intentionally excluded. A follow-up documentation commit finalizes the Part 3.2
report links without changing the checked application code.
