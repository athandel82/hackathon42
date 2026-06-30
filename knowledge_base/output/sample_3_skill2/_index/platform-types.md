# Platform Type Index

`Consumers` = number of model elements that reference the type (data elements,
arguments, or other types). Counts cover references found in the ECU extract.

## Base Types (`/ArcCore/Platform/BaseTypes`)

| Type | Category | Kind | Consumers | File |
|------|----------|------|----------:|------|
| boolean | base | SW-BASE-TYPE | 2 | [BaseTypes.md](../platform/BaseTypes.md) |
| uint8 | base | SW-BASE-TYPE | 2 | [BaseTypes.md](../platform/BaseTypes.md) |
| uint16 | base | SW-BASE-TYPE | 2 | [BaseTypes.md](../platform/BaseTypes.md) |
| uint32 | base | SW-BASE-TYPE | 2 | [BaseTypes.md](../platform/BaseTypes.md) |
| sint8 | base | SW-BASE-TYPE | 2 | [BaseTypes.md](../platform/BaseTypes.md) |
| sint16 | base | SW-BASE-TYPE | 2 | [BaseTypes.md](../platform/BaseTypes.md) |
| sint32 | base | SW-BASE-TYPE | 2 | [BaseTypes.md](../platform/BaseTypes.md) |
| float32 | base | SW-BASE-TYPE | 2 | [BaseTypes.md](../platform/BaseTypes.md) |
| float64 | base | SW-BASE-TYPE | 2 | [BaseTypes.md](../platform/BaseTypes.md) |
| void | base | SW-BASE-TYPE | 4 | [BaseTypes.md](../platform/BaseTypes.md) |

> Base-type consumer counts reflect the implementation data types that reference
> them (the `/ArcCore` set + the duplicate `/AUTOSAR` set). `void` is referenced by
> ConstVoidPtr and VoidPtr in both sets.

## Implementation Data Types

| Type | Package | Category | Consumers | File |
|------|---------|----------|----------:|------|
| boolean | /ArcCore/Platform/ImplementationDataTypes | VALUE | 7 | [ImplementationDataTypes.md](../platform/ImplementationDataTypes.md) |
| uint8 | /ArcCore/Platform/ImplementationDataTypes | VALUE | 2 | [ImplementationDataTypes.md](../platform/ImplementationDataTypes.md) |
| uint16 | /ArcCore/Platform/ImplementationDataTypes | VALUE | 0 | [ImplementationDataTypes.md](../platform/ImplementationDataTypes.md) |
| uint32 | /ArcCore/Platform/ImplementationDataTypes | VALUE | 1 | [ImplementationDataTypes.md](../platform/ImplementationDataTypes.md) |
| sint8 | /ArcCore/Platform/ImplementationDataTypes | VALUE | 0 | [ImplementationDataTypes.md](../platform/ImplementationDataTypes.md) |
| sint16 | /ArcCore/Platform/ImplementationDataTypes | VALUE | 0 | [ImplementationDataTypes.md](../platform/ImplementationDataTypes.md) |
| sint32 | /ArcCore/Platform/ImplementationDataTypes | VALUE | 0 | [ImplementationDataTypes.md](../platform/ImplementationDataTypes.md) |
| float32 | /ArcCore/Platform/ImplementationDataTypes | VALUE | 0 | [ImplementationDataTypes.md](../platform/ImplementationDataTypes.md) |
| float64 | /ArcCore/Platform/ImplementationDataTypes | VALUE | 0 | [ImplementationDataTypes.md](../platform/ImplementationDataTypes.md) |
| ConstVoidPtr | /ArcCore/Platform/ImplementationDataTypes | DATA_REFERENCE | 0 | [ImplementationDataTypes.md](../platform/ImplementationDataTypes.md) |
| VoidPtr | /ArcCore/Platform/ImplementationDataTypes | DATA_REFERENCE | 0 | [ImplementationDataTypes.md](../platform/ImplementationDataTypes.md) |
| IoHwAb_SignalType_ | /Demo/Services/IoHwAb | TYPE_REFERENCE → uint32 | 1 | [ImplementationDataTypes.md](../platform/ImplementationDataTypes.md) |
| SignalQuality | /Demo/Services/IoHwAb | TYPE_REFERENCE → uint8 | 0 | [ImplementationDataTypes.md](../platform/ImplementationDataTypes.md) |
| DigitalLevel | /Demo/Services/IoHwAb | TYPE_REFERENCE → uint8 | 1 | [ImplementationDataTypes.md](../platform/ImplementationDataTypes.md) |
| dummy_IoHwAb_SignalType_ | /Demo/Services/IoHwAb | APPLICATION-PRIMITIVE (VALUE) | 1 | [ImplementationDataTypes.md](../platform/ImplementationDataTypes.md) |

## Computation Methods

| CompuMethod | Package | Category | File |
|-------------|---------|----------|------|
| boolean | /ArcCore/Platform/CompuMethods | TEXTTABLE | [ImplementationDataTypes.md](../platform/ImplementationDataTypes.md) |
| SignalQuality_def | /Demo/Services/IoHwAb | TEXTTABLE | [ImplementationDataTypes.md](../platform/ImplementationDataTypes.md) |
| DigitalLevel_def | /Demo/Services/IoHwAb | TEXTTABLE | [ImplementationDataTypes.md](../platform/ImplementationDataTypes.md) |

## Notes

- `boolean` (impl) is by far the most used type: every `DoorStatus`,
  `CombinedStatus` data element and the `DoorCommands.SetLock` argument use it.
- `DigitalLevel` is consumed by the `DigitalServiceWrite.Write` operation argument.
- `uint16`, `sint*`, `float*`, and the pointer types are defined in the platform
  blueprint but unused by application elements in this extract.
