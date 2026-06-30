# Signal Chains (end-to-end data flow)

Each chain lists every hop. Cut at any node to see downstream impact. All four
chains share the same shape: a `Door` instance produces a status bit, `Control`
(DoorControl) aggregates it into `CombinedStatus`, and it is delegated out of
`EDC` and mapped to a network system signal → I-Signal → I-PDU.

## Chain 1: Combined Lock Status (Left door)

```
DoorLeft.DoorMain (runnable, write DoorStatus/Locked)  [port: DoorLeft.Status]
  → connector: DoorLeft_Status_to_Control_StatusLeft
    → Control.Main (read DoorStatus/Locked)  [port: Control.StatusLeft]
      → Control.Main (write CombinedStatus/LockedLeft)  [port: Control.CombinedStatus]
        → delegation: CombinedStatus_delegate_connector0 → EDC.CombinedStatus
          → system signal: CombinedStatusLockedLeftSSig
            → I-Signal: CombinedStatusLockedLeftISig
              → I-PDU: CombinedStatusLockedLeftIPdu
```

**Endpoints:** producer `Door` (instance DoorLeft) → network PDU `CombinedStatusLockedLeftIPdu`
**Cut analysis:** removing `DoorLeft` breaks this chain at the source; the PDU and
the `CombinedStatus.LockedLeft` contribution are lost. Removing `Control` severs
every chain at the aggregation hop.

## Chain 2: Combined Open Status (Left door)

```
DoorLeft.DoorMain (runnable, write DoorStatus/Open)  [port: DoorLeft.Status]
  → connector: DoorLeft_Status_to_Control_StatusLeft
    → Control.Main (read DoorStatus/Open)  [port: Control.StatusLeft]
      → Control.Main (write CombinedStatus/OpenLeft)  [port: Control.CombinedStatus]
        → delegation: CombinedStatus_delegate_connector0 → EDC.CombinedStatus
          → system signal: CombinedStatusOpenLeftSSig
            → I-Signal: CombinedStatusOpenLeftISig
              → I-PDU: CombinedStatusOpenLeftIPdu
```

**Endpoints:** producer `Door` (instance DoorLeft) → network PDU `CombinedStatusOpenLeftIPdu`

## Chain 3: Combined Lock Status (Right door)

```
DoorRight.DoorMain (runnable, write DoorStatus/Locked)  [port: DoorRight.Status]
  → connector: DoorRight_Status_to_Control_StatusRight
    → Control.Main (read DoorStatus/Locked)  [port: Control.StatusRight]
      → Control.Main (write CombinedStatus/LockedRight)  [port: Control.CombinedStatus]
        → delegation: CombinedStatus_delegate_connector0 → EDC.CombinedStatus
          → system signal: CombinedStatusLockedRightSSig
            → I-Signal: CombinedStatusLockedRightISig
              → I-PDU: CombinedStatusLockedRightIPdu
```

**Endpoints:** producer `Door` (instance DoorRight) → network PDU `CombinedStatusLockedRightIPdu`

## Chain 4: Combined Open Status (Right door)

```
DoorRight.DoorMain (runnable, write DoorStatus/Open)  [port: DoorRight.Status]
  → connector: DoorRight_Status_to_Control_StatusRight
    → Control.Main (read DoorStatus/Open)  [port: Control.StatusRight]
      → Control.Main (write CombinedStatus/OpenRight)  [port: Control.CombinedStatus]
        → delegation: CombinedStatus_delegate_connector0 → EDC.CombinedStatus
          → system signal: CombinedStatusOpenRightSSig
            → I-Signal: CombinedStatusOpenRightISig
              → I-PDU: CombinedStatusOpenRightIPdu
```

**Endpoints:** producer `Door` (instance DoorRight) → network PDU `CombinedStatusOpenRightIPdu`

## Command Path (control, not mapped to network)

```
Control.Main (server call: serverCallPoint_Main_CommandsLeft_SetLock)
  [port: Control.CommandsLeft → DoorCommands/SetLock]
    → connector: DoorLeft_Command_to_Control_CommandsLeft
      → DoorLeft.SetLocked (runnable, OPERATION-INVOKED via Command_SetLock)
```

A mirrored path exists for the right door (`serverCallPoint_Main_CommandsRight_SetLock`
→ `DoorRight_Command_to_Control_CommandsRight` → `DoorRight.SetLocked`).

## Actuation Path (LED, not mapped to network)

```
Control.Main (server call: serverCallPoint_Main_Led_Write)
  [port: Control.Led → DigitalServiceWrite/Write]
    → connector: IO_Digital_Led_to_Control_Led
      → IO.DigitalWrite (runnable, OPERATION-INVOKED via Digital_Led_Write)
```

**Cut analysis:** removing `IoHwAb` (IO) breaks this actuation path only; the four
network status chains are unaffected.
