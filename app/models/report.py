"""报告请求/响应数据模型"""
from pydantic import BaseModel, Field

from app.models.student import StudentProfile


class ReportRequest(BaseModel):
    """报告生成请求"""

    student_profile: StudentProfile = Field(description="学生画像")
    report_type: str = Field(
        default="full",
        description="报告类型：full|summary",
    )


class ReportResponse(BaseModel):
    """报告生成响应"""

    report_id: str = Field(description="报告唯一标识")
    markdown_content: str = Field(description="Markdown 报告正文")
    metadata: dict = Field(default_factory=dict, description="元数据")
