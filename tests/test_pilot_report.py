from pathlib import Path

from cliptranslate import pilot_report

HEADER = (
    "creator_id,clip_id,clip_seconds,correction_minutes,output_usable_1_to_5,paid_price,"
    "variable_cash_cost,estimated_energy_hardware_cost,payment_fees,refunds,"
    "review_labor_cost,support_labor_cost,repeated_use_yn\n"
)


def write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "score.csv"
    path.write_text(HEADER + body, encoding="utf-8")
    return path


def test_contribution_counts_every_cost(tmp_path):
    path = write(tmp_path, "c1,a,60,10,5,30,1,0.5,1.5,0,10,5,y\n")
    summary = pilot_report.load(path)
    assert summary.rows[0].cost == 18.0
    assert summary.rows[0].contribution == 12.0
    assert summary.profitable_clips == 1


def test_unpaid_and_unprofitable_clips_are_flagged_and_not_a_success(tmp_path):
    path = write(tmp_path, "c1,a,60,30,5,0,0,0,0,0,20,0,y\nc2,b,60,30,4,10,0,0,0,0,25,0,n\n")
    summary = pilot_report.load(path)
    assert [row.contribution for row in summary.rows] == [-20.0, -15.0]
    assert any("no payment" in problem for problem in summary.problems)
    assert not summary.meets_goal
    assert "Goal not yet met" in pilot_report.render(summary)


def test_goal_requires_ten_distinct_creators(tmp_path):
    rows = "".join(f"c{i},a,60,5,5,40,0,0,1,0,5,2,y\n" for i in range(10))
    assert pilot_report.load(write(tmp_path, rows)).meets_goal
    same = "".join("c1,a,60,5,5,40,0,0,1,0,5,2,y\n" for _ in range(10))
    assert not pilot_report.load(write(tmp_path, same)).meets_goal


def test_bad_numbers_are_reported_not_hidden(tmp_path):
    summary = pilot_report.load(write(tmp_path, "c1,a,sixty,5,9,40,0,0,1,0,5,2,y\n"))
    assert any("clip_seconds" in problem for problem in summary.problems)
    assert any("usability" in problem for problem in summary.problems)


def test_blank_template_and_missing_columns(tmp_path):
    blank = pilot_report.load(Path(__file__).parents[1] / "pilot_scorecard.csv")
    assert blank.rows == []
    assert pilot_report.render(blank) == "No pilot rows yet."
    bad = tmp_path / "bad.csv"
    bad.write_text("x,y\n1,2\n", encoding="utf-8")
    assert pilot_report.main([str(bad)]) == 1
