"""Explicit pipeline tuning; values are chosen from evaluation results."""

from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.models import NonEmptyText, PositiveInt


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RAG_", extra="forbid", frozen=True)
    lexical_candidates: PositiveInt
    dense_candidates: PositiveInt
    fusion_rank_constant: PositiveInt
    rerank_candidates: PositiveInt
    max_subqueries: PositiveInt
    evidence_token_budget: PositiveInt
    cache_similarity_threshold: Annotated[float, Field(ge=-1, le=1, allow_inf_nan=False)]
    cache_ttl_seconds: PositiveInt
    embedding_model: NonEmptyText
    generator_model: NonEmptyText
    retrieval_config_version: NonEmptyText
    reranker_config_version: NonEmptyText
    prompt_version: NonEmptyText
