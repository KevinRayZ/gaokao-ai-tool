"""数据模型"""
from app.models.student import StudentInfo, FamilyContext, StudentProfile
from app.models.analysis import (
    DimensionScore,
    MajorRecommendation,
    UniversityRecommendation,
    AnalysisResult,
)
from app.models.report import ReportRequest, ReportResponse

__all__ = [
    "StudentInfo",
    "FamilyContext",
    "StudentProfile",
    "DimensionScore",
    "MajorRecommendation",
    "UniversityRecommendation",
    "AnalysisResult",
    "ReportRequest",
    "ReportResponse",
]
