"""Tests for formatters."""

import pytest

from nitrodump.formatter import format_user_status, format_model_table, format_full_status
from nitrodump.models import (
    QuotaInfo,
    ModelOrAlias,
    ClientModelConfig,
    PlanInfo,
    PlanStatus,
    UserTier,
    UserStatus,
    CascadeModelConfigData,
)


@pytest.fixture
def sample_user_status():
    """Create a sample UserStatus for testing."""
    return UserStatus(
        name="Test User",
        email="test@example.com",
        planStatus=PlanStatus(
            planInfo=PlanInfo(
                teamsTier="TEAMS_TIER_PRO",
                planName="Pro",
                monthlyPromptCredits=50000,
                monthlyFlowCredits=150000,
            )
        ),
        userTier=UserTier(
            id="g1-pro-tier",
            name="Google AI Pro",
            description="Google AI Pro",
        ),
        availablePromptCredits=500,
        availableFlowCredits=100,
    )


@pytest.fixture
def sample_model_configs():
    """Create sample model configs for testing."""
    return [
        ClientModelConfig(
            label="Claude Sonnet 4.5",
            modelOrAlias=ModelOrAlias(model="MODEL_CLAUDE_4_5_SONNET"),
            supportsImages=True,
            isRecommended=True,
            quotaInfo=QuotaInfo(remainingFraction=0.8, resetTime="2026-02-19T12:00:00Z"),
        ),
        ClientModelConfig(
            label="Gemini 3 Flash",
            modelOrAlias=ModelOrAlias(model="MODEL_GEMINI_3_FLASH"),
            supportsImages=True,
            isRecommended=True,
            quotaInfo=QuotaInfo(remainingFraction=1.0, resetTime="2026-02-19T14:00:00Z"),
        ),
    ]


class TestFormatUserStatus:
    """Tests for format_user_status."""

    def test_basic_format(self, sample_user_status):
        """Test basic user status formatting."""
        output = format_user_status(sample_user_status)

        assert "Test User" in output
        assert "test@example.com" in output
        assert "Google AI Pro" in output

    def test_credits_display(self, sample_user_status):
        """Test credits are displayed."""
        output = format_user_status(sample_user_status)

        assert "Prompt: 500 / 50000" in output
        assert "Flow:   100 / 150000" in output

    def test_no_credits(self):
        """Test formatting when credits are not available."""
        status = UserStatus(
            name="Test User",
            email="test@example.com",
            planStatus=PlanStatus(
                planInfo=PlanInfo(
                    teamsTier="TEAMS_TIER_FREE",
                    planName="Free",
                )
            ),
            userTier=UserTier(
                id="free-tier",
                name="Free",
                description="Free Tier",
            ),
        )
        output = format_user_status(status)

        assert "Prompt:" not in output
        assert "Flow:" not in output


class TestFormatModelTable:
    """Tests for format_model_table."""

    def test_basic_format(self, sample_model_configs):
        """Test basic model config formatting."""
        output = format_model_table(sample_model_configs)

        assert "Claude Sonnet 4.5" in output
        assert "Gemini 3 Flash" in output
        assert "80%" in output
        assert "100%" in output

    def test_table_structure(self, sample_model_configs):
        """Test that table has proper borders."""
        output = format_model_table(sample_model_configs)

        # Check for box drawing characters
        assert "┌" in output  # top left corner
        assert "┐" in output  # top right corner
        assert "└" in output  # bottom left corner
        assert "┘" in output  # bottom right corner
        assert "│" in output  # vertical bars
        assert "─" in output  # horizontal bars
        assert "┬" in output  # top T junction
        assert "├" in output  # left T junction
        assert "┼" in output  # cross junction
        assert "┴" in output  # bottom T junction

    def test_quota_display(self, sample_model_configs):
        """Test quota information is displayed correctly."""
        output = format_model_table(sample_model_configs)

        assert "80%" in output
        assert "100%" in output
        assert "2026-02-19T12:00:00Z" in output
        assert "2026-02-19T14:00:00Z" in output

    def test_sorted_output(self):
        """Test that models are sorted alphabetically."""
        configs = [
            ClientModelConfig(
                label="Zebra Model",
                modelOrAlias=ModelOrAlias(model="MODEL_ZEBRA"),
                supportsImages=False,
                isRecommended=False,
                quotaInfo=QuotaInfo(remainingFraction=1.0, resetTime="2026-02-19T12:00:00Z"),
            ),
            ClientModelConfig(
                label="Alpha Model",
                modelOrAlias=ModelOrAlias(model="MODEL_ALPHA"),
                supportsImages=False,
                isRecommended=False,
                quotaInfo=QuotaInfo(remainingFraction=1.0, resetTime="2026-02-19T12:00:00Z"),
            ),
        ]
        output = format_model_table(configs)

        # Alpha should appear before Zebra
        alpha_pos = output.find("Alpha Model")
        zebra_pos = output.find("Zebra Model")
        assert alpha_pos < zebra_pos

    def test_empty_configs(self):
        """Test formatting with no model configs."""
        output = format_model_table([])
        assert output == ""

    def test_headers(self, sample_model_configs):
        """Test that table headers are present."""
        output = format_model_table(sample_model_configs)

        assert "Model" in output
        assert "Remaining" in output
        assert "Reset Time" in output


class TestFormatFullStatus:
    """Tests for format_full_status."""

    def test_combined_output(self, sample_user_status, sample_model_configs):
        """Test that full status combines user and model info."""
        sample_user_status.cascade_model_config_data = CascadeModelConfigData(
            clientModelConfigs=sample_model_configs
        )

        output = format_full_status(sample_user_status)

        assert "Test User" in output
        assert "Google AI Pro" in output
        assert "Claude Sonnet 4.5" in output
        assert "Gemini 3 Flash" in output

    def test_full_status_without_models(self, sample_user_status):
        """Test full status when no model configs are available."""
        sample_user_status.cascade_model_config_data = None

        output = format_full_status(sample_user_status)

        assert "Test User" in output
        assert "┌" not in output  # No table borders
