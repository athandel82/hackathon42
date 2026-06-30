---
inclusion: manual
---

# Generate Minimal Baseline Design Documentation

## Purpose

Analyze an existing project (e.g. an embedded/ROS-based system such as
`input/autosar`) and generate a **minimal baseline design-documentation set** that
captures the current architecture so that a new feature (e.g. a WiFi module) can be
designed against accurate, traceable context.

The skill produces **exactly 8 Markdown documents** — no more, no less. No diagrams,
no PNG files, no summary/index/README scaffolding. The output is intentionally lean:
each document focuses on **interfaces and extension points**, not exhaustive internals.

## Parameters

- **input_project** (required): Path to the source project to analyze
  (e.g. `input/autosar`). All relevant source is read from here.
- **output_project** (required): Path where the documentation is written. Documents
  are placed under `<output_project>/requirements/` (e.g. `output/requirements`).

## Procedure

### Step 1: Analyze the Input Project

1. Recursively inspect `<input_project>`.
2. Identify the three architectural layers: **Hardware → Firmware → ROS Software**.
3. Locate integration points relevant to adding a new feature/module (e.g. WiFi):
   buses, packet pipelines, ROS packages, state machine, safety chain.
4. Collect concrete code snippets that show where new modules plug in.

### Step 2: Generate the 8 Documents

Write all documents into `<output_project>/requirements/`. **Generate all 8 in a
single batch using bash commands.** Create ONLY these files:

1. **`01-System-Architecture.md`** — Three-layer system overview
   (Hardware → Firmware → ROS Software), component relationships, data flow between
   layers, and the main subsystem boundaries.
2. **`02-System-Requirements.md`** — Current functional requirements
   (FR-1 through FR-8), non-functional requirements, and safety requirements. Use a
   numbered requirement format (`FR-X.Y`) so new requirements can be appended.
3. **`03-Hardware-Architecture.md`** — Mainboard components, microcontroller specs
   (RP2040 dual-core), pin assignments, communication buses (UART, SPI, I2C), and
   available GPIO for expansion.
4. **`05-Firmware-Architecture.md`** — Dual-core firmware design, main loop
   structure, packet handling pipeline, and module integration pattern. Show how new
   modules (like WiFi) would plug into the existing architecture.
5. **`06-Communication-Protocols.md`** — Current protocols (serial between firmware
   and ROS, ROS topics/services), message formats, and data flow. Include the pattern
   for adding new communication channels.
6. **`07-Software-Architecture.md`** — ROS node structure, package layout,
   topic/service interfaces, and launch file organization. Document how to add a new
   ROS package to the workspace.
7. **`09-Safety-Systems.md`** — Emergency stop chain, safety state machine, response
   time requirements, and watchdog mechanisms. Document the current safety
   architecture that new features must integrate with.
8. **`10-State-Machine-Design.md`** — Mower operational states (idle, mowing, docking,
   error), state transitions, and command handling. Document how start/stop commands
   currently flow through the system.

> Note the intentional numbering gaps (04 and 08 are omitted). Use the exact filenames
> above.

### Step 3: Verify Output

1. Confirm exactly 8 `.md` files exist under `<output_project>/requirements/`.
2. Confirm no PNG/diagram or excluded-topic files were created.

## Requirements for Each Document

- **Target 50–200 lines** — concise but complete for the new-feature (WiFi) context.
  The 200-line figure is a **soft target, not a hard limit**. If a few documents end
  up slightly over 200 lines, that is acceptable — leave them as-is.
- Include **relevant code snippets from source** showing integration points.
- Use a **consistent heading structure**: `##` for sections, `###` for subsections.
- Add **cross-references between documents** where relevant.
- Focus on **interfaces and extension points**, not exhaustive internals.

## Rules

- Generate **ONLY** the 8 documents listed above.
- Do **NOT** generate: PNG diagrams, Executive Summary, README, Document Index,
  Quick Reference, Hardware Interfaces, Power Management, Configuration Management,
  User Interface, or Sensor Subsystems documents.
- Generate all 8 documents in a **single batch using bash commands**.
- After generating, do **NOT** regenerate, recreate, or trim any document solely
  because it is slightly over the 200-line target. Once a document is created and meets
  the content requirements, **leave it in place**.
