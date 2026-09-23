"""PersonalKnowledgeContextSource adapter for Module 06 Context Management integration."""

from max.context.domain.enums import ContextCategory, ContextPriority, SourceTrustLevel
from max.context.domain.item import ContextItem
from max.context.domain.request import ContextRequest
from max.knowledge.domain.entity import KnowledgeEntity
from max.knowledge.domain.enums import KnowledgeConfidence, KnowledgeStatus
from max.knowledge.domain.summary import KnowledgeSummary


class PersonalKnowledgeContextSource:
    """ContextSource adapter supplying personal knowledge entities and facts to ContextManager."""

    def __init__(
        self,
        default_entities: list[KnowledgeEntity] | None = None,
        default_summaries: list[KnowledgeSummary] | None = None,
    ) -> None:
        self._enabled = True
        self._default_entities = default_entities or []
        self._default_summaries = default_summaries or []

    @property
    def source_id(self) -> str:
        """Unique identifier for this ContextSource."""
        return "personal_knowledge_engine"

    @property
    def category(self) -> ContextCategory:
        """Context category taxonomy."""
        return ContextCategory.KNOWLEDGE

    @property
    def priority(self) -> ContextPriority:
        """Default priority level for personal knowledge context items."""
        return ContextPriority.NORMAL

    @property
    def enabled(self) -> bool:
        """Flag indicating whether this source is active."""
        return self._enabled

    def provide(self, request: ContextRequest) -> list[ContextItem]:
        """Convert candidate knowledge entities/summaries into ContextItem instances."""
        items: list[ContextItem] = []

        # 1. Process explicit knowledge summaries passed in source_options
        summaries: list[KnowledgeSummary] = []
        raw_sums = request.source_options.get("knowledge_summaries") or request.source_options.get(
            "summaries"
        )
        if raw_sums and isinstance(raw_sums, list):
            for s in raw_sums:
                if isinstance(s, KnowledgeSummary):
                    summaries.append(s)
                elif isinstance(s, dict):
                    summaries.append(KnowledgeSummary(**s))
        elif self._default_summaries:
            summaries = self._default_summaries

        for summary in summaries:
            entity = summary.entity
            if entity.status in (KnowledgeStatus.DELETED, KnowledgeStatus.DEPRECATED):
                continue

            # Format summary content
            lines = [
                f"[Knowledge Entity: {entity.name} ({entity.type.value})]",
                f"Status: {entity.status.value}",
            ]
            if entity.description:
                lines.append(f"Description: {entity.description}")
            if summary.facts:
                lines.append("Facts:")
                for f in summary.facts:
                    if f.status == KnowledgeStatus.ACTIVE:
                        lines.append(f"  - {f.subject} {f.predicate} {f.object} ({f.value})")
            if summary.outgoing_relations:
                lines.append("Relations:")
                for r in summary.outgoing_relations:
                    if r.status == KnowledgeStatus.ACTIVE:
                        lines.append(f"  - {r.relation_type.value} -> {r.target_entity_id}")

            content_text = "\n".join(lines)
            prio = (
                ContextPriority.HIGH
                if entity.confidence == KnowledgeConfidence.HIGH
                else ContextPriority.NORMAL
            )
            token_est = max(1, len(content_text) // 4)

            items.append(
                ContextItem(
                    context_id=f"know_sum_{entity.id}",
                    category=ContextCategory.KNOWLEDGE,
                    content=content_text,
                    priority=prio,
                    required=False,
                    source=self.source_id,
                    token_estimate=token_est,
                    trust_level=SourceTrustLevel.TRUSTED,
                    metadata={
                        "entity_id": entity.id,
                        "type": entity.type.value,
                        "confidence": entity.confidence.value,
                        "fact_count": len(summary.facts),
                    },
                )
            )

        # 2. Process standalone entities if summaries were not provided
        if not items:
            entities: list[KnowledgeEntity] = []
            raw_ents = request.source_options.get(
                "knowledge_entities"
            ) or request.source_options.get("entities")

            if raw_ents and isinstance(raw_ents, list):
                for e in raw_ents:
                    if isinstance(e, KnowledgeEntity):
                        entities.append(e)
                    elif isinstance(e, dict):
                        entities.append(KnowledgeEntity(**e))
            elif self._default_entities:
                entities = self._default_entities

            for ent in entities:
                if ent.status in (KnowledgeStatus.DELETED, KnowledgeStatus.DEPRECATED):
                    continue

                lines = [f"[Knowledge Entity: {ent.name} ({ent.type.value})]"]
                if ent.description:
                    lines.append(f"Description: {ent.description}")

                content_text = "\n".join(lines)
                prio = (
                    ContextPriority.HIGH
                    if ent.confidence == KnowledgeConfidence.HIGH
                    else ContextPriority.NORMAL
                )
                token_est = max(1, len(content_text) // 4)

                items.append(
                    ContextItem(
                        context_id=f"know_ent_{ent.id}",
                        category=ContextCategory.KNOWLEDGE,
                        content=content_text,
                        priority=prio,
                        required=False,
                        source=self.source_id,
                        token_estimate=token_est,
                        trust_level=SourceTrustLevel.TRUSTED,
                        metadata={
                            "entity_id": ent.id,
                            "type": ent.type.value,
                            "confidence": ent.confidence.value,
                        },
                    )
                )

        return items
