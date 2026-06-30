# Composition Tree

Containment hierarchy rooted at the `SYSTEM` ECU extract. Instance names are the
`SW-COMPONENT-PROTOTYPE` short-names; their types link to the component file.

```
SYSTEM /Demo/EDC/EDCEcuExtract  (CATEGORY: ECU_EXTRACT)   [EcuExtract.arxml:694]
└── ROOT-SW-COMPOSITION-PROTOTYPE EDCPrototype             [EcuExtract.arxml:782]
    └── /Demo/EDC/EDC  (COMPOSITION-SW-COMPONENT-TYPE)     [EcuExtract.arxml:597]
        ├── DoorLeft  : /Demo/Door/Door                    [EcuExtract.arxml:606]
        ├── DoorRight : /Demo/Door/Door                    [EcuExtract.arxml:610]
        ├── Control   : /Demo/DoorControl/DoorControl      [EcuExtract.arxml:614]
        └── IO        : /Demo/Services/IoHwAb/IoHwAb        [EcuExtract.arxml:618]
```

## Containment Table

| Parent | Instance | Component Type | Source Ref |
|--------|----------|----------------|------------|
| [/Demo/EDC/EDC](../components/EDC.md) | Control | [/Demo/DoorControl/DoorControl](../components/DoorControl.md) | EcuExtract.arxml:614 |
| [/Demo/EDC/EDC](../components/EDC.md) | DoorLeft | [/Demo/Door/Door](../components/Door.md) | EcuExtract.arxml:606 |
| [/Demo/EDC/EDC](../components/EDC.md) | DoorRight | [/Demo/Door/Door](../components/Door.md) | EcuExtract.arxml:610 |
| [/Demo/EDC/EDC](../components/EDC.md) | IO | [/Demo/Services/IoHwAb/IoHwAb](../components/IoHwAb.md) | EcuExtract.arxml:618 |

## Notes

- `Door` is instantiated twice (`DoorLeft`, `DoorRight`) — both share the single
  `DoorImplementation`. Removing the `Door` type removes both instances.
- The composition's only outer port is `CombinedStatus`, delegated from
  `Control.CombinedStatus` (see [signal-chains.md](signal-chains.md)).
