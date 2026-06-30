# Door

## Impact Tags

- **type:** APPLICATION-SW-COMPONENT-TYPE
- **safety-relevant:** unknown (no ASIL tagging present in the extract)
- **network-connected:** yes (its `Status` data ultimately reaches the `CombinedStatus*` I-PDUs via DoorControl)
- **shared-implementation:** yes — `DoorImplementation` is reused by both `DoorLeft` and `DoorRight` instances
- **composition-parent:** EDC (as instances DoorLeft, DoorRight)
- **signal-producer:** CombinedStatusLockedLeftSSig, CombinedStatusOpenLeftSSig, CombinedStatusLockedRightSSig, CombinedStatusOpenRightSSig (indirectly, via DoorControl)
- **leaf:** yes (no forward dependencies — provides only)

## Component Information

| Field | Value |
|-------|-------|
| Name | Door |
| Type | APPLICATION-SW-COMPONENT-TYPE |
| UUID | 2dbc5fd9-e3c1-3151-a0e4-b723a660be32 |
| Package | /Demo/Door |
| Source File | EcuExtract.arxml |
| Source Reference | EcuExtract.arxml:10 (/Demo/Door/Door) |

## Description

Represents a single physical door. Periodically publishes its lock/open status
and accepts a lock command. Instantiated twice (left and right) inside the EDC
composition.

## Ports

### Provided Ports (P-PORT)

| Port Name | Interface | Interface Type | UUID | Source Ref |
|-----------|-----------|----------------|------|------------|
| Status | [/Demo/Interfaces/DoorStatus](../interfaces/DoorStatus.md) | SENDER-RECEIVER | 9dc49b58-a185-36d4-8594-1e564711dd28 | EcuExtract.arxml:13 |
| Command | [/Demo/Interfaces/DoorCommands](../interfaces/DoorCommands.md) | CLIENT-SERVER | 48d04d5b-cf28-3086-80a1-8712384b653f | EcuExtract.arxml:17 |

### Required Ports (R-PORT)

_None_

## Internal Behavior

| Field | Value |
|-------|-------|
| Name | DoorInternals |
| UUID | bb6117d7-83a1-3462-b603-ee7ec68670c8 |
| Handle Termination | NO-SUPPORT |
| Multiple Instantiation | false |
| Source Reference | EcuExtract.arxml:23 |

## Events

| Event Name | Type | Trigger (Runnable) | Period | UUID |
|------------|------|--------------------|--------|------|
| timingEvent_0_1 | TIMING-EVENT | DoorMain | 0.1 | 57cbf43a-2a8f-4509-91d8-c1a559dc4aa6 |
| Command_SetLock | OPERATION-INVOKED-EVENT | SetLocked | — (on Command/SetLock invocation) | 7b360f21-6683-466d-b140-1c575170e137 |

## Runnables

### DoorMain

| Field | Value |
|-------|-------|
| UUID | 63379bbf-877f-310e-adeb-86aa20deec24 |
| Symbol | DoorMain |
| Minimum Start Interval | 0.0 |
| Concurrent Invocation | false |
| Source Reference | EcuExtract.arxml:42 |

**Data Write Access:**

| Access Name | Port | Data Element |
|-------------|------|--------------|
| dataWriteAccess_DoorMain_Status_Locked | Status | [/Demo/Interfaces/DoorStatus/Locked](../interfaces/DoorStatus.md) |
| dataWriteAccess_DoorMain_Status_Open | Status | [/Demo/Interfaces/DoorStatus/Open](../interfaces/DoorStatus.md) |

### SetLocked

| Field | Value |
|-------|-------|
| UUID | 2a34834f-1c98-305e-ad9e-a063fd47f3ad |
| Symbol | SetLocked |
| Minimum Start Interval | 0.0 |
| Concurrent Invocation | false |
| Source Reference | EcuExtract.arxml:68 |

Invoked by the `Command_SetLock` operation-invoked event when a client calls
[/Demo/Interfaces/DoorCommands/SetLock](../interfaces/DoorCommands.md) on the `Command` port.

## Implementation

| Field | Value |
|-------|-------|
| Name | DoorImplementation |
| UUID | 0854a69e-6bbb-3735-80a1-2345b6c7942e |
| Programming Language | C |
| Vendor ID | 0 |
| Behavior Reference | /Demo/Door/Door/DoorInternals |
| Source Reference | EcuExtract.arxml:79 |

## Dependencies

### Provides To

| Consumer Component | Via Port | Interface | Data Elements / Operations |
| --- | --- | --- | --- |
| DoorControl | Status → StatusLeft / StatusRight | DoorStatus | Locked, Open |
| DoorControl | Command → CommandsLeft / CommandsRight | DoorCommands | SetLock |

### Requires From

_None_

### Calls (client → server)

_None_

### Called By (server ← client)

| Caller Component | Via Port | Operation |
| --- | --- | --- |
| DoorControl | Command (CommandsLeft / CommandsRight) | SetLock |

### Participates In Signal Chains

| Chain | Role |
| --- | --- |
| [Chain 1: Combined Lock Status (Left)](../_index/signal-chains.md) | producer (DoorLeft) |
| [Chain 2: Combined Open Status (Left)](../_index/signal-chains.md) | producer (DoorLeft) |
| [Chain 3: Combined Lock Status (Right)](../_index/signal-chains.md) | producer (DoorRight) |
| [Chain 4: Combined Open Status (Right)](../_index/signal-chains.md) | producer (DoorRight) |
| [Command Path](../_index/signal-chains.md) | consumer/server (SetLocked runnable) |
