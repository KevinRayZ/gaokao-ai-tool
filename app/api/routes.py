"""API 路由"""
import asyncio
import json
import re
import traceback
from datetime import date
from urllib.parse import quote
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, Response
import markdown

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
from app.services.code_store import code_store

router = APIRouter(prefix="/api/v1", tags=["志愿分析"])


def _sse_event(data: dict) -> str:
    """构造 SSE 事件字符串"""
    return "data: " + json.dumps(data, ensure_ascii=False) + "\n\n"


def _markdown_to_html_report(md_text: str, student_name: str) -> str:
    """将 Markdown 转换为带精美样式的 HTML 报告"""
    html_body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "nl2br"]
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>高考志愿分析报告 - {student_name}</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: "Noto Sans SC", "Microsoft YaHei", "PingFang SC", "Helvetica Neue", Arial, sans-serif;
        font-size: 15px;
        line-height: 1.9;
        color: #2d3748;
        background: #f7fafc;
        padding: 40px 20px;
    }}
    .report-container {{
        max-width: 800px;
        margin: 0 auto;
        background: #fff;
        border-radius: 12px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.08);
        overflow: hidden;
    }}
    .report-header {{
        background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%);
        color: #fff;
        padding: 40px 40px 30px;
    }}
    .report-header h1 {{
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 8px;
    }}
    .report-header .meta {{
        font-size: 14px;
        opacity: 0.85;
    }}
    .report-body {{
        padding: 35px 40px 50px;
    }}
    h1 {{
        font-size: 24px;
        color: #1e3a5f;
        border-bottom: 3px solid #1e3a5f;
        padding-bottom: 8px;
        margin: 35px 0 18px;
    }}
    h1:first-child {{ margin-top: 0; }}
    h2 {{
        font-size: 20px;
        color: #2c5282;
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 6px;
        margin: 28px 0 14px;
    }}
    h3 {{
        font-size: 17px;
        color: #2d3748;
        margin: 22px 0 10px;
    }}
    h4 {{
        font-size: 15px;
        color: #4a5568;
        margin: 18px 0 8px;
    }}
    p {{
        margin: 10px 0;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 18px 0;
        font-size: 14px;
    }}
    th, td {{
        border: 1px solid #e2e8f0;
        padding: 10px 14px;
        text-align: left;
    }}
    th {{
        background: #edf2f7;
        font-weight: 600;
        color: #2d3748;
    }}
    tr:nth-child(even) {{ background: #f7fafc; }}
    tr:hover {{ background: #ebf8ff; }}
    ul, ol {{
        padding-left: 24px;
        margin: 10px 0;
    }}
    li {{ margin: 6px 0; }}
    strong {{ color: #1a202c; font-weight: 600; }}
    em {{ color: #718096; }}
    blockquote {{
        border-left: 4px solid #4299e1;
        padding: 12px 18px;
        margin: 16px 0;
        background: #ebf8ff;
        color: #2b6cb0;
        border-radius: 0 6px 6px 0;
    }}
    code {{
        background: #edf2f7;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 13px;
        font-family: "SF Mono", "Fira Code", monospace;
    }}
    pre {{
        background: #1a202c;
        color: #e2e8f0;
        padding: 16px 20px;
        border-radius: 8px;
        overflow-x: auto;
        margin: 16px 0;
    }}
    pre code {{
        background: none;
        padding: 0;
        color: inherit;
    }}
    hr {{
        border: none;
        border-top: 1px solid #e2e8f0;
        margin: 24px 0;
    }}
    .report-footer {{
        text-align: center;
        padding: 20px 40px;
        border-top: 1px solid #e2e8f0;
        font-size: 12px;
        color: #a0aec0;
        background: #f7fafc;
    }}
    @media print {{
        body {{ background: #fff; padding: 0; }}
        .report-container {{ box-shadow: none; }}
        .report-header {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    }}
</style>
</head>
<body>
<div class="report-container">
    <div class="report-header">
        <h1>高考志愿分析报告</h1>
        <div class="meta">学生：{student_name} ｜ 生成日期：{date.today().strftime('%Y年%m月%d日')}</div>
    </div>
    <div class="report-body">
        {html_body}
    </div>
    <div class="report-footer">
        本报告由 AI 高考志愿填报工具生成 ｜ 仅供参考，请结合官方数据综合判断
    </div>
</div>
</body>
</html>"""


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "version": settings.app_version}


@router.get("/usage")
async def usage_info():
    """查询今日用量"""
    return get_usage_info()


@router.post("/redeem")
async def redeem_code(request: Request):
    """
    兑换码兑换接口。

    不使用 HTTPException，以便前端解析 success/message 字段。
    """
    body = await request.json()
    code = body.get("code", "")

    if not code:
        return {"success": False, "credits": 0, "message": "请输入兑换码"}

    result = code_store.redeem_code(code)
    return result


@router.post("/analyze", response_model=ReportResponse)
async def analyze_and_report(request: Request, body: ReportRequest):
    """主接口：输入学生信息，返回完整分析报告"""
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
        raise HTTPException(status_code=500, detail=f"分析过程中出错：{str(e)}")


@router.post("/analyze-with-progress")
async def analyze_with_progress(request: Request, body: ReportRequest):
    """带进度推送的分析接口（SSE）"""
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


@router.post("/download-html")
async def download_html(request: Request):
    """
    将 Markdown 报告转换为精排版 HTML 文件下载

    接收 markdown_content，返回带样式的 HTML 文件
    """
    body = await request.json()
    markdown_content = body.get("markdown_content", "")
    student_name = body.get("student_name", "匿名")

    if not markdown_content:
        raise HTTPException(status_code=400, detail="报告内容为空")

    try:
        html_content = _markdown_to_html_report(markdown_content, student_name)
        html_bytes = html_content.encode("utf-8")

        filename = f"高考志愿分析报告_{student_name}_{date.today()}.html"
        # URL编码文件名，避免中文字符在HTTP头中触发latin-1编码错误
        encoded_filename = quote(filename)

        return Response(
            content=html_bytes,
            media_type="text/html; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
                "Content-Length": str(len(html_bytes)),
            }
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"HTML 生成失败：{str(e)}")
