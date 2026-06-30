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

Sender-Receiver interface representing the status of a single door. Contains boolean signals for the locked state and the open/closed state.

## Data Elements

| Element Name | Type | Implementation Policy | UUID |
|--------------|------|-----------------------|------|
| Locked | /ArcCore/Platform/ImplementationDataTypes/boolean | STANDARD | 1801e168-fcc8-362f-b5f0-3a7f5d392a9b |
| Open | /ArcCore/Platform/ImplementationDataTypes/boolean | STANDARD | ed09ee66-7aa2-335d-b6d5-cc88d496f5ce |

## Usage

| Component | Port Name | Direction |
|-----------|-----------|-----------|
| Door | Status | Provided (writes Locked, Open) |
| DoorControl | StatusLeft | Required (reads Locked, Open) |
| DoorControl | StatusRight | Required (reads Locked, Open) |
