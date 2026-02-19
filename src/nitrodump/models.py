"""Data models for Codeium API responses."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List


class QuotaInfo(BaseModel):
    """Rate limit quota information for a model."""

    remaining_fraction: float = Field(alias="remainingFraction")
    reset_time: str = Field(alias="resetTime")

    @property
    def remaining_percent(self) -> int:
        """Return remaining quota as a percentage (0-100)."""
        return int(self.remaining_fraction * 100)


class ModelOrAlias(BaseModel):
    """Model identifier."""

    model: str


class SupportedMimeTypes(BaseModel):
    """Supported MIME types for a model."""

    pass  # Simplified - full model would include all fields


class ClientModelConfig(BaseModel):
    """Configuration for a single AI model."""

    label: str
    model_or_alias: ModelOrAlias = Field(alias="modelOrAlias")
    supports_images: Optional[bool] = Field(alias="supportsImages", default=None)
    is_recommended: Optional[bool] = Field(alias="isRecommended", default=None)
    quota_info: QuotaInfo = Field(alias="quotaInfo")


class PlanInfo(BaseModel):
    """User plan information."""

    teams_tier: str = Field(alias="teamsTier")
    plan_name: str = Field(alias="planName")
    monthly_prompt_credits: Optional[int] = Field(alias="monthlyPromptCredits", default=None)
    monthly_flow_credits: Optional[int] = Field(alias="monthlyFlowCredits", default=None)


class PlanStatus(BaseModel):
    """Plan status information."""

    plan_info: PlanInfo = Field(alias="planInfo")


class UserTier(BaseModel):
    """User tier information."""

    id: str
    name: str
    description: str


class UserStatus(BaseModel):
    """Complete user status response from Codeium API."""

    name: str
    email: str
    plan_status: PlanStatus = Field(alias="planStatus")
    user_tier: UserTier = Field(alias="userTier")
    available_prompt_credits: Optional[int] = Field(alias="availablePromptCredits", default=None)
    available_flow_credits: Optional[int] = Field(alias="availableFlowCredits", default=None)
    cascade_model_config_data: Optional["CascadeModelConfigData"] = Field(
        alias="cascadeModelConfigData", default=None
    )


class CascadeModelConfigData(BaseModel):
    """Model configuration data."""

    client_model_configs: List[ClientModelConfig] = Field(alias="clientModelConfigs")


class GetUserStatusResponse(BaseModel):
    """Root response wrapper for GetUserStatus API call."""

    user_status: UserStatus = Field(alias="userStatus")
