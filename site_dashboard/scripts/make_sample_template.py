"""더미 데이터가 채워진 월간 현장 보고 템플릿(xlsx)을 생성한다.

실제 현장 데이터는 레포에 올리지 않는다. 이 스크립트가 만드는 파일은
양식 구조만 본뜬 가상의 값이다.

실행: python scripts/make_sample_template.py
"""

from datetime import date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "sample_report_2026-09.xlsx"

HEADER_FILL = PatternFill("solid", fgColor="1F3864")
HEADER_FONT = Font(bold=True, color="FFFFFF")

SITE_INFO = [
    ("보고월", "2026-09"),
    ("현장명", "가상 물류센터 신축공사"),
    ("발주처", "가상개발(주)"),
    ("위치", "경기도 OO시 OO동"),
    ("공사기간_시작", date(2025, 3, 1)),
    ("공사기간_종료", date(2027, 2, 28)),
    ("계약금액_억원", 1250),
    ("실행예산_억원", 1120),
    ("현장소장", "홍길동"),
    ("주요공종", "철골조, 지하2층/지상5층, 연면적 85,000㎡"),
]

# (보고월, 계획 누계 공정률 %, 실적 누계 공정률 %)
PROGRESS = [
    ("2025-03", 1.0, 1.0), ("2025-04", 2.5, 2.3), ("2025-05", 4.5, 4.0),
    ("2025-06", 7.0, 6.2), ("2025-07", 10.0, 9.1), ("2025-08", 13.5, 12.0),
    ("2025-09", 17.5, 15.8), ("2025-10", 22.0, 20.4), ("2025-11", 27.0, 25.1),
    ("2025-12", 32.0, 29.5), ("2026-01", 36.5, 33.0), ("2026-02", 41.0, 37.2),
    ("2026-03", 46.0, 42.5), ("2026-04", 51.5, 48.0), ("2026-05", 57.0, 53.6),
    ("2026-06", 62.0, 58.1), ("2026-07", 66.5, 62.0), ("2026-08", 71.0, 66.3),
    ("2026-09", 75.0, 70.2),
]

# (보고월, 계획 누계 집행액 억원, 실적 누계 집행액 억원)
BUDGET = [
    ("2025-03", 15, 14), ("2025-04", 32, 30), ("2025-05", 55, 52),
    ("2025-06", 82, 80), ("2025-07", 115, 113), ("2025-08", 152, 150),
    ("2025-09", 195, 196), ("2025-10", 243, 247), ("2025-11", 296, 302),
    ("2025-12", 350, 360), ("2026-01", 398, 410), ("2026-02", 446, 461),
    ("2026-03", 502, 520), ("2026-04", 562, 583), ("2026-05", 623, 648),
    ("2026-06", 679, 707), ("2026-07", 728, 760), ("2026-08", 777, 812),
    ("2026-09", 820, 858),
]

RISK_COLUMNS = ["ID", "리스크항목", "분류", "영향도", "발생가능성", "담당자",
                "등록일", "조치계획", "진행상태", "목표완료일", "비고"]
RISKS = [
    ("R-01", "철골 자재 단가 상승", "원가", "상", "상", "김공무",
     date(2025, 11, 3), "대체 공급사 견적 확보 및 선발주 검토", "진행중", date(2026, 10, 31), ""),
    ("R-02", "인근 주민 소음 민원", "민원", "중", "상", "이공사",
     date(2026, 1, 12), "방음벽 보강, 야간작업 제한", "진행중", date(2026, 9, 15), "9월 민원 3건"),
    ("R-03", "우기 토공사 지연", "공정", "상", "중", "박공정",
     date(2026, 5, 20), "배수 계획 수립, 작업 순서 조정", "완료", date(2026, 8, 31), ""),
    ("R-04", "타워크레인 충돌 위험", "안전", "상", "하", "최안전",
     date(2025, 6, 2), "충돌방지장치 설치, 신호수 배치", "완료", date(2025, 7, 15), ""),
    ("R-05", "설계변경(물류 동선) 요청", "공정", "상", "상", "김공무",
     date(2026, 8, 18), "발주처 협의 및 변경 범위 확정", "미착수", date(2026, 11, 30), "발주처 회신 대기"),
    ("R-06", "외벽 패널 품질 불량", "품질", "중", "중", "정품질",
     date(2026, 7, 7), "제작사 공장 검수 강화", "진행중", date(2026, 10, 15), ""),
    ("R-07", "전기 인입 일정 지연", "공정", "중", "중", "박공정",
     date(2026, 9, 2), "한전 협의 일정 확정", "미착수", date(2026, 12, 31), ""),
    ("R-08", "하도급사 인력 수급 불안", "공정", "중", "하", "이공사",
     date(2026, 4, 10), "예비 협력사 Pool 확보", "완료", date(2026, 6, 30), ""),
]


def style_header(ws, ncols):
    for col in range(1, ncols + 1):
        cell = ws.cell(row=1, column=col)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.freeze_panes = "A2"


def add_list_validation(ws, col_letter, options, nrows=200):
    dv = DataValidation(type="list", formula1='"' + ",".join(options) + '"', allow_blank=True)
    dv.add(f"{col_letter}2:{col_letter}{nrows}")
    ws.add_data_validation(dv)


def build_workbook():
    wb = Workbook()

    ws = wb.active
    ws.title = "현장정보"
    ws.append(["항목", "값"])
    for key, value in SITE_INFO:
        ws.append([key, value])
    for row in ws.iter_rows(min_row=2, min_col=2, max_col=2):
        if isinstance(row[0].value, date):
            row[0].number_format = "yyyy-mm-dd"
    style_header(ws, 2)
    ws.column_dimensions["A"].width = 16
    ws.column_dimensions["B"].width = 44

    ws = wb.create_sheet("공정률")
    ws.append(["보고월", "계획공정률(%)", "실적공정률(%)"])
    for row in PROGRESS:
        ws.append(list(row))
    style_header(ws, 3)
    for col in "ABC":
        ws.column_dimensions[col].width = 16

    ws = wb.create_sheet("예산집행")
    ws.append(["보고월", "계획집행누계(억원)", "실적집행누계(억원)"])
    for row in BUDGET:
        ws.append(list(row))
    style_header(ws, 3)
    for col in "ABC":
        ws.column_dimensions[col].width = 20

    ws = wb.create_sheet("리스크")
    ws.append(RISK_COLUMNS)
    for row in RISKS:
        ws.append(list(row))
    for row in ws.iter_rows(min_row=2):
        row[6].number_format = "yyyy-mm-dd"
        row[9].number_format = "yyyy-mm-dd"
    style_header(ws, len(RISK_COLUMNS))
    add_list_validation(ws, "C", ["공정", "원가", "안전", "품질", "민원", "기타"])
    add_list_validation(ws, "D", ["상", "중", "하"])
    add_list_validation(ws, "E", ["상", "중", "하"])
    add_list_validation(ws, "I", ["미착수", "진행중", "완료"])
    widths = [8, 28, 8, 8, 10, 10, 12, 36, 10, 12, 18]
    for i, w in enumerate(widths):
        ws.column_dimensions[chr(ord("A") + i)].width = w

    return wb


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    build_workbook().save(OUT_PATH)
    print(f"생성 완료: {OUT_PATH}")


if __name__ == "__main__":
    main()
