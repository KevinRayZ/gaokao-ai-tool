"""数据模型测试"""
import pytest
from app.models import (
    StudentInfo,
    FamilyContext,
    StudentProfile,
    DimensionScore,
    MajorRecommendation,
    UniversityRecommendation,
    AnalysisResult,
    ReportRequest,
    ReportResponse,
)


class TestStudentInfo:
    """StudentInfo 模型测试"""

    def test_create_student_info(self):
        """测试创建学生信息"""
        student = StudentInfo(
            name="张三",
            province="广东",
            score=580,
            rank=15000,
            subjects=["物理", "化学", "生物"],
            subject_type="物理类",
            year=2026,
        )
        assert student.name == "张三"
        assert student.province == "广东"
        assert student.score == 580
        assert student.rank == 15000
        assert len(student.subjects) == 3

    def test_optional_fields(self):
        """测试可选字段"""
        student = StudentInfo(
            name="李四",
            province="北京",
            score=600,
            subject_type="物理类",
        )
        assert student.rank is None
        assert student.subjects == []
        assert student.year == 2026

    def test_score_validation(self):
        """测试分数验证"""
        # 分数不能为负
        with pytest.raises(Exception):
            StudentInfo(
                name="test",
                province="test",
                score=-1,
                subject_type="物理类",
            )


class TestFamilyContext:
    """FamilyContext 模型测试"""

    def test_default_values(self):
        """测试默认值"""
        family = FamilyContext()
        assert family.economic_level == "一般"
        assert family.location_pref is None
        assert family.has_abroad_plan is False
        assert family.industry_connections == []


class TestStudentProfile:
    """StudentProfile 模型测试"""

    def test_create_profile(self):
        """测试创建学生画像"""
        profile = StudentProfile(
            student=StudentInfo(
                name="张三",
                province="广东",
                score=580,
                subject_type="物理类",
            ),
            interests=["计算机", "人工智能"],
            career_goals=["进大厂"],
            constraints=["不去北方"],
        )
        assert profile.student.name == "张三"
        assert len(profile.interests) == 2
        assert profile.family.economic_level == "一般"


class TestAnalysisModels:
    """分析结果模型测试"""

    def test_dimension_score(self):
        """测试维度评分"""
        score = DimensionScore(
            dimension="就业导向",
            score=8.5,
            reasoning="就业前景好",
            key_factors=["薪资高", "需求大"],
        )
        assert score.score == 8.5

    def test_university_recommendation(self):
        """测试院校推荐"""
        uni = UniversityRecommendation(
            university_name="华南理工大学",
            location="广州",
            is_985=True,
            is_211=True,
            is_double_first_class=True,
            admission_probability="稳",
            recommended_majors=[],
        )
        assert uni.is_985 is True
        assert uni.admission_probability == "稳"


class TestReportModels:
    """报告模型测试"""

    def test_report_request(self):
        """测试报告请求"""
        request = ReportRequest(
            student_profile=StudentProfile(
                student=StudentInfo(
                    name="test",
                    province="test",
                    score=500,
                    subject_type="物理类",
                ),
            ),
        )
        assert request.report_type == "full"

    def test_report_response(self):
        """测试报告响应"""
        response = ReportResponse(
            report_id="test123",
            markdown_content="# Test Report",
            metadata={"version": "1.0"},
        )
        assert response.report_id == "test123"
        assert "# Test Report" in response.markdown_content
