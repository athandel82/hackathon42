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

## Description

Platform service interface for writing a digital output level (e.g. an LED).
Provided by `IoHwAb.Digital_Led`; called by `DoorControl.Led`.

## Data Elements (Sender-Receiver)

_None_

## Operations (Client-Server)

### Write

| Field | Value |
|-------|-------|
| UUID | dd88cf8a-23ab-37e8-a76c-091e9d710794 |

**Arguments:**

| Argument Name | Type | Direction | UUID |
|---------------|------|-----------|------|
| Level | [/Demo/Services/IoHwAb/DigitalLevel](../platform/ImplementationDataTypes.md) | IN | 6d32b864-ef0d-3a9d-bff2-bc7bfc13c06d |

**Possible Errors:**

| Error Name | Error Code | UUID |
|------------|------------|------|
| E_OK | 0 | 1d7ed684-3d16-38d3-a1a2-a0e0c39c9bc4 |
| E_NOT_OK | 1 | 9d93fffd-5efc-3045-aafd-2f6154db6f11 |

## Usage (resolved from port-map / dependency-graph)

| Component | Port | Direction (P/R) |
|-----------|------|-----------------|
| IoHwAb | Digital_Led | P (server) |
| DoorControl | Led | R (client) |

The `Level` argument uses the IoHwAb-local `DigitalLevel` type (TEXTTABLE:
0 = IOHWAB_LOW, 1 = IOHWAB_HIGH).
