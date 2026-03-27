"""Unit tests for cd_lib (CooldownLib)."""

import pytest
from conftest import (
    MockCharacter,
    load_cd_lib,
    set_mock_time,
    reset_mock_time,
)

NOW = 1_700_000_000  # fixed epoch for deterministic tests


@pytest.fixture(autouse=True)
def fixed_time():
    """Pin time to NOW for all tests in this module."""
    set_mock_time(NOW)
    yield
    reset_mock_time()


@pytest.fixture
def ch():
    return MockCharacter()


@pytest.fixture
def cooldowns(ch):
    """Return a fresh Cooldowns() instance."""
    ns = load_cd_lib(character=ch)
    return ns['Cooldowns']()


# ---------------------------------------------------------------------------
# ts / format_window / format_remaining
# ---------------------------------------------------------------------------

class TestFormatting:
    def test_ts_relative(self, cooldowns):
        assert cooldowns['ts'](12345, "R") == "<t:12345:R>"

    def test_ts_date(self, cooldowns):
        assert cooldowns['ts'](12345, "D") == "<t:12345:D>"

    def test_format_remaining_short(self, cooldowns):
        # 60 seconds from now → "in 60 seconds"
        result = cooldowns['format_remaining'](60)
        assert "in 60 seconds" == result

    def test_format_remaining_long(self, cooldowns):
        # 7200 seconds (2 hours) → relative discord timestamp
        result = cooldowns['format_remaining'](7200)
        expiry = NOW + 7200
        assert f"<t:{expiry}:R>" == result

    def test_format_remaining_over_24h(self, cooldowns):
        # 90000 seconds (25 hours) → date + time timestamps
        result = cooldowns['format_remaining'](90000)
        assert "<t:" in result
        assert ":D>" in result
        assert ":T>" in result


# ---------------------------------------------------------------------------
# set_timer / get_expiry / remaining / ready
# ---------------------------------------------------------------------------

class TestTimerCore:
    def test_set_timer_returns_expiry(self, cooldowns):
        expiry = cooldowns['set_timer']("mining", 7200, now=NOW)
        assert expiry == NOW + 7200

    def test_get_expiry_after_set(self, cooldowns):
        cooldowns['set_timer']("mining", 7200, now=NOW)
        assert cooldowns['get_expiry']("mining") == NOW + 7200

    def test_get_expiry_missing_key(self, cooldowns):
        assert cooldowns['get_expiry']("missing") is None

    def test_remaining_active(self, cooldowns):
        cooldowns['set_timer']("mining", 7200, now=NOW)
        assert cooldowns['remaining']("mining", now=NOW) == 7200

    def test_remaining_expired(self, cooldowns):
        cooldowns['set_timer']("mining", 7200, now=NOW)
        assert cooldowns['remaining']("mining", now=NOW + 8000) == 0

    def test_ready_when_no_timer(self, cooldowns):
        assert cooldowns['ready']("mining") is True

    def test_ready_when_active(self, cooldowns):
        cooldowns['set_timer']("mining", 7200, now=NOW)
        assert cooldowns['ready']("mining", now=NOW + 100) is False

    def test_ready_when_expired(self, cooldowns):
        cooldowns['set_timer']("mining", 7200, now=NOW)
        assert cooldowns['ready']("mining", now=NOW + 9000) is True

    def test_clear_removes_timer(self, cooldowns):
        cooldowns['set_timer']("mining", 7200, now=NOW)
        assert cooldowns['clear']("mining") is True
        assert cooldowns['get_expiry']("mining") is None

    def test_clear_missing_key_returns_false(self, cooldowns):
        assert cooldowns['clear']("missing") is False


# ---------------------------------------------------------------------------
# gate (internal store)
# ---------------------------------------------------------------------------

class TestGate:
    def test_passes_when_no_timer(self, cooldowns):
        result = cooldowns['gate']("mining", 7200, now=NOW)
        assert result["ok"] is True

    def test_sets_timer_on_pass(self, cooldowns):
        cooldowns['gate']("mining", 7200, now=NOW)
        assert cooldowns['get_expiry']("mining") == NOW + 7200

    def test_blocks_when_active(self, cooldowns):
        cooldowns['set_timer']("mining", 7200, now=NOW)
        result = cooldowns['gate']("mining", 7200, now=NOW + 100)
        assert result["ok"] is False
        assert result["remaining"] == 7100

    def test_does_not_modify_when_blocked(self, cooldowns):
        cooldowns['set_timer']("mining", 7200, now=NOW)
        original_expiry = cooldowns['get_expiry']("mining")
        cooldowns['gate']("mining", 7200, now=NOW + 100)
        assert cooldowns['get_expiry']("mining") == original_expiry

    def test_passes_after_expiry(self, cooldowns):
        cooldowns['set_timer']("mining", 7200, now=NOW)
        result = cooldowns['gate']("mining", 7200, now=NOW + 9000)
        assert result["ok"] is True

    def test_set_on_pass_false_does_not_set(self, cooldowns):
        result = cooldowns['gate']("mining", 7200, now=NOW, set_on_pass=False)
        assert result["ok"] is True
        assert cooldowns['get_expiry']("mining") is None


# ---------------------------------------------------------------------------
# gate_cvar (external start-time cvar)
# ---------------------------------------------------------------------------

class TestGateCvar:
    def test_passes_when_no_cvar(self, ch):
        ns = load_cd_lib(character=ch)
        cd = ns['Cooldowns']()
        result = cd['gate_cvar']("last_hunt", 7200, now=NOW)
        assert result["ok"] is True

    def test_writes_cvar_on_pass(self, ch):
        ns = load_cd_lib(character=ch)
        cd = ns['Cooldowns']()
        cd['gate_cvar']("last_hunt", 7200, now=NOW)
        assert ch.get_cvar("last_hunt") == str(NOW)

    def test_blocks_when_within_cooldown(self, ch):
        ch.set_cvar("last_hunt", str(NOW - 3600))  # started 1 hour ago
        ns = load_cd_lib(character=ch)
        cd = ns['Cooldowns']()
        result = cd['gate_cvar']("last_hunt", 7200, now=NOW)
        assert result["ok"] is False
        assert result["remaining"] == 3600

    def test_passes_when_cooldown_expired(self, ch):
        ch.set_cvar("last_hunt", str(NOW - 9000))  # started 2.5 hours ago
        ns = load_cd_lib(character=ch)
        cd = ns['Cooldowns']()
        result = cd['gate_cvar']("last_hunt", 7200, now=NOW)
        assert result["ok"] is True

    def test_expiry_is_start_plus_seconds(self, ch):
        start = NOW - 3600
        ch.set_cvar("last_hunt", str(start))
        ns = load_cd_lib(character=ch)
        cd = ns['Cooldowns']()
        result = cd['gate_cvar']("last_hunt", 7200, now=NOW)
        assert result["expiry"] == int(start) + 7200

    def test_does_not_write_when_blocked(self, ch):
        start = NOW - 3600
        ch.set_cvar("last_hunt", str(start))
        ns = load_cd_lib(character=ch)
        cd = ns['Cooldowns']()
        cd['gate_cvar']("last_hunt", 7200, now=NOW)
        # cvar should still be the original start time
        assert ch.get_cvar("last_hunt") == str(start)

    def test_set_on_pass_false_does_not_write(self, ch):
        ns = load_cd_lib(character=ch)
        cd = ns['Cooldowns']()
        cd['gate_cvar']("last_hunt", 7200, now=NOW, set_on_pass=False)
        assert ch.get_cvar("last_hunt") is None


# ---------------------------------------------------------------------------
# gate_any
# ---------------------------------------------------------------------------

class TestGateAny:
    def test_passes_when_all_clear(self, cooldowns):
        result = cooldowns['gate_any'](["a", "b"], 3600, now=NOW)
        assert result["ok"] is True

    def test_blocked_if_any_active(self, cooldowns):
        cooldowns['set_timer']("a", 3600, now=NOW)
        result = cooldowns['gate_any'](["a", "b"], 3600, now=NOW + 100)
        assert result["ok"] is False
        assert any(b["key"] == "a" for b in result["blocked"])

    def test_sets_all_keys_on_pass(self, cooldowns):
        cooldowns['gate_any'](["a", "b"], 3600, now=NOW)
        assert cooldowns['get_expiry']("a") == NOW + 3600
        assert cooldowns['get_expiry']("b") == NOW + 3600


# ---------------------------------------------------------------------------
# save
# ---------------------------------------------------------------------------

class TestSave:
    def test_save_writes_cvar(self, ch):
        ns = load_cd_lib(character=ch)
        cd = ns['Cooldowns']()
        cd['set_timer']("mining", 7200, now=NOW)
        result = cd['save']()
        assert result == 1
        assert ch.get_cvar("cooldowns") is not None

    def test_save_returns_minus_one_on_error(self, ch):
        ns = load_cd_lib(character=ch)
        cd = ns['Cooldowns']()
        result = cd['save'](error=True)
        assert result == -1

    def test_save_skipped_when_user_mode_false(self, ch):
        ns = load_cd_lib(character=ch)
        cd = ns['Cooldowns'](user_mode=False)
        cd['set_timer']("mining", 7200, now=NOW)
        result = cd['save']()
        assert result == -1
        assert ch.get_cvar("cooldowns") is None
