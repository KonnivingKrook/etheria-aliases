"""
Smoke tests for the production aliases (mining, lumber).

These tests exercise the full alias pipeline end-to-end using mocked
character data and controlled dice rolls. They verify that the alias
produces sensible output for each major scenario, not the exact embed
string format.
"""

import pytest
from conftest import (
    MockCharacter, MockSkill, MockSkills, MockStats,
    set_mock_time, reset_mock_time, run_alias,
)

NOW = 1_700_000_000
MINING_ALIAS = "Customizations/tmine.alias"
LUMBER_ALIAS = "Customizations/tlumber.alias"


@pytest.fixture(autouse=True)
def fixed_time():
    set_mock_time(NOW)
    yield
    reset_mock_time()


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
        cvars={"last_hunt": str(NOW - 1800)},  # 30 min ago, 2h cooldown active
        stats=MockStats(prof_bonus=3),
    )


# ---------------------------------------------------------------------------
# Mining alias
# ---------------------------------------------------------------------------

class TestMiningAlias:
    def test_help_returns_output(self, fresh_ch):
        output = run_alias(MINING_ALIAS, ["help"], character=fresh_ch)
        assert output is not None
        assert "Mining" in output

    def test_cooldown_blocks_when_active(self, cooled_down_ch):
        output = run_alias(MINING_ALIAS, [], character=cooled_down_ch)
        assert "Available" in output

    def test_successful_run_contains_resources(self, fresh_ch):
        # High roll (20) → find succeeds, harvest succeeds
        output = run_alias(MINING_ALIAS, [], character=fresh_ch, vroll_total=20)
        assert output is not None
        assert "added to your bag" in output

    def test_find_failure_no_resources(self, fresh_ch):
        # Very low roll (1) → find fails
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

    def test_set_subcommand_returns_output(self, fresh_ch):
        output = run_alias(MINING_ALIAS, ["set"], character=fresh_ch)
        assert "Mining" in output


# ---------------------------------------------------------------------------
# Lumber alias
# ---------------------------------------------------------------------------

class TestLumberAlias:
    def test_help_returns_output(self, fresh_ch):
        output = run_alias(LUMBER_ALIAS, ["help"], character=fresh_ch)
        assert output is not None
        assert "Lumbering" in output

    def test_cooldown_blocks_when_active(self, cooled_down_ch):
        output = run_alias(LUMBER_ALIAS, [], character=cooled_down_ch)
        assert "Available" in output

    def test_successful_run_contains_lumber(self, fresh_ch):
        output = run_alias(LUMBER_ALIAS, [], character=fresh_ch, vroll_total=20)
        assert output is not None
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
