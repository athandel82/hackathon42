# Platform Base Types

## Package Information

| Field | Value |
|-------|-------|
| Package | /ArcCore/Platform/BaseTypes |
| Category | BLUEPRINT |
| Source File | ArcCore_Types.arxml |
| AUTOSAR Schema | R4.0 (autosar_4-0-3.xsd) |

## Description

Defines the fundamental software base types used across the AUTOSAR platform. These map to native C data types and provide the foundation for all implementation data types.

## Base Types

| Name | Size (bits) | Encoding | Native Declaration | Description |
|------|-------------|----------|-------------------|-------------|
| boolean | 8 | BOOLEAN | boolean | Boolean type (TRUE/FALSE) |
| float32 | 32 | IEEE754 | float | 32-bit IEEE 754 floating point |
| float64 | 64 | IEEE754 | double | 64-bit IEEE 754 floating point |
| sint16 | 16 | 2C | sint16 | Signed 16-bit integer (two's complement) |
| sint32 | 32 | 2C | sint32 | Signed 32-bit integer (two's complement) |
| sint8 | 8 | 2C | sint8 | Signed 8-bit integer (two's complement) |
| uint16 | 16 | NONE | uint16 | Unsigned 16-bit integer |
| uint32 | 32 | NONE | uint32 | Unsigned 32-bit integer |
| uint8 | 8 | NONE | uint8 | Unsigned 8-bit integer |
| void | — | VOID | void | Void type (used for pointer targets) |

## Notes

- All numeric types use `FIXED_LENGTH` category
- Signed integers use two's complement (2C) encoding
- Floating point types use IEEE 754 encoding
- The `void` type has no specified size and is used as a pointer target for `ConstVoidPtr` and `VoidPtr` implementation data types
