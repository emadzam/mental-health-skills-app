# Part 3.1 verification and limitations

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
