# Interfaces Index

All port interfaces in the model.

| Interface | Type | Is Service | Provided By | Required By | File | Source Ref |
|-----------|------|------------|-------------|-------------|------|------------|
| [/Demo/Interfaces/CombinedStatus](../interfaces/CombinedStatus.md) | SENDER-RECEIVER-INTERFACE | false | DoorControl, EDC | _None_ (→ system signals) | [CombinedStatus.md](../interfaces/CombinedStatus.md) | EcuExtract.arxml:364 |
| [/Demo/Interfaces/DoorCommands](../interfaces/DoorCommands.md) | CLIENT-SERVER-INTERFACE | false | Door | DoorControl | [DoorCommands.md](../interfaces/DoorCommands.md) | EcuExtract.arxml:348 |
| [/Demo/Interfaces/DoorStatus](../interfaces/DoorStatus.md) | SENDER-RECEIVER-INTERFACE | false | Door | DoorControl | [DoorStatus.md](../interfaces/DoorStatus.md) | EcuExtract.arxml:320 |
| [/Demo/Services/IoHwAb/DigitalServiceWrite](../interfaces/DigitalServiceWrite.md) | CLIENT-SERVER-INTERFACE | true | IoHwAb | DoorControl | [DigitalServiceWrite.md](../interfaces/DigitalServiceWrite.md) | EcuExtract.arxml:213 |
