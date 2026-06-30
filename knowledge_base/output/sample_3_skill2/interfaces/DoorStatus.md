# DoorStatus

## Interface Information

| Field | Value |
|-------|-------|
| Name | DoorStatus |
| Type | SENDER-RECEIVER-INTERFACE |
| UUID | 1aa75fd5-0de9-3040-bdb6-cd3cf3d3964e |
| Package | /Demo/Interfaces |
| Is Service | false |
| Source File | EcuExtract.arxml |

## Description

Sender-receiver interface carrying a single door's boolean lock and open state.
Provided by `Door.Status`, consumed by `DoorControl` for each door.

## Data Elements (Sender-Receiver)

| Element Name | Type | Implementation Policy | UUID |
|--------------|------|-----------------------|------|
| Locked | [/ArcCore/Platform/ImplementationDataTypes/boolean](../platform/ImplementationDataTypes.md) | STANDARD | 1801e168-fcc8-362f-b5f0-3a7f5d392a9b |
| Open | [/ArcCore/Platform/ImplementationDataTypes/boolean](../platform/ImplementationDataTypes.md) | STANDARD | ed09ee66-7aa2-335d-b6d5-cc88d496f5ce |

## Operations (Client-Server)

_None_

## Usage (resolved from port-map / dependency-graph)

| Component | Port | Direction (P/R) |
|-----------|------|-----------------|
| Door | Status | P |
| DoorControl | StatusLeft | R |
| DoorControl | StatusRight | R |
