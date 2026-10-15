# IST 402 Assignment 3 — Part 3.1: Research and Design

## My project idea

For this project, I chose paced breathing. My app idea is called Breathing Break.
The scenario is a fictional student taking a short break before giving a
presentation. I wanted to keep the experience simple so the student could start
without typing about their feelings or answering a list of questions.

The exercise follows the assignment's 4–6 breathing pattern: breathe in for four
counts and breathe out for six. My proposed session has six cycles, with each
count lasting one second. That adds up to 60 seconds. This is the planned length;
I have not measured it in a working app yet. Time spent on the entry screen or
reading an explanation would be separate.

## How the design works

The entry screen briefly explains the exercise and has a Start button. During
the exercise, the main instruction is either “Breathe in” or “Breathe out,” with
a count and a circle that would grow or shrink with the pace. There is also a
text-only option for someone who does not want the moving circle.

The student can stop at any point. Stopping leads to a different ending from
finishing all six cycles, and neither ending pressures them to keep going. They
can return to the start, repeat the exercise, or leave. Crisis-support access
stays visible throughout the design and would work independently of the model.
Opening support during an exercise would pause it, with the choice to resume or
stop afterward.

The Figma storyboard has eight screens: entry, inhale, exhale, completed, stopped,
text-only breathing, example history, and support. These are static mockups, not
a working app or a clickable Figma prototype. The support page is labeled as a
placeholder because the actual resources still need to be selected and verified.
The history examples are fictional.

## How I used the research

R1 influenced the session length. The study reported that around 60 seconds was
comfortable and that people lost attention beyond 90–100 seconds. I chose a
60-second session instead of 90 seconds. This gives the student fewer cycles,
but it asks for less time before their presentation.

D2 influenced the breathing screen. Showing one instruction at a time keeps the
focus on the current action. I considered having chat and other information on
the same screen, but that could compete with the breathing cue. D3 also supported
letting the student begin without a required mood check-in. A check-in could give
the app more context, but it would add effort and require personal disclosure.

R3 and R4 influenced the controls. The student chooses when to start, stop,
repeat, or leave. I prefer an immediate Stop action over a confirmation popup,
even though that means an accidental stop is possible. The student can choose
to start again. R2 and D4 explain why support access stays visible instead of
being hidden in a menu or only shown at the beginning.

D5 influenced my proposed personalization. The app could optionally remember
whether someone prefers the circle or text-only cues. They could change or
forget that choice without going through a setup questionnaire. For D6, I chose
plain wording and restrained visuals instead of bright effects or rewards.

For D1, the exercise screen contains less information than the entry screen.
However, I would not have the app guess that someone is distressed based on
their clicks. The user chooses the simpler cue option. The research supports
these design choices, but it does not prove that my app improves mental health.

## The model and saved information

I plan to use Vue for the interface, FastAPI for the backend, and SQLite for
saved records. The model would have a limited role outside the timed exercise:
explaining reviewed information or answering an optional question about saved
history. The application code would control the breathing steps, timing, Stop
button, support access, and saving.

The backend would retrieve relevant records before the model answers a history
question. It would check any proposed retrieval query and restrict it to allowed,
read-only data. The model would not connect directly to SQLite or invent missing
history. The exercise and support route would still be available if a model
request failed.

I plan to save conversation messages in order, session dates and durations,
whether a session was completed or stopped, and an optional cue preference.
History would show what the person did, without claiming that they became calmer
or improved clinically. A failed save would need to be shown honestly rather than
appearing successful.

## What is finished and what I still need to decide

For Part 3.1, the project has a design proposal, a flow diagram, Figma mockups,
research explanations, and a plan for the model and saved data. The README and
AGENTS.md have also been updated. No code from my earlier travel app has been
reused in this project so far.

The Figma screens were checked through the connected tool, and text clipping
found in the first layout was corrected. This helps show the intended layout,
but it does not test real breathing timing, keyboard access, saving, or model
responses. I have not built the application or tested it with real users.

Before implementation, I still need to finalize how long records are kept,
how users delete them, and what happens after a refresh or interruption. I also
need to select verified support resources and finalize the response to
crisis-related messages. Any detection would have limits and would never be
required to access support. The project is a coursework prototype, not therapy
or a monitored service. Any later testing will use fictional scenarios only.

I used Codex to help interpret the assignment, draft the design notes and report,
and create the initial sketch and Figma screens. I selected paced breathing, the
student presentation scenario, and the circle-cue direction. More detail about
the AI assistance is included in my design notes.

## Project links and submission details

- Repository: [mental-health-skills-app](https://github.com/emadzam/mental-health-skills-app)
- Submitted commit: **PENDING — these local files have not been committed or uploaded.**
- [Figma storyboard](https://www.figma.com/design/Ec255iH4NSnqPSmo5N6WQ6?node-id=1-391)
- [Design notes and flow diagram](docs/design-pipeline.md)
- [README](README.md) and [agent instructions](AGENTS.md)
- [Verification notes](docs/verification.md)

Before submitting, I still need to upload the documents, add the actual commit ID,
and replace the local document links above with accessible links to the submitted
version. I also need to check that my instructor can access the repository and
Figma file.
