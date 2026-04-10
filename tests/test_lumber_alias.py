"""
Smoke tests for the lumber alias (Customizations/tlumber.alias).

End-to-end tests using mocked character data and controlled dice rolls.
Shared fixtures (fresh_ch, cooled_down_ch) come from conftest.

Lumber has no complex mode or disabled tiers, so those classes are absent.
"""

import pytest
from conftest import GATHER_NOW, set_mock_time, reset_mock_time, run_alias

LUMBER_ALIAS = "Customizations/tlumber.alias"


@pytest.fixture(autouse=True)
def fixed_time():
    set_mock_time(GATHER_NOW)
    yield
    reset_mock_time()


class TestLumberHelp:
    def test_help_returns_output(self, fresh_ch):
        output = run_alias(LUMBER_ALIAS, ["help"], character=fresh_ch)
        assert output is not None
        assert "Lumbering" in output

    def test_help_mentions_set_commands(self, fresh_ch):
        output = run_alias(LUMBER_ALIAS, ["help"], character=fresh_ch)
        assert "set" in output


class TestLumberCooldown:
    def test_cooldown_blocks_when_active(self, cooled_down_ch):
        output = run_alias(LUMBER_ALIAS, [], character=cooled_down_ch)
        assert "Available" in output

    def test_no_cooldown_proceeds(self, fresh_ch):
        output = run_alias(LUMBER_ALIAS, [], character=fresh_ch, vroll_total=20)
        assert "Lumbering" in output


class TestLumberRun:
    def test_successful_run_contains_lumber(self, fresh_ch):
        output = run_alias(LUMBER_ALIAS, [], character=fresh_ch, vroll_total=20)
        assert "Lumber" in output

    def test_find_failure_no_resources(self, fresh_ch):
        output = run_alias(LUMBER_ALIAS, [], character=fresh_ch, vroll_total=1)
        assert "No resources" in output or "No workable" in output

    def test_explicit_tier_appears_in_output(self, fresh_ch):
        output = run_alias(LUMBER_ALIAS, ["common"], character=fresh_ch, vroll_total=20)
        assert "Common" in output

    def test_nat_override_uses_nature(self, fresh_ch):
        output = run_alias(LUMBER_ALIAS, ["nat"], character=fresh_ch, vroll_total=20)
        assert "Nature" in output

    def test_surv_override_uses_survival(self, fresh_ch):
        output = run_alias(LUMBER_ALIAS, ["surv"], character=fresh_ch, vroll_total=20)
        assert "Survival" in output


class TestLumberSetSubcommand:
    def test_set_no_target_shows_settings(self, fresh_ch):
        output = run_alias(LUMBER_ALIAS, ["set"], character=fresh_ch)
        assert "Lumber" in output
        assert "set" in output

    def test_set_bonus_saves_cvar(self, fresh_ch):
        output = run_alias(LUMBER_ALIAS, ["set", "bonus", "1d4"], character=fresh_ch)
        assert "Bonus Saved" in output
        assert fresh_ch.get_cvar("lumber_bonus_pref") == "1d4"

    def test_set_bonus_clear_removes_cvar(self, fresh_ch):
        fresh_ch.set_cvar("lumber_bonus_pref", "1d4")
        output = run_alias(LUMBER_ALIAS, ["set", "bonus", "clear"], character=fresh_ch)
        assert "Bonus Cleared" in output
        assert fresh_ch.get_cvar("lumber_bonus_pref") == ""

    def test_set_guidance_on_saves_cvar(self, fresh_ch):
        output = run_alias(LUMBER_ALIAS, ["set", "guidance", "on"], character=fresh_ch)
        assert "Guidance Preference Saved" in output
        assert fresh_ch.get_cvar("lumber_guidance_pref") == "true"

    def test_set_guidance_off_clears_cvar(self, fresh_ch):
        fresh_ch.set_cvar("lumber_guidance_pref", "true")
        output = run_alias(LUMBER_ALIAS, ["set", "guidance", "off"], character=fresh_ch)
        assert "Guidance Cleared" in output
        assert fresh_ch.get_cvar("lumber_guidance_pref") == ""
