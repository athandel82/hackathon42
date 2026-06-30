# Base Types

`SW-BASE-TYPE` definitions from `/ArcCore/Platform/BaseTypes` (CATEGORY: BLUEPRINT).
These are the low-level encodings that implementation data types refine.

| Name | Category | Size (bits) | Encoding | Native Declaration | Source Ref |
|------|----------|------------:|----------|--------------------|------------|
| boolean | FIXED_LENGTH | 8 | BOOLEAN | boolean | ArcCore_Types.arxml:14 |
| uint8 | FIXED_LENGTH | 8 | NONE | uint8 | ArcCore_Types.arxml:24 |
| uint16 | FIXED_LENGTH | 16 | NONE | uint16 | ArcCore_Types.arxml:34 |
| uint32 | FIXED_LENGTH | 32 | NONE | uint32 | ArcCore_Types.arxml:44 |
| sint8 | FIXED_LENGTH | 8 | 2C | sint8 | ArcCore_Types.arxml:54 |
| sint16 | FIXED_LENGTH | 16 | 2C | sint16 | ArcCore_Types.arxml:64 |
| sint32 | FIXED_LENGTH | 32 | 2C | sint32 | ArcCore_Types.arxml:74 |
| float32 | FIXED_LENGTH | 32 | IEEE754 | float | ArcCore_Types.arxml:84 |
| float64 | FIXED_LENGTH | 64 | IEEE754 | double | ArcCore_Types.arxml:94 |
| void | — | — | VOID | void | ArcCore_Types.arxml:104 |

## Usage Notes

- Only `boolean` is referenced by the application interfaces in this extract
  (DoorStatus, DoorCommands, CombinedStatus). `uint8`/`uint32` are referenced by
  the IoHwAb local types. The remaining base types are part of the platform
  blueprint and are not directly used by the modeled components.
