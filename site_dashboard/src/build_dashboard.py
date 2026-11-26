"""보고 템플릿(xlsx) → 대시보드 HTML 파일 한 개를 만든다.

실행: python src/build_dashboard.py data/raw/sample_report_2026-09.xlsx
출력: output/dashboard_2026-09.html  (더블클릭하면 브라우저로 열림, 인터넷 연결 불필요)
"""

import argparse
import json
from pathlib import Path

from parse_report import PROJECT_ROOT, ReportError, build_dashboard_data

TEMPLATE = PROJECT_ROOT / "templates" / "dashboard.html"
OUTPUT_DIR = PROJECT_ROOT / "output"
PLACEHOLDER = "/*__DATA__*/"


def render_html(data: dict) -> str:
    # </script> 같은 문자열이 데이터에 섞여도 HTML이 깨지지 않도록 '</'를 이스케이프한다.
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    template = TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        raise RuntimeError(f"템플릿에 {PLACEHOLDER} 자리표시자가 없습니다: {TEMPLATE}")
    return template.replace(PLACEHOLDER, payload)


def main():
    parser = argparse.ArgumentParser(description="월간 현장 보고 xlsx → 대시보드 HTML")
    parser.add_argument("input", type=Path, help="보고 템플릿 xlsx 경로")
    parser.add_argument("-o", "--output", type=Path, help="출력 HTML 경로 (기본: output/dashboard_<보고월>.html)")
    args = parser.parse_args()

    try:
        data = build_dashboard_data(args.input)
    except ReportError as e:
        raise SystemExit(f"[양식 오류] {e}")

    out = args.output or OUTPUT_DIR / f"dashboard_{data['meta']['report_month']}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_html(data), encoding="utf-8")
    print(f"대시보드 생성: {out}")


if __name__ == "__main__":
    main()
