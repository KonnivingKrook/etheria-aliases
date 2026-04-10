"""
Smoke tests for the mining alias (Customizations/tmine.alias).

End-to-end tests using mocked character data and controlled dice rolls.
Shared fixtures (fresh_ch, cooled_down_ch) come from conftest.
"""

import pytest
from conftest import GATHER_NOW, set_mock_time, reset_mock_time, run_alias

MINING_ALIAS = "Customizations/tmine.alias"


@pytest.fixture(autouse=True)
def fixed_time():
    set_mock_time(GATHER_NOW)
    yield
    reset_mock_time()


class TestMiningHelp:
    def test_help_returns_output(self, fresh_ch):
        output = run_alias(MINING_ALIAS, ["help"], character=fresh_ch)
        assert output is not None
        assert "Mining" in output

    def test_help_mentions_set_commands(self, fresh_ch):
        output = run_alias(MINING_ALIAS, ["help"], character=fresh_ch)
        assert "set" in output


class TestMiningCooldown:
    def test_cooldown_blocks_when_active(self, cooled_down_ch):
        output = run_alias(MINING_ALIAS, [], character=cooled_down_ch)
        assert "Available" in output

    def test_no_cooldown_proceeds(self, fresh_ch):
        output = run_alias(MINING_ALIAS, [], character=fresh_ch, vroll_total=20)
        assert "Mining Report" in output


class TestMiningRun:
    def test_successful_run_contains_resources(self, fresh_ch):
        output = run_alias(MINING_ALIAS, [], character=fresh_ch, vroll_total=20)
        assert "added to your bag" in output

    def test_find_failure_no_resources(self, fresh_ch):
        output = run_alias(MINING_ALIAS, [], character=fresh_ch, vroll_total=1)
        assert "No usable material" in output or "nothing workable" in output

    def test_explicit_tier_appears_in_output(self, fresh_ch):
        output = run_alias(MINING_ALIAS, ["common"], character=fresh_ch, vroll_total=20)
        assert "Common" in output

    def test_expertise_appears_in_reward_lines(self, fresh_ch):
        output = run_alias(MINING_ALIAS, [], character=fresh_ch, vroll_total=20)
        assert "Expertise" in output

    def test_proficiency_appears_in_reward_lines(self, fresh_ch):
        output = run_alias(MINING_ALIAS, [], character=fresh_ch, vroll_total=20)
        assert "Proficiency" in output


class TestMiningDisabledTier:
    def test_legendary_tier_blocked(self, fresh_ch):
        output = run_alias(MINING_ALIAS, ["legendary"], character=fresh_ch)
        assert "unavailable" in output

    def test_legendary_alias_blocked(self, fresh_ch):
        # "l" resolves to legendary via tier_aliases
        output = run_alias(MINING_ALIAS, ["l"], character=fresh_ch)
        assert "unavailable" in output


class TestMiningComplexMode:
    def test_complex_mode_shows_named_node(self, fresh_ch):
        # mock randchoices always picks first → tier=basic → node=Stone
        output = run_alias(MINING_ALIAS, ["basic", "complex"], character=fresh_ch, vroll_total=20)
        assert "Stone" in output

    def test_simple_mode_shows_generic_tier_ore(self, fresh_ch):
        output = run_alias(MINING_ALIAS, ["basic", "simple"], character=fresh_ch, vroll_total=20)
        assert "Basic Ore" in output

    def test_stored_complex_mode_pref_used(self, fresh_ch):
        fresh_ch.set_cvar("tmine_mode_pref", "complex")
        output = run_alias(MINING_ALIAS, ["basic"], character=fresh_ch, vroll_total=20)
        assert "Stone" in output

    def test_inline_override_beats_stored_pref(self, fresh_ch):
        # stored pref is complex, but simple flag overrides
        fresh_ch.set_cvar("tmine_mode_pref", "complex")
        output = run_alias(MINING_ALIAS, ["basic", "simple"], character=fresh_ch, vroll_total=20)
        assert "Basic Ore" in output


class TestMiningSetSubcommand:
    def test_set_no_target_shows_settings(self, fresh_ch):
        output = run_alias(MINING_ALIAS, ["set"], character=fresh_ch)
        assert "Mining" in output
        assert "set" in output

    def test_set_simple_saves_cvar(self, fresh_ch):
        output = run_alias(MINING_ALIAS, ["set", "simple"], character=fresh_ch)
        assert "Mode Saved" in output
        assert fresh_ch.get_cvar("tmine_mode_pref") == "simple"

    def test_set_complex_saves_cvar(self, fresh_ch):
        output = run_alias(MINING_ALIAS, ["set", "complex"], character=fresh_ch)
        assert "Mode Saved" in output
        assert fresh_ch.get_cvar("tmine_mode_pref") == "complex"

    def test_set_bonus_saves_cvar(self, fresh_ch):
        output = run_alias(MINING_ALIAS, ["set", "bonus", "1d4"], character=fresh_ch)
        assert "Bonus Saved" in output
        assert fresh_ch.get_cvar("tmine_bonus_pref") == "1d4"

    def test_set_bonus_clear_removes_cvar(self, fresh_ch):
        fresh_ch.set_cvar("tmine_bonus_pref", "1d4")
        output = run_alias(MINING_ALIAS, ["set", "bonus", "clear"], character=fresh_ch)
        assert "Bonus Cleared" in output
        assert fresh_ch.get_cvar("tmine_bonus_pref") == ""

    def test_set_guidance_on_saves_cvar(self, fresh_ch):
        output = run_alias(MINING_ALIAS, ["set", "guidance", "on"], character=fresh_ch)
        assert "Guidance Preference Saved" in output
        assert fresh_ch.get_cvar("tmine_guidance_pref") == "true"

    def test_set_guidance_off_clears_cvar(self, fresh_ch):
        fresh_ch.set_cvar("tmine_guidance_pref", "true")
        output = run_alias(MINING_ALIAS, ["set", "guidance", "off"], character=fresh_ch)
        assert "Guidance Cleared" in output
        assert fresh_ch.get_cvar("tmine_guidance_pref") == ""
