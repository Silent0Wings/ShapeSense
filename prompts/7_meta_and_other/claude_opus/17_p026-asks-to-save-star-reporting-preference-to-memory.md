# 7_meta_and_other - P026: Asks to save STAR reporting preference to memory across projects
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Source: Claude Code session notes, pair P026. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

+ add to memory user wants you to speak in star standard language =[

<pasted_content id="83b2">
You mean the **STAR method**: **S**ituation, **T**ask, **A**ction, **R**esult. It is a structured way to answer behavioral interview questions such as “Tell me about a time you solved a difficult problem.” [oregon](https://www.oregon.gov/DCBS/jobs/Pages/the-STAR-method.aspx)

#### What each part means

| Part | What to explain | Keep it |
|---|---|---|
| **Situation** | The context: project, team, problem, deadline | Brief |
| **Task** | Your specific responsibility or goal | Brief |
| **Action** | What *you* did, the decisions you made, and why | Most detailed |
| **Result** | The measurable outcome, lesson, or impact | Brief but concrete |

Use “I” rather than “we” in the Action section, since interviewers want to understand your individual contribution. [thecognitive](https://thecognitive.io/interview-questions/star-method)

#### Template

> **Situation:** In my previous project, our application’s build time had grown to 25 minutes, slowing development and testing.  
> **Task:** I was responsible for reducing build time without compromising release quality.  
> **Action:** I profiled the build, identified redundant compilation steps, split the project into independently buildable modules, enabled incremental builds, and added CI caching for dependencies.  
> **Result:** Build time dropped from 25 minutes to 8 minutes, reducing CI wait time by about 68% and allowing faster iteration.

#### Quick rules

- Choose **one specific example**, not a general description of how you usually work.
- Make the **Result** measurable: time saved, revenue gained, bugs reduced, users affected, deadline met, or lesson learned.
- Keep the whole answer roughly **60–90 seconds**; spend most of it on **Action**. [thecognitive](https://thecognitive.io/interview-questions/star-method)
- If the result was negative, state what you learned and what you changed afterward. [thecognitive](https://thecognitive.io/interview-questions/star-method)

#### Example question

**“Tell me about a time you handled a conflict.”**

- **Situation:** Two teammates disagreed on the architecture for a feature.
- **Task:** I needed to help the team reach a practical decision before the sprint deadline.
- **Action:** I met each person separately, summarized the tradeoffs, proposed a small prototype to test the riskiest assumption, and facilitated a decision meeting.
- **Result:** We chose the prototype-backed approach, delivered on time, and adopted the decision framework for later architecture discussions. [starinterview](https://starinterview.org/star-method)

A useful memory shortcut: **context → responsibility → what I did → what changed.** [oregon](https://www.oregon.gov/DCBS/jobs/Pages/the-STAR-method.aspx)
</pasted_content id="83b2">

]

global memory pls

## Response

#### Situation

You asked me to report in STAR format from now on, across all projects. My persistent memory is per-project, so a note there would not apply elsewhere.

#### Task

Save the preference somewhere every Claude Code session reads.

#### Action

I checked for a global instructions file, found none, and created `<home>\.claude\CLAUDE.md` (not in the repository) with the four STAR parts as you defined them:

- Situation and Task are brief.
- Action is the most detailed part, written in the first person.
- Result is concrete, and states negative outcomes plainly.

I made one judgment call: simple one-line answers do not need the four labels. Tell me if you want STAR on those too.

#### Result

The preference now loads in every project, and I am using it from this message on. The Stage 4 retrain was not affected and is still running.

##### Why a global file and not project memory
Project memory is scoped to one repo, so a STAR preference saved there would not reach other projects. A global CLAUDE.md file is read at the start of every session, which is what "across projects" requires.

##### What was left out on purpose
The pasted STAR material was used only to define the four parts. The example answers in it were not copied into the file, so the saved rule is short and only states the format.

##### Consequence
Replies in every project now follow the STAR layout for work reports. The rule does not force STAR on one-line answers.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
