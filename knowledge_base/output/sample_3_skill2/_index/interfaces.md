# Interface Index

`Providers` = how many ports provide it; `Requesters` = how many require it.
High requester counts flag high-impact interfaces.

| Interface | Type | Providers | Requesters | File |
|-----------|------|----------:|-----------:|------|
| CombinedStatus | SENDER-RECEIVER | 2 | 0 | [CombinedStatus.md](../interfaces/CombinedStatus.md) |
| DigitalServiceWrite | CLIENT-SERVER | 1 | 1 | [DigitalServiceWrite.md](../interfaces/DigitalServiceWrite.md) |
| DoorCommands | CLIENT-SERVER | 1 | 2 | [DoorCommands.md](../interfaces/DoorCommands.md) |
| DoorStatus | SENDER-RECEIVER | 1 | 2 | [DoorStatus.md](../interfaces/DoorStatus.md) |

## Notes

- `DoorStatus` and `DoorCommands` are each provided by `Door` and required twice by
  `DoorControl` (left + right instances) — changing them affects the busiest paths.
- `CombinedStatus` is provided by `DoorControl` and delegated out through `EDC`; it
  has 0 internal requesters but feeds 4 network system signals.
- `DigitalServiceWrite` is the only `IS-SERVICE=true` interface (a platform service).
