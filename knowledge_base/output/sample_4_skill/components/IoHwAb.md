# IoHwAb

## Impact Tags

- **type:** SERVICE-SW-COMPONENT-TYPE
- **safety-relevant:** unknown (no ASIL tagging present in the extract)
- **network-connected:** no (provides a local actuation service only)
- **shared-implementation:** No (`IoHwAbImpl`, single instance `IO`)
- **composition-parent:** EDC (as instance IO)
- **signal-producer:** None (not mapped to any system signal)
- **leaf:** yes (no forward dependencies — provides only)

## Component Information

| Field | Value |
|-------|-------|
| Name | IoHwAb |
| Type | SERVICE-SW-COMPONENT-TYPE |
| UUID | c97e31d8-af34-3dd0-9392-52e0287af468 |
| Package | /Demo/Services/IoHwAb |
| Source File | EcuExtract.arxml |
| Source Reference | EcuExtract.arxml:243 (/Demo/Services/IoHwAb/IoHwAb) |

## Description

I/O hardware abstraction service. Exposes a `DigitalServiceWrite` server operation
(`Write`) used by `DoorControl` to drive a digital LED output. The IoHwAb package
also defines local data types (`DigitalLevel`, `SignalQuality`, `IoHwAb_SignalType_`).

## Ports

### Provided Ports (P-PORT)

| Port Name | Interface | Interface Type | UUID | Source Ref |
|-----------|-----------|----------------|------|------------|
| Digital_Led | [/Demo/Services/IoHwAb/DigitalServiceWrite](../interfaces/DigitalServiceWrite.md) | CLIENT-SERVER | 48892b28-c309-3dea-8d9f-988a97beb6f6 | EcuExtract.arxml:246 |

### Required Ports (R-PORT)

_None_

## Internal Behavior

| Field | Value |
|-------|-------|
| Name | IoHwAbBehavior |
| UUID | 4662198d-0242-3cad-bdb4-5dc69cab0129 |
| Handle Termination | NO-SUPPORT |
| Multiple Instantiation | false |
| Source Reference | EcuExtract.arxml:252 |

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
| Source Reference | EcuExtract.arxml:282 |

Server runnable invoked when a client calls
[/Demo/Services/IoHwAb/DigitalServiceWrite/Write](../interfaces/DigitalServiceWrite.md)
on the `Digital_Led` port.

## Implementation

| Field | Value |
|-------|-------|
| Name | IoHwAbImpl |
| UUID | 943c7691-0acc-341e-b272-c0a71a5c8cba |
| Programming Language | C |
| Vendor ID | 0 |
| Behavior Reference | /Demo/Services/IoHwAb/IoHwAb/IoHwAbBehavior |
| Source Reference | EcuExtract.arxml:293 |

## Dependencies

### Provides To

| Consumer Component | Via Port | Interface | Data Elements / Operations |
| --- | --- | --- | --- |
| DoorControl | Digital_Led → Led | DigitalServiceWrite | Write |

### Requires From

_None_

### Calls (client → server)

_None_

### Called By (server ← client)

| Caller Component | Via Port | Operation |
| --- | --- | --- |
| DoorControl | Led | Write |

### Participates In Signal Chains

| Chain | Role |
| --- | --- |
| [Actuation Path](../_index/signal-chains.md) | server (DigitalWrite runnable) |
