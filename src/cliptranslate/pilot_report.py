"""Summarise the pilot scorecard so nobody has to do the money arithmetic by hand.

Usage:  python -m cliptranslate.pilot_report pilot_data/scorecard.csv

Contribution per clip = paid price minus every cost in the sheet (cash, energy/hardware,
payment fees, refunds, review labour and support labour). Keep real data outside Git.
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass, field
from pathlib import Path

COST_COLUMNS = (
    "variable_cash_cost",
    "estimated_energy_hardware_cost",
    "payment_fees",
    "refunds",
    "review_labor_cost",
    "support_labor_cost",
)
REQUIRED = ("creator_id", "clip_seconds", "paid_price", "output_usable_1_to_5")


@dataclass
class Row:
    creator_id: str
    clip_seconds: float
    paid_price: float
    cost: float
    usable: int
    correction_minutes: float
    repeated: bool
    contribution: float
    problems: list[str] = field(default_factory=list)


@dataclass
class Summary:
    rows: list[Row]
    problems: list[str]

    @property
    def paid(self) -> list[Row]:
        return [row for row in self.rows if row.paid_price > 0]

    @property
    def total_contribution(self) -> float:
        return sum(row.contribution for row in self.rows)

    @property
    def profitable_clips(self) -> int:
        return sum(1 for row in self.rows if row.contribution > 0)

    @property
    def creators(self) -> int:
        return len({row.creator_id for row in self.rows})

    @property
    def liked(self) -> int:
        return sum(1 for row in self.rows if row.usable >= 4)

    @property
    def meets_goal(self) -> bool:
        """The stated goal: ten creators, satisfied, paying more than the full cost."""
        winners = {row.creator_id for row in self.rows if row.usable >= 4 and row.contribution > 0}
        return len(winners) >= 10 and not self.problems


def _number(value: str, name: str, problems: list[str], line: int) -> float:
    text = (value or "").strip()
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        problems.append(f"line {line}: {name} is not a number ({text!r}); counted as 0")
        return 0.0


def load(path: Path) -> Summary:
    rows: list[Row] = []
    problems: list[str] = []
    with Path(path).open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        missing = [name for name in REQUIRED if name not in (reader.fieldnames or [])]
        if missing:
            raise ValueError("Missing column(s): " + ", ".join(missing))
        for line, record in enumerate(reader, start=2):
            if not any((value or "").strip() for value in record.values()):
                continue
            local: list[str] = []
            costs = {n: _number(record.get(n, ""), n, local, line) for n in COST_COLUMNS}
            paid = _number(record["paid_price"], "paid_price", local, line)
            usable = int(_number(record["output_usable_1_to_5"], "usable", local, line))
            if not 0 <= usable <= 5:
                local.append(f"line {line}: usability must be 1-5")
                usable = 0
            if not (record["creator_id"] or "").strip():
                local.append(f"line {line}: creator_id is empty")
            if paid <= 0:
                local.append(
                    f"line {line}: no payment recorded (willingness to pay is not revenue)"
                )
            rows.append(
                Row(
                    creator_id=(record["creator_id"] or "").strip(),
                    clip_seconds=_number(record["clip_seconds"], "clip_seconds", local, line),
                    paid_price=paid,
                    cost=sum(costs.values()),
                    usable=usable,
                    correction_minutes=_number(
                        record.get("correction_minutes", ""), "correction_minutes", local, line
                    ),
                    repeated=(record.get("repeated_use_yn", "") or "").strip().lower()
                    in {"y", "yes"},
                    contribution=paid - sum(costs.values()),
                    problems=local,
                )
            )
            problems.extend(local)
    return Summary(rows, problems)


def render(summary: Summary) -> str:
    rows = summary.rows
    if not rows:
        return "No pilot rows yet."
    minutes = sum(row.correction_minutes for row in rows)
    seconds = sum(row.clip_seconds for row in rows)
    lines = [
        f"Clips: {len(rows)}   Creators: {summary.creators}   Paid clips: {len(summary.paid)}",
        f"Output rated 4-5: {summary.liked}/{len(rows)}   Would use again: "
        f"{sum(row.repeated for row in rows)}/{len(rows)}",
        f"Total paid: {sum(row.paid_price for row in rows):.2f}   "
        f"Total cost: {sum(row.cost for row in rows):.2f}   "
        f"Total contribution: {summary.total_contribution:.2f}",
        f"Clips with positive contribution: {summary.profitable_clips}/{len(rows)}",
    ]
    if seconds:
        lines.append(
            f"Correction effort: {minutes / (seconds / 60):.1f} human minutes per video minute"
        )
    lines.append(
        "GOAL MET: ten creators liked the result and paid more than full cost."
        if summary.meets_goal
        else "Goal not yet met (needs 10 creators rated 4-5 whose clip paid more than its cost)."
    )
    if summary.problems:
        lines += ["", "Check these rows:", *("  - " + item for item in summary.problems)]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("Usage: python -m cliptranslate.pilot_report SCORECARD.csv")
        return 2
    try:
        print(render(load(Path(args[0]))))
    except (OSError, ValueError) as exc:
        print(f"Could not read the scorecard: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
