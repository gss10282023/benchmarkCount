"""Human review timing checks for contract review and lock."""

from __future__ import annotations

from dataclasses import dataclass

from evidence_system.contracts.common import ContractLifecycleError, duration_minutes, parse_timestamp


@dataclass(frozen=True)
class ReviewTiming:
    review_started_at: str
    review_finished_at: str
    duration_minutes: float
    locked_at: str | None = None
    first_scoring_started_at: str | None = None

    def to_dict(self) -> dict[str, float | str | None]:
        return {
            "review_started_at": self.review_started_at,
            "review_finished_at": self.review_finished_at,
            "duration_minutes": self.duration_minutes,
            "locked_at": self.locked_at,
            "first_scoring_started_at": self.first_scoring_started_at,
        }


def review_timing(
    *,
    review_started_at: str,
    review_finished_at: str,
    locked_at: str | None = None,
    first_scoring_started_at: str | None = None,
) -> ReviewTiming:
    observed_duration = duration_minutes(review_started_at, review_finished_at)
    started = parse_timestamp(review_started_at, "review_started_at")
    finished = parse_timestamp(review_finished_at, "review_finished_at")
    if not started < finished:
        raise ContractLifecycleError("review_started_at must be before review_finished_at")
    if locked_at is not None:
        locked = parse_timestamp(locked_at, "locked_at")
        if finished > locked:
            raise ContractLifecycleError("review_finished_at must be at or before locked_at")
    if first_scoring_started_at is not None:
        if locked_at is None:
            raise ContractLifecycleError("first_scoring_started_at requires locked_at")
        locked = parse_timestamp(locked_at, "locked_at")
        first_scoring = parse_timestamp(first_scoring_started_at, "first_scoring_started_at")
        if not locked < first_scoring:
            raise ContractLifecycleError("first_scoring_started_at must be after locked_at")
    return ReviewTiming(
        review_started_at=review_started_at,
        review_finished_at=review_finished_at,
        duration_minutes=observed_duration,
        locked_at=locked_at,
        first_scoring_started_at=first_scoring_started_at,
    )


def record_review_time(**kwargs: str) -> ReviewTiming:
    return review_timing(**kwargs)
