# Knowledge Base Input Repositories

This directory contains input repositories used as knowledge base sources.

## Repositories

| Repository | Source | Description |
|---|---|---|
| [autosar](./autosar) | https://github.com/patrikja/autosar | AUTOSAR modeling in Haskell |

## Adding New Repositories

To add a new input repository as a submodule:

```bash
git submodule add <repository-url> knowledge_base/input/<repo-name>
```

After cloning this project, initialize submodules with:

```bash
git submodule update --init --recursive
```
