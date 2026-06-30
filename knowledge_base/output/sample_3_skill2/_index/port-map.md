# Port Map

Universal port lookup: every port in the system in one table.
Direction: `P` = provided, `R` = required.

| Component.Port | Direction | Interface | Interface Type |
|----------------|-----------|-----------|----------------|
| Door.Command | P | /Demo/Interfaces/DoorCommands | CLIENT-SERVER |
| Door.Status | P | /Demo/Interfaces/DoorStatus | SENDER-RECEIVER |
| DoorControl.CombinedStatus | P | /Demo/Interfaces/CombinedStatus | SENDER-RECEIVER |
| DoorControl.CommandsLeft | R | /Demo/Interfaces/DoorCommands | CLIENT-SERVER |
| DoorControl.CommandsRight | R | /Demo/Interfaces/DoorCommands | CLIENT-SERVER |
| DoorControl.Led | R | /Demo/Services/IoHwAb/DigitalServiceWrite | CLIENT-SERVER |
| DoorControl.StatusLeft | R | /Demo/Interfaces/DoorStatus | SENDER-RECEIVER |
| DoorControl.StatusRight | R | /Demo/Interfaces/DoorStatus | SENDER-RECEIVER |
| EDC.CombinedStatus | P | /Demo/Interfaces/CombinedStatus | SENDER-RECEIVER |
| IoHwAb.Digital_Led | P | /Demo/Services/IoHwAb/DigitalServiceWrite | CLIENT-SERVER |

## Notes

- `EDC.CombinedStatus` is the composition's outer port; it delegates to
  `DoorControl.CombinedStatus` (the inner provider) via
  `CombinedStatus_delegate_connector0`.
- Within the `EDC` composition, `Door` is instantiated as `DoorLeft` and
  `DoorRight`, so `Door.Status`/`Door.Command` appear twice at the instance level
  (see [composition-tree.md](composition-tree.md) and [EDC.md](../components/EDC.md)).
