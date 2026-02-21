"""Tests for data models."""

import pytest

from nitrodump.models import (
    QuotaInfo,
    ModelOrAlias,
    ClientModelConfig,
    PlanInfo,
    PlanStatus,
    UserTier,
    UserStatus,
    CascadeModelConfigData,
    GetUserStatusResponse,
)


def test_quota_info_remaining_percent():
    """Test QuotaInfo.remaining_percent property."""
    quota = QuotaInfo(remainingFraction=0.8, resetTime="2026-02-19T12:00:00Z")
    assert quota.remaining_percent == 80

    quota = QuotaInfo(remainingFraction=1.0, resetTime="2026-02-19T12:00:00Z")
    assert quota.remaining_percent == 100

    quota = QuotaInfo(remainingFraction=0.0, resetTime="2026-02-19T12:00:00Z")
    assert quota.remaining_percent == 0


def test_model_or_alias():
    """Test ModelOrAlias model."""
    model = ModelOrAlias(model="MODEL_CLAUDE_4_5_SONNET")
    assert model.model == "MODEL_CLAUDE_4_5_SONNET"


def test_client_model_config():
    """Test ClientModelConfig model."""
    config = ClientModelConfig(
        label="Claude Sonnet 4.5",
        modelOrAlias={"model": "MODEL_CLAUDE_4_5_SONNET"},
        supportsImages=True,
        isRecommended=True,
        quotaInfo={
            "remainingFraction": 0.8,
            "resetTime": "2026-02-19T12:00:00Z",
        },
    )
    assert config.label == "Claude Sonnet 4.5"
    assert config.model_or_alias.model == "MODEL_CLAUDE_4_5_SONNET"
    assert config.supports_images is True
    assert config.quota_info.remaining_percent == 80


def test_plan_info():
    """Test PlanInfo model."""
    plan = PlanInfo(
        teamsTier="TEAMS_TIER_PRO",
        planName="Pro",
        monthlyPromptCredits=50000,
        monthlyFlowCredits=150000,
    )
    assert plan.teams_tier == "TEAMS_TIER_PRO"
    assert plan.plan_name == "Pro"
    assert plan.monthly_prompt_credits == 50000
    assert plan.monthly_flow_credits == 150000


def test_user_status():
    """Test UserStatus model."""
    status = UserStatus(
        name="Test User",
        email="test@example.com",
        planStatus={
            "planInfo": {
                "teamsTier": "TEAMS_TIER_PRO",
                "planName": "Pro",
            }
        },
        userTier={
            "id": "g1-pro-tier",
            "name": "Google AI Pro",
            "description": "Google AI Pro",
        },
        availablePromptCredits=500,
        availableFlowCredits=100,
    )
    assert status.name == "Test User"
    assert status.email == "test@example.com"
    assert status.available_prompt_credits == 500
    assert status.user_tier.name == "Google AI Pro"


def test_full_response_structure():
    """Test a complete GetUserStatusResponse."""
    response_data = {
        "userStatus": {
            "name": "Sharp Mouse",
            "email": "sharmpmouse123@gmail.com",
            "planStatus": {
                "planInfo": {
                    "teamsTier": "TEAMS_TIER_PRO",
                    "planName": "Pro",
                    "monthlyPromptCredits": 50000,
                    "monthlyFlowCredits": 150000,
                }
            },
            "userTier": {
                "id": "g1-pro-tier",
                "name": "Google AI Pro",
                "description": "Google AI Pro",
            },
            "availablePromptCredits": 500,
            "availableFlowCredits": 100,
            "cascadeModelConfigData": {
                "clientModelConfigs": [
                    {
                        "label": "Claude Sonnet 4.5",
                        "modelOrAlias": {"model": "MODEL_CLAUDE_4_5_SONNET"},
                        "supportsImages": True,
                        "isRecommended": True,
                        "quotaInfo": {
                            "remainingFraction": 0.8,
                            "resetTime": "2026-02-19T12:00:00Z",
                        },
                    }
                ]
            },
        },
    }
    response = GetUserStatusResponse.model_validate(response_data)
    assert response.user_status.name == "Sharp Mouse"
    assert len(response.user_status.cascade_model_config_data.client_model_configs) == 1
    assert (
        response.user_status.cascade_model_config_data.client_model_configs[0].label
        == "Claude Sonnet 4.5"
    )
