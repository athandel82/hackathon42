# Port Map

Every port on every component, with the interface it carries. P = provided,
R = required.

| Component | Port | P/R | Interface | Source Ref |
|-----------|------|-----|-----------|------------|
| [/Demo/Door/Door](../components/Door.md) | Command | P | [/Demo/Interfaces/DoorCommands](../interfaces/DoorCommands.md) | EcuExtract.arxml:17 |
| [/Demo/Door/Door](../components/Door.md) | Status | P | [/Demo/Interfaces/DoorStatus](../interfaces/DoorStatus.md) | EcuExtract.arxml:13 |
| [/Demo/DoorControl/DoorControl](../components/DoorControl.md) | CombinedStatus | P | [/Demo/Interfaces/CombinedStatus](../interfaces/CombinedStatus.md) | EcuExtract.arxml:442 |
| [/Demo/DoorControl/DoorControl](../components/DoorControl.md) | CommandsLeft | R | [/Demo/Interfaces/DoorCommands](../interfaces/DoorCommands.md) | EcuExtract.arxml:430 |
| [/Demo/DoorControl/DoorControl](../components/DoorControl.md) | CommandsRight | R | [/Demo/Interfaces/DoorCommands](../interfaces/DoorCommands.md) | EcuExtract.arxml:434 |
| [/Demo/DoorControl/DoorControl](../components/DoorControl.md) | Led | R | [/Demo/Services/IoHwAb/DigitalServiceWrite](../interfaces/DigitalServiceWrite.md) | EcuExtract.arxml:438 |
| [/Demo/DoorControl/DoorControl](../components/DoorControl.md) | StatusLeft | R | [/Demo/Interfaces/DoorStatus](../interfaces/DoorStatus.md) | EcuExtract.arxml:422 |
| [/Demo/DoorControl/DoorControl](../components/DoorControl.md) | StatusRight | R | [/Demo/Interfaces/DoorStatus](../interfaces/DoorStatus.md) | EcuExtract.arxml:426 |
| [/Demo/EDC/EDC](../components/EDC.md) | CombinedStatus | P | [/Demo/Interfaces/CombinedStatus](../interfaces/CombinedStatus.md) | EcuExtract.arxml:600 |
| [/Demo/Services/IoHwAb/IoHwAb](../components/IoHwAb.md) | Digital_Led | P | [/Demo/Services/IoHwAb/DigitalServiceWrite](../interfaces/DigitalServiceWrite.md) | EcuExtract.arxml:246 |
