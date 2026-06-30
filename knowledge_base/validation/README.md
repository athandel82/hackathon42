# Knowledge Base Validation

A benchmark harness that measures **how well each generated knowledge-base
sample answers the questions the SDV tool actually needs to answer** — blast
radius, dependency tracing, signal flow, and de-contenting impact.

Every sample under `knowledge_base/output/` represents the **same** AUTOSAR
system (the Electronic Door Control demo) in a different structure. This harness
asks all of them the same questions, **in a clean context**, scores the answers
against known ground truth, and writes a **timestamped comparison report**.

## Contents

| File | Purpose |
|------|---------|
| `skill.md` | The validation skill — the procedure an agent follows to run the benchmark. Invoke it manually (`#` context). |
| `questions.md` | The benchmark question bank with expected key facts (ground truth) used for scoring. Covers inventory, ports, dependency, blast-radius, signal-flow, data-type, composition, reuse, and de-content use cases. |
| `reports/` | Timestamped validation reports. One file per run, named `validation-report_<YYYY-MM-DD_HHMMSS>.md`. Never overwritten. |

## How it works

1. **Discover** each sample under `knowledge_base/output/` and find its
   knowledge-base root (`components/`, `interfaces/`, `system/`, `_index/`).
2. **Ask** every question from `questions.md` against each sample using a
   **fresh sub-agent restricted to that one sample's files** — so each sample is
   judged purely on its own content, with no cross-contamination.
3. **Score** each answer (✅ correct / ⚠️ partial / ❌ incorrect) against the
   expected key facts, and note how many files the agent had to open.
4. **Write** a timestamped report comparing all samples side by side.

## Running it

In a Kiro chat, add the skill to context and ask to run it:

> Run the validation skill in `knowledge_base/validation/skill.md` against all
> samples and generate a report.

Defaults: samples from `knowledge_base/output`, questions from `questions.md`,
reports to `reports/`. See `skill.md` for parameters (`samples_dir`,
`questions_file`, `reports_dir`, `mode`).

## Why clean context matters

The samples differ only in structure, so the benchmark is really measuring
*which layout communicates the system best to an agent*. If one sample's content
leaked into another's evaluation, the comparison would be meaningless. Each
question is therefore answered in isolation, and the answering agent never sees
the expected answers — scoring is done separately by the orchestrator.
