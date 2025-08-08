# Coding Standards

## General
- Prefer clarity over cleverness.
- Pure functions where practical.
- Fail fast with meaningful errors.

## Python
- Use `typing` & `collections.abc` for annotations.
- Use dataclasses for simple data aggregates.
- Avoid hard-coded constants; centralize in `config`.

## Error Handling
- Raise domain-specific exceptions (future `exceptions.py`).
- Avoid silent excepts.

## Logging (Planned)
- Use `structlog` or stdlib logging with structured output (JSON) for machine parsing.

## TODO / FIXME Tags
```
# TODO(tag): description
# FIXME(tag): description
```
Automated tooling will parse these.
