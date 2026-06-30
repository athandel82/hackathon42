# CombinedStatus

## Interface Information

| Field | Value |
|-------|-------|
| Name | CombinedStatus |
| Type | SENDER-RECEIVER-INTERFACE |
| UUID | ac79088e-db77-300d-b6bf-72580349ffb0 |
| Package | /Demo/Interfaces |
| Is Service | false |
| Source File | EcuExtract.arxml |

## Description

Sender-Receiver interface aggregating the lock and open status of both left and right doors into a single interface. This is the externally-visible status output of the EDC composition.

## Data Elements

| Element Name | Type | Implementation Policy | UUID |
|--------------|------|-----------------------|------|
| LockedLeft | /ArcCore/Platform/ImplementationDataTypes/boolean | STANDARD | a4fbcfbd-24e9-3222-9fbe-be25ac6e9740 |
| OpenLeft | /ArcCore/Platform/ImplementationDataTypes/boolean | STANDARD | 080e1423-0f5b-3f2f-83e8-25b9c81d65ef |
| LockedRight | /ArcCore/Platform/ImplementationDataTypes/boolean | STANDARD | 3c81145a-4f69-3436-8b28-a9edf9359d90 |
| OpenRight | /ArcCore/Platform/ImplementationDataTypes/boolean | STANDARD | 6f5961a2-003e-3845-8369-62d2f365fa8c |

## Usage

| Component | Port Name | Direction |
|-----------|-----------|-----------|
| DoorControl | CombinedStatus | Provided (writes all 4 elements) |
| EDC | CombinedStatus | Provided (delegated from DoorControl) |

## System Signal Mapping

| Data Element | System Signal |
|--------------|---------------|
| LockedLeft | /Demo/EDC/SystemSignals/CombinedStatusLockedLeftSSig |
| OpenLeft | /Demo/EDC/SystemSignals/CombinedStatusOpenLeftSSig |
| LockedRight | /Demo/EDC/SystemSignals/CombinedStatusLockedRightSSig |
| OpenRight | /Demo/EDC/SystemSignals/CombinedStatusOpenRightSSig |
