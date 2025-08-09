# Testing Strategy

## Scope
Outline levels of testing.

## Test Pyramid (Planned)
- Unit: Fast, pure logic
- Integration: Boundary interactions
- E2E (if needed): External contract

## Tooling
- pytest (run via uv)
- coverage
- hypothesis (property-based) optional

## Conventions
- Tests under `tests/` mirroring source tree.

## How to run tests
- Quiet: `uv run pytest -q`
- Verbose: `uv run --with pytest python -m pytest -v`
- Script helper: `scripts/test.sh` (set `VERBOSE=1` for `-v`)
- Fallback (no dev sync): `uvx pytest -q`
