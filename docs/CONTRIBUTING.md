# Contributing Guide

## Workflow
1. Fork & branch: feature/short-description
2. Write tests (if applicable)
3. Keep commits atomic & conventional (see below)
4. Submit PR referencing issue IDs

## Commit Message Format
```
<type>(scope): short summary

Body (why, not what)

Footer (issues, breaking changes)
```
Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert

## Code Style
- Python >=3.13
- Use `ruff` + `black` (planned)
- Type hints mandatory for public functions

## Tests
- Framework TBD (`pytest` likely)

## Security
- Report privately first (add security policy later)
