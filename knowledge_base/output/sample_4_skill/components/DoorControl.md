# DoorControl

## Impact Tags

- **type:** APPLICATION-SW-COMPONENT-TYPE
- **safety-relevant:** unknown (no ASIL tagging present in the extract)
- **network-connected:** yes — aggregates door state into `CombinedStatus`, which feeds all four `CombinedStatus*` system signals
- **shared-implementation:** No (`DoorControlImplementation`, single instance `Control`)
- **composition-parent:** EDC (as instance Control)
- **signal-producer:** CombinedStatusLockedLeftSSig, CombinedStatusOpenLeftSSig, CombinedStatusLockedRightSSig, CombinedStatusOpenRightSSig
- **leaf:** no (requires Door and IoHwAb)

## Component Information

| Field | Value |
|-------|-------|
| Name | DoorControl |
| Type | APPLICATION-SW-COMPONENT-TYPE |
| UUID | 01ed669d-6d02-35c0-9433-9b2acdd49751 |
| Package | /Demo/DoorControl |
| Source File | EcuExtract.arxml |
| Source Reference | EcuExtract.arxml:419 (/Demo/DoorControl/DoorControl) |

## Description

Central control component. Reads the status of the left and right doors, computes
an aggregated `CombinedStatus`, issues `SetLock` commands to each door, and drives
the LED via the IoHwAb service.

## Ports

### Provided Ports (P-PORT)

| Port Name | Interface | Interface Type | UUID | Source Ref |
|-----------|-----------|----------------|------|------------|
| CombinedStatus | [/Demo/Interfaces/CombinedStatus](../interfaces/CombinedStatus.md) | SENDER-RECEIVER | 5a63577a-a4d8-342f-8daf-d7cf49be95b3 | EcuExtract.arxml:442 |

### Required Ports (R-PORT)

| Port Name | Interface | Interface Type | UUID | Source Ref |
|-----------|-----------|----------------|------|------------|
| StatusLeft | [/Demo/Interfaces/DoorStatus](../interfaces/DoorStatus.md) | SENDER-RECEIVER | 3179e3a7-1b49-3950-86db-d5c615049fb4 | EcuExtract.arxml:422 |
| StatusRight | [/Demo/Interfaces/DoorStatus](../interfaces/DoorStatus.md) | SENDER-RECEIVER | 6f3c8fac-0a52-381b-a69a-9387a3306235 | EcuExtract.arxml:426 |
| CommandsLeft | [/Demo/Interfaces/DoorCommands](../interfaces/DoorCommands.md) | CLIENT-SERVER | f4d8a3f8-863b-350a-a7b3-58e627e2e373 | EcuExtract.arxml:430 |
| CommandsRight | [/Demo/Interfaces/DoorCommands](../interfaces/DoorCommands.md) | CLIENT-SERVER | f5508438-caf6-31e3-9dd4-dbeb1dc46417 | EcuExtract.arxml:434 |
| Led | [/Demo/Services/IoHwAb/DigitalServiceWrite](../interfaces/DigitalServiceWrite.md) | CLIENT-SERVER | 44652102-e3c2-3674-a07b-5b8a3294a3de | EcuExtract.arxml:438 |

## Internal Behavior

| Field | Value |
|-------|-------|
| Name | DoorControlInternals |
| UUID | b88b3e24-7769-3458-82de-ab6db1ba97b8 |
| Handle Termination | NO-SUPPORT |
| Multiple Instantiation | false |
| Source Reference | EcuExtract.arxml:448 |

## Events

| Event Name | Type | Trigger (Runnable) | Period | UUID |
|------------|------|--------------------|--------|------|
| timingEvent_0_1 | TIMING-EVENT | Main | 0.1 | b4ece841-5f77-424f-ad60-91091aa4c7f8 |

## Runnables

### Main

| Field | Value |
|-------|-------|
| UUID | 87d18679-251c-3c5e-87b7-259b28927aad |
| Symbol | Main |
| Minimum Start Interval | 0.0 |
| Concurrent Invocation | false |
| Source Reference | EcuExtract.arxml:459 |

**Data Read Access:**

| Access Name | Port | Data Element |
|-------------|------|--------------|
| dataReadAccess_Main_StatusLeft_Locked | StatusLeft | [/Demo/Interfaces/DoorStatus/Locked](../interfaces/DoorStatus.md) |
| dataReadAccess_Main_StatusLeft_Open | StatusLeft | [/Demo/Interfaces/DoorStatus/Open](../interfaces/DoorStatus.md) |
| dataReadAccess_Main_StatusRight_Locked | StatusRight | [/Demo/Interfaces/DoorStatus/Locked](../interfaces/DoorStatus.md) |
| dataReadAccess_Main_StatusRight_Open | StatusRight | [/Demo/Interfaces/DoorStatus/Open](../interfaces/DoorStatus.md) |

**Data Write Access:**

| Access Name | Port | Data Element |
|-------------|------|--------------|
| dataWriteAccess_Main_CombinedStatus_LockedLeft | CombinedStatus | [/Demo/Interfaces/CombinedStatus/LockedLeft](../interfaces/CombinedStatus.md) |
| dataWriteAccess_Main_CombinedStatus_OpenLeft | CombinedStatus | [/Demo/Interfaces/CombinedStatus/OpenLeft](../interfaces/CombinedStatus.md) |
| dataWriteAccess_Main_CombinedStatus_LockedRight | CombinedStatus | [/Demo/Interfaces/CombinedStatus/LockedRight](../interfaces/CombinedStatus.md) |
| dataWriteAccess_Main_CombinedStatus_OpenRight | CombinedStatus | [/Demo/Interfaces/CombinedStatus/OpenRight](../interfaces/CombinedStatus.md) |

**Server Call Points:**

| Call Point | Port | Target Operation |
|------------|------|------------------|
| serverCallPoint_Main_CommandsLeft_SetLock | CommandsLeft | [/Demo/Interfaces/DoorCommands/SetLock](../interfaces/DoorCommands.md) |
| serverCallPoint_Main_CommandsRight_SetLock | CommandsRight | [/Demo/Interfaces/DoorCommands/SetLock](../interfaces/DoorCommands.md) |
| serverCallPoint_Main_Led_Write | Led | [/Demo/Services/IoHwAb/DigitalServiceWrite/Write](../interfaces/DigitalServiceWrite.md) |

## Implementation

| Field | Value |
|-------|-------|
| Name | DoorControlImplementation |
| UUID | 219f3a51-31ab-3858-87ed-16e0299c4f28 |
| Programming Language | C |
| Vendor ID | 0 |
| Behavior Reference | /Demo/DoorControl/DoorControl/DoorControlInternals |
| Source Reference | EcuExtract.arxml:572 |

## Dependencies

### Provides To

| Consumer Component | Via Port | Interface | Data Elements / Operations |
| --- | --- | --- | --- |
| EDC (delegation → system) | CombinedStatus | CombinedStatus | LockedLeft, OpenLeft, LockedRight, OpenRight |

### Requires From

| Provider Component | Via Port | Interface | Data Elements / Operations |
| --- | --- | --- | --- |
| Door | StatusLeft, StatusRight | DoorStatus | Locked, Open |
| Door | CommandsLeft, CommandsRight | DoorCommands | SetLock |
| IoHwAb | Led | DigitalServiceWrite | Write |

### Calls (client → server)

| Server Component | Via Port | Operation |
| --- | --- | --- |
| Door | CommandsLeft / CommandsRight | SetLock |
| IoHwAb | Led | Write |

### Called By (server ← client)

_None_

### Participates In Signal Chains

| Chain | Role |
| --- | --- |
| [Chain 1–4: CombinedStatus*](../_index/signal-chains.md) | aggregator (reads DoorStatus, writes CombinedStatus) |
| [Command Path](../_index/signal-chains.md) | client (SetLock server calls) |
| [Actuation Path](../_index/signal-chains.md) | client (LED Write server call) |
