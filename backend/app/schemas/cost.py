"""Cost estimation schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    """Token usage statistics from LLM calls."""

    prompt_tokens: int = Field(..., description="Tokens in the prompt")
    completion_tokens: int = Field(..., description="Tokens in the completion")
    total_tokens: int = Field(..., description="Total tokens used")


class CostEstimate(BaseModel):
    """Estimated cost for an operation."""

    tool_name: str = Field(..., description="Name of the tool that incurred the cost")
    model: str = Field(..., description="LLM model used (e.g., 'llama-3.3-70b-versatile')")
    input_cost_usd: float = Field(..., ge=0, description="Cost of input tokens")
    output_cost_usd: float = Field(..., ge=0, description="Cost of output tokens")
    total_cost_usd: float = Field(..., ge=0, description="Total cost in USD")
    usage: TokenUsage = Field(..., description="Token usage details")

    def __str__(self) -> str:
        return f"${self.total_cost_usd:.6f}"

    @classmethod
    def from_usage(
        cls,
        tool_name: str,
        model: str,
        usage: TokenUsage,
        input_price_per_mtok: float = 0.05,
        output_price_per_mtok: float = 0.15,
    ) -> CostEstimate:
        """Create a cost estimate from token usage.

        Args:
            tool_name: Name of the tool.
            model: Model name.
            usage: Token usage information.
            input_price_per_mtok: Input price per million tokens (default: $0.05/M for Groq 70B).
            output_price_per_mtok: Output price per million tokens (default: $0.15/M for Groq 70B).

        Returns:
            CostEstimate instance.
        """
        input_cost = (usage.prompt_tokens / 1_000_000) * input_price_per_mtok
        output_cost = (usage.completion_tokens / 1_000_000) * output_price_per_mtok
        total_cost = input_cost + output_cost

        return cls(
            tool_name=tool_name,
            model=model,
            input_cost_usd=input_cost,
            output_cost_usd=output_cost,
            total_cost_usd=total_cost,
            usage=usage,
        )
