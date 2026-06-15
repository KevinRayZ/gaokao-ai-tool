"""API 路由"""
import asyncio
import io
import json
import traceback
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, Response
import markdown
from xhtml2pdf import pisa

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

    接收 markdown_content，返回 PDF 文件
    """
    body = await request.json()
    markdown_content = body.get("markdown_content", "")
    student_name = body.get("student_name", "匿名")

    if not markdown_content:
        raise HTTPException(status_code=400, detail="报告内容为空")

    try:
        # Markdown 转 HTML
        html_body = markdown.markdown(
            markdown_content,
            extensions=["tables", "fenced_code", "nl2br"]
        )

        # 拼接完整 HTML（带样式）
        styled_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{ size: A4; margin: 2cm; }}
    body {{
        font-family: "Noto Sans SC", "Microsoft YaHei", "PingFang SC", "Helvetica Neue", Arial, sans-serif;
        font-size: 11pt;
        line-height: 1.8;
        color: #333;
    }}
    h1 {{
        font-size: 22pt;
        color: #1e3a5f;
        border-bottom: 3px solid #1e3a5f;
        padding-bottom: 8px;
        margin-top: 30px;
    }}
    h2 {{
        font-size: 16pt;
        color: #2c5282;
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 5px;
        margin-top: 25px;
    }}
    h3 {{
        font-size: 13pt;
        color: #2d3748;
        margin-top: 20px;
    }}
    h4 {{
        font-size: 11pt;
        color: #4a5568;
        margin-top: 15px;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
        font-size: 10pt;
    }}
    th, td {{
        border: 1px solid #cbd5e0;
        padding: 8px 10px;
        text-align: left;
    }}
    th {{
        background-color: #edf2f7;
        font-weight: 600;
        color: #2d3748;
    }}
    tr:nth-child(even) {{
        background-color: #f7fafc;
    }}
    ul, ol {{
        padding-left: 20px;
        margin: 10px 0;
    }}
    li {{
        margin: 5px 0;
    }}
    strong {{
        color: #2d3748;
    }}
    em {{
        color: #718096;
    }}
    blockquote {{
        border-left: 4px solid #4299e1;
        padding: 10px 15px;
        margin: 15px 0;
        background: #ebf8ff;
        color: #2b6cb0;
    }}
    code {{
        background: #edf2f7;
        padding: 2px 5px;
        border-radius: 3px;
        font-size: 10pt;
    }}
    hr {{
        border: none;
        border-top: 1px solid #e2e8f0;
        margin: 20px 0;
    }}
    .footer {{
        margin-top: 40px;
        padding-top: 15px;
        border-top: 1px solid #e2e8f0;
        font-size: 9pt;
        color: #a0aec0;
        text-align: center;
    }}
</style>
</head>
<body>
{html_body}
<div class="footer">
    本报告由 AI 高考志愿填报工具生成 | 仅供参考，请结合官方数据综合判断
</div>
</body>
</html>"""

        # 生成 PDF
        pdf_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(styled_html, dest=pdf_buffer, encoding="utf-8")

        if pisa_status.err:
            raise Exception("PDF 生成失败")

        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()

        filename = f"高考志愿分析报告_{student_name}_{__import__('datetime').date.today()}.pdf"

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
