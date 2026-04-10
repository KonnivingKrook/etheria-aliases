"""
Smoke tests for the herb alias (Customizations/therb.alias).

End-to-end tests using mocked character data and controlled dice rolls.
Shared fixtures (fresh_ch, cooled_down_ch) come from conftest.

Herb-specific scenarios not covered by mining/lumber:
  - `list` command
  - Disabled tier check (legendary is enabled: false in the gvar)
  - Simple vs complex mode (complex selects a named herb node)
  - set simple/complex/bonus/guidance — verified via both output and cvar state
"""

import pytest
from conftest import GATHER_NOW, set_mock_time, reset_mock_time, run_alias, MockCharacter, MockSkills, MockSkill, MockStats

HERB_ALIAS = "Customizations/therb.alias"


@pytest.fixture(autouse=True)
def fixed_time():
    set_mock_time(GATHER_NOW)
    yield
    reset_mock_time()


class TestHerbHelp:
    def test_help_returns_output(self, fresh_ch):
        output = run_alias(HERB_ALIAS, ["help"], character=fresh_ch)
        assert output is not None
        assert "Herbalism" in output

    def test_list_returns_output(self, fresh_ch):
        output = run_alias(HERB_ALIAS, ["list"], character=fresh_ch)
        assert "Herbalism List" in output

    def test_help_mentions_tiers(self, fresh_ch):
        output = run_alias(HERB_ALIAS, ["help"], character=fresh_ch)
        assert "Common" in output
        assert "Uncommon" in output

    def test_help_mentions_set_commands(self, fresh_ch):
        output = run_alias(HERB_ALIAS, ["help"], character=fresh_ch)
        assert "set" in output


class TestHerbCooldown:
    def test_cooldown_blocks_when_active(self, cooled_down_ch):
        output = run_alias(HERB_ALIAS, [], character=cooled_down_ch)
        assert "Available" in output

    def test_no_cooldown_proceeds(self, fresh_ch):
        output = run_alias(HERB_ALIAS, [], character=fresh_ch, vroll_total=20)
        assert "Herbalism Report" in output


class TestHerbRun:
    def test_successful_run_contains_herbs(self, fresh_ch):
        output = run_alias(HERB_ALIAS, [], character=fresh_ch, vroll_total=20)
        assert "added to your bag" in output

    def test_find_failure_no_resources(self, fresh_ch):
        output = run_alias(HERB_ALIAS, [], character=fresh_ch, vroll_total=1)
        assert "No herbs recovered" in output

    def test_explicit_tier_appears_in_output(self, fresh_ch):
        output = run_alias(HERB_ALIAS, ["common"], character=fresh_ch, vroll_total=20)
        assert "Common" in output

    def test_proficiency_appears_in_reward_lines(self, fresh_ch):
        # fresh_ch has nature prof=1, no tool cvars → skill wins → Proficiency bonus
        output = run_alias(HERB_ALIAS, [], character=fresh_ch, vroll_total=20)
        assert "Proficiency" in output

    def test_surv_override_uses_survival(self, fresh_ch):
        output = run_alias(HERB_ALIAS, ["surv"], character=fresh_ch, vroll_total=20)
        assert "Survival" in output

    def test_nat_override_uses_nature(self, fresh_ch):
        output = run_alias(HERB_ALIAS, ["nat"], character=fresh_ch, vroll_total=20)
        assert "Nature" in output


class TestHerbDisabledTier:
    def test_legendary_tier_blocked(self, fresh_ch):
        # legendary has enabled: false in the gvar
        output = run_alias(HERB_ALIAS, ["legendary"], character=fresh_ch)
        assert "not available" in output

    def test_legendary_alias_blocked(self, fresh_ch):
        # "l" resolves to legendary via tier_aliases
        output = run_alias(HERB_ALIAS, ["l"], character=fresh_ch)
        assert "not available" in output


class TestHerbComplexMode:
    def test_complex_mode_shows_named_herb(self, fresh_ch):
        # mock randchoices always picks first → tier=common → node=Silverleaf
        output = run_alias(HERB_ALIAS, ["complex"], character=fresh_ch, vroll_total=20)
        assert "Silverleaf" in output

    def test_simple_mode_shows_generic_tier_herb(self, fresh_ch):
        output = run_alias(HERB_ALIAS, ["simple"], character=fresh_ch, vroll_total=20)
        assert "Common Herb" in output

    def test_stored_complex_mode_pref_used(self, fresh_ch):
        fresh_ch.set_cvar("herb_mode_pref", "complex")
        output = run_alias(HERB_ALIAS, [], character=fresh_ch, vroll_total=20)
        assert "Silverleaf" in output

    def test_inline_override_beats_stored_pref(self, fresh_ch):
        # stored pref is complex, but -s flag overrides to simple
        fresh_ch.set_cvar("herb_mode_pref", "complex")
        output = run_alias(HERB_ALIAS, ["simple"], character=fresh_ch, vroll_total=20)
        assert "Common Herb" in output


class TestHerbSetSubcommand:
    def test_set_no_target_shows_settings(self, fresh_ch):
        output = run_alias(HERB_ALIAS, ["set"], character=fresh_ch)
        assert "Herbalism" in output
        assert "set" in output

    def test_set_simple_saves_cvar(self, fresh_ch):
        output = run_alias(HERB_ALIAS, ["set", "simple"], character=fresh_ch)
        assert "Mode Saved" in output
        assert fresh_ch.get_cvar("herb_mode_pref") == "simple"

    def test_set_complex_saves_cvar(self, fresh_ch):
        output = run_alias(HERB_ALIAS, ["set", "complex"], character=fresh_ch)
        assert "Mode Saved" in output
        assert fresh_ch.get_cvar("herb_mode_pref") == "complex"

    def test_set_bonus_saves_cvar(self, fresh_ch):
        output = run_alias(HERB_ALIAS, ["set", "bonus", "1d4"], character=fresh_ch)
        assert "Bonus Saved" in output
        assert fresh_ch.get_cvar("herb_bonus_pref") == "1d4"

    def test_set_bonus_clear_removes_cvar(self, fresh_ch):
        fresh_ch.set_cvar("herb_bonus_pref", "1d4")
        output = run_alias(HERB_ALIAS, ["set", "bonus", "clear"], character=fresh_ch)
        assert "Bonus Cleared" in output
        assert fresh_ch.get_cvar("herb_bonus_pref") == ""

    def test_set_guidance_on_saves_cvar(self, fresh_ch):
        output = run_alias(HERB_ALIAS, ["set", "guidance", "on"], character=fresh_ch)
        assert "Guidance Preference Saved" in output
        assert fresh_ch.get_cvar("herb_guidance_pref") == "true"

    def test_set_guidance_off_clears_cvar(self, fresh_ch):
        fresh_ch.set_cvar("herb_guidance_pref", "true")
        output = run_alias(HERB_ALIAS, ["set", "guidance", "off"], character=fresh_ch)
        assert "Guidance Cleared" in output
        assert fresh_ch.get_cvar("herb_guidance_pref") == ""


class TestHerbToolAbilitySelection:
    """Verify _best_tool_ability picks the higher-mod ability for herbalism kit."""

    @pytest.fixture
    def int_dominant_ch(self):
        """Character with INT +5, WIS +0, herbalism kit proficiency (no skill prof)."""
        return MockCharacter(
            skills=MockSkills(nature=MockSkill(prof=0, value=0)),
            cvars={"pTools": "herbalism kit"},
            stats=MockStats(prof_bonus=2, wis=0, int=5),
        )

    @pytest.fixture
    def wis_dominant_ch(self):
        """Character with WIS +5, INT +0, herbalism kit proficiency (no skill prof)."""
        return MockCharacter(
            skills=MockSkills(nature=MockSkill(prof=0, value=0)),
            cvars={"pTools": "herbalism kit"},
            stats=MockStats(prof_bonus=2, wis=5, int=0),
        )

    def test_int_higher_mod_uses_int(self, int_dominant_ch):
        output = run_alias(HERB_ALIAS, ["common"], character=int_dominant_ch, vroll_total=20)
        assert "(INT)" in output

    def test_wis_higher_mod_uses_wis(self, wis_dominant_ch):
        output = run_alias(HERB_ALIAS, ["common"], character=wis_dominant_ch, vroll_total=20)
        assert "(WIS)" in output
