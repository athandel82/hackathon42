# Platform Base Types

## Package Information

| Field | Value |
|-------|-------|
| Package | /ArcCore/Platform/BaseTypes |
| Package UUID | (none on package element) |
| Category | BLUEPRINT |
| Source File | ArcCore_Types.arxml |
| AUTOSAR Schema | autosar_4-0-3.xsd (r4.0) |

## Base Types

`Consumers` = implementation data types that reference this base type (the
`/ArcCore` set plus the duplicate `/AUTOSAR` set).

| Name | Size (bits) | Encoding | Native Declaration | Consumers | Description |
|------|-------------|----------|--------------------|----------:|-------------|
| boolean | 8 | BOOLEAN | boolean | 2 | Boolean fixed-length type |
| uint8 | 8 | NONE | uint8 | 2 | Unsigned 8-bit |
| uint16 | 16 | NONE | uint16 | 2 | Unsigned 16-bit |
| uint32 | 32 | NONE | uint32 | 2 | Unsigned 32-bit |
| sint8 | 8 | 2C | sint8 | 2 | Signed 8-bit (two's complement) |
| sint16 | 16 | 2C | sint16 | 2 | Signed 16-bit (two's complement) |
| sint32 | 32 | 2C | sint32 | 2 | Signed 32-bit (two's complement) |
| float32 | 32 | IEEE754 | float | 2 | Single-precision float |
| float64 | 64 | IEEE754 | double | 2 | Double-precision float |
| void | (none) | VOID | void | 4 | Void base type (used by pointer types) |

## Notes

- All sized types are `CATEGORY=FIXED_LENGTH`. `void` has no `BASE-TYPE-SIZE`.
- `void` is referenced by `ConstVoidPtr` and `VoidPtr` in both the `/ArcCore` and
  `/AUTOSAR` implementation-data-type sets, hence 4 consumers.
- These base types underpin the implementation data types documented in
  [ImplementationDataTypes.md](ImplementationDataTypes.md).
