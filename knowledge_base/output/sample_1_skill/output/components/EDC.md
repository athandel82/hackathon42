# EDC (Electronic Door Control)

## Component Information

| Field | Value |
|-------|-------|
| Name | EDC |
| Type | COMPOSITION-SW-COMPONENT-TYPE |
| UUID | 034525f7-3ff6-33b2-a2b2-56321b03e240 |
| Package | /Demo/EDC |
| Source File | EcuExtract.arxml |

## Description

Top-level composition component that integrates left/right Door components, the DoorControl logic, and the IoHwAb service into a complete Electronic Door Control system.

## Ports

### Provided Ports (P-PORT)

| Port Name | Interface | Interface Type | UUID |
|-----------|-----------|----------------|------|
| CombinedStatus | /Demo/Interfaces/CombinedStatus | SENDER-RECEIVER-INTERFACE | dc98dc78-1aca-36dd-9d98-e0a89fd18a21 |

### Required Ports (R-PORT)

_None_

## Internal Components

| Instance Name | Component Type | Type Reference | UUID |
|---------------|----------------|----------------|------|
| Control | APPLICATION-SW-COMPONENT-TYPE | /Demo/DoorControl/DoorControl | 89c6bf8e-984f-376e-ad33-607d91e5a6ab |
| DoorLeft | APPLICATION-SW-COMPONENT-TYPE | /Demo/Door/Door | 0d9d3407-5a9c-33f3-84b4-9080804a4ad0 |
| DoorRight | APPLICATION-SW-COMPONENT-TYPE | /Demo/Door/Door | 8b499a52-aea4-3b6a-a1bc-f52dbc9c776c |
| IO | SERVICE-SW-COMPONENT-TYPE | /Demo/Services/IoHwAb/IoHwAb | c4d885db-369c-3268-bdaf-521bdf1887ab |

## Assembly Connectors

| Connector Name | Provider (Component.Port) | Requester (Component.Port) | UUID |
|----------------|---------------------------|----------------------------|------|
| DoorLeft_Command_to_Control_CommandsLeft | DoorLeft.Command | Control.CommandsLeft | a9c2b7f4-ee22-3bed-af64-d39c1194552a |
| DoorLeft_Status_to_Control_StatusLeft | DoorLeft.Status | Control.StatusLeft | f297dc64-c381-377b-b5f5-06db999a09fb |
| DoorRight_Command_to_Control_CommandsRight | DoorRight.Command | Control.CommandsRight | b50acda8-1379-30f2-8b5b-9620a85276d1 |
| DoorRight_Status_to_Control_StatusRight | DoorRight.Status | Control.StatusRight | ed1d8867-02cb-3bda-8263-3a2bbd9cb01e |
| IO_Digital_Led_to_Control_Led | IO.Digital_Led | Control.Led | d86f2f14-ec48-3159-ba69-d029e2628924 |

## Delegation Connectors

| Connector Name | Inner (Component.Port) | Outer Port | UUID |
|----------------|------------------------|------------|------|
| CombinedStatus_delegate_connector0 | Control.CombinedStatus | EDC.CombinedStatus | f7b45156-878a-3beb-895e-85845c887435 |

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ EDC Composition                                             │
│                                                             │
│  ┌──────────┐    Status     ┌──────────────┐               │
│  │ DoorLeft │──────────────▶│              │               │
│  │  (Door)  │◀──────────────│              │               │
│  └──────────┘    Command    │              │  CombinedStatus│
│                             │  DoorControl │──────────────▶ ║ P-PORT
│  ┌──────────┐    Status     │              │               │
│  │ DoorRight│──────────────▶│              │               │
│  │  (Door)  │◀──────────────│              │               │
│  └──────────┘    Command    │              │               │
│                             └──────┬───────┘               │
│                                    │ Led                    │
│                                    ▼                        │
│                             ┌──────────────┐               │
│                             │     IO       │               │
│                             │  (IoHwAb)    │               │
│                             └──────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

## Relationships

- **Contains** two Door instances (DoorLeft, DoorRight), one DoorControl instance (Control), one IoHwAb instance (IO)
- **Delegates** CombinedStatus from Control to the composition-level port
- **Root composition** for EDCEcuExtract system
