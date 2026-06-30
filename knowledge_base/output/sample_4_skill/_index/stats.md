# Knowledge Base Statistics

| Metric | Count |
|--------|------:|
| Source ARXML files | 2 |
| Total source lines | 1392 |
| Components | 4 |
| Interfaces | 4 |
| Platform types | 21 (10 base + 11 impl) + 6 IoHwAb-local |
| Systems | 1 |
| Signal chains traced | 6 (4 network + command + actuation) |
| Unresolved references | 0 |

## Processing Mode

Small mode — single pass. 2 files (EcuExtract.arxml 869 lines, ArcCore_Types.arxml
523 lines), well under the ~10 files / ~5,000 lines threshold.

## Validation Summary

`python validate_kb.py . --source ../../input/autosar/ARXML` → exit 0 (clean).
Validator: merged advanced build (ignores fenced code blocks/inline code as
illustrative, and resolves sub-element paths via ancestor prefix).

| Check | Result |
|-------|--------|
| Markdown links resolve | PASS |
| AUTOSAR paths in path-index | PASS |
| Source refs valid (file exists, line matches sn_path/UUID) | PASS |
| UUID consistency (MD ↔ source) | PASS |
| Dependency graph bidirectional consistency | PASS |
| Last validated | 2026-06-30 12:27 |
| Auto-fixed this run | 0 |
| Remaining manual issues | 0 |

## Unresolved / Manual Issues

_None_
