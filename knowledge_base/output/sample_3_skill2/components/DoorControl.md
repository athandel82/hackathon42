# DoorControl

## Impact Tags

- **type:** APPLICATION-SW-COMPONENT-TYPE
- **safety-relevant:** unknown (no ASIL tagging present in the extract)
- **network-connected:** yes — produces `CombinedStatus`, mapped to all four `CombinedStatus*` system signals / I-PDUs
- **shared-implementation:** No (`DoorControlImplementation` used only by the single `Control` instance)
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

## Description

Central control logic. Reads the status of the left and right doors, aggregates
them into a `CombinedStatus`, issues lock commands to both doors, and drives an
LED through the IoHwAb digital write service.

## Ports

### Provided Ports (P-PORT)

| Port Name | Interface | Interface Type | UUID |
|-----------|-----------|----------------|------|
| CombinedStatus | [/Demo/Interfaces/CombinedStatus](../interfaces/CombinedStatus.md) | SENDER-RECEIVER | 5a63577a-a4d8-342f-8daf-d7cf49be95b3 |

### Required Ports (R-PORT)

| Port Name | Interface | Interface Type | UUID |
|-----------|-----------|----------------|------|
| StatusLeft | [/Demo/Interfaces/DoorStatus](../interfaces/DoorStatus.md) | SENDER-RECEIVER | 3179e3a7-1b49-3950-86db-d5c615049fb4 |
| StatusRight | [/Demo/Interfaces/DoorStatus](../interfaces/DoorStatus.md) | SENDER-RECEIVER | 6f3c8fac-0a52-381b-a69a-9387a3306235 |
| CommandsLeft | [/Demo/Interfaces/DoorCommands](../interfaces/DoorCommands.md) | CLIENT-SERVER | f4d8a3f8-863b-350a-a7b3-58e627e2e373 |
| CommandsRight | [/Demo/Interfaces/DoorCommands](../interfaces/DoorCommands.md) | CLIENT-SERVER | f5508438-caf6-31e3-9dd4-dbeb1dc46417 |
| Led | [/Demo/Services/IoHwAb/DigitalServiceWrite](../interfaces/DigitalServiceWrite.md) | CLIENT-SERVER | 44652102-e3c2-3674-a07b-5b8a3294a3de |

## Internal Behavior

| Field | Value |
|-------|-------|
| Name | DoorControlInternals |
| UUID | b88b3e24-7769-3458-82de-ab6db1ba97b8 |
| Handle Termination | NO-SUPPORT |
| Multiple Instantiation | false |

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

**Data Read Access:**

| Access Name | Port | Data Element |
|-------------|------|--------------|
| dataReadAccess_Main_StatusLeft_Locked | StatusLeft | /Demo/Interfaces/DoorStatus/Locked |
| dataReadAccess_Main_StatusLeft_Open | StatusLeft | /Demo/Interfaces/DoorStatus/Open |
| dataReadAccess_Main_StatusRight_Locked | StatusRight | /Demo/Interfaces/DoorStatus/Locked |
| dataReadAccess_Main_StatusRight_Open | StatusRight | /Demo/Interfaces/DoorStatus/Open |

**Data Write Access:**

| Access Name | Port | Data Element |
|-------------|------|--------------|
| dataWriteAccess_Main_CombinedStatus_LockedLeft | CombinedStatus | /Demo/Interfaces/CombinedStatus/LockedLeft |
| dataWriteAccess_Main_CombinedStatus_OpenLeft | CombinedStatus | /Demo/Interfaces/CombinedStatus/OpenLeft |
| dataWriteAccess_Main_CombinedStatus_LockedRight | CombinedStatus | /Demo/Interfaces/CombinedStatus/LockedRight |
| dataWriteAccess_Main_CombinedStatus_OpenRight | CombinedStatus | /Demo/Interfaces/CombinedStatus/OpenRight |

**Server Call Points:**

| Call Point Name | Port | Operation | Timeout |
|-----------------|------|-----------|---------|
| serverCallPoint_Main_CommandsLeft_SetLock | CommandsLeft | [DoorCommands/SetLock](../interfaces/DoorCommands.md) | 0.0 |
| serverCallPoint_Main_CommandsRight_SetLock | CommandsRight | [DoorCommands/SetLock](../interfaces/DoorCommands.md) | 0.0 |
| serverCallPoint_Main_Led_Write | Led | [DigitalServiceWrite/Write](../interfaces/DigitalServiceWrite.md) | 0.0 |

## Implementation

| Field | Value |
|-------|-------|
| Name | DoorControlImplementation |
| UUID | 219f3a51-31ab-3858-87ed-16e0299c4f28 |
| Programming Language | C |
| Vendor ID | 0 |
| Behavior Reference | /Demo/DoorControl/DoorControl/DoorControlInternals |

## Dependencies

### Provides To

| Consumer Component | Via Port | Interface | Data Elements / Operations |
|--------------------|----------|-----------|----------------------------|
| EDC (delegated to network) | CombinedStatus | CombinedStatus | LockedLeft, OpenLeft, LockedRight, OpenRight |

### Requires From

| Provider Component | Via Port | Interface | Data Elements / Operations |
|--------------------|----------|-----------|----------------------------|
| Door (DoorLeft) | StatusLeft | DoorStatus | Locked, Open |
| Door (DoorRight) | StatusRight | DoorStatus | Locked, Open |
| Door (DoorLeft) | CommandsLeft | DoorCommands | SetLock |
| Door (DoorRight) | CommandsRight | DoorCommands | SetLock |
| IoHwAb (IO) | Led | DigitalServiceWrite | Write |

### Calls (client → server)

| Target Component | Via Port | Operation |
|------------------|----------|-----------|
| Door (DoorLeft) | CommandsLeft | SetLock |
| Door (DoorRight) | CommandsRight | SetLock |
| IoHwAb (IO) | Led | Write |

### Called By (server ← client)

_None_

### Participates In Signal Chains

| Chain | Role |
|-------|------|
| [Chain 1–4: CombinedStatus*](../_index/signal-chains.md) | relay / aggregator (reads Door status, writes CombinedStatus) |
| [Command Path](../_index/signal-chains.md) | client (calls Door.SetLock) |
| [Actuation Path](../_index/signal-chains.md) | client (calls IoHwAb.Write) |
