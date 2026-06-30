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

Client-Server service interface for writing digital output levels. Used to control hardware outputs such as LEDs through the I/O Hardware Abstraction layer.

## Operations

### Write

| Field | Value |
|-------|-------|
| UUID | dd88cf8a-23ab-37e8-a76c-091e9d710794 |

**Arguments:**

| Argument Name | Type | Direction | UUID |
|---------------|------|-----------|------|
| Level | /Demo/Services/IoHwAb/DigitalLevel | IN | 6d32b864-ef0d-3a9d-bff2-bc7bfc13c06d |

**Possible Errors:**

| Error Name | Error Code | UUID |
|------------|------------|------|
| E_OK | 0 | 1d7ed684-3d16-38d3-a1a2-a0e0c39c9bc4 |
| E_NOT_OK | 1 | 9d93fffd-5efc-3045-aafd-2f6154db6f11 |

## Usage

| Component | Port Name | Direction |
|-----------|-----------|-----------|
| IoHwAb | Digital_Led | Provided (server - handles Write) |
| DoorControl | Led | Required (client - calls Write) |
