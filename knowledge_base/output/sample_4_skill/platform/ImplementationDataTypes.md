# Implementation Data Types

Implementation data types and compu-methods. Two groups: the reusable
`/ArcCore/Platform` blueprint types, and the project-local `/Demo/Services/IoHwAb`
types defined alongside the IoHwAb service.

## ArcCore Platform Value Types (`/ArcCore/Platform/ImplementationDataTypes`)

| Name | Category | Base Type / Ref | Type Emitter | Source Ref |
|------|----------|-----------------|--------------|------------|
| boolean | VALUE | BaseTypes/boolean + CompuMethods/boolean | Platform_Types.h | ArcCore_Types.arxml:118 |
| uint8 | VALUE | BaseTypes/uint8 | Platform_Types.h | ArcCore_Types.arxml:134 |
| uint16 | VALUE | BaseTypes/uint16 | Platform_Types.h | ArcCore_Types.arxml:149 |
| uint32 | VALUE | BaseTypes/uint32 | Platform_Types.h | ArcCore_Types.arxml:164 |
| sint8 | VALUE | BaseTypes/sint8 | Platform_Types.h | ArcCore_Types.arxml:179 |
| sint16 | VALUE | BaseTypes/sint16 | Platform_Types.h | ArcCore_Types.arxml:194 |
| sint32 | VALUE | BaseTypes/sint32 | Platform_Types.h | ArcCore_Types.arxml:209 |
| float32 | VALUE | BaseTypes/float32 | Platform_Types.h | ArcCore_Types.arxml:224 |
| float64 | VALUE | BaseTypes/float64 | Platform_Types.h | ArcCore_Types.arxml:239 |
| ConstVoidPtr | DATA_REFERENCE | BaseTypes/void (CONST) | — | ArcCore_Types.arxml:254 |
| VoidPtr | DATA_REFERENCE | BaseTypes/void | — | ArcCore_Types.arxml:275 |

> Note: the `AUTOSAR/Platform/ImplementationDataTypes` package (ArcCore_Types.arxml:339+)
> redefines the same blueprint value types (`boolean`, `uint8`, … `VoidPtr`). They
> share short-names with the `/ArcCore` set and are referenced only by full path in
> the source; the application model uses the `/ArcCore/Platform` variants.

## ArcCore Compu-Methods (`/ArcCore/Platform/CompuMethods`)

| Name | Category | Scales | Source Ref |
|------|----------|--------|------------|
| boolean | TEXTTABLE | 0 → FALSE, 1 → TRUE | ArcCore_Types.arxml:301 |

## Project-Local Types (`/Demo/Services/IoHwAb`)

| Name | Tag | Category | Refines / Definition | Source Ref |
|------|-----|----------|----------------------|------------|
| IoHwAb_SignalType_ | IMPLEMENTATION-DATA-TYPE | TYPE_REFERENCE | → ArcCore uint32 | EcuExtract.arxml:107 |
| dummy_IoHwAb_SignalType_ | APPLICATION-PRIMITIVE-DATA-TYPE | VALUE | mapped to IoHwAb_SignalType_ | EcuExtract.arxml:118 |
| SignalQuality | IMPLEMENTATION-DATA-TYPE | TYPE_REFERENCE | → ArcCore uint8 + SignalQuality_def | EcuExtract.arxml:131 |
| SignalQuality_def | COMPU-METHOD | TEXTTABLE | 0=INIVAL, 1=ERR, 2=BAD, 3=GOOD | EcuExtract.arxml:143 |
| DigitalLevel | IMPLEMENTATION-DATA-TYPE | TYPE_REFERENCE | → ArcCore uint8 + DigitalLevel_def | EcuExtract.arxml:179 |
| DigitalLevel_def | COMPU-METHOD | TEXTTABLE | 0=LOW, 1=HIGH | EcuExtract.arxml:191 |

## Usage Notes

- `DigitalLevel` is the argument type of `DigitalServiceWrite.Write`
  (see [interfaces/DigitalServiceWrite.md](../interfaces/DigitalServiceWrite.md)).
- `SignalQuality`, `IoHwAb_SignalType_`, and `dummy_IoHwAb_SignalType_` are
  declared in the IoHwAb package but are not referenced by any modeled port in
  this extract.
