import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from make_sample_template import build_workbook  # noqa: E402
from parse_report import ReportError, build_dashboard_data, risk_grade, to_month  # noqa: E402


@pytest.fixture
def sample_path(tmp_path):
    path = tmp_path / "report.xlsx"
    build_workbook().save(path)
    return path


def save_modified(tmp_path, modify):
    wb = build_workbook()
    modify(wb)
    path = tmp_path / "modified.xlsx"
    wb.save(path)
    return path


def test_sample_report_parses(sample_path):
    data = build_dashboard_data(sample_path)

    assert data["meta"]["report_month"] == "2026-09"
    assert data["progress"]["latest"] == {"month": "2026-09", "plan": 75.0, "actual": 70.2, "gap": -4.8}
    assert len(data["progress"]["history"]) == 19
    assert data["budget"]["latest"]["actual_rate"] == 76.6
    summary = data["risks"]["summary"]
    assert summary["total"] == 8
    assert summary["by_status"] == {"미착수": 2, "진행중": 3, "완료": 3}
    assert summary["overdue"] == 1  # R-02: 목표 9/15, 진행중


@pytest.mark.parametrize("impact, likelihood, expected", [
    ("상", "상", "High"), ("상", "중", "High"), ("중", "중", "Medium"),
    ("상", "하", "Medium"), ("중", "하", "Low"), ("하", "하", "Low"),
])
def test_risk_grade(impact, likelihood, expected):
    assert risk_grade(impact, likelihood) == expected


@pytest.mark.parametrize("raw", ["2026-09", "2026.09", "2026/9", "2026-09-01"])
def test_to_month_normalizes(raw):
    assert to_month(raw) == "2026-09"


def test_missing_sheet(tmp_path):
    path = save_modified(tmp_path, lambda wb: wb.remove(wb["리스크"]))
    with pytest.raises(ReportError, match="필수 시트 '리스크'"):
        build_dashboard_data(path)


def test_progress_over_100_rejected(tmp_path):
    path = save_modified(tmp_path, lambda wb: wb["공정률"].cell(row=20, column=3, value=120))
    with pytest.raises(ReportError, match="허용 범위"):
        build_dashboard_data(path)


def test_report_month_row_missing(tmp_path):
    path = save_modified(tmp_path, lambda wb: wb["공정률"].delete_rows(20))
    with pytest.raises(ReportError, match="보고월\\(2026-09\\) 데이터가 없습니다"):
        build_dashboard_data(path)


def test_invalid_risk_status(tmp_path):
    path = save_modified(tmp_path, lambda wb: wb["리스크"].cell(row=2, column=9, value="보류"))
    with pytest.raises(ReportError, match="진행상태"):
        build_dashboard_data(path)
