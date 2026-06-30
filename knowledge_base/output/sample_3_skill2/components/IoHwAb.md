# IoHwAb

## Impact Tags

- **type:** SERVICE-SW-COMPONENT-TYPE
- **safety-relevant:** unknown (no ASIL tagging present in the extract)
- **network-connected:** no (provides a local digital-write service only)
- **shared-implementation:** No (`IoHwAbImpl` used only by the single `IO` instance)
- **composition-parent:** EDC (as instance IO)
- **signal-producer:** None
- **leaf:** yes (no forward dependencies — provides only)

## Component Information

| Field | Value |
|-------|-------|
| Name | IoHwAb |
| Type | SERVICE-SW-COMPONENT-TYPE |
| UUID | c97e31d8-af34-3dd0-9392-52e0287af468 |
| Package | /Demo/Services/IoHwAb |
| Source File | EcuExtract.arxml |

## Description

I/O hardware abstraction service component. Exposes a digital write service used
by DoorControl to drive an LED actuator. Also owns the IoHwAb-local data types and
compu methods (DigitalLevel, SignalQuality — see
[ImplementationDataTypes.md](../platform/ImplementationDataTypes.md)).

## Ports

### Provided Ports (P-PORT)

| Port Name | Interface | Interface Type | UUID |
|-----------|-----------|----------------|------|
| Digital_Led | [/Demo/Services/IoHwAb/DigitalServiceWrite](../interfaces/DigitalServiceWrite.md) | CLIENT-SERVER | 48892b28-c309-3dea-8d9f-988a97beb6f6 |

### Required Ports (R-PORT)

_None_

## Internal Behavior

| Field | Value |
|-------|-------|
| Name | IoHwAbBehavior |
| UUID | 4662198d-0242-3cad-bdb4-5dc69cab0129 |
| Handle Termination | NO-SUPPORT |
| Multiple Instantiation | false |

A `PORT-API-OPTION` on `Digital_Led` defines a port-defined argument value
(`IoHwAb_SignalType_` = 0) of type
[/Demo/Services/IoHwAb/IoHwAb_SignalType_](../platform/ImplementationDataTypes.md).

## Events

| Event Name | Type | Trigger (Runnable) | Period | UUID |
|------------|------|--------------------|--------|------|
| Digital_Led_Write | OPERATION-INVOKED-EVENT | DigitalWrite | — (on Digital_Led/Write invocation) | 3ed86257-0078-400a-a1f6-cbacef1f1375 |

## Runnables

### DigitalWrite

| Field | Value |
|-------|-------|
| UUID | 22494afe-312b-368d-8232-3e304753c18f |
| Symbol | IoHwAb_Digital_Write |
| Minimum Start Interval | 0.0 |
| Concurrent Invocation | true |

Triggered by `Digital_Led_Write` when a client calls `DigitalServiceWrite/Write`
on the `Digital_Led` port.

## Implementation

| Field | Value |
|-------|-------|
| Name | IoHwAbImpl |
| UUID | 943c7691-0acc-341e-b272-c0a71a5c8cba |
| Programming Language | C |
| Vendor ID | 0 |
| Behavior Reference | /Demo/Services/IoHwAb/IoHwAb/IoHwAbBehavior |

## Dependencies

### Provides To

| Consumer Component | Via Port | Interface | Data Elements / Operations |
|--------------------|----------|-----------|----------------------------|
| DoorControl | Digital_Led → Led | DigitalServiceWrite | Write(Level) |

### Requires From

_None_

### Calls (client → server)

_None_

### Called By (server ← client)

| Caller Component | Via Port | Operation |
|------------------|----------|-----------|
| DoorControl | Led | Write |

### Participates In Signal Chains

| Chain | Role |
|-------|------|
| [Actuation Path (LED)](../_index/signal-chains.md) | server (DigitalWrite runnable) |
