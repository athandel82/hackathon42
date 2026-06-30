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
| Source Reference | EcuExtract.arxml:348 (/Demo/Interfaces/DoorCommands) |

## Description

Client-server interface used to command a door lock. The server is `Door.Command`
(handled by the `SetLocked` runnable); the client is `DoorControl`, calling once
per door via `CommandsLeft` / `CommandsRight`.

## Data Elements (Sender-Receiver)

_None_

## Operations (Client-Server)

| Operation | Arguments | UUID | Source Ref |
|-----------|-----------|------|------------|
| SetLock | Locked: [/ArcCore/Platform/ImplementationDataTypes/boolean](../platform/ImplementationDataTypes.md) (IN) | a73320ad-51df-3501-92c1-2fc861753e9a | EcuExtract.arxml:352 |

## Usage (resolved from port-map / dependency-graph)

| Component | Port | Direction (P/R) |
|-----------|------|-----------------|
| Door | Command | P |
| DoorControl | CommandsLeft | R |
| DoorControl | CommandsRight | R |
