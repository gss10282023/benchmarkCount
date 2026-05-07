"""Paper table generation helpers."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from evidence_system.core.errors import BootstrapOnlyError
from evidence_system.core.schemas import validate_object


class PaperTableError(RuntimeError):
    """Raised when a paper table would use invalid provenance."""


@dataclass(frozen=True)
class HumanTimeCostRow:
    domain: str | None
    activity_type: str
    duration_minutes: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "activity_type": self.activity_type,
            "duration_minutes": self.duration_minutes,
        }


def make_tables() -> None:
    raise BootstrapOnlyError("Paper table generation is not implemented in Step 2.")


def build_cost_rows_from_human_time(records: Iterable[Mapping[str, Any]]) -> list[HumanTimeCostRow]:
    """Build `tab:cost` rows strictly from `human_time/v1` records.

    This is the Step 6 guard that prevents OpenRouter/LLM token cost logs from
    being interpreted as trained annotator wall-clock human-time cost.
    """

    totals: dict[tuple[str | None, str], float] = defaultdict(float)
    for index, record in enumerate(records):
        schema_version = record.get("schema_version")
        if schema_version != "human_time/v1":
            raise PaperTableError(f"tab:cost may only read human_time/v1 records; record {index} is {schema_version!r}")
        validate_object("human_time", record, raise_on_error=True)
        if record.get("counts_for_cost_table") is not True:
            raise PaperTableError("tab:cost human-time records require counts_for_cost_table=true")
        for field in (
            "no_llm_cost_included",
            "no_vps_cost_included",
            "no_cloud_bill_included",
            "no_benchmark_execution_compute_included",
            "no_local_machine_runtime_included",
        ):
            if record.get(field) is not True:
                raise PaperTableError("tab:cost human-time records must exclude LLM, VPS, cloud, benchmark, and runtime costs")
        key = (record.get("domain"), str(record.get("activity_type")))
        totals[key] += float(record.get("duration_minutes") or 0.0)
    return [
        HumanTimeCostRow(domain=domain, activity_type=activity_type, duration_minutes=round(duration, 6))
        for (domain, activity_type), duration in sorted(totals.items(), key=lambda item: (str(item[0][0]), item[0][1]))
    ]
