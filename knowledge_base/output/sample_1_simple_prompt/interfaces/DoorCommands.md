# DoorCommands

## Interface Information

| Field | Value |
|-------|-------|
| Name | DoorCommands |
| Type | CLIENT-SERVER-INTERFACE |
| UUID | 0fc0e7ac-fbe4-3814-94c3-69077a1f35f3 |
| Package | /Demo/Interfaces |
| Is Service | false |
| Source File | EcuExtract.arxml |

## Description

Client-Server interface for issuing commands to a door. Provides the SetLock operation to lock or unlock a door.

## Operations

### SetLock

| Field | Value |
|-------|-------|
| UUID | a73320ad-51df-3501-92c1-2fc861753e9a |

**Arguments:**

| Argument Name | Type | Direction | UUID |
|---------------|------|-----------|------|
| Locked | /ArcCore/Platform/ImplementationDataTypes/boolean | IN | c7c13e49-2905-3f35-a105-94268ffb4ba1 |

## Usage

| Component | Port Name | Direction |
|-----------|-----------|-----------|
| Door | Command | Provided (server - handles SetLock) |
| DoorControl | CommandsLeft | Required (client - calls SetLock) |
| DoorControl | CommandsRight | Required (client - calls SetLock) |
