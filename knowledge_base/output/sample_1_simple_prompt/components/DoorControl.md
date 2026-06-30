# DoorControl

## Component Information

| Field | Value |
|-------|-------|
| Name | DoorControl |
| Type | APPLICATION-SW-COMPONENT-TYPE |
| UUID | 01ed669d-6d02-35c0-9433-9b2acdd49751 |
| Package | /Demo/DoorControl |
| Source File | EcuExtract.arxml |

## Ports

### Provided Ports (P-PORT)

| Port Name | Interface | Interface Type | UUID |
|-----------|-----------|----------------|------|
| CombinedStatus | /Demo/Interfaces/CombinedStatus | SENDER-RECEIVER-INTERFACE | 5a63577a-a4d8-342f-8daf-d7cf49be95b3 |

### Required Ports (R-PORT)

| Port Name | Interface | Interface Type | UUID |
|-----------|-----------|----------------|------|
| StatusLeft | /Demo/Interfaces/DoorStatus | SENDER-RECEIVER-INTERFACE | 3179e3a7-1b49-3950-86db-d5c615049fb4 |
| StatusRight | /Demo/Interfaces/DoorStatus | SENDER-RECEIVER-INTERFACE | 6f3c8fac-0a52-381b-a69a-9387a3306235 |
| CommandsLeft | /Demo/Interfaces/DoorCommands | CLIENT-SERVER-INTERFACE | f4d8a3f8-863b-350a-a7b3-58e627e2e373 |
| CommandsRight | /Demo/Interfaces/DoorCommands | CLIENT-SERVER-INTERFACE | f5508438-caf6-31e3-9dd4-dbeb1dc46417 |
| Led | /Demo/Services/IoHwAb/DigitalServiceWrite | CLIENT-SERVER-INTERFACE | 44652102-e3c2-3674-a07b-5b8a3294a3de |

## Internal Behavior

| Field | Value |
|-------|-------|
| Name | DoorControlInternals |
| UUID | b88b3e24-7769-3458-82de-ab6db1ba97b8 |
| Handle Termination | NO-SUPPORT |
| Multiple Instantiation | false |

## Events

| Event Name | Type | Trigger | Period | UUID |
|------------|------|---------|--------|------|
| timingEvent_0_1 | TIMING-EVENT | Main | 0.1s | b4ece841-5f77-424f-ad60-91091aa4c7f8 |

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
| dataReadAccess_Main_StatusLeft_Locked | /Demo/DoorControl/DoorControl/StatusLeft | /Demo/Interfaces/DoorStatus/Locked |
| dataReadAccess_Main_StatusLeft_Open | /Demo/DoorControl/DoorControl/StatusLeft | /Demo/Interfaces/DoorStatus/Open |
| dataReadAccess_Main_StatusRight_Locked | /Demo/DoorControl/DoorControl/StatusRight | /Demo/Interfaces/DoorStatus/Locked |
| dataReadAccess_Main_StatusRight_Open | /Demo/DoorControl/DoorControl/StatusRight | /Demo/Interfaces/DoorStatus/Open |

**Data Write Access:**

| Access Name | Port | Data Element |
|-------------|------|--------------|
| dataWriteAccess_Main_CombinedStatus_LockedLeft | /Demo/DoorControl/DoorControl/CombinedStatus | /Demo/Interfaces/CombinedStatus/LockedLeft |
| dataWriteAccess_Main_CombinedStatus_OpenLeft | /Demo/DoorControl/DoorControl/CombinedStatus | /Demo/Interfaces/CombinedStatus/OpenLeft |
| dataWriteAccess_Main_CombinedStatus_LockedRight | /Demo/DoorControl/DoorControl/CombinedStatus | /Demo/Interfaces/CombinedStatus/LockedRight |
| dataWriteAccess_Main_CombinedStatus_OpenRight | /Demo/DoorControl/DoorControl/CombinedStatus | /Demo/Interfaces/CombinedStatus/OpenRight |

**Server Call Points:**

| Call Point Name | Port | Operation | Timeout |
|-----------------|------|-----------|---------|
| serverCallPoint_Main_CommandsLeft_SetLock | CommandsLeft | /Demo/Interfaces/DoorCommands/SetLock | 0.0 |
| serverCallPoint_Main_CommandsRight_SetLock | CommandsRight | /Demo/Interfaces/DoorCommands/SetLock | 0.0 |
| serverCallPoint_Main_Led_Write | Led | /Demo/Services/IoHwAb/DigitalServiceWrite/Write | 0.0 |

## Implementation

| Field | Value |
|-------|-------|
| Name | DoorControlImplementation |
| UUID | 219f3a51-31ab-3858-87ed-16e0299c4f28 |
| Programming Language | C |
| Vendor ID | 0 |
| Behavior Reference | /Demo/DoorControl/DoorControl/DoorControlInternals |

## Relationships

- **Reads** door status from left and right Door components (Locked, Open)
- **Writes** combined status (LockedLeft, OpenLeft, LockedRight, OpenRight) via CombinedStatus port
- **Calls** SetLock on both left and right doors via CommandsLeft / CommandsRight
- **Calls** Write on LED via Led port (IoHwAb DigitalServiceWrite)
- **Used by** EDC composition as `Control` instance
