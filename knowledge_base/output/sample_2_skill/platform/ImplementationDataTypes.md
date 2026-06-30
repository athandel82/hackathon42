# Implementation Data Types

## Package Information

| Field | Value |
|-------|-------|
| Package | /ArcCore/Platform/ImplementationDataTypes |
| Category | BLUEPRINT |
| Source File | ArcCore_Types.arxml |
| AUTOSAR Schema | R4.0 (autosar_4-0-3.xsd) |

## Description

Implementation data types that map to the platform base types. These are the types used by software components in their port interfaces and internal data. They are emitted via `Platform_Types.h`.

## Value Types

| Name | Category | Base Type Reference | Type Emitter |
|------|----------|---------------------|--------------|
| boolean | VALUE | /ArcCore/Platform/BaseTypes/boolean | Platform_Types.h |
| float32 | VALUE | /ArcCore/Platform/BaseTypes/float32 | Platform_Types.h |
| float64 | VALUE | /ArcCore/Platform/BaseTypes/float64 | Platform_Types.h |
| sint16 | VALUE | /ArcCore/Platform/BaseTypes/sint16 | Platform_Types.h |
| sint32 | VALUE | /ArcCore/Platform/BaseTypes/sint32 | Platform_Types.h |
| sint8 | VALUE | /ArcCore/Platform/BaseTypes/sint8 | Platform_Types.h |
| uint16 | VALUE | /ArcCore/Platform/BaseTypes/uint16 | Platform_Types.h |
| uint32 | VALUE | /ArcCore/Platform/BaseTypes/uint32 | Platform_Types.h |
| uint8 | VALUE | /ArcCore/Platform/BaseTypes/uint8 | Platform_Types.h |

## Pointer Types

| Name | Category | Target Type | Target Category | Const |
|------|----------|-------------|-----------------|-------|
| ConstVoidPtr | DATA_REFERENCE | /ArcCore/Platform/BaseTypes/void | VALUE | Yes (SW-IMPL-POLICY: CONST) |
| VoidPtr | DATA_REFERENCE | /ArcCore/Platform/BaseTypes/void | VALUE | No |

## Computation Methods

### boolean

| Field | Value |
|-------|-------|
| Package | /ArcCore/Platform/CompuMethods |
| Category | TEXTTABLE |

| Internal Value | Physical Value |
|----------------|----------------|
| 0 | FALSE |
| 1 | TRUE |

## AUTOSAR Standard Platform Types

The same implementation data types are also defined under the `/AUTOSAR/Platform/ImplementationDataTypes` package for AUTOSAR standard compatibility. They reference the same ArcCore base types.

## Notes

- The `boolean` type has an associated computation method mapping 0→FALSE and 1→TRUE
- Pointer types (`ConstVoidPtr`, `VoidPtr`) use the `DATA_REFERENCE` category with `SW-POINTER-TARGET-PROPS`
- All value types are generated into the `Platform_Types.h` header file
