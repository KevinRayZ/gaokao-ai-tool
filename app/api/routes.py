"""API 路由"""
import asyncio
import json
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

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

    流程：
    1. 数据采集：根据学生信息生成搜索查询，获取相关数据
    2. 分析引擎：五维度分析，生成院校和专业推荐
    3. 报告生成：将分析结果渲染为 Markdown 报告
    """
    # 用量检查
    check_rate_limit(request)
    check_daily_limit(request)

    try:
        # 1. 数据采集
        collector = DataCollector()
        data = await collector.collect(body.student_profile)

        # 2. 分析
        engine = AnalysisEngine()
        result = await engine.analyze(body.student_profile, data)

        # 3. 生成报告
        generator = ReportGenerator()
        report = await generator.generate(result)

        # 增加计数
        increment_daily_count()

        return report

    except HTTPException:
        raise
    except Exception as e:
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
    # 用量检查
    check_rate_limit(request)
    check_daily_limit(request)

    async def event_stream():
        try:
            # Step 1: 数据准备
            yield f"data: {json.dumps({'step': 1, 'total': 3, 'message': '正在准备学生数据...', 'progress': 10})}\n\n"
            await asyncio.sleep(0.1)

            collector = DataCollector()
            data = await collector.collect(body.student_profile)

            yield f"data: {json.dumps({'step': 1, 'total': 3, 'message': '数据准备完成', 'progress': 30})}\n\n"
            await asyncio.sleep(0.1)

            # Step 2: AI分析
            yield f"data: {json.dumps({'step': 2, 'total': 3, 'message': '正在进行AI分析（五维度评估）...', 'progress': 40})}\n\n"
            await asyncio.sleep(0.1)

            engine = AnalysisEngine()
            result = await engine.analyze(body.student_profile, data)

            yield f"data: {json.dumps({'step': 2, 'total': 3, 'message': 'AI分析完成', 'progress': 80})}\n\n"
            await asyncio.sleep(0.1)

            # Step 3: 生成报告
            yield f"data: {json.dumps({'step': 3, 'total': 3, 'message': '正在生成分析报告...', 'progress': 90})}\n\n"
            await asyncio.sleep(0.1)

            generator = ReportGenerator()
            report = await generator.generate(result)

            # 增加计数
            increment_daily_count()

            yield f"data: {json.dumps({'step': 3, 'total': 3, 'message': '报告生成完成！', 'progress': 100, 'data': report.model_dump()})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': True, 'message': f'分析出错：{str(e)}'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
