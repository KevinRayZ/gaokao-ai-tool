"""分析结果数据模型"""
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.student import StudentProfile


class DimensionScore(BaseModel):
    """单维度评分"""

    dimension: str = Field(description="维度名称")
    score: float = Field(ge=0, le=10, description="评分 0-10")
    reasoning: str = Field(description="评分依据")
    key_factors: list[str] = Field(default_factory=list, description="关键影响因素")


class MajorRecommendation(BaseModel):
    """专业推荐"""

    major_name: str = Field(description="专业名称")
    major_code: str | None = Field(default=None, description="专业代码")
    category: str = Field(description="学科门类")
    dimensions: list[DimensionScore] = Field(description="五维度评分")
    overall_score: float = Field(ge=0, le=10, description="综合评分")
    match_reason: str = Field(description="推荐理由")
    warnings: list[str] = Field(default_factory=list, description="风险提示")


class UniversityRecommendation(BaseModel):
    """院校推荐"""

    university_name: str = Field(description="院校名称")
    location: str = Field(description="所在城市")
    is_985: bool = Field(default=False, description="是否 985")
    is_211: bool = Field(default=False, description="是否 211")
    is_double_first_class: bool = Field(default=False, description="是否双一流")
    admission_probability: str = Field(description="录取概率分类：冲|稳|保")
    estimated_rank_range: tuple[int, int] | None = Field(
        default=None,
        description="预估录取排名区间",
    )
    recommended_majors: list[MajorRecommendation] = Field(
        default_factory=list,
        description="推荐专业",
    )


class AnalysisResult(BaseModel):
    """完整分析结果"""

    student_profile: StudentProfile
    universities: list[UniversityRecommendation] = Field(
        default_factory=list,
        description="推荐院校列表",
    )
    overall_strategy: str = Field(description="总体填报策略")
    risk_assessment: str = Field(description="风险评估")
    generated_at: datetime = Field(
        default_factory=datetime.now,
        description="生成时间",
    )
