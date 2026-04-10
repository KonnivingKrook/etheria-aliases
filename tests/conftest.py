"""
Shared fixtures, mocks, and loaders for Avrae/Draconic test suite.

Provides:
  - MockCharacter, MockSkill, MockSkills, MockStats  — character model stubs
  - MockRollResult                                   — vroll() stub
  - MockBagLib                                       — baglib stub
  - build_namespace()                                — Draconic builtin injection
  - load_gvar()                                      — exec a .gvar file
  - load_gather_lib() / load_cd_lib()                — convenience loaders
  - ModuleProxy                                      — wrap a namespace as an object
  - run_alias()                                      — execute an alias file end-to-end
  - set_mock_time() / reset_mock_time()              — control time in cd_lib tests
"""

import json
import math
import re
import time as _time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# Draconic preprocessor
# ---------------------------------------------------------------------------

def preprocess_draconic(source):
    """Convert Draconic-specific syntax to valid Python."""
    # Strip Avrae template wrapper (embed/multiline + <drac2>...</drac2>)
    source = re.sub(r'^(embed|multiline)\s*\n', '', source)
    source = re.sub(r'<drac2>\s*\n?', '', source)
    source = re.sub(r'</drac2>', '', source)
    # Strip Draconic string-typed except clauses
    source = re.sub(r'except\s+"[^"]+"\s*:', 'except:', source)
    return source

# ---------------------------------------------------------------------------
# Mock character model
# ---------------------------------------------------------------------------

class MockSkill:
    """Avrae skill object stub.

    prof:  0 = none, 0.5 = Jack of All Trades, 1 = proficient, 2 = expertise
    value: total skill modifier (ability mod + prof component)
    """
    def __init__(self, prof=0, value=0):
        self.prof = prof
        self.value = value

    def d20(self, base_adv=None):
        if base_adv is True:
            return "2d20kh1"
        if base_adv is False:
            return "2d20kl1"
        return "1d20"


class MockSkills:
    NAMES = [
        'athletics', 'acrobatics', 'sleightOfHand', 'stealth',
        'arcana', 'history', 'investigation', 'nature', 'religion',
        'animalHandling', 'insight', 'medicine', 'perception', 'survival',
        'deception', 'intimidation', 'performance', 'persuasion',
    ]

    def __init__(self, **overrides):
        for name in self.NAMES:
            setattr(self, name, overrides.get(name, MockSkill(0, 0)))


class MockStats:
    def __init__(self, prof_bonus=2, **ability_mods):
        self.prof_bonus = prof_bonus
        self._mods = {'str': 0, 'dex': 0, 'con': 0, 'int': 0, 'wis': 0, 'cha': 0}
        self._mods.update({k.lower(): v for k, v in ability_mods.items()})

    def get_mod(self, ability):
        return self._mods.get(ability.lower(), 0)


class MockCharacter:
    def __init__(self, *, skills=None, cvars=None, image=None, stats=None):
        self.skills = skills or MockSkills()
        self._cvars = dict(cvars or {})
        self.image = image or "https://example.com/avatar.png"
        self.stats = stats or MockStats()

    def get_cvar(self, key, default=None):
        return self._cvars.get(key, default)

    def set_cvar(self, key, value):
        self._cvars[key] = str(value)

# ---------------------------------------------------------------------------
# Mock roll result
# ---------------------------------------------------------------------------

class MockRollResult:
    def __init__(self, total=10, expr="1d20"):
        self.total = total
        self._expr = expr

    def __str__(self):
        return f"{self._expr} = {self.total}"

    def __add__(self, other):
        if isinstance(other, str):
            return MockRollResult(total=self.total, expr=self._expr + other)
        return NotImplemented

# ---------------------------------------------------------------------------
# DraconicDict — dict with attribute-style access (mirrors Draconic SafeDict)
# ---------------------------------------------------------------------------

class DraconicDict(dict):
    """Dict subclass supporting both d['key'] and d.key access."""
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __or__(self, other):
        result = DraconicDict(self)
        result.update(other)
        return result

    def __ror__(self, other):
        result = DraconicDict(other)
        result.update(self)
        return result

# ---------------------------------------------------------------------------
# Mock baglib
# ---------------------------------------------------------------------------

class MockBagManager:
    def __init__(self):
        self.bags = {}

    def get_bag(self, name, exact_match=False):
        return (name, self.bags[name]) if name in self.bags else None

    def new_bag(self, name):
        self.bags[name] = {}
        return (name, self.bags[name])

    def modify_item(self, *, item, quantity, bag_name, create_on_fail=False):
        if bag_name in self.bags:
            self.bags[bag_name][item] = self.bags[bag_name].get(item, 0) + quantity

    def save_bags(self):
        pass


class MockBagLib:
    def LoadedBags(self, ch=None, cvar="bags"):
        return MockBagManager()

# ---------------------------------------------------------------------------
# Controllable time
# ---------------------------------------------------------------------------

_FIXED_TIME = None

def set_mock_time(t):
    global _FIXED_TIME
    _FIXED_TIME = float(t)

def reset_mock_time():
    global _FIXED_TIME
    _FIXED_TIME = None

def _mock_time():
    return _FIXED_TIME if _FIXED_TIME is not None else _time.time()

# ---------------------------------------------------------------------------
# Draconic builtins
# ---------------------------------------------------------------------------

def _mock_typeof(val):
    return {
        list: "list",
        tuple: "tuple",
        dict: "SafeDict",
        str: "str",
        int: "int",
        float: "float",
        bool: "bool",
        type(None): "NoneType",
    }.get(type(val), type(val).__name__)


def _mock_randchoices(population, weights=None, k=1):
    """Deterministic: always returns the first element."""
    return [population[0]] if population else []


class _ParseResult:
    """Minimal argparse result stub."""
    def __init__(self):
        self._data = {}

    def get(self, key, default=None):
        return self._data.get(key, default)

# ---------------------------------------------------------------------------
# Namespace builder
# ---------------------------------------------------------------------------

def build_namespace(character=None, vroll_total=10, extra=None):
    ch = character or MockCharacter()

    def _vroll(expr):
        return MockRollResult(total=vroll_total, expr=str(expr))

    def _get(key, default=None):
        return ch.get_cvar(key, default)

    ns = {
        '__builtins__': __builtins__,
        # Character
        'character': lambda: ch,
        # Dice / random
        'vroll': _vroll,
        'randchoices': _mock_randchoices,
        # Type system
        'typeof': _mock_typeof,
        # Module system
        'using': lambda **kwargs: None,
        'baglib': MockBagLib(),
        # Data
        'load_json': json.loads,
        'load_yaml': json.loads,
        'dump_json': json.dumps,
        'get_gvar': lambda uuid: '{}',
        # Arg parsing
        'argparse': lambda args: _ParseResult(),
        # Control flow
        'err': lambda msg: (_ for _ in ()).throw(Exception(str(msg))),
        # Time
        'time': _mock_time,
        # Avrae cvar/svar access
        'get': _get,
        # Math
        'floor': math.floor,
        'ceil': math.ceil,
        'round': round,
        'min': min,
        'max': max,
        'abs': abs,
        # Python builtins
        'int': int,
        'str': str,
        'float': float,
        'bool': bool,
        'list': list,
        'dict': dict,
        'tuple': tuple,
        'set': set,
        'len': len,
        'range': range,
        'enumerate': enumerate,
        'zip': zip,
        'sorted': sorted,
        'reversed': reversed,
        'isinstance': isinstance,
        'hasattr': hasattr,
        'getattr': getattr,
        'repr': repr,
        'type': type,
        'print': print,
    }
    if extra:
        ns.update(extra)
    return ns

# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

class ModuleProxy:
    """Wraps a namespace dict as an object with attribute access."""
    def __init__(self, namespace):
        for k, v in namespace.items():
            if not k.startswith('__'):
                setattr(self, k, v)


def load_gvar(filepath, character=None, vroll_total=10, extra=None):
    """Load and exec a .gvar file, returning the populated namespace."""
    path = REPO_ROOT / filepath
    source = preprocess_draconic(path.read_text())
    ns = build_namespace(character=character, vroll_total=vroll_total, extra=extra)
    exec(compile(source, str(path), 'exec'), ns)
    return ns


def load_gather_lib(character=None, vroll_total=10):
    return load_gvar(
        "gather_lib/gather_lib2_ ba111c52-33c1-4933-a04c-a2c73bf086a2.gvar",
        character=character,
        vroll_total=vroll_total,
    )


def load_cd_lib(character=None):
    return load_gvar(
        "cooldown_lib/cd_lib_ cc413a98-489e-49f9-aac2-907993761792.gvar",
        character=character,
    )


# ---------------------------------------------------------------------------
# Shared gather-alias fixtures
# ---------------------------------------------------------------------------

# Fixed epoch used by all gather alias tests (import this in each test file)
GATHER_NOW = 1_700_000_000

@pytest.fixture
def fresh_ch():
    """Character with no cooldown history and moderate skills."""
    return MockCharacter(
        skills=MockSkills(
            athletics=MockSkill(prof=2, value=9),
            nature=MockSkill(prof=1, value=4),
            survival=MockSkill(prof=0, value=2),
        ),
        cvars={},
        stats=MockStats(prof_bonus=3, str=4),
    )


@pytest.fixture
def cooled_down_ch():
    """Character currently on cooldown (last_hunt set 30 minutes ago)."""
    return MockCharacter(
        skills=MockSkills(
            athletics=MockSkill(prof=1, value=5),
            nature=MockSkill(prof=1, value=4),
        ),
        cvars={"last_hunt": str(GATHER_NOW - 1800)},  # 30 min ago, 2h cooldown active
        stats=MockStats(prof_bonus=3),
    )


# ---------------------------------------------------------------------------
# Alias runner
# ---------------------------------------------------------------------------

_GVAR_SEARCH_DIRS = ['mining', 'lumber', 'herbalism']


def run_alias(filepath, args, *, character=None, vroll_total=10, gvar_overrides=None):
    """
    Execute an alias file and return its output string.

    gvar_overrides: {uuid: dict} — data to serve for specific get_gvar() calls.
    Falls back to local .gvar files for known UUIDs.
    """
    path = REPO_ROOT / filepath
    source = preprocess_draconic(path.read_text())
    source = source.replace('&ARGS&', 'ARGS')

    # Wrap in a function so top-level return statements are valid
    indented = '\n'.join('    ' + line for line in source.split('\n'))
    wrapped = f'def _alias():\n{indented}\n'

    ch = character or MockCharacter()
    gather_ns = load_gather_lib(character=ch, vroll_total=vroll_total)
    cd_ns = load_cd_lib(character=ch)

    # Wrap Cooldowns so it returns DraconicDict (supports dot-notation like Draconic SafeDict)
    _orig_cooldowns = cd_ns['Cooldowns']
    def _cooldowns_factory(*args, **kwargs):
        result = _orig_cooldowns(*args, **kwargs)
        return DraconicDict(result) if isinstance(result, dict) else result
    cd_ns['Cooldowns'] = _cooldowns_factory

    overrides = dict(gvar_overrides or {})

    def _get_gvar(uuid):
        if uuid in overrides:
            return json.dumps(overrides[uuid])
        for search_dir in _GVAR_SEARCH_DIRS:
            gvar_dir = REPO_ROOT / search_dir
            if gvar_dir.is_dir():
                for gvar_file in gvar_dir.glob('*.gvar'):
                    if uuid in gvar_file.name:
                        return gvar_file.read_text()
        return '{}'

    ns = build_namespace(character=ch, vroll_total=vroll_total, extra={
        'ARGS': list(args),
        'gather': ModuleProxy(gather_ns),
        'cdlib': ModuleProxy(cd_ns),
        'get_gvar': _get_gvar,
        'load_json': json.loads,
    })

    exec(compile(wrapped, str(path), 'exec'), ns)
    return ns['_alias']()
