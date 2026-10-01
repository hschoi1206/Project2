import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_dashboard import PLACEHOLDER, render_html  # noqa: E402
from make_sample_template import build_workbook  # noqa: E402
from parse_report import build_dashboard_data  # noqa: E402


def test_render_embeds_data(tmp_path):
    path = tmp_path / "report.xlsx"
    build_workbook().save(path)
    data = build_dashboard_data(path)

    html = render_html(data)

    assert PLACEHOLDER not in html
    embedded = re.search(r'<script id="dashboard-data" type="application/json">(.*?)</script>', html, re.S).group(1)
    assert json.loads(embedded)["site"]["현장명"] == "가상 물류센터 신축공사"


def test_script_tag_in_data_is_escaped():
    html = render_html({"meta": {"note": "</script><script>alert(1)</script>"}})
    assert "</script><script>alert(1)" not in html
