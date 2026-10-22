# Mental Health Skills App

IST 402 — Assignment 3, Part 3.2: Working Application and Safety

## Purpose

Build a local application that lets someone practice a short skill, stop at any
point, and return to useful session history. The interface should ask for little
reading or typing and keep the person in control. A conversational model can
help introduce the skill and explain the app, using reviewed content and saved
context.

This is a coursework prototype, tested only with fictional scenarios. It must
not diagnose, provide therapy, imply human monitoring, or be offered as a real
mental health support service.

## Current milestone

The local Vue/FastAPI/SQLite prototype now supports the 60-second exercise,
pause/stop, text-only cues, saved sessions/messages, optional remembered cues,
read-only scoped SQL retrieval, and independent U.S. support information.
The real model path was verified with GPT-5.4 Mini: query planning, restricted SQL
retrieval, a grounded answer, and persistence of the actual reply. Mock mode is
also available and clearly labeled; fresh checkouts default to mock without a key.
See [the design and implementation notes](docs/design-pipeline.md),
[verification evidence](docs/verification.md), and the [Part 3.2 report](docs/part-3-2/report.md).
The original [Part 3.1 report](report.md) is preserved.
Repository: https://github.com/emadzam/mental-health-skills-app

[Original Figma storyboard](https://www.figma.com/design/Ec255iH4NSnqPSmo5N6WQ6?node-id=1-391)
contains eight editable static design screens. The student confirmed instructor
access for Part 3.1. Original frames were preserved; no new Figma work was needed.

## Project design guidelines

The skill, fictional scenario, and circle-cue direction were selected with the
student. The guidelines below originated in Part 3.1; implementation status and
resolved behavior are recorded in the Part 3.2 section of the design notes.

Class principles to carry into your design:

- Keep the guided skill within 90 seconds at its intended pace. Show one clear
  action at a time and keep reading, typing, and configuration demands low.
- Let people start, stop, skip, and change their choices. Keep support information
  visible and usable independently of model responses.
- Use calm, readable language, sufficient contrast, visible keyboard focus,
  a narrow-screen layout, and an alternative to motion.
- Make personalization understandable and changeable. Keep self-report,
  observed behavior, and interpretation distinct; clicks do not establish an
  emotional state or diagnosis.
- Explain how a design choice follows from a class finding, what alternative
  you considered, and what tradeoff you accepted. Check the running result later.

- Chosen skill and fictional user/task: 4–6 paced breathing; a fictional student
  taking a short break before a presentation. No required emotional disclosure.
- Proposed flow: entry → six breathing cycles → completed, with Stop leading to
  a separate stopped state. Keep support accessible throughout; offer repeat,
  leave, history, and a text-only cue alternative.
- Proposed duration: six cycles of 4-second inhales and 6-second exhales = 60
  seconds, with no model calls or planned delays inside the guided sequence (R1).
- Interface guidelines: one current instruction (D2), minimal required input
  (D3), visible Stop and support (R2/R3/D4), user choice (R4), calm wording,
  readable contrast, keyboard focus, and optional motion (D6).
- Proposed model role: optional reviewed explanations and grounded questions
  about saved history, outside the timed exercise. Code owns the exercise rules.
- Proposed personalization: optionally remember circle/text cue preference;
  explain it and permit change or forgetting (D5). Do not infer distress (D1).
- Alternatives and tradeoffs: circle cues communicate pace spatially; text-only
  cues reduce visual stimulation. Direct start avoids the burden of a mandatory
  chatbot or mood questionnaire. Detailed rationale and open questions are in
  [docs/design-pipeline.md](docs/design-pipeline.md).

You may choose paced breathing, sensory grounding, STOP, or a cognitive reframe
within the assignment's scope. Record detailed design decisions in
`docs/design-pipeline.md` as the design develops.

## Technology and separation

- Frontend: Vue with JavaScript, HTML, and CSS. It presents the interface,
  responds to input, and sends HTTP requests to the backend. Node.js provides
  the frontend development tools.
- Backend: Python with FastAPI. It exposes the API, validates requests, applies
  business rules, calls the conversational model, and reads/writes the database.
- Database: SQLite. The planned database is data/app.sqlite3. Only the Python
  backend accesses it; the frontend receives data through the API.

The application runs on localhost. Use one tab; all records belong to one fictional
demo student. This is not an authenticated or multi-user service.

## Run the working prototype

The currently verified Windows environment uses Python 3.12.14, Node 24.19.0,
and pnpm 11.25.0. Dependencies are local to backend/.venv and frontend/node_modules.
Secrets and the working database are ignored by Git. SQLite is created once on
startup; no fictional records are reseeded. Browser walkthrough records persist.

From the project root, with the frontend already built:

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. Press Ctrl+C in that server terminal to stop it.
Starting the same command again preserves the SQLite records. These start/stop
and restart operations were checked. No activation script is necessary.

For a fresh checkout, install Python/Node/pnpm first if they are not present.
The exact executables below were used on this computer (rather than the broken
WindowsApps Python alias):

```powershell
$pythonExe = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$pnpmExe = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd"
& $pythonExe -m venv backend/.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements.lock.txt
& $pnpmExe --dir frontend install --frozen-lockfile --store-dir .pnpm-store
& $pnpmExe --dir frontend build
```

On another computer use its Python and pnpm executable paths. The checked build
command is `pnpm --dir frontend build`; the checked development command is
`pnpm --dir frontend dev` (port 5173, proxies /api to FastAPI on port 8000).
The approved esbuild installation script is declared in frontend/pnpm-workspace.yaml.

Configuration: backend/config.py explicitly loads backend/.env. A local file was
initially created from backend/.env.example; the student subsequently entered a
private API key locally. It remains ignored and was never printed or committed.
If absent, mock mode defaults on. For live setup, set MODEL_MODE=openai,
OPENAI_API_KEY, and an available OPENAI_MODEL locally, then restart FastAPI.
Never send a key in chat. Health reports presence only, not values; it does not
establish a successful live call. live_verified becomes true only after a live
answer is saved successfully during the current server run; it resets on restart.
The approved verification used one rejected generation attempt, then two successful
generation calls, plus one read-only model-access check. No further calls were made.

## Checked commands

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend/tests -q
pnpm --dir frontend test
pnpm --dir frontend build
.\backend\.venv\Scripts\python.exe backend/inspect_db.py
.\backend\.venv\Scripts\python.exe -m backend.verify_records
```

Use the bundled pnpm path above if pnpm is not on PATH. Backend checks use isolated
temporary databases. inspect_db.py opens the runtime database read-only;
verify_records compares API messages/sessions with the same SQLite rows. See
docs/verification.md for observed results, screenshots, and known limitations.
Some operations required the desktop host's normal permissions because the
sandbox blocked local sockets, temporary files, and installation symlinks.

## Secrets and APIs

Store model-provider API keys and other secrets in `backend/.env`. Keep this
file out of Git with `.gitignore` before adding credentials. Provide a
`backend/.env.example` containing variable names and empty or dummy values so
another developer knows what to configure. The backend must explicitly load its
configuration; placing a file in the folder does not load it automatically.
Never put private keys in Vue code, browser-exposed environment variables,
API responses, logs, screenshots, prompts, or Figma.

Vue calls our FastAPI endpoints using HTTP and JSON. FastAPI validates requests,
calls the external model API, and reads or writes SQLite. Document each endpoint's
input, response, and failure behavior in `docs/design-pipeline.md`. Use finite
timeouts, clear loading and failure states, and a bounded number of provider
calls. A configured key, a mocked response, and a successful live API call are
different checks. Ordinary history browsing should not require a model call.

## Conversations, RAG, and data views

Save submitted user messages and actual model replies in SQLite, linked by a
conversation ID. Keep a message ID, role, content, timestamp, and request status
so the app can reconstruct the conversation in order. Store exercise outcomes
and preferences in related records. A failed model request must not create a
fabricated reply, and a failed database write must not appear as a successful
save. Saved records should survive refresh and backend restart without duplicates.

**Retrieval-augmented generation (RAG)** supplies relevant stored information to
the model before it answers. Use the SQL-based pattern covered in class:

1. FastAPI sends the question and relevant database schema to the model API.
2. The model proposes a retrieval query. FastAPI checks it, restricts it to
   allowed data for the current conversation or demo user, and executes it using
   read-only SQLite access with limits on the results.
3. FastAPI sends the selected records and reviewed skill information in a second
   model call. The answer should identify its supporting records and acknowledge
   missing information instead of inventing history.
4. Backend application code saves the actual reply and returns the result to Vue.

The model never connects directly to SQLite. RAG retrieval cannot insert,
update, or delete records; normal conversation saves use separate, parameterized
backend operations. The query-planning and answer-generation calls both count
toward the API budget. SQLite is sufficient for this baseline; it does not
require a vector database.

Make the saved data visible. Provide a Vue conversation-history view and a
session table or timeline, both populated through FastAPI from SQLite. Show
message order and time, plus exercise duration and stopped/completed status.
Any summary or chart must come from those records and must not imply a diagnosis
or improvement in mental health. During development, also inspect the schema,
relationships, and rows with an available SQLite viewer or read-only queries.
Compare the database, API response, and displayed history for the same fictional
conversation, including after a refresh and backend restart.

## Project folders

```text
project-root/
|-- README.md                 Project purpose and starting direction
|-- AGENTS.md                  Instructions for the coding agent
|-- .gitignore                 Local files to exclude from Git
|-- frontend/                  Vue interface and frontend dependencies
|-- backend/                   Python/FastAPI API and application logic
|   |-- .env                   Local secrets; ignored by Git
|   `-- .env.example           Configuration names with safe placeholders
|-- data/                      Local SQLite database and fictional fixtures
|-- docs/
|   |-- design-pipeline.md     Architecture, behavior, and design decisions
|   `-- verification.md        Checks to run and evidence of what happened
|-- prompts/
|   `-- 01-start.md            First scoped instruction for the agent
`-- handoffs/
    `-- current.md            Current state and next step for a new session
```

This map includes files to add as the project develops. At startup, create only
the base folders and the two root documents, README.md and AGENTS.md. Leave
existing supporting files intact if you already have them. Add the ignore rules
before introducing credentials or runtime data; create environment files and
the SQLite database during implementation. Keep fictional fixtures separate
from runtime records and do not commit the working database.

## Later design workflow

The separate Figma and MCP activity covers building a small interface, bringing
it into editable Figma frames, and using a selected design to guide a Vue
revision. That work comes after this startup step and your initial design
guidelines. Figma edits do not automatically update application code.

## Getting started

Read `AGENTS.md` and the Part 3.2 section of `docs/design-pipeline.md`. Use the run
commands above to open the local prototype. The original Part 3.1 design/report
remains available; Part 3.2 has implementation evidence and an honest mock/live distinction.

Add supporting project notes as work requires them. Installation, interface
building, FastAPI/model connections, SQLite, RAG, and data views are later tasks.
Record actual setup, configuration, run, stop, and test commands here only after
they have been implemented and checked.
