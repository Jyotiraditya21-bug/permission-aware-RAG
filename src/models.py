"""Validated data contracts; authorization is resolved outside these models."""

from typing import Annotated, Literal, Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints, model_validator


NonEmptyText = Annotated[str, StringConstraints(min_length=1, pattern=r"\S")]
NonNegativeInt = Annotated[int, Field(strict=True, ge=0)]
PositiveInt = Annotated[int, Field(strict=True, gt=0)]
FiniteScore = Annotated[float, Field(allow_inf_nan=False)]
Route = Literal["direct-retrieve", "decompose", "no-retrieval-needed"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class QueryRequest(Contract):
    """Public input deliberately excludes identity and access fields."""

    query: NonEmptyText


class AccessScope(Contract):
    """Constructed from trusted authentication, never from QueryRequest."""

    tenant_id: NonEmptyText
    principal_id: NonEmptyText
    group_ids: frozenset[NonEmptyText]
    source_policy_attributes: dict[NonEmptyText, frozenset[NonEmptyText]]
    permission_epoch: NonNegativeInt


class SourceACL(Contract):
    """Explicit empty grants represent deny-all, never public access."""

    principal_ids: frozenset[NonEmptyText]
    group_ids: frozenset[NonEmptyText]
    source_policy_attributes: dict[NonEmptyText, frozenset[NonEmptyText]]
    acl_version: NonEmptyText


class Version(Contract):
    document_version: NonEmptyText
    corpus_version: NonEmptyText
    acl_version: NonEmptyText


class SourceRecord(Contract):
    source_type: Literal["docs", "tickets", "wikis"]
    source_id: NonEmptyText
    document_id: NonEmptyText
    tenant_id: NonEmptyText
    text: str
    modified_at: AwareDatetime
    content_hash: NonEmptyText
    deleted: bool = Field(strict=True)
    acl: SourceACL


class Chunk(Contract):
    chunk_id: NonEmptyText
    document_id: NonEmptyText
    document_version: NonEmptyText
    text: NonEmptyText
    source_locator: NonEmptyText
    tenant_id: NonEmptyText
    acl: SourceACL


class RetrievalResult(Contract):
    """Produced only by retrieval that applies the trusted access predicate."""

    chunk_id: NonEmptyText
    text: NonEmptyText
    version: Version
    lexical_score: FiniteScore | None = None
    dense_score: FiniteScore | None = None
    fusion_rank: PositiveInt
    rerank_score: FiniteScore | None = None


class Citation(Contract):
    claim: NonEmptyText
    chunk_ids: Annotated[tuple[NonEmptyText, ...], Field(min_length=1)]


class Answer(Contract):
    status: Literal["grounded", "abstained", "conversational"]
    text: NonEmptyText
    citations: tuple[Citation, ...]
    route: Route
    trace_id: NonEmptyText

    @model_validator(mode="after")
    def validate_grounding_shape(self) -> Self:
        """Check shape only; evidence authorization/support needs runtime checks."""
        if self.status == "grounded":
            if not self.citations or self.route == "no-retrieval-needed":
                raise ValueError("Grounded answers require citations and retrieval")
        elif self.citations:
            raise ValueError("Only grounded answers can carry citations")
        if self.status == "conversational" and self.route != "no-retrieval-needed":
            raise ValueError("Conversational answers require the conversational route")
        return self
