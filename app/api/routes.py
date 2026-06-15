"""API 路由"""
import asyncio
import io
import json
import os
import re
import traceback
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, Response
from fpdf import FPDF

from app.config import settings
from app.middleware.rate_limiter import (
    check_daily_limit,
    check_rate_limit,
    increment_daily_count,
    get_usage_info,
)
from app.models.report import ReportRequest, ReportResponse
from app.services.data_collector import DataCollector
from app.services.analysis_engine import AnalysisEngine
from app.services.report_generator import ReportGenerator

router = APIRouter(prefix="/api/v1", tags=["志愿分析"])

# 字体路径
FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "fonts")
FONT_PATH = os.path.join(FONT_DIR, "NotoSansSC-Regular.otf")


class ChinesePDF(FPDF):
    """支持中文的PDF生成器"""

    def __init__(self):
        super().__init__()
        self.font_added = False
        self._ensure_font()

    def _ensure_font(self):
        if not self.font_added and os.path.exists(FONT_PATH):
            self.add_font("NotoSansSC", "", FONT_PATH, uni=True)
            self.font_added = True

    def header(self):
        if self.page_no() > 1:
            self.set_font("NotoSansSC", size=8)
            self.set_text_color(160, 174, 192)
            self.cell(0, 10, "AI 高考志愿分析报告", align="C")
            self.ln(5)

    def footer(self):
        self.set_y(-20)
        self.set_font("NotoSansSC", size=7)
        self.set_text_color(160, 174, 192)
        self.cell(0, 10, f"第 {self.page_no()} 页 | 仅供参考，请结合官方数据综合判断", align="C")


def _parse_markdown_to_pdf(md_text: str, student_name: str) -> bytes:
    """将 Markdown 文本解析并渲染为 PDF"""

    pdf = ChinesePDF()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()

    # 标题页
    pdf.set_font("NotoSansSC", size=24)
    pdf.set_text_color(30, 58, 95)
    pdf.ln(30)
    pdf.multi_cell(0, 14, "高考志愿分析报告", align="C")
    pdf.ln(5)

    pdf.set_font("NotoSansSC", size=14)
    pdf.set_text_color(74, 85, 104)
    pdf.cell(0, 10, f"学生：{student_name}", align="C")
    pdf.ln(8)

    from datetime import date
    pdf.set_font("NotoSansSC", size=11)
    pdf.set_text_color(113, 128, 150)
    pdf.cell(0, 8, f"生成日期：{date.today().strftime('%Y年%m月%d日')}", align="C")
    pdf.ln(15)

    # 分隔线
    pdf.set_draw_color(226, 232, 240)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(15)

    # 解析 Markdown 正文
    lines = md_text.split("\n")
    i = 0
    in_table = False
    table_rows = []

    while i < len(lines):
        line = lines[i].rstrip()

        # 跳过空行
        if not line:
            if in_table and table_rows:
                _render_table(pdf, table_rows)
                table_rows = []
                in_table = False
            pdf.ln(4)
            i += 1
            continue

        # 标题 h1
        if line.startswith("# ") and not line.startswith("## "):
            pdf.ln(6)
            pdf.set_font("NotoSansSC", size=18)
            pdf.set_text_color(30, 58, 95)
            text = line[2:].strip()
            # 下划线效果
            pdf.multi_cell(0, 10, text)
            y = pdf.get_y()
            pdf.set_draw_color(30, 58, 95)
            pdf.set_line_width(0.6)
            pdf.line(20, y, 190, y)
            pdf.set_line_width(0.2)
            pdf.ln(4)
            i += 1
            continue

        # 标题 h2
        if line.startswith("## ") and not line.startswith("### "):
            pdf.ln(5)
            pdf.set_font("NotoSansSC", size=14)
            pdf.set_text_color(44, 82, 130)
            text = line[3:].strip()
            pdf.multi_cell(0, 9, text)
            y = pdf.get_y()
            pdf.set_draw_color(226, 232, 240)
            pdf.line(20, y, 190, y)
            pdf.ln(3)
            i += 1
            continue

        # 标题 h3
        if line.startswith("### "):
            pdf.ln(4)
            pdf.set_font("NotoSansSC", size=12)
            pdf.set_text_color(45, 55, 72)
            pdf.multi_cell(0, 8, line[4:].strip())
            pdf.ln(2)
            i += 1
            continue

        # 标题 h4
        if line.startswith("#### "):
            pdf.ln(3)
            pdf.set_font("NotoSansSC", size=11)
            pdf.set_text_color(74, 85, 104)
            pdf.multi_cell(0, 7, line[5:].strip())
            pdf.ln(1)
            i += 1
            continue

        # 水平线
        if line.strip() == "---":
            if in_table and table_rows:
                _render_table(pdf, table_rows)
                table_rows = []
                in_table = False
            pdf.ln(2)
            pdf.set_draw_color(226, 232, 240)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(4)
            i += 1
            continue

        # 表格行检测
        if "|" in line and not line.strip().startswith("```"):
            cells = [c.strip() for c in line.split("|")]
            cells = [c for c in cells if c]  # 去除首尾空元素

            # 跳过分隔行 (|---|---|)
            if all(re.match(r"^[\s\-:]+$", c) for c in cells):
                i += 1
                continue

            table_rows.append(cells)
            in_table = True
            i += 1
            continue

        # 如果在表格中遇到非表格行，先渲染表格
        if in_table and table_rows:
            _render_table(pdf, table_rows)
            table_rows = []
            in_table = False

        # 无序列表
        if re.match(r"^[\s]*[-*+]\s", line):
            pdf.set_font("NotoSansSC", size=10)
            pdf.set_text_color(45, 55, 72)
            indent = len(line) - len(line.lstrip())
            text = re.sub(r"^[\s]*[-*+]\s+", "", line)
            bullet = "  •" if indent >= 2 else "•"
            pdf.set_x(22 + indent * 3)
            pdf.cell(6, 6, bullet)
            _write_wrapped(pdf, text, x_offset=28 + indent * 3)
            i += 1
            continue

        # 有序列表
        if re.match(r"^[\s]*\d+\.\s", line):
            pdf.set_font("NotoSansSC", size=10)
            pdf.set_text_color(45, 55, 72)
            m = re.match(r"^[\s]*(\d+)\.\s+(.*)", line)
            if m:
                num = m.group(1)
                text = m.group(2)
                pdf.set_x(22)
                pdf.cell(6, 6, f"{num}.")
                _write_wrapped(pdf, text, x_offset=28)
            i += 1
            continue

        # 引用块
        if line.startswith(">"):
            pdf.set_font("NotoSansSC", size=10)
            pdf.set_text_color(43, 108, 176)
            quote_text = line[1:].strip()
            pdf.set_fill_color(235, 248, 255)
            # 引用左边框效果
            y_start = pdf.get_y()
            pdf.set_x(22)
            pdf.multi_cell(166, 6, quote_text, fill=True)
            y_end = pdf.get_y()
            pdf.set_draw_color(66, 153, 225)
            pdf.set_line_width(0.8)
            pdf.line(20, y_start, 20, y_end)
            pdf.set_line_width(0.2)
            pdf.ln(2)
            i += 1
            continue

        # 代码块
        if line.strip().startswith("```"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # 跳过结束的 ```
            pdf.set_font("Courier", size=8)
            pdf.set_text_color(74, 85, 104)
            pdf.set_fill_color(237, 242, 247)
            for cl in code_lines:
                pdf.set_x(22)
                pdf.multi_cell(166, 5, "  " + cl, fill=True)
            pdf.ln(2)
            continue

        # 普通段落（处理加粗和斜体）
        pdf.set_font("NotoSansSC", size=10)
        pdf.set_text_color(45, 55, 72)
        clean = _clean_markdown_formatting(line)
        if clean:
            _write_wrapped(pdf, clean, x_offset=20)
        i += 1

    # 处理末尾残留表格
    if in_table and table_rows:
        _render_table(pdf, table_rows)

    return pdf.output()


def _clean_markdown_formatting(text: str) -> str:
    """清理 Markdown 格式标记，保留纯文本"""
    # 去掉 emoji（NotoSansSC 不包含 emoji 字形，会导致字体警告）
    import re as _re
    text = _re.sub(
        r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF'
        r'\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF'
        r'\U00002702-\U000027B0\U000024C2-\U0001F251]+',
        '', text
    )
    # 去掉 **text** 和 __text__ 加粗标记（但保留文字）
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    # 去掉 *text* 和 _text_ 斜体标记
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    # 去掉 `code` 标记
    text = re.sub(r'`(.+?)`', r'\1', text)
    # 去掉 [text](url) 链接，只留文字
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    return text


def _write_wrapped(pdf: FPDF, text: str, x_offset: float = 20):
    """写带自动换行的文本"""
    pdf.set_x(x_offset)
    pdf.multi_cell(170 - (x_offset - 20), 6, text)


def _render_table(pdf: FPDF, rows: list):
    """渲染表格"""
    if not rows:
        return

    pdf.ln(3)
    col_count = max(len(row) for row in rows)
    page_w = 170
    col_w = page_w / col_count

    # 表头样式
    pdf.set_fill_color(237, 242, 247)
    pdf.set_text_color(45, 55, 72)
    pdf.set_font("NotoSansSC", size=9)

    for row_idx, row in enumerate(rows):
        # 补齐列数
        while len(row) < col_count:
            row.append("")
        # 截断多余列
        row = row[:col_count]

        is_header = (row_idx == 0)
        if is_header:
            pdf.set_font("NotoSansSC", size=9)
            pdf.set_text_color(45, 55, 72)
        else:
            pdf.set_font("NotoSansSC", size=8)
            pdf.set_text_color(51, 65, 85)

        max_h = 6
        for cell_idx, cell_text in enumerate(row):
            # 计算需要的行数来容纳文本
            clean_text = _clean_markdown_formatting(cell_text)
            chars_per_line = int(col_w / 5.5)  # 中文字符宽度估算
            needed_lines = max(1, (len(clean_text) // chars_per_line) + 1)
            cell_h = max(6, needed_lines * 6)
            max_h = max(max_h, cell_h)

        x_start = pdf.get_x()
        y_start = pdf.get_y()

        for cell_idx, cell_text in enumerate(row):
            pdf.set_xy(x_start + cell_idx * col_w, y_start)
            clean_text = _clean_markdown_formatting(cell_text)
            # 绘制单元格边框和背景
            if is_header:
                pdf.rect(x_start + cell_idx * col_w, y_start, col_w, max_h, 'DF')
            else:
                pdf.rect(x_start + cell_idx * col_w, y_start, col_w, max_h, 'D')
            # 写入文字
            pdf.set_xy(x_start + cell_idx * col_w + 1.5, y_start + 1)
            pdf.multi_cell(col_w - 3, 5, clean_text)

        pdf.set_xy(x_start, y_start + max_h)

    pdf.ln(4)


# ============================================================
# SSE 工具函数
# ============================================================

def _sse_event(data: dict) -> str:
    """构造 SSE 事件字符串"""
    return "data: " + json.dumps(data, ensure_ascii=False) + "\n\n"


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "version": settings.app_version}


@router.get("/usage")
async def usage_info():
    """查询今日用量"""
    return get_usage_info()


@router.post("/analyze", response_model=ReportResponse)
async def analyze_and_report(request: Request, body: ReportRequest):
    """
    主接口：输入学生信息，返回完整分析报告
    """
    check_rate_limit(request)
    check_daily_limit(request)

    try:
        collector = DataCollector()
        data = await collector.collect(body.student_profile)

        engine = AnalysisEngine()
        result = await engine.analyze(body.student_profile, data)

        generator = ReportGenerator()
        report = await generator.generate(result)

        increment_daily_count()
        return report

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"分析过程中出错：{str(e)}",
        )


@router.post("/analyze-with-progress")
async def analyze_with_progress(request: Request, body: ReportRequest):
    """
    带进度推送的分析接口（SSE）

    实时推送分析进度，让用户知道当前正在做什么
    """
    check_rate_limit(request)
    check_daily_limit(request)

    async def event_stream():
        try:
            yield _sse_event({"step": 1, "total": 3, "message": "正在准备学生数据...", "progress": 10})
            await asyncio.sleep(0.1)

            collector = DataCollector()
            data = await collector.collect(body.student_profile)

            yield _sse_event({"step": 1, "total": 3, "message": "数据准备完成", "progress": 30})
            await asyncio.sleep(0.1)

            yield _sse_event({"step": 2, "total": 3, "message": "正在进行AI分析（五维度评估）...", "progress": 40})
            await asyncio.sleep(0.1)

            engine = AnalysisEngine()
            result = await engine.analyze(body.student_profile, data)

            yield _sse_event({"step": 2, "total": 3, "message": "AI分析完成", "progress": 80})
            await asyncio.sleep(0.1)

            yield _sse_event({"step": 3, "total": 3, "message": "正在生成分析报告...", "progress": 90})
            await asyncio.sleep(0.1)

            generator = ReportGenerator()
            report = await generator.generate(result)

            increment_daily_count()

            yield _sse_event({"step": 3, "total": 3, "message": "报告生成完成！", "progress": 100, "data": report.model_dump()})

        except Exception as e:
            traceback.print_exc()
            yield _sse_event({"error": True, "message": f"分析出错：{str(e)}"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/download-pdf")
async def download_pdf(request: Request):
    """
    将 Markdown 报告转换为 PDF 下载

    接收 markdown_content，返回 PDF 文件（使用 fpdf2 纯 Python 生成）
    """
    body = await request.json()
    markdown_content = body.get("markdown_content", "")
    student_name = body.get("student_name", "匿名")

    if not markdown_content:
        raise HTTPException(status_code=400, detail="报告内容为空")

    try:
        pdf_bytes = bytes(_parse_markdown_to_pdf(markdown_content, student_name))

        from datetime import date
        filename = f"高考志愿分析报告_{student_name}_{date.today()}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(pdf_bytes)),
            }
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PDF 生成失败：{str(e)}")
