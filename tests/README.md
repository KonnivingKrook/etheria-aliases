# Tests

Unit and smoke tests for the Etheria gathering aliases and shared libraries.

## Requirements

Python 3.9+ (for `dict | dict` merge syntax used in `cd_lib`).

Install the test dependency:

```bash
pip install pytest
# or
pip install -r requirements-test.txt
```

## Running

From the repo root:

```bash
# Run everything
pytest tests/ -v

# Run a single file
pytest tests/test_gather_lib2.py -v

# Run a single test class or case
pytest tests/test_cd_lib.py::TestGateCvar -v
pytest tests/test_aliases.py::TestMiningAlias::test_expertise_appears_in_reward_lines -v
```

## Test files

| File | What it covers |
|---|---|
| `test_gather_lib2.py` | Unit tests for every public function in `gather_lib2` — tier selection, skill resolution, roll checks, reward calculation, etc. |
| `test_cd_lib.py` | Unit tests for `cd_lib` — timer core, `gate`, `gate_cvar`, `gate_any`, save/load. |
| `test_aliases.py` | Smoke tests for the production aliases (`Customizations/tmine.alias`, `Customizations/tlumber.alias`) — exercises the full pipeline end-to-end with mocked character data and fixed dice rolls. |

## How it works

Avrae aliases and gvars are written in **Draconic**, a Python-like dialect. The test harness (`conftest.py`) runs them inside a normal Python `exec()` call with mocked Draconic builtins:

- `vroll(expr)` — returns a `MockRollResult` with a configurable fixed total (default 10, pass `vroll_total=` to override)
- `character()` — returns a `MockCharacter` stub with controllable skills, stats, and cvars
- `get(key)` — reads from the mock character's cvars (mirrors Draconic's cvar access)
- `randchoices(population, weights, k)` — deterministic, always returns the first element
- `typeof(val)` — maps Python types to Draconic type name strings (`SafeDict`, `str`, etc.)
- `time()` — real wall clock by default; pin it with `set_mock_time(epoch)` for cooldown tests
- `using(...)` — no-op; `gather` and `cdlib` are pre-populated as `ModuleProxy` objects

The preprocessor handles Draconic-specific syntax before `exec()`:

- Strips `embed` / `<drac2>` / `</drac2>` wrapper from alias files
- Rewrites `except "NotDefined":` → `except:` (Draconic string-typed exception clauses)
- Replaces `&ARGS&` with `ARGS` (Avrae argument injection)
- Wraps alias source in `def _alias():` so top-level `return` statements are valid Python

`DraconicDict` is a `dict` subclass that supports both `d['key']` and `d.key` access, mirroring Draconic's `SafeDict`. It is used as the return type of `Cooldowns()` so aliases can call `cd.gate_cvar(...)`.

## Adding tests

**For a library function** — add a class to `test_gather_lib2.py` or `test_cd_lib.py` and use the `g` or `cooldowns` fixture from `conftest.py`.

**For an alias scenario** — add a method to the relevant class in `test_aliases.py` and call `run_alias(ALIAS_PATH, args, character=..., vroll_total=...)`. The return value is the string the alias would post to Discord.

**To mock character data** — build a `MockCharacter` with `MockSkills` and `MockStats`:

```python
ch = MockCharacter(
    skills=MockSkills(
        athletics=MockSkill(prof=2, value=9),   # expertise
        nature=MockSkill(prof=1, value=4),       # proficient
        survival=MockSkill(prof=0, value=2),     # untrained
    ),
    cvars={"last_hunt": str(some_epoch)},
    stats=MockStats(prof_bonus=3, str=4),
)
```

`MockSkill.prof` values: `0` = none, `0.5` = Jack of All Trades, `1` = proficient, `2` = expertise.
