"""报告模板渲染测试"""
from datetime import datetime

from app.models import (
    StudentInfo,
    FamilyContext,
    StudentProfile,
    DimensionScore,
    MajorRecommendation,
    UniversityRecommendation,
    AnalysisResult,
)
from app.services.report_generator import ReportGenerator


async def test_report_generation():
    """测试报告生成"""
    # 创建测试数据
    profile = StudentProfile(
        student=StudentInfo(
            name="张三",
            province="广东",
            score=580,
            rank=15000,
            subjects=["物理", "化学", "生物"],
            subject_type="物理类",
            year=2026,
        ),
        family=FamilyContext(
            economic_level="一般",
            location_pref="珠三角",
        ),
        interests=["计算机", "人工智能"],
        career_goals=["进大厂", "做技术"],
        constraints=["不去北方"],
    )

    # 创建模拟的分析结果
    result = AnalysisResult(
        student_profile=profile,
        universities=[
            UniversityRecommendation(
                university_name="华南理工大学",
                location="广州",
                is_985=True,
                is_211=True,
                is_double_first_class=True,
                admission_probability="稳",
                estimated_rank_range=(12000, 18000),
                recommended_majors=[
                    MajorRecommendation(
                        major_name="计算机科学与技术",
                        category="工学",
                        dimensions=[
                            DimensionScore(
                                dimension="就业导向",
                                score=9.0,
                                reasoning="IT行业需求旺盛，薪资水平高",
                                key_factors=["互联网大厂", "人工智能"],
                            ),
                            DimensionScore(
                                dimension="经济理性",
                                score=7.5,
                                reasoning="学费适中，奖学金机会多",
                                key_factors=["学费", "奖学金"],
                            ),
                            DimensionScore(
                                dimension="个人匹配",
                                score=8.5,
                                reasoning="与学生兴趣高度匹配",
                                key_factors=["兴趣", "能力"],
                            ),
                            DimensionScore(
                                dimension="政策环境",
                                score=8.0,
                                reasoning="国家重点支持领域",
                                key_factors=["政策支持"],
                            ),
                            DimensionScore(
                                dimension="趋势前瞻",
                                score=9.0,
                                reasoning="数字化转型趋势",
                                key_factors=["行业趋势"],
                            ),
                        ],
                        overall_score=8.5,
                        match_reason="与学生兴趣高度匹配，就业前景广阔",
                        warnings=["竞争激烈，需要较强数学基础"],
                    ),
                ],
            ),
        ],
        overall_strategy="以计算机类专业为主，选择珠三角地区的985/211院校",
        risk_assessment="分数处于中等偏上水平，需要合理设置梯度",
        generated_at=datetime(2026, 6, 12, 10, 30),
    )

    # 生成报告
    generator = ReportGenerator()
    report = await generator.generate(result)

    # 使用 UTF-8 编码输出
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 60)
    print("生成的报告：")
    print("=" * 60)
    print(report.markdown_content)
    print("=" * 60)
    print(f"报告ID: {report.report_id}")
    print(f"元数据: {report.metadata}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_report_generation())
