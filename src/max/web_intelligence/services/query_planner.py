"""QueryPlanner service for generating and normalizing search queries."""

import re

from max.web_intelligence.domain.models import ResearchQuery, ResearchRequest


class QueryPlanner:
    """Generates, normalizes, and deduplicates complementary search queries."""

    @staticmethod
    def normalize_query(query_str: str) -> str:
        """Clean and normalize query string."""
        # Strip excessive whitespace and non-printable characters
        cleaned = re.sub(r"\s+", " ", query_str.strip())
        # Strip trailing punctuation except quotes
        cleaned = re.sub(r"[?:!;,]+$", "", cleaned)
        return cleaned

    def generate_queries(self, request: ResearchRequest) -> list[ResearchQuery]:
        """Generate complementary queries up to request.constraints.max_queries."""
        queries: list[ResearchQuery] = []
        seen_normalized: set[str] = set()

        raw_candidates: list[tuple[str, str]] = []

        # Primary question
        raw_candidates.append((request.objective.question, "PRIMARY"))

        # Topic core
        raw_candidates.append((request.objective.topic, "PRIMARY"))

        # Sub questions
        for subq in request.objective.sub_questions:
            raw_candidates.append((subq, "TECHNICAL"))

        # Mode specific queries
        if request.scope.time_range_days:
            raw_candidates.append(
                (f"{request.objective.topic} news past {request.scope.time_range_days} days", "RECENT")
            )
        else:
            raw_candidates.append((f"{request.objective.topic} official documentation", "OFFICIAL"))

        # Alternative formulation
        raw_candidates.append((f"overview of {request.objective.topic}", "ALTERNATIVE"))

        max_q = request.constraints.max_queries

        for raw, purpose in raw_candidates:
            norm = self.normalize_query(raw)
            if not norm or norm.lower() in seen_normalized:
                continue

            seen_normalized.add(norm.lower())
            queries.append(
                ResearchQuery(
                    research_id=request.id,
                    original_query=raw,
                    normalized_query=norm,
                    purpose=purpose,
                )
            )

            if len(queries) >= max_q:
                break

        return queries
