"""学生信息数据模型"""
from pydantic import BaseModel, Field


class StudentInfo(BaseModel):
    """学生基本信息"""

    name: str = Field(description="姓名（可匿名）")
    province: str = Field(description="省份（如'广东'）")
    score: int = Field(ge=0, le=750, description="高考总分")
    rank: int | None = Field(default=None, ge=0, description="省排名（可选）")
    subjects: list[str] = Field(default_factory=list, description="选科组合（如['物理','化学','生物']）")
    subject_type: str = Field(description="科类：物理类|历史类|理科|文科")
    year: int = Field(default=2026, ge=2020, le=2030, description="高考年份")


class FamilyContext(BaseModel):
    """家庭背景信息"""

    economic_level: str = Field(
        default="一般",
        description="经济水平：困难|一般|较好|富裕",
    )
    location_pref: str | None = Field(
        default=None,
        description="偏好地区（如'长三角'、'珠三角'）",
    )
    has_abroad_plan: bool = Field(default=False, description="是否有出国计划")
    industry_connections: list[str] = Field(
        default_factory=list,
        description="家庭在哪些行业有资源",
    )


class StudentProfile(BaseModel):
    """完整学生画像"""

    student: StudentInfo
    family: FamilyContext = Field(default_factory=FamilyContext)
    interests: list[str] = Field(
        default_factory=list,
        description="兴趣方向（如'计算机'、'医学'）",
    )
    career_goals: list[str] = Field(
        default_factory=list,
        description="职业目标（如'进大厂'、'考公务员'）",
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="特殊约束（如'不去北方'、'不学医'）",
    )
