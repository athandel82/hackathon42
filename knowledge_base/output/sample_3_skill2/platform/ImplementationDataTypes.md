# Implementation Data Types

This file groups all implementation data types, application data types, and
computation methods from the platform packages and the IoHwAb-local package.

## Package Information

| Field | Value |
|-------|-------|
| Packages | /ArcCore/Platform/ImplementationDataTypes, /AUTOSAR/Platform/ImplementationDataTypes, /ArcCore/Platform/CompuMethods, /Demo/Services/IoHwAb |
| Category | BLUEPRINT (platform packages) |
| Source Files | ArcCore_Types.arxml, EcuExtract.arxml |
| AUTOSAR Schema | autosar_4-0-3.xsd / autosar_4-1-1.xsd (r4.0) |

## Value Types — `/ArcCore/Platform/ImplementationDataTypes`

| Name | Category | Base Type Reference | Type Emitter | Consumers |
|------|----------|---------------------|--------------|----------:|
| boolean | VALUE | [/ArcCore/Platform/BaseTypes/boolean](BaseTypes.md) (compu /ArcCore/Platform/CompuMethods/boolean) | Platform_Types.h | 7 |
| uint8 | VALUE | [/ArcCore/Platform/BaseTypes/uint8](BaseTypes.md) | Platform_Types.h | 2 |
| uint16 | VALUE | [/ArcCore/Platform/BaseTypes/uint16](BaseTypes.md) | Platform_Types.h | 0 |
| uint32 | VALUE | [/ArcCore/Platform/BaseTypes/uint32](BaseTypes.md) | Platform_Types.h | 1 |
| sint8 | VALUE | [/ArcCore/Platform/BaseTypes/sint8](BaseTypes.md) | Platform_Types.h | 0 |
| sint16 | VALUE | [/ArcCore/Platform/BaseTypes/sint16](BaseTypes.md) | Platform_Types.h | 0 |
| sint32 | VALUE | [/ArcCore/Platform/BaseTypes/sint32](BaseTypes.md) | Platform_Types.h | 0 |
| float32 | VALUE | [/ArcCore/Platform/BaseTypes/float32](BaseTypes.md) | Platform_Types.h | 0 |
| float64 | VALUE | [/ArcCore/Platform/BaseTypes/float64](BaseTypes.md) | Platform_Types.h | 0 |

## Pointer Types — `/ArcCore/Platform/ImplementationDataTypes`

| Name | Category | Target Type | Target Category | Const |
|------|----------|-------------|-----------------|-------|
| ConstVoidPtr | DATA_REFERENCE | [/ArcCore/Platform/BaseTypes/void](BaseTypes.md) | VALUE | yes (SW-IMPL-POLICY CONST) |
| VoidPtr | DATA_REFERENCE | [/ArcCore/Platform/BaseTypes/void](BaseTypes.md) | VALUE | no |

## Duplicate Set — `/AUTOSAR/Platform/ImplementationDataTypes`

A second blueprint package defines the same eleven types (boolean, uint8, uint16,
uint32, sint8, sint16, sint32, float32, float64, ConstVoidPtr, VoidPtr) with
identical base-type references and `TYPE-EMITTER=Platform_Types.h`. **Not
referenced by any element in the ECU extract** — the model uses the `/ArcCore`
set. Retained here for completeness.

## IoHwAb-Local Types — `/Demo/Services/IoHwAb` (from EcuExtract.arxml)

| Name | Category | Resolves To | Compu Method | UUID | Consumers |
|------|----------|-------------|--------------|------|----------:|
| IoHwAb_SignalType_ | TYPE_REFERENCE | [/ArcCore/Platform/ImplementationDataTypes/uint32](#) | — | 6e499ceb-e086-39a3-a8aa-cad156c2235d | 1 (port-defined arg on IoHwAb.Digital_Led) |
| SignalQuality | TYPE_REFERENCE | [/ArcCore/Platform/ImplementationDataTypes/uint8](#) | SignalQuality_def | db4b6add-7698-3ee4-9dae-adaa7488c81a | 0 |
| DigitalLevel | TYPE_REFERENCE | [/ArcCore/Platform/ImplementationDataTypes/uint8](#) | DigitalLevel_def | ce7d4658-6239-3091-8e78-7747c6a4fdfd | 1 (DigitalServiceWrite.Write.Level) |
| dummy_IoHwAb_SignalType_ | APPLICATION-PRIMITIVE (VALUE) | — | — | 8968fc96-1503-316f-ba51-1e3d7e72eaae | 1 (mapped to IoHwAb_SignalType_) |

### Data Type Mapping Set: dummyMappingSet

| Application Data Type | Implementation Data Type |
|-----------------------|--------------------------|
| /Demo/Services/IoHwAb/dummy_IoHwAb_SignalType_ | /Demo/Services/IoHwAb/IoHwAb_SignalType_ |

UUID: 280a6153-330a-3898-bc36-1586c4372f47

## Computation Methods

### boolean — `/ArcCore/Platform/CompuMethods` (TEXTTABLE)

| Internal Value | Physical Value |
|----------------|----------------|
| 0 | FALSE |
| 1 | TRUE |

### SignalQuality_def — `/Demo/Services/IoHwAb` (TEXTTABLE)

UUID: b846afca-e52e-31cd-8e75-8cd16e26e46f

| Internal Value | Physical Value |
|----------------|----------------|
| 0 | IOHWAB_INIVAL |
| 1 | IOHWAB_ERR |
| 2 | IOHWAB_BAD |
| 3 | IOHWAB_GOOD |

### DigitalLevel_def — `/Demo/Services/IoHwAb` (TEXTTABLE)

UUID: f716328f-e783-329b-a342-af0ccd060cef

| Internal Value | Physical Value |
|----------------|----------------|
| 0 | IOHWAB_LOW |
| 1 | IOHWAB_HIGH |
