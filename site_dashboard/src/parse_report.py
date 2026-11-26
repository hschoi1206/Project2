"""월간 현장 보고 템플릿(xlsx)을 읽어 대시보드용 JSON으로 변환한다.

실행: python src/parse_report.py data/raw/sample_report_2026-09.xlsx
출력: data/processed/dashboard_data.json
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "dashboard_data.json"

REQUIRED_COLUMNS = {
    "현장정보": ["항목", "값"],
    "공정률": ["보고월", "계획공정률(%)", "실적공정률(%)"],
    "예산집행": ["보고월", "계획집행누계(억원)", "실적집행누계(억원)"],
    "리스크": ["ID", "리스크항목", "분류", "영향도", "발생가능성", "담당자",
             "등록일", "조치계획", "진행상태", "목표완료일"],
}
REQUIRED_SITE_KEYS = ["보고월", "현장명", "실행예산_억원"]

LEVEL_SCORE = {"상": 3, "중": 2, "하": 1}
STATUSES = ["미착수", "진행중", "완료"]


class ReportError(ValueError):
    """템플릿 양식 또는 입력값 오류."""


def to_month(value) -> str:
    """'2026-09', datetime, '2026.9' 등을 'YYYY-MM'으로 통일한다."""
    text = str(value).strip().replace(".", "-").replace("/", "-")
    try:
        return pd.to_datetime(text).strftime("%Y-%m")
    except (ValueError, TypeError):
        raise ReportError(f"보고월 형식을 해석할 수 없습니다: {value!r}")


def to_date_str(value):
    if pd.isna(value):
        return None
    return pd.to_datetime(value).strftime("%Y-%m-%d")


def risk_grade(impact: str, likelihood: str) -> str:
    """영향도 x 발생가능성 (3x3 매트릭스) → High / Medium / Low."""
    score = LEVEL_SCORE[impact] * LEVEL_SCORE[likelihood]
    if score >= 6:
        return "High"
    if score >= 3:
        return "Medium"
    return "Low"


def read_sheets(path: Path) -> dict:
    try:
        sheets = pd.read_excel(path, sheet_name=None)
    except FileNotFoundError:
        raise ReportError(f"파일이 없습니다: {path}")
    for name, columns in REQUIRED_COLUMNS.items():
        if name not in sheets:
            raise ReportError(f"필수 시트 '{name}'가 없습니다.")
        missing = [c for c in columns if c not in sheets[name].columns]
        if missing:
            raise ReportError(f"'{name}' 시트에 필수 열이 없습니다: {missing}")
    return sheets


def parse_site(df: pd.DataFrame) -> dict:
    df = df.dropna(subset=["항목"])
    site = {}
    for key, value in zip(df["항목"].astype(str).str.strip(), df["값"]):
        if isinstance(value, (datetime, pd.Timestamp)):
            value = value.strftime("%Y-%m-%d")
        elif pd.isna(value):
            value = None
        site[key] = value
    missing = [k for k in REQUIRED_SITE_KEYS if site.get(k) in (None, "")]
    if missing:
        raise ReportError(f"현장정보에 필수 항목이 비어 있습니다: {missing}")
    site["보고월"] = to_month(site["보고월"])
    try:
        site["실행예산_억원"] = float(site["실행예산_억원"])
    except (TypeError, ValueError):
        raise ReportError(f"실행예산_억원은 숫자여야 합니다: {site['실행예산_억원']!r}")
    return site


def parse_series(df: pd.DataFrame, sheet: str, plan_col: str, actual_col: str,
                 report_month: str, upper: float | None) -> list[dict]:
    df = df.dropna(subset=["보고월"]).copy()
    df["보고월"] = df["보고월"].map(to_month)
    if df["보고월"].duplicated().any():
        raise ReportError(f"'{sheet}' 시트에 중복된 보고월이 있습니다.")
    # 보고월 이후의 행(계획만 미리 입력된 미래 월)은 대시보드 대상이 아니다.
    df = df[df["보고월"] <= report_month].sort_values("보고월")
    if report_month not in set(df["보고월"]):
        raise ReportError(f"'{sheet}' 시트에 보고월({report_month}) 데이터가 없습니다.")
    for col in (plan_col, actual_col):
        values = pd.to_numeric(df[col], errors="coerce")
        bad = df.loc[values.isna(), "보고월"].tolist()
        if bad:
            raise ReportError(f"'{sheet}' 시트 {col}이 비었거나 숫자가 아닙니다: {bad}")
        out_of_range = df.loc[(values < 0) | (values > (upper if upper is not None else float("inf"))), "보고월"].tolist()
        if out_of_range:
            raise ReportError(f"'{sheet}' 시트 {col} 값이 허용 범위를 벗어났습니다: {out_of_range}")
        df[col] = values
    return [
        {"month": m, "plan": float(p), "actual": float(a)}
        for m, p, a in zip(df["보고월"], df[plan_col], df[actual_col])
    ]


def parse_risks(df: pd.DataFrame, report_month: str) -> dict:
    df = df.dropna(subset=["ID"])
    month_end = pd.Period(report_month, "M").end_time.normalize()
    items = []
    for _, row in df.iterrows():
        rid = str(row["ID"]).strip()
        for col, allowed in (("영향도", LEVEL_SCORE), ("발생가능성", LEVEL_SCORE), ("진행상태", STATUSES)):
            if row[col] not in allowed:
                raise ReportError(f"리스크 {rid}의 {col} 값이 올바르지 않습니다: {row[col]!r} "
                                  f"(허용: {list(allowed)})")
        due = to_date_str(row["목표완료일"])
        overdue = row["진행상태"] != "완료" and due is not None and pd.Timestamp(due) < month_end
        items.append({
            "id": rid,
            "title": row["리스크항목"],
            "category": row["분류"],
            "impact": row["영향도"],
            "likelihood": row["발생가능성"],
            "grade": risk_grade(row["영향도"], row["발생가능성"]),
            "owner": row["담당자"],
            "registered": to_date_str(row["등록일"]),
            "action": row["조치계획"],
            "status": row["진행상태"],
            "due": due,
            "overdue": bool(overdue),
            "note": None if pd.isna(row.get("비고")) else row.get("비고"),
        })
    if len({i["id"] for i in items}) != len(items):
        raise ReportError("리스크 ID가 중복되었습니다.")

    open_items = [i for i in items if i["status"] != "완료"]
    return {
        "summary": {
            "total": len(items),
            "open": len(open_items),
            "overdue": sum(i["overdue"] for i in items),
            "by_status": {s: sum(i["status"] == s for i in items) for s in STATUSES},
            "open_by_grade": {g: sum(i["grade"] == g for i in open_items)
                              for g in ("High", "Medium", "Low")},
        },
        "items": items,
    }


def latest_with_gap(history: list[dict]) -> dict:
    last = history[-1]
    return {**last, "gap": round(last["actual"] - last["plan"], 1)}


def build_dashboard_data(path: Path) -> dict:
    sheets = read_sheets(path)
    site = parse_site(sheets["현장정보"])
    month = site["보고월"]

    progress = parse_series(sheets["공정률"], "공정률", "계획공정률(%)", "실적공정률(%)", month, 100)
    budget = parse_series(sheets["예산집행"], "예산집행", "계획집행누계(억원)", "실적집행누계(억원)", month, None)
    total_budget = site["실행예산_억원"]
    budget_latest = latest_with_gap(budget)
    budget_latest["plan_rate"] = round(budget_latest["plan"] / total_budget * 100, 1)
    budget_latest["actual_rate"] = round(budget_latest["actual"] / total_budget * 100, 1)

    return {
        "meta": {
            "source_file": path.name,
            "report_month": month,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        },
        "site": site,
        "progress": {"latest": latest_with_gap(progress), "history": progress},
        "budget": {"total": total_budget, "latest": budget_latest, "history": budget},
        "risks": parse_risks(sheets["리스크"], month),
    }


def main():
    parser = argparse.ArgumentParser(description="월간 현장 보고 xlsx → 대시보드 JSON")
    parser.add_argument("input", type=Path, help="보고 템플릿 xlsx 경로")
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    try:
        data = build_dashboard_data(args.input)
    except ReportError as e:
        raise SystemExit(f"[양식 오류] {e}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    p, b, r = data["progress"]["latest"], data["budget"]["latest"], data["risks"]["summary"]
    print(f"[{data['meta']['report_month']}] {data['site']['현장명']}")
    print(f"  공정률   계획 {p['plan']}% / 실적 {p['actual']}% (차이 {p['gap']:+}%p)")
    print(f"  예산집행 계획 {b['plan_rate']}% / 실적 {b['actual_rate']}% ({b['actual']:.0f}/{data['budget']['total']:.0f}억원)")
    print(f"  리스크   전체 {r['total']}건, 미해결 {r['open']}건 (High {r['open_by_grade']['High']}), 기한초과 {r['overdue']}건")
    print(f"저장: {args.output}")


if __name__ == "__main__":
    main()
