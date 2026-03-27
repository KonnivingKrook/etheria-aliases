"""Unit tests for gather_lib2."""

import pytest
from conftest import (
    MockCharacter, MockSkill, MockSkills, MockStats,
    load_gather_lib,
)


@pytest.fixture
def g():
    return load_gather_lib()


@pytest.fixture
def expert_ch():
    """Character with Athletics expertise, Nature proficiency, Survival untrained."""
    return MockCharacter(
        skills=MockSkills(
            athletics=MockSkill(prof=2, value=9),
            nature=MockSkill(prof=1, value=4),
            survival=MockSkill(prof=0, value=2),
        ),
        cvars={"eTools": "mason's tools", "pTools": "woodcarver's tools"},
        stats=MockStats(prof_bonus=3, str=4),
    )


# ---------------------------------------------------------------------------
# title_words
# ---------------------------------------------------------------------------

class TestTitleWords:
    def test_basic(self, g):
        assert g['title_words']("hello world") == "Hello World"

    def test_single_char_words(self, g):
        assert g['title_words']("a b c") == "A B C"

    def test_empty_returns_default(self, g):
        assert g['title_words']("", default="Fallback") == "Fallback"

    def test_none_returns_default(self, g):
        assert g['title_words'](None, default="None") == "None"

    def test_extra_spaces_collapsed(self, g):
        assert g['title_words']("hello  world") == "Hello World"

    def test_single_word(self, g):
        assert g['title_words']("mithril") == "Mithril"


# ---------------------------------------------------------------------------
# q (quote helper)
# ---------------------------------------------------------------------------

class TestQ:
    def test_replaces_double_with_single_quotes(self, g):
        assert g['q']('say "hello"') == "say 'hello'"

    def test_none_returns_empty_string(self, g):
        assert g['q'](None) == ""

    def test_no_quotes_unchanged(self, g):
        assert g['q']("hello world") == "hello world"


# ---------------------------------------------------------------------------
# resolve_tier
# ---------------------------------------------------------------------------

class TestResolveTier:
    def test_resolves_alias(self, g):
        assert g['resolve_tier']("c", {"c": "common"}) == "common"

    def test_passthrough_unknown(self, g):
        assert g['resolve_tier']("common", {}) == "common"

    def test_empty_cmd_returns_empty(self, g):
        assert g['resolve_tier']("", {}) == ""

    def test_normalizes_to_lowercase(self, g):
        assert g['resolve_tier']("COMMON", {"common": "common"}) == "common"


# ---------------------------------------------------------------------------
# pick_weighted_label
# ---------------------------------------------------------------------------

class TestPickWeightedLabel:
    def test_returns_label_from_pool(self, g):
        result = g['pick_weighted_label']({"common": 70, "uncommon": 25})
        assert result in ["common", "uncommon"]

    def test_empty_map_returns_default(self, g):
        assert g['pick_weighted_label']({}, default_label="common") == "common"

    def test_zero_weight_excluded(self, g):
        # Only "rare" has positive weight; mock randchoices picks first
        result = g['pick_weighted_label']({"common": 0, "rare": 10})
        assert result == "rare"


# ---------------------------------------------------------------------------
# select_tier
# ---------------------------------------------------------------------------

class TestSelectTier:
    MINING_DATA = {
        "tiers": {
            "basic":    {"dc": 11, "label": "Basic",    "enabled": True},
            "common":   {"dc": 13, "label": "Common",   "enabled": True},
            "uncommon": {"dc": 16, "label": "Uncommon", "enabled": True},
        },
        "tier_aliases": {"b": "basic", "c": "common", "u": "uncommon"},
        "config": {"default_tier": "common"},
    }

    def test_explicit_tier_cmd(self, g):
        result = g['select_tier'](self.MINING_DATA, "common")
        assert result["tier"] == "common"
        assert result["mode"] == "tier"

    def test_alias_resolves(self, g):
        result = g['select_tier'](self.MINING_DATA, "c")
        assert result["tier"] == "common"

    def test_empty_cmd_uses_weighted(self, g):
        result = g['select_tier'](self.MINING_DATA, "")
        assert result["mode"] == "all"
        assert result["tier"] in ["basic", "common", "uncommon"]

    def test_dc_matches_tier(self, g):
        result = g['select_tier'](self.MINING_DATA, "uncommon")
        assert result["dc_val"] == 16

    def test_disabled_tier_not_selected(self, g):
        data = {
            "tiers": {
                "common":   {"dc": 13, "enabled": True},
                "legendary": {"dc": 30, "enabled": False},
            },
            "config": {"default_tier": "common"},
        }
        result = g['select_tier'](data, "legendary")
        # legendary not in enabled pool, falls back to weighted
        assert result["tier"] != "legendary"


# ---------------------------------------------------------------------------
# skill_tier  — key test, recently fixed to use numeric prof
# ---------------------------------------------------------------------------

class TestSkillTier:
    def test_no_proficiency(self, g):
        assert g['skill_tier'](MockSkill(prof=0)) == 0

    def test_jack_of_all_trades_is_not_proficient(self, g):
        assert g['skill_tier'](MockSkill(prof=0.5)) == 0

    def test_proficient(self, g):
        assert g['skill_tier'](MockSkill(prof=1)) == 1

    def test_expertise(self, g):
        assert g['skill_tier'](MockSkill(prof=2)) == 2

    def test_invalid_prof_defaults_zero(self, g):
        assert g['skill_tier'](MockSkill(prof="bad")) == 0


# ---------------------------------------------------------------------------
# resolve_skill_or_none
# ---------------------------------------------------------------------------

class TestResolveSkillOrNone:
    def test_known_skill(self, g):
        ch = MockCharacter(skills=MockSkills(athletics=MockSkill(prof=1, value=5)))
        result = g['resolve_skill_or_none'](ch, "athletics")
        assert result is ch.skills.athletics

    def test_unknown_skill_returns_none(self, g):
        ch = MockCharacter()
        assert g['resolve_skill_or_none'](ch, "notaskill") is None

    def test_case_insensitive(self, g):
        ch = MockCharacter()
        result = g['resolve_skill_or_none'](ch, "NATURE")
        assert result is ch.skills.nature

    def test_sleight_of_hand_with_spaces(self, g):
        ch = MockCharacter()
        result = g['resolve_skill_or_none'](ch, "sleight of hand")
        assert result is ch.skills.sleightOfHand


# ---------------------------------------------------------------------------
# roll_check
# ---------------------------------------------------------------------------

class TestRollCheck:
    def test_success_when_roll_meets_dc(self, g):
        ch = MockCharacter(skills=MockSkills(nature=MockSkill(prof=1, value=4)))
        ns = load_gather_lib(character=ch, vroll_total=15)
        result = ns['roll_check'](ch, skill="nature", dc=10)
        assert result["ok"] is True

    def test_failure_when_roll_below_dc(self, g):
        ch = MockCharacter(skills=MockSkills(nature=MockSkill(prof=1, value=4)))
        ns = load_gather_lib(character=ch, vroll_total=5)
        result = ns['roll_check'](ch, skill="nature", dc=10)
        assert result["ok"] is False

    def test_unknown_skill_returns_error(self, g):
        ch = MockCharacter()
        result = g['roll_check'](ch, skill="notreal", dc=10)
        assert result.get("error") is not None
        assert result["ok"] is False


# ---------------------------------------------------------------------------
# roll_check_best  — key test, new function
# ---------------------------------------------------------------------------

class TestRollCheckBest:
    def test_picks_highest_tier(self):
        ch = MockCharacter(skills=MockSkills(
            nature=MockSkill(prof=1, value=4),
            survival=MockSkill(prof=0, value=2),
        ))
        ns = load_gather_lib(character=ch, vroll_total=15)
        result = ns['roll_check_best'](ch, ["nature", "survival"], dc=10)
        assert result["name"] == "Nature"

    def test_tiebreaks_by_modifier(self):
        ch = MockCharacter(skills=MockSkills(
            nature=MockSkill(prof=1, value=6),
            survival=MockSkill(prof=1, value=3),
        ))
        ns = load_gather_lib(character=ch, vroll_total=15)
        # survival listed first but nature has higher modifier
        result = ns['roll_check_best'](ch, ["survival", "nature"], dc=10)
        assert result["name"] == "Nature"

    def test_expertise_beats_proficiency(self):
        ch = MockCharacter(skills=MockSkills(
            nature=MockSkill(prof=1, value=5),
            athletics=MockSkill(prof=2, value=9),
        ))
        ns = load_gather_lib(character=ch, vroll_total=15)
        result = ns['roll_check_best'](ch, ["nature", "athletics"], dc=10)
        assert result["name"] == "Athletics"

    def test_ok_true_when_roll_meets_dc(self):
        ch = MockCharacter(skills=MockSkills(nature=MockSkill(prof=1, value=4)))
        ns = load_gather_lib(character=ch, vroll_total=15)
        result = ns['roll_check_best'](ch, ["nature"], dc=10)
        assert result["ok"] is True

    def test_ok_false_when_roll_below_dc(self):
        ch = MockCharacter(skills=MockSkills(nature=MockSkill(prof=1, value=4)))
        ns = load_gather_lib(character=ch, vroll_total=5)
        result = ns['roll_check_best'](ch, ["nature"], dc=10)
        assert result["ok"] is False

    def test_unknown_skill_returns_error(self):
        ch = MockCharacter()
        ns = load_gather_lib(character=ch)
        result = ns['roll_check_best'](ch, ["notarealskill"], dc=10)
        assert result.get("error") is not None


# ---------------------------------------------------------------------------
# tool_tier_from_cvars
# ---------------------------------------------------------------------------

class TestToolTierFromCvars:
    def test_expertise(self, g):
        ch = MockCharacter(cvars={"eTools": "mason's tools"})
        assert g['tool_tier_from_cvars'](ch, "mason's tools") == 2

    def test_proficiency(self, g):
        ch = MockCharacter(cvars={"pTools": "mason's tools"})
        assert g['tool_tier_from_cvars'](ch, "mason's tools") == 1

    def test_none(self, g):
        ch = MockCharacter(cvars={})
        assert g['tool_tier_from_cvars'](ch, "mason's tools") == 0

    def test_case_insensitive(self, g):
        ch = MockCharacter(cvars={"pTools": "Mason's Tools"})
        assert g['tool_tier_from_cvars'](ch, "mason's tools") == 1


# ---------------------------------------------------------------------------
# extraction_flags
# ---------------------------------------------------------------------------

class TestExtractionFlags:
    def test_no_proficiency(self, g):
        result = {"use_tools": False, "tool_tier": 0, "skill_tier": 0}
        assert g['extraction_flags'](result) == {"prof": False, "exp": False}

    def test_skill_proficient(self, g):
        result = {"use_tools": False, "tool_tier": 0, "skill_tier": 1}
        flags = g['extraction_flags'](result)
        assert flags["prof"] is True
        assert flags["exp"] is False

    def test_skill_expertise(self, g):
        result = {"use_tools": False, "tool_tier": 0, "skill_tier": 2}
        flags = g['extraction_flags'](result)
        assert flags["prof"] is True
        assert flags["exp"] is True

    def test_tools_override_skill(self, g):
        result = {"use_tools": True, "tool_tier": 2, "skill_tier": 0}
        flags = g['extraction_flags'](result)
        assert flags["prof"] is True
        assert flags["exp"] is True

    def test_none_result(self, g):
        assert g['extraction_flags'](None) == {"prof": False, "exp": False}


# ---------------------------------------------------------------------------
# calc_reward_points
# ---------------------------------------------------------------------------

class TestCalcRewardPoints:
    def test_base_one_point_on_success(self, g):
        assert g['calc_reward_points'](True)["points"] == 1

    def test_zero_points_on_failure(self, g):
        assert g['calc_reward_points'](False)["points"] == 0

    def test_advantage_adds_one(self, g):
        assert g['calc_reward_points'](True, adv=True)["points"] == 2

    def test_disadvantage_no_bonus(self, g):
        assert g['calc_reward_points'](True, dis=True)["points"] == 1

    def test_adv_and_dis_cancel(self, g):
        assert g['calc_reward_points'](True, adv=True, dis=True)["points"] == 1

    def test_proficiency_adds_one(self, g):
        assert g['calc_reward_points'](True, prof=True)["points"] == 2

    def test_expertise_adds_one(self, g):
        assert g['calc_reward_points'](True, exp=True)["points"] == 2

    def test_prof_and_exp_stack(self, g):
        assert g['calc_reward_points'](True, prof=True, exp=True)["points"] == 3

    def test_all_bonuses(self, g):
        assert g['calc_reward_points'](True, adv=True, prof=True, exp=True)["points"] == 4

    def test_line_count_matches_bonuses(self, g):
        result = g['calc_reward_points'](True, adv=True, prof=True, exp=True)
        # base line + 3 bonus lines = 4 total
        assert len(result["lines"]) == 4

    def test_failure_lines_indicate_nothing_gained(self, g):
        result = g['calc_reward_points'](False)
        assert any("No resources" in line for line in result["lines"])
