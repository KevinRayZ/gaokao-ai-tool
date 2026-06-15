"""Markdown 报告生成器"""
from pathlib import Path
from uuid import uuid4

from jinja2 import Environment, FileSystemLoader

from app.models.analysis import AnalysisResult
from app.models.report import ReportResponse


# 模板目录路径
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class ReportGenerator:
    """Markdown 报告生成器"""

    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=False,  # Markdown 不需要 HTML 转义
        )

    async def generate(self, result: AnalysisResult) -> ReportResponse:
        """生成 Markdown 报告

        Args:
            result: 分析结果

        Returns:
            报告响应对象
        """
        template = self.env.get_template("report.md.j2")

        # 渲染模板
        markdown = template.render(
            student=result.student_profile,
            universities=result.universities,
            strategy=result.overall_strategy,
            risk=result.risk_assessment,
            generated_at=result.generated_at.strftime("%Y-%m-%d %H:%M"),
        )

        return ReportResponse(
            report_id=uuid4().hex,
            markdown_content=markdown,
            metadata={
                "version": "1.0",
                "engine": "phase1",
                "generated_at": result.generated_at.isoformat(),
                "student_name": result.student_profile.student.name,
                "province": result.student_profile.student.province,
            },
        )
