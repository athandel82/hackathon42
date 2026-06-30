---
inclusion: manual
---

# Generate AUTOSAR ARXML Knowledge Base

## Purpose

Parse AUTOSAR ARXML files from a given repository path and generate a structured knowledge base as a set of Markdown files — one file per component, interface, platform package, and system element.

## Parameters

- **repo_path** (required): Path to the directory containing source`.arxml` files to process. All `.arxml` files in this directory will be parsed.
- **output_path** (required): Path where the knowledge base output should be written.

## Procedure

### Step 1: Discover ARXML Files

1. List all `.arxml` files in the provided `repo_path` directory.
2. Read each file and identify the AUTOSAR schema version from the root `<AUTOSAR>` element.

### Step 2: Extract and Classify Elements

Parse each ARXML file and classify elements into the following categories:

- **Components** — Any of these SWC types:
  - `APPLICATION-SW-COMPONENT-TYPE`
  - `SERVICE-SW-COMPONENT-TYPE`
  - `COMPOSITION-SW-COMPONENT-TYPE`
  - `SENSOR-ACTUATOR-SW-COMPONENT-TYPE`
  - `COMPLEX-DEVICE-DRIVER-SW-COMPONENT-TYPE`
  - `ECU-ABSTRACTION-SW-COMPONENT-TYPE`
- **Interfaces** — Any of:
  - `SENDER-RECEIVER-INTERFACE`
  - `CLIENT-SERVER-INTERFACE`
  - `MODE-SWITCH-INTERFACE`
  - `TRIGGER-INTERFACE`
- **Platform Types** — Packages containing:
  - `SW-BASE-TYPE` elements → group into BaseTypes
  - `IMPLEMENTATION-DATA-TYPE` elements → group into ImplementationDataTypes
  - `COMPU-METHOD` elements → include with related types
- **System** — `SYSTEM` elements (especially ECU_EXTRACT category)

### Step 3: Generate Output Structure

Create the following directory structure under `output_path`:

```
<output_path>/
├── README.md
├── components/
│   └── <ComponentName>.md        (one per SW component)
├── interfaces/
│   └── <InterfaceName>.md        (one per interface)
├── platform/
│   ├── BaseTypes.md              (all base types in one file)
│   └── ImplementationDataTypes.md (all impl types in one file)
└── system/
    └── <SystemName>.md           (one per system element)
```

### Step 4: Generate Component Markdown Files

For each SW component, create a markdown file with this structure:

```markdown
# <ComponentName>

## Component Information

| Field | Value |
|-------|-------|
| Name | <SHORT-NAME> |
| Type | <element tag, e.g. APPLICATION-SW-COMPONENT-TYPE> |
| UUID | <UUID attribute> |
| Package | <full AUTOSAR path> |
| Source File | <originating .arxml filename> |

## Description

<If available from DESC element, otherwise describe based on context>

## Ports

### Provided Ports (P-PORT)

| Port Name | Interface | Interface Type | UUID |
|-----------|-----------|----------------|------|
| ... | ... | ... | ... |

### Required Ports (R-PORT)

| Port Name | Interface | Interface Type | UUID |
|-----------|-----------|----------------|------|
| ... | ... | ... | ... |

## Internal Behavior

| Field | Value |
|-------|-------|
| Name | <behavior SHORT-NAME> |
| UUID | <UUID> |
| Handle Termination | <value> |
| Multiple Instantiation | <true/false> |

## Events

| Event Name | Type | Trigger | Period | UUID |
|------------|------|---------|--------|------|
| ... | ... | ... | ... | ... |

## Runnables

### <RunnableName>

| Field | Value |
|-------|-------|
| UUID | ... |
| Symbol | ... |
| Minimum Start Interval | ... |
| Concurrent Invocation | ... |

**Data Read Access:** (if any)

| Access Name | Port | Data Element |
|-------------|------|--------------|
| ... | ... | ... |

**Data Write Access:** (if any)

| Access Name | Port | Data Element |
|-------------|------|--------------|
| ... | ... | ... |

**Server Call Points:** (if any)

| Call Point Name | Port | Operation | Timeout |
|-----------------|------|-----------|---------|
| ... | ... | ... | ... |

## Implementation

| Field | Value |
|-------|-------|
| Name | <SWC-IMPLEMENTATION SHORT-NAME> |
| UUID | ... |
| Programming Language | ... |
| Vendor ID | ... |
| Behavior Reference | ... |

## Relationships

- Bullet list of relationships to other components
```

For **COMPOSITION-SW-COMPONENT-TYPE**, add these additional sections:

```markdown
## Internal Components

| Instance Name | Component Type | Type Reference | UUID |
|---------------|----------------|----------------|------|
| ... | ... | ... | ... |

## Assembly Connectors

| Connector Name | Provider (Component.Port) | Requester (Component.Port) | UUID |
|----------------|---------------------------|----------------------------|------|
| ... | ... | ... | ... |

## Delegation Connectors

| Connector Name | Inner (Component.Port) | Outer Port | UUID |
|----------------|------------------------|------------|------|
| ... | ... | ... | ... |
```

### Step 5: Generate Interface Markdown Files

For each interface, create a markdown file:

```markdown
# <InterfaceName>

## Interface Information

| Field | Value |
|-------|-------|
| Name | <SHORT-NAME> |
| Type | <SENDER-RECEIVER-INTERFACE or CLIENT-SERVER-INTERFACE etc.> |
| UUID | ... |
| Package | <full path> |
| Is Service | <true/false> |
| Source File | ... |

## Description

<Describe the interface purpose>

## Data Elements (for Sender-Receiver)

| Element Name | Type | Implementation Policy | UUID |
|--------------|------|-----------------------|------|
| ... | ... | ... | ... |

## Operations (for Client-Server)

### <OperationName>

| Field | Value |
|-------|-------|
| UUID | ... |

**Arguments:**

| Argument Name | Type | Direction | UUID |
|---------------|------|-----------|------|
| ... | ... | ... | ... |

**Possible Errors:** (if any)

| Error Name | Error Code | UUID |
|------------|------------|------|
| ... | ... | ... |

## Usage

| Component | Port Name | Direction |
|-----------|-----------|-----------|
| ... | ... | ... |
```

### Step 6: Generate Platform Type Files

Create `platform/BaseTypes.md`:

```markdown
# Platform Base Types

## Package Information

| Field | Value |
|-------|-------|
| Package | <path> |
| Category | BLUEPRINT |
| Source File | ... |
| AUTOSAR Schema | ... |

## Base Types

| Name | Size (bits) | Encoding | Native Declaration | Description |
|------|-------------|----------|-------------------|-------------|
| ... | ... | ... | ... | ... |
```

Create `platform/ImplementationDataTypes.md`:

```markdown
# Implementation Data Types

## Package Information
...

## Value Types

| Name | Category | Base Type Reference | Type Emitter |
|------|----------|---------------------|--------------|
| ... | ... | ... | ... |

## Pointer Types

| Name | Category | Target Type | Target Category | Const |
|------|----------|-------------|-----------------|-------|
| ... | ... | ... | ... | ... |

## Computation Methods

### <name>
| Internal Value | Physical Value |
|----------------|----------------|
| ... | ... |
```

### Step 7: Generate System Files

For SYSTEM elements (ECU_EXTRACT), create:

```markdown
# <SystemName>

## System Information

| Field | Value |
|-------|-------|
| Name | ... |
| Type | SYSTEM |
| Category | ECU_EXTRACT |
| UUID | ... |
| Package | ... |
| Source File | ... |

## Root Software Composition
...

## Implementation Mappings

| Mapping Name | Component Instance | Implementation | UUID |
|--------------|-------------------|----------------|------|
| ... | ... | ... | ... |

## Signal Mappings
...

## Communication (I-Signals and I-PDUs)
...
```

### Step 8: Generate README

Create a `README.md` at the output root documenting:

1. Overview of the system described by the ARXML files
2. Source files table (filename + description)
3. Generation details (generated by, date, method, input/output format)
4. The prompt used to trigger generation
5. Directory structure listing
6. Description of how the knowledge base was generated

## Rules

- One markdown file per component/interface/system element
- Platform types are grouped (one file for base types, one for implementation data types)
- Preserve all UUIDs and AUTOSAR path references for traceability
- Use tables for structured data, bullet lists for relationships
- Include architecture diagrams (text-based) for composition components when possible
- Cross-reference between files using AUTOSAR paths
- If a section has no data (e.g., no required ports), write "_None_"
- Sort elements within tables alphabetically by name where practical
