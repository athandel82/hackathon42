# Door

## Component Information

| Field | Value |
|-------|-------|
| Name | Door |
| Type | APPLICATION-SW-COMPONENT-TYPE |
| UUID | 2dbc5fd9-e3c1-3151-a0e4-b723a660be32 |
| Package | /Demo/Door |
| Source File | EcuExtract.arxml |

## Description

Application software component representing a single physical door. Provides door status (locked/open state) and accepts lock commands. Two instances of this component are used in the EDC system (DoorLeft and DoorRight).

## Ports

### Provided Ports (P-PORT)

| Port Name | Interface | Interface Type | UUID |
|-----------|-----------|----------------|------|
| Command | /Demo/Interfaces/DoorCommands | CLIENT-SERVER-INTERFACE | 48d04d5b-cf28-3086-80a1-8712384b653f |
| Status | /Demo/Interfaces/DoorStatus | SENDER-RECEIVER-INTERFACE | 9dc49b58-a185-36d4-8594-1e564711dd28 |

### Required Ports (R-PORT)

_None_

## Internal Behavior

| Field | Value |
|-------|-------|
| Name | DoorInternals |
| UUID | bb6117d7-83a1-3462-b603-ee7ec68670c8 |
| Handle Termination | NO-SUPPORT |
| Multiple Instantiation | false |

## Events

| Event Name | Type | Trigger | Period | UUID |
|------------|------|---------|--------|------|
| Command_SetLock | OPERATION-INVOKED-EVENT | SetLocked (via Command/SetLock) | — | 7b360f21-6683-466d-b140-1c575170e137 |
| timingEvent_0_1 | TIMING-EVENT | DoorMain | 0.1s | 57cbf43a-2a8f-4509-91d8-c1a559dc4aa6 |

## Runnables

### DoorMain

| Field | Value |
|-------|-------|
| UUID | 63379bbf-877f-310e-adeb-86aa20deec24 |
| Symbol | DoorMain |
| Minimum Start Interval | 0.0 |
| Concurrent Invocation | false |

**Data Write Access:**

| Access Name | Port | Data Element |
|-------------|------|--------------|
| dataWriteAccess_DoorMain_Status_Locked | /Demo/Door/Door/Status | /Demo/Interfaces/DoorStatus/Locked |
| dataWriteAccess_DoorMain_Status_Open | /Demo/Door/Door/Status | /Demo/Interfaces/DoorStatus/Open |

### SetLocked

| Field | Value |
|-------|-------|
| UUID | 2a34834f-1c98-305e-ad9e-a063fd47f3ad |
| Symbol | SetLocked |
| Minimum Start Interval | 0.0 |
| Concurrent Invocation | false |

## Implementation

| Field | Value |
|-------|-------|
| Name | DoorImplementation |
| UUID | 0854a69e-6bbb-3735-80a1-2345b6c7942e |
| Programming Language | C |
| Vendor ID | 0 |
| Behavior Reference | /Demo/Door/Door/DoorInternals |

## Relationships

- **Provides** door status (Locked, Open) to consumers via the `Status` port
- **Receives** lock commands via the `Command` port (SetLock operation)
- **Used by** EDC composition as `DoorLeft` and `DoorRight` instances
