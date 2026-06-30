---
inclusion: manual
---

# Validate Knowledge Base Samples (Q&A Benchmark)

## Purpose

Measure **how well each generated knowledge-base sample answers questions** a
real user of the SDV ("Still Defined Vehicle") tool would ask — blast-radius,
dependency tracing, signal flow, inventory, and de-contenting impact.

Every sample under `knowledge_base/output/` is a different *representation* of
the **same** underlying AUTOSAR system (the Electronic Door Control demo). They
differ only in structure (flat per-component files vs. an indexed,
relationship-aware layout). This skill runs an identical question set against
each sample **in a clean context**, records the answers, scores them against
expected key facts, and writes a single **timestamped comparison report**.

> Goal: an apples-to-apples comparison that shows which knowledge-base layout
> lets an agent answer the product's real questions fastest and most correctly.

## Parameters

- **samples_dir** (optional, default `knowledge_base/output`): directory whose
  immediate subdirectories are each treated as one knowledge-base sample.
- **questions_file** (optional, default `knowledge_base/validation/questions.md`):
  the benchmark question bank with expected answers.
- **reports_dir** (optional, default `knowledge_base/validation/reports`): where
  the timestamped report is written.
- **mode** (optional, default `per-question`): `per-question` (most rigorous —
  one clean context per sample×question) or `per-sample` (one clean context per
  sample, all questions in sequence; cheaper).

---

## Core Principle: Clean Context Per Sample

The whole point of the benchmark is fairness, so isolation is mandatory:

- When evaluating a sample, the answering agent may **only read files inside that
  one sample's directory**. It must not read other samples, the input ARXML, the
  `questions.md` expected answers, or this skill.
- Use a **fresh sub-agent** (`invokeSubAgent` → `general-task-execution`) for each
  evaluation unit so no prior answer, file content, or reasoning leaks between
  samples or questions.
- The orchestrator (you) holds the expected answers and does the scoring. The
  answering sub-agent never sees the expected answer — it only sees the question
  and its assigned sample directory.

This guarantees each sample is judged purely on what its own files communicate.

---

## Procedure

### Step 1: Discover Samples

1. List the immediate subdirectories of `samples_dir`. Each is one sample
   (e.g. `sample_1_simple_prompt`, `sample_2_skill`, `sample_3_skill2`).
2. For each sample, locate the actual knowledge-base root (the folder containing
   `components/`, `interfaces/`, `system/`, and/or `_index/`). Some samples put
   the content directly in the sample folder; others use an `output/`
   subdirectory. Record the resolved root path per sample.
3. Skip files that are only generators (e.g. a `skill.md` describing how the
   sample was made) — they are not part of the queryable knowledge base.

### Step 2: Load the Question Bank

Read `questions_file`. Each entry has: an **ID**, a **use-case category**, the
**question text**, and a list of **expected key facts** used for scoring. Do
**not** pass expected facts to the answering agents.

### Step 3: Run the Benchmark (clean context)

For each sample, and for each question:

1. Invoke a `general-task-execution` sub-agent with a prompt of the form:

   > You are answering a single question using ONLY the knowledge base located
   > at `<resolved sample root>`. You may read any files under that directory and
   > nothing else — do not read parent directories, sibling samples, source
   > ARXML, or any validation files. If the knowledge base does not contain the
   > answer, say so explicitly. Be concise and factual; cite the file(s) you used.
   >
   > Question: `<question text>`

2. Capture the returned answer verbatim, plus which files the sub-agent reported
   reading and (if available) a rough sense of effort (files opened).

In `per-sample` mode, instead pass all questions to one sub-agent per sample with
instructions to answer each in order under the same read-only constraint. Prefer
`per-question` mode when the budget allows — it is the cleanest.

### Step 4: Score Each Answer

For each (sample, question), the orchestrator compares the answer to the
question's **expected key facts**:

- **Correct (✅)**: all key facts present and nothing contradicting them.
- **Partial (⚠️)**: some key facts present, or correct but incomplete.
- **Incorrect/Missing (❌)**: key facts wrong, or the agent could not answer.

Also note **navigation efficiency**: how many files the agent had to open to
answer (fewer is better — this is where an indexed sample should win).

### Step 5: Write the Timestamped Report

1. Compute a timestamp: `date +"%Y-%m-%d_%H%M%S"`.
2. Write the report to
   `<reports_dir>/validation-report_<timestamp>.md` (never overwrite a previous
   report — the timestamp keeps history).
3. Use the report template below. Include the per-sample × per-question score
   matrix, a summary score per sample, the full answers, and observations about
   navigation efficiency and structural strengths/weaknesses.

---

## Report Template

```markdown
# Knowledge Base Validation Report

| Field | Value |
|-------|-------|
| Generated | <YYYY-MM-DD HH:MM:SS> |
| Timestamp tag | <YYYY-MM-DD_HHMMSS> |
| Samples evaluated | <n> (<names>) |
| Questions | <n> |
| Mode | per-question / per-sample |
| Question bank | knowledge_base/validation/questions.md |

## Score Matrix

| ID | Category | <sample_1> | <sample_2> | <sample_3> |
|----|----------|:----------:|:----------:|:----------:|
| Q01 | inventory | ✅ | ✅ | ✅ |
| ... | ... | ... | ... | ... |
| **Score** | | **x/n** | **x/n** | **x/n** |

Legend: ✅ correct · ⚠️ partial · ❌ incorrect/missing

## Summary

| Sample | Correct | Partial | Incorrect | Avg files opened | Notes |
|--------|--------:|--------:|----------:|-----------------:|-------|
| <sample> | | | | | |

<1–2 paragraphs: which layout answered best, where each struggled, and whether
the indexed layout reduced navigation effort for blast-radius questions.>

## Detailed Results

### Q01 — <question text>
**Category:** <category> · **Use case:** <use case>
**Expected key facts:** <short list>

| Sample | Score | Files opened | Answer |
|--------|:-----:|--------------|--------|
| <sample_1> | ✅ | components/Door.md | <verbatim answer, trimmed> |
| <sample_2> | ⚠️ | ... | ... |
| <sample_3> | ✅ | _index/dependency-graph.md | ... |

### Q02 — ...
...
```

---

## Rules

- **Read-only.** This skill never modifies any sample or source file. It only
  writes the report under `reports_dir`.
- **Isolation is non-negotiable.** A sample is only ever judged on its own files,
  in a clean context. Never let one sample's content or a prior answer influence
  another.
- **Never reveal expected answers to the answering agent.** Scoring is the
  orchestrator's job.
- **Always timestamp the report** and never overwrite an existing one — reports
  accumulate as a history of how the samples evolve.
- Keep recorded answers verbatim (trim only for length) so the report is auditable.
- If a sample is missing a knowledge-base root (only a generator file), record it
  as "not evaluable" rather than failing the whole run.
- Report navigation effort (files opened) alongside correctness — for this
  product, *fast* correct answers matter as much as correct ones.
