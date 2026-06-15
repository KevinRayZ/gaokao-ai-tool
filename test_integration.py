# -*- coding: utf-8 -*-
"""集成测试 - 测试完整的报告生成流程"""
import asyncio
import json
from app.models.student import StudentProfile, StudentInfo, FamilyContext
from app.services.data_collector import DataCollector
from app.services.analysis_engine import AnalysisEngine
from app.services.report_generator import ReportGenerator


async def test_full_pipeline():
    """测试完整的分析报告生成流程"""
    print("=" * 60)
    print("开始集成测试 - 高考志愿填报分析报告生成")
    print("=" * 60)

    # 1. 创建测试学生数据
    print("\n[1/5] 创建测试学生数据...")
    student_info = StudentInfo(
        name="张三",
        province="云南",
        score=580,
        rank=15000,
        subject_type="理科",
        subjects=["物理", "化学", "生物"],
        target_cities=["昆明", "成都", "重庆"],
        interested_majors=["计算机科学", "人工智能", "软件工程"],
        excluded_majors=["医学", "农学"]
    )

    family_context = FamilyContext(
        economic_level="中等",
        first_generation_student=False,
        family_industry_preferences=["IT/互联网", "金融"],
        location_preference="西南地区"
    )

    profile = StudentProfile(
        student=student_info,
        family=family_context,
        interests=["编程", "数学", "科技创新"],
        career_goals=["互联网公司技术岗", "AI研究员"],
        additional_info="对编程有浓厚兴趣，参加过信息学竞赛"
    )

    print(f"  学生: {profile.student.name}")
    print(f"  省份: {profile.student.province}")
    print(f"  分数: {profile.student.score}")
    print(f"  位次: {profile.student.rank}")

    # 2. 初始化服务
    print("\n[2/5] 初始化服务组件...")
    data_collector = DataCollector()
    analysis_engine = AnalysisEngine()
    report_generator = ReportGenerator()
    print("  [OK] 所有服务初始化完成")

    # 3. 数据采集
    print("\n[3/5] 开始数据采集...")
    collected_data = await data_collector.collect(profile)
    print(f"  [OK] 数据采集完成")
    print(f"  - 搜索结果数: {len(collected_data.search_results)} 条")

    # 4. 五维度分析
    print("\n[4/5] 开始五维度分析...")
    analysis_result = await analysis_engine.analyze(profile, collected_data)
    print(f"  [OK] 分析完成")
    print(f"  - 推荐院校数: {len(analysis_result.universities)}")
    print(f"  - 风险评估: {analysis_result.risk_assessment[:50]}...")

    # 5. 生成报告
    print("\n[5/5] 生成分析报告...")
    report_response = await report_generator.generate(analysis_result)
    report = report_response.markdown_content
    print(f"  [OK] 报告生成完成")
    print(f"  - 报告ID: {report_response.report_id}")
    print(f"  - 报告长度: {len(report)} 字符")

    # 保存报告
    output_file = "test_report_output.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)

    print("\n" + "=" * 60)
    print("[OK] 集成测试完成！")
    print(f"[报告] 已保存到: {output_file}")
    print("=" * 60)

    # 打印报告摘要
    print("\n[报告摘要] 前500字:")
    print("-" * 40)
    print(report[:500])
    print("-" * 40)

    return report


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
