# Signal Chains (end-to-end data flow)

Each chain lists every hop. Cut at any node to see downstream impact. All four
network chains share the same shape: a `Door` instance produces a status bit,
`Control` (DoorControl) aggregates it into `CombinedStatus`, and it is delegated
out of `EDC` and mapped to a network system signal → I-Signal → I-PDU. Source
refs point at the element that defines each hop.

## Chain 1: Combined Lock Status (Left door)

```
DoorLeft.DoorMain (runnable, write DoorStatus/Locked)  [port: DoorLeft.Status]   [EcuExtract.arxml:42]
  → connector: DoorLeft_Status_to_Control_StatusLeft                              [EcuExtract.arxml:649]
    → Control.Main (read DoorStatus/Locked)  [port: Control.StatusLeft]          [EcuExtract.arxml:459]
      → Control.Main (write CombinedStatus/LockedLeft)  [port: Control.CombinedStatus]
        → delegation: CombinedStatus_delegate_connector0 → EDC.CombinedStatus    [EcuExtract.arxml:682]
          → system signal: CombinedStatusLockedLeftSSig                           [EcuExtract.arxml:793]
            → I-Signal: CombinedStatusLockedLeftISig                              [EcuExtract.arxml:810]
              → I-PDU: CombinedStatusLockedLeftIPdu                               [EcuExtract.arxml:814]
```

**Endpoints:** producer `Door` (instance DoorLeft) → network PDU `CombinedStatusLockedLeftIPdu`
**Cut analysis:** removing `DoorLeft` breaks this chain at the source; the PDU and
the `CombinedStatus.LockedLeft` contribution are lost. Removing `Control` severs
every chain at the aggregation hop.

## Chain 2: Combined Open Status (Left door)

```
DoorLeft.DoorMain (runnable, write DoorStatus/Open)  [port: DoorLeft.Status]     [EcuExtract.arxml:42]
  → connector: DoorLeft_Status_to_Control_StatusLeft                              [EcuExtract.arxml:649]
    → Control.Main (read DoorStatus/Open)  [port: Control.StatusLeft]            [EcuExtract.arxml:459]
      → Control.Main (write CombinedStatus/OpenLeft)  [port: Control.CombinedStatus]
        → delegation: CombinedStatus_delegate_connector0 → EDC.CombinedStatus    [EcuExtract.arxml:682]
          → system signal: CombinedStatusOpenLeftSSig                             [EcuExtract.arxml:796]
            → I-Signal: CombinedStatusOpenLeftISig                                [EcuExtract.arxml:823]
              → I-PDU: CombinedStatusOpenLeftIPdu                                 [EcuExtract.arxml:827]
```

**Endpoints:** producer `Door` (instance DoorLeft) → network PDU `CombinedStatusOpenLeftIPdu`

## Chain 3: Combined Lock Status (Right door)

```
DoorRight.DoorMain (runnable, write DoorStatus/Locked)  [port: DoorRight.Status] [EcuExtract.arxml:42]
  → connector: DoorRight_Status_to_Control_StatusRight                           [EcuExtract.arxml:660]
    → Control.Main (read DoorStatus/Locked)  [port: Control.StatusRight]         [EcuExtract.arxml:459]
      → Control.Main (write CombinedStatus/LockedRight)  [port: Control.CombinedStatus]
        → delegation: CombinedStatus_delegate_connector0 → EDC.CombinedStatus    [EcuExtract.arxml:682]
          → system signal: CombinedStatusLockedRightSSig                          [EcuExtract.arxml:799]
            → I-Signal: CombinedStatusLockedRightISig                             [EcuExtract.arxml:836]
              → I-PDU: CombinedStatusLockedRightIPdu                              [EcuExtract.arxml:840]
```

**Endpoints:** producer `Door` (instance DoorRight) → network PDU `CombinedStatusLockedRightIPdu`

## Chain 4: Combined Open Status (Right door)

```
DoorRight.DoorMain (runnable, write DoorStatus/Open)  [port: DoorRight.Status]   [EcuExtract.arxml:42]
  → connector: DoorRight_Status_to_Control_StatusRight                           [EcuExtract.arxml:660]
    → Control.Main (read DoorStatus/Open)  [port: Control.StatusRight]           [EcuExtract.arxml:459]
      → Control.Main (write CombinedStatus/OpenRight)  [port: Control.CombinedStatus]
        → delegation: CombinedStatus_delegate_connector0 → EDC.CombinedStatus    [EcuExtract.arxml:682]
          → system signal: CombinedStatusOpenRightSSig                            [EcuExtract.arxml:802]
            → I-Signal: CombinedStatusOpenRightISig                               [EcuExtract.arxml:849]
              → I-PDU: CombinedStatusOpenRightIPdu                                [EcuExtract.arxml:853]
```

**Endpoints:** producer `Door` (instance DoorRight) → network PDU `CombinedStatusOpenRightIPdu`

## Command Path (control, not mapped to network)

```
Control.Main (server call: serverCallPoint_Main_CommandsLeft_SetLock)            [EcuExtract.arxml:459]
  [port: Control.CommandsLeft → DoorCommands/SetLock]
    → connector: DoorLeft_Command_to_Control_CommandsLeft                        [EcuExtract.arxml:624]
      → DoorLeft.SetLocked (runnable, OPERATION-INVOKED via Command_SetLock)     [EcuExtract.arxml:68]
```

A mirrored path exists for the right door (`serverCallPoint_Main_CommandsRight_SetLock`
→ `DoorRight_Command_to_Control_CommandsRight` [EcuExtract.arxml:638] → `DoorRight.SetLocked`).

## Actuation Path (LED, not mapped to network)

```
Control.Main (server call: serverCallPoint_Main_Led_Write)                       [EcuExtract.arxml:459]
  [port: Control.Led → DigitalServiceWrite/Write]
    → connector: IO_Digital_Led_to_Control_Led                                   [EcuExtract.arxml:671]
      → IO.DigitalWrite (runnable, OPERATION-INVOKED via Digital_Led_Write)      [EcuExtract.arxml:282]
```

**Cut analysis:** removing `IoHwAb` (IO) breaks this actuation path only; the four
network status chains are unaffected.
