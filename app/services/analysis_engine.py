"""五维度分析引擎"""
from datetime import datetime

from app.models.student import StudentProfile
from app.models.analysis import (
    DimensionScore,
    MajorRecommendation,
    UniversityRecommendation,
    AnalysisResult,
)
from app.services.data_collector import CollectedData
from app.services.llm_client import chat_completion_json
from app.prompts.analysis import (
    DIMENSIONS,
    SYSTEM_PROMPT as ANALYSIS_SYSTEM_PROMPT,
    build_analysis_prompt,
)

# 英文维度名 → 中文维度名（兜底翻译，防止LLM返回英文）
_DIMENSION_NAME_MAP = {
    "career_orientation": "就业导向",
    "economic_rationality": "经济理性",
    "personal_fit": "个人匹配",
    "personal_match": "个人匹配",
    "policy_environment": "政策环境",
    "trend_outlook": "趋势前瞻",
    "trend_forecast": "趋势前瞻",
}


def _normalize_dimension_name(name: str) -> str:
    """将英文维度名翻译为中文，已经是中文的保持不变"""
    if not name:
        return name
    return _DIMENSION_NAME_MAP.get(name.strip().lower(), name)


class AnalysisEngine:
    """五维度分析引擎"""

    async def analyze(
        self,
        profile: StudentProfile,
        data: CollectedData,
    ) -> AnalysisResult:
        """主分析流程（优化版 - 合并为单次LLM调用）

        Args:
            profile: 学生画像
            data: 采集到的数据

        Returns:
            完整分析结果
        """
        # Step 1: 构建学生信息摘要
        student_info = self._build_student_summary(profile)

        # Step 2: 调用 LLM 进行五维度分析（一次性返回所有结果）
        analysis_prompt = build_analysis_prompt(
            student_info=student_info,
            search_data=data.to_text(),
        )

        analysis_result = await chat_completion_json(
            ANALYSIS_SYSTEM_PROMPT,
            analysis_prompt,
            temperature=0.3,
            max_tokens=8000,
        )

        # Step 3: 解析结果为数据模型
        universities = self._parse_universities(analysis_result)

        # Step 4: 直接从结果中提取策略和风险评估（不再调用LLM）
        return AnalysisResult(
            student_profile=profile,
            universities=universities,
            overall_strategy=analysis_result.get("overall_strategy", ""),
            risk_assessment=analysis_result.get("risk_assessment", ""),
            generated_at=datetime.now(),
        )

    def _build_student_summary(self, profile: StudentProfile) -> str:
        """构建学生信息摘要"""
        parts = [
            f"姓名：{profile.student.name}",
            f"省份：{profile.student.province}",
            f"分数：{profile.student.score}",
            f"科类：{profile.student.subject_type}",
            f"年份：{profile.student.year}",
        ]

        if profile.student.rank is not None:
            parts.append(f"排名：{profile.student.rank}")

        if profile.student.subjects:
            parts.append(f"选科：{'、'.join(profile.student.subjects)}")

        if profile.interests:
            parts.append(f"兴趣方向：{'、'.join(profile.interests)}")

        if profile.career_goals:
            parts.append(f"职业目标：{'、'.join(profile.career_goals)}")

        if profile.constraints:
            parts.append(f"特殊约束：{'、'.join(profile.constraints)}")

        # 家庭背景
        parts.append(f"家庭经济：{profile.family.economic_level}")

        if profile.family.location_pref:
            parts.append(f"偏好地区：{profile.family.location_pref}")

        if profile.family.has_abroad_plan:
            parts.append("有出国计划")

        if profile.family.industry_connections:
            parts.append(
                f"家庭行业资源：{'、'.join(profile.family.industry_connections)}"
            )

        return "\n".join(parts)

    def _parse_universities(
        self,
        analysis_result: dict,
    ) -> list[UniversityRecommendation]:
        """解析院校推荐结果"""
        universities = []

        for uni_data in analysis_result.get("universities", []):
            # 解析专业
            majors = []
            for major_data in uni_data.get("majors", []):
                # 解析维度评分
                dimensions = []
                for dim_data in major_data.get("dimensions", []):
                    dimensions.append(
                        DimensionScore(
                            dimension=_normalize_dimension_name(dim_data.get("dimension", "")),
                            score=dim_data.get("score", 0),
                            reasoning=dim_data.get("reasoning", ""),
                            key_factors=dim_data.get("key_factors", []),
                        )
                    )

                majors.append(
                    MajorRecommendation(
                        major_name=major_data.get("name", ""),
                        category=major_data.get("category", ""),
                        dimensions=dimensions,
                        overall_score=major_data.get("overall_score", 0),
                        match_reason=major_data.get("match_reason", ""),
                        warnings=major_data.get("warnings", []),
                    )
                )

            # 解析排名区间
            rank_range = uni_data.get("estimated_rank_range")
            if rank_range and len(rank_range) == 2:
                rank_range = (rank_range[0], rank_range[1])
            else:
                rank_range = None

            universities.append(
                UniversityRecommendation(
                    university_name=uni_data.get("name", ""),
                    location=uni_data.get("location", ""),
                    is_985=uni_data.get("is_985", False),
                    is_211=uni_data.get("is_211", False),
                    is_double_first_class=uni_data.get("is_double_first_class", False),
                    admission_probability=uni_data.get("admission_probability", "稳"),
                    estimated_rank_range=rank_range,
                    recommended_majors=majors,
                )
            )

        return universities
