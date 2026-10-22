# IST 402 Assignment 3 — Part 3.2: Working Application and Safety

## What I built

For Part 3.2, I turned my Breathing Break design into a working local app. I kept
the fictional scenario of a student taking a short break before a presentation.
The app uses Vue for the interface, FastAPI for the backend, and SQLite for saved
records. It runs on localhost and is only a coursework prototype.

The main exercise has six cycles of breathing in for four counts and out for six.
The circle follows the pace, and there is a text-only alternative. The student can
pause, stop, repeat, or leave without explaining their feelings or finishing a
questionnaire. I kept the original Figma frames as the design reference.

## The model's contribution

The exercise helper now connects to a real OpenAI model, GPT-5.4 Mini. It works
outside the timed breathing exercise. It can explain reviewed exercise information
or answer a question using the fictional student's saved history. The application
code controls the exercise steps, timers, exits, and support access.

I verified the live history path by asking for the latest completed session's
duration, status, and record ID. The first model call proposed a retrieval query.
FastAPI checked it and ran it through restricted, read-only SQLite views. A second
call used the selected record to answer. The actual reply reported a completed
session lasting 60.108 server seconds and cited its correct record ID. It did not
make a claim about how the student felt. The reply was saved and appeared in the
conversation history.

The first live attempt failed with HTTP 400. After changing the response format
to strict JSON schemas, both stages succeeded. The approved verification used
three generation attempts total, including that rejected attempt, and one read-only
model-access check. There were no automatic retries. The app still offers a
clearly labeled mock mode for repeatable testing without paid calls.

## Saved records and failures

SQLite stores conversation messages in order, session duration and status, and an
optional cue preference. History shows completed and stopped sessions separately.
The user can choose whether to remember the cue preference and can forget it later.
These records show activity, not mental-health improvement.

Request IDs prevent repeated submissions from creating duplicate rows. A failed
save is shown as unconfirmed instead of successful. Retrying uses the same ID.
Provider failures keep the submitted question with failed status and do not invent
an assistant reply. The real rejected request and a separate mock failure both
showed this behavior. Database tests also checked that a failed reply write rolls
back the success state.

## Timing, control, and support

The full browser walkthrough measured 60.014 seconds of guided time. The server
recorded 60.108 seconds, including request overhead. Both are under the assignment's
90-second limit. Pauses are recorded separately and excluded from guidance. The
outcome screen also reports this visit's entry/setup time separately. A fast
automated walkthrough showed 0.1 seconds of setup; a person's reading and decisions
would take a different amount of time.

Opening crisis-support information pauses the exercise. Returning does not resume
it automatically. Stop saves the outcome as stopped. In-app navigation stops the
exercise before leaving. If a page closes unexpectedly, the next visit recovers
the unfinished session as stopped, without claiming an uncertain interval was a
completed guided exercise.

Support access stays visible in the header and does not depend on the model or
backend. The dialog opened after a model failure and while FastAPI was stopped.
Its U.S. resource details were verified through the hotline connector. No support
service was called or texted during testing. A limited phrase check can show a
fixed boundary response for crisis-related input, but it is not an assessment and
can miss or misclassify text. Support is available regardless of that check.

## Verification evidence

All 18 backend checks and seven frontend checks passed, and the production build
passed. The checks covered pacing boundaries, pauses, interruptions, duplicate
requests, restricted SQL retrieval, missing configuration, provider errors, and
failed saves. Mocked transport checks are separate from the successful live calls.

I compared the same fictional record IDs and message content across SQLite,
FastAPI responses, and the browser. Records survived refresh and a backend restart
without duplicates. A 320px check showed no horizontal page overflow and kept Stop
and support visible during guidance. Keyboard access to the support dialog was
also checked. Screenshots and exact record IDs are linked in the verification notes.

## Project links

- Repository: [Part 3.2 branch](https://github.com/emadzam/mental-health-skills-app/tree/codex/part-3-2)
- Submitted implementation commit: [93796ae7b23e90885ce64e014124771974dcca04](https://github.com/emadzam/mental-health-skills-app/commit/93796ae7b23e90885ce64e014124771974dcca04)
- [Implementation and API notes](https://github.com/emadzam/mental-health-skills-app/blob/93796ae7b23e90885ce64e014124771974dcca04/docs/design-pipeline.md)
- [Verification results and screenshots](https://github.com/emadzam/mental-health-skills-app/blob/93796ae7b23e90885ce64e014124771974dcca04/docs/verification.md)
- [Successful live model reply](https://github.com/emadzam/mental-health-skills-app/blob/93796ae7b23e90885ce64e014124771974dcca04/docs/evidence/part-3-2-live-model.png)
- [Original Figma storyboard](https://www.figma.com/design/Ec255iH4NSnqPSmo5N6WQ6?node-id=1-391)

## Limits and AI use

The implementation and evidence were committed and uploaded on the Part 3.2 branch.
The links above identify that fixed version. This report was finalized afterward
to add the verified commit and links. Part 3.1 remains preserved on main.

This version is for one fictional demo user in one tab. It does not have login,
automatic data deletion, or a full accessibility audit. Broader evaluation belongs
to the next milestone. No video recording has been made; the screenshots, tests,
and database/API comparison are the evidence for this milestone. A successful
live reply does not establish that every possible model response will be correct.

This app does not diagnose, provide therapy, or imply human monitoring. All checks
used fictional scenarios. I used Codex to help implement the app, prepare tests,
inspect browser/database behavior, and draft the documentation. I selected the
skill and scenario, approved the dependencies, and supplied the API key locally.
The key and working database are excluded from GitHub. The original Part 3.1
report is preserved separately.
