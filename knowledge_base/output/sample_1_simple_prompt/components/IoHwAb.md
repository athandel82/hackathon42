# IoHwAb

## Component Information

| Field | Value |
|-------|-------|
| Name | IoHwAb |
| Type | SERVICE-SW-COMPONENT-TYPE |
| UUID | c97e31d8-af34-3dd0-9392-52e0287af468 |
| Package | /Demo/Services/IoHwAb |
| Source File | EcuExtract.arxml |

## Description

I/O Hardware Abstraction service component. Provides an abstraction layer for digital I/O operations, specifically LED control in this configuration.

## Ports

### Provided Ports (P-PORT)

| Port Name | Interface | Interface Type | UUID |
|-----------|-----------|----------------|------|
| Digital_Led | /Demo/Services/IoHwAb/DigitalServiceWrite | CLIENT-SERVER-INTERFACE | 48892b28-c309-3dea-8d9f-988a97beb6f6 |

### Required Ports (R-PORT)

_None_

## Internal Behavior

| Field | Value |
|-------|-------|
| Name | IoHwAbBehavior |
| UUID | 4662198d-0242-3cad-bdb4-5dc69cab0129 |
| Handle Termination | NO-SUPPORT |
| Multiple Instantiation | false |

## Events

| Event Name | Type | Trigger | UUID |
|------------|------|---------|------|
| Digital_Led_Write | OPERATION-INVOKED-EVENT | DigitalWrite (via Digital_Led/Write) | 3ed86257-0078-400a-a1f6-cbacef1f1375 |

## Runnables

### DigitalWrite

| Field | Value |
|-------|-------|
| UUID | 22494afe-312b-368d-8232-3e304753c18f |
| Symbol | IoHwAb_Digital_Write |
| Minimum Start Interval | 0.0 |
| Concurrent Invocation | true |

## Port API Options

| Port | Argument Type | Value |
|------|---------------|-------|
| Digital_Led | IoHwAb_SignalType_ | 0 |

## Implementation

| Field | Value |
|-------|-------|
| Name | IoHwAbImpl |
| UUID | 943c7691-0acc-341e-b272-c0a71a5c8cba |
| Programming Language | C |
| Vendor ID | 0 |
| Behavior Reference | /Demo/Services/IoHwAb/IoHwAb/IoHwAbBehavior |

## Associated Data Types

| Type Name | Category | Base Type Reference | UUID |
|-----------|----------|---------------------|------|
| IoHwAb_SignalType_ | TYPE_REFERENCE | /ArcCore/Platform/ImplementationDataTypes/uint32 | 6e499ceb-e086-39a3-a8aa-cad156c2235d |
| SignalQuality | TYPE_REFERENCE | /ArcCore/Platform/ImplementationDataTypes/uint8 | ce7d4658-6239-3091-8e78-7747c6a4fdfd |
| DigitalLevel | TYPE_REFERENCE | /ArcCore/Platform/ImplementationDataTypes/uint8 | db4b6add-7698-3ee4-9dae-adaa7488c81a |

## Enumerations

### SignalQuality (SignalQuality_def)

| Value | Label |
|-------|-------|
| 0 | IOHWAB_INIVAL |
| 1 | IOHWAB_ERR |
| 2 | IOHWAB_BAD |
| 3 | IOHWAB_GOOD |

### DigitalLevel (DigitalLevel_def)

| Value | Label |
|-------|-------|
| 0 | IOHWAB_LOW |
| 1 | IOHWAB_HIGH |

## Relationships

- **Provides** digital write service for LED control
- **Consumed by** DoorControl component via the `Led` port
- **Used by** EDC composition as `IO` instance
