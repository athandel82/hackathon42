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

Client-server interface for commanding a door's lock state. The server is the
`Door` component; clients are the `DoorControl` left/right command ports.

## Data Elements (Sender-Receiver)

_None_

## Operations (Client-Server)

### SetLock

| Field | Value |
|-------|-------|
| UUID | a73320ad-51df-3501-92c1-2fc861753e9a |

**Arguments:**

| Argument Name | Type | Direction | UUID |
|---------------|------|-----------|------|
| Locked | [/ArcCore/Platform/ImplementationDataTypes/boolean](../platform/ImplementationDataTypes.md) | IN | c7c13e49-2905-3f35-a105-94268ffb4ba1 |

**Possible Errors:** _None_

## Usage (resolved from port-map / dependency-graph)

| Component | Port | Direction (P/R) |
|-----------|------|-----------------|
| Door | Command | P (server) |
| DoorControl | CommandsLeft | R (client) |
| DoorControl | CommandsRight | R (client) |

On `Door`, the `Command_SetLock` operation-invoked event triggers the `SetLocked`
runnable when `SetLock` is called. `DoorControl.Main` calls `SetLock` via two
synchronous server call points (left and right).
