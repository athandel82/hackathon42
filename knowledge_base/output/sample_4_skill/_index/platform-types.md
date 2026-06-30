# Platform Types Index

Base types, implementation data types, and compu-methods. The `/ArcCore` types
are the reusable platform blueprint; the `/Demo/Services/IoHwAb` types are
project-local types defined in the IoHwAb package.

## Base Types (`/ArcCore/Platform/BaseTypes`)

| Type | Size (bits) | Encoding | Native | Source Ref |
|------|------------:|----------|--------|------------|
| [/ArcCore/Platform/BaseTypes/boolean](../platform/BaseTypes.md) | 8 | BOOLEAN | boolean | ArcCore_Types.arxml:14 |
| [/ArcCore/Platform/BaseTypes/uint8](../platform/BaseTypes.md) | 8 | NONE | uint8 | ArcCore_Types.arxml:24 |
| [/ArcCore/Platform/BaseTypes/uint16](../platform/BaseTypes.md) | 16 | NONE | uint16 | ArcCore_Types.arxml:34 |
| [/ArcCore/Platform/BaseTypes/uint32](../platform/BaseTypes.md) | 32 | NONE | uint32 | ArcCore_Types.arxml:44 |
| [/ArcCore/Platform/BaseTypes/sint8](../platform/BaseTypes.md) | 8 | 2C | sint8 | ArcCore_Types.arxml:54 |
| [/ArcCore/Platform/BaseTypes/sint16](../platform/BaseTypes.md) | 16 | 2C | sint16 | ArcCore_Types.arxml:64 |
| [/ArcCore/Platform/BaseTypes/sint32](../platform/BaseTypes.md) | 32 | 2C | sint32 | ArcCore_Types.arxml:74 |
| [/ArcCore/Platform/BaseTypes/float32](../platform/BaseTypes.md) | 32 | IEEE754 | float | ArcCore_Types.arxml:84 |
| [/ArcCore/Platform/BaseTypes/float64](../platform/BaseTypes.md) | 64 | IEEE754 | double | ArcCore_Types.arxml:94 |
| [/ArcCore/Platform/BaseTypes/void](../platform/BaseTypes.md) | — | VOID | void | ArcCore_Types.arxml:104 |

## Implementation Data Types (`/ArcCore/Platform/ImplementationDataTypes`)

| Type | Category | Base/Ref | Source Ref |
|------|----------|----------|------------|
| [/ArcCore/Platform/ImplementationDataTypes/boolean](../platform/ImplementationDataTypes.md) | VALUE | BaseTypes/boolean | ArcCore_Types.arxml:118 |
| [/ArcCore/Platform/ImplementationDataTypes/uint8](../platform/ImplementationDataTypes.md) | VALUE | BaseTypes/uint8 | ArcCore_Types.arxml:134 |
| [/ArcCore/Platform/ImplementationDataTypes/uint16](../platform/ImplementationDataTypes.md) | VALUE | BaseTypes/uint16 | ArcCore_Types.arxml:149 |
| [/ArcCore/Platform/ImplementationDataTypes/uint32](../platform/ImplementationDataTypes.md) | VALUE | BaseTypes/uint32 | ArcCore_Types.arxml:164 |
| [/ArcCore/Platform/ImplementationDataTypes/sint8](../platform/ImplementationDataTypes.md) | VALUE | BaseTypes/sint8 | ArcCore_Types.arxml:179 |
| [/ArcCore/Platform/ImplementationDataTypes/sint16](../platform/ImplementationDataTypes.md) | VALUE | BaseTypes/sint16 | ArcCore_Types.arxml:194 |
| [/ArcCore/Platform/ImplementationDataTypes/sint32](../platform/ImplementationDataTypes.md) | VALUE | BaseTypes/sint32 | ArcCore_Types.arxml:209 |
| [/ArcCore/Platform/ImplementationDataTypes/float32](../platform/ImplementationDataTypes.md) | VALUE | BaseTypes/float32 | ArcCore_Types.arxml:224 |
| [/ArcCore/Platform/ImplementationDataTypes/float64](../platform/ImplementationDataTypes.md) | VALUE | BaseTypes/float64 | ArcCore_Types.arxml:239 |
| [/ArcCore/Platform/ImplementationDataTypes/ConstVoidPtr](../platform/ImplementationDataTypes.md) | DATA_REFERENCE | BaseTypes/void (CONST) | ArcCore_Types.arxml:254 |
| [/ArcCore/Platform/ImplementationDataTypes/VoidPtr](../platform/ImplementationDataTypes.md) | DATA_REFERENCE | BaseTypes/void | ArcCore_Types.arxml:275 |

## Compu-Methods (`/ArcCore/Platform/CompuMethods`)

| Compu-Method | Category | Source Ref |
|--------------|----------|------------|
| [/ArcCore/Platform/CompuMethods/boolean](../platform/ImplementationDataTypes.md) | TEXTTABLE | ArcCore_Types.arxml:301 |

## Project-Local Types (`/Demo/Services/IoHwAb`)

| Type | Tag | Category | Refines | Source Ref |
|------|-----|----------|---------|------------|
| [/Demo/Services/IoHwAb/IoHwAb_SignalType_](../platform/ImplementationDataTypes.md) | IMPLEMENTATION-DATA-TYPE | TYPE_REFERENCE | ArcCore uint32 | EcuExtract.arxml:107 |
| [/Demo/Services/IoHwAb/dummy_IoHwAb_SignalType_](../platform/ImplementationDataTypes.md) | APPLICATION-PRIMITIVE-DATA-TYPE | VALUE | — | EcuExtract.arxml:118 |
| [/Demo/Services/IoHwAb/SignalQuality](../platform/ImplementationDataTypes.md) | IMPLEMENTATION-DATA-TYPE | TYPE_REFERENCE | ArcCore uint8 + SignalQuality_def | EcuExtract.arxml:131 |
| [/Demo/Services/IoHwAb/SignalQuality_def](../platform/ImplementationDataTypes.md) | COMPU-METHOD | TEXTTABLE | 4 scales (INIVAL/ERR/BAD/GOOD) | EcuExtract.arxml:143 |
| [/Demo/Services/IoHwAb/DigitalLevel](../platform/ImplementationDataTypes.md) | IMPLEMENTATION-DATA-TYPE | TYPE_REFERENCE | ArcCore uint8 + DigitalLevel_def | EcuExtract.arxml:179 |
| [/Demo/Services/IoHwAb/DigitalLevel_def](../platform/ImplementationDataTypes.md) | COMPU-METHOD | TEXTTABLE | 2 scales (LOW/HIGH) | EcuExtract.arxml:191 |
