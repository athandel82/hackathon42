# DigitalServiceWrite

## Interface Information

| Field | Value |
|-------|-------|
| Name | DigitalServiceWrite |
| Type | CLIENT-SERVER-INTERFACE |
| UUID | 3134600e-be9d-377d-bdba-008a5441a7e2 |
| Package | /Demo/Services/IoHwAb |
| Is Service | true |
| Source File | EcuExtract.arxml |
| Source Reference | EcuExtract.arxml:213 (/Demo/Services/IoHwAb/DigitalServiceWrite) |

## Description

Service client-server interface for writing a digital output level. The server is
`IoHwAb.Digital_Led` (runnable `DigitalWrite`); the client is `DoorControl.Led`.

## Data Elements (Sender-Receiver)

_None_

## Operations (Client-Server)

| Operation | Arguments | Possible Errors | UUID | Source Ref |
|-----------|-----------|-----------------|------|------------|
| Write | Level: [/Demo/Services/IoHwAb/DigitalLevel](../platform/ImplementationDataTypes.md) (IN) | E_OK (0), E_NOT_OK (1) | dd88cf8a-23ab-37e8-a76c-091e9d710794 | EcuExtract.arxml:217 |

## Usage (resolved from port-map / dependency-graph)

| Component | Port | Direction (P/R) |
|-----------|------|-----------------|
| IoHwAb | Digital_Led | P |
| DoorControl | Led | R |
