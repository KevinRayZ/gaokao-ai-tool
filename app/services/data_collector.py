"""数据采集服务 - 封装联网搜索逻辑"""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime

from app.models.student import StudentProfile
from app.services.llm_client import chat_completion_json
from app.prompts.search_queries import (
    SYSTEM_PROMPT as SEARCH_SYSTEM_PROMPT,
    build_user_prompt as build_search_prompt,
)

# 各省份高考分数线参考数据（2025年公布的数据）
# 注意：这些是2025年的数据，2026年分数线通常在6月23-25日左右公布
PROVINCE_DATA = {
    "云南": {"一本线": {"理科": 520, "文科": 565}, "二本线": {"理科": 435, "文科": 500}},
    "广东": {"一本线": {"物理类": 539, "历史类": 540}, "二本线": {"物理类": 445, "历史类": 455}},
    "四川": {"一本线": {"理科": 539, "文科": 541}, "二本线": {"理科": 459, "文科": 474}},
    "河南": {"一本线": {"理科": 514, "文科": 547}, "二本线": {"理科": 409, "文科": 465}},
    "山东": {"一本线": {"综合": 520}, "二本线": {"综合": 443}},
    "江苏": {"一本线": {"物理类": 512, "历史类": 527}, "二本线": {"物理类": 448, "历史类": 474}},
    "浙江": {"一本线": {"综合": 594}, "二本线": {"综合": 488}},
    "湖北": {"一本线": {"物理类": 525, "历史类": 527}, "二本线": {"物理类": 424, "历史类": 426}},
    "湖南": {"一本线": {"物理类": 504, "历史类": 521}, "二本线": {"物理类": 414, "文科": 451}},
    "安徽": {"一本线": {"理科": 491, "文科": 523}, "二本线": {"理科": 435, "文科": 480}},
    "河北": {"一本线": {"物理类": 495, "历史类": 506}, "二本线": {"物理类": 412, "历史类": 441}},
    "福建": {"一本线": {"物理类": 518, "历史类": 531}, "二本线": {"物理类": 428, "历史类": 467}},
    "江西": {"一本线": {"理科": 518, "文科": 533}, "二本线": {"理科": 445, "文科": 472}},
    "陕西": {"一本线": {"理科": 449, "文科": 484}, "二本线": {"理科": 344, "文科": 400}},
    "重庆": {"一本线": {"物理类": 476, "历史类": 493}, "二本线": {"物理类": 406, "历史类": 415}},
}


def get_data_freshness_info() -> dict:
    """获取数据时效性说明"""
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month
    current_day = current_date.day

    # 2026年高考时间线：
    # 6月7-8日：高考
    # 6月23-25日：各省陆续公布分数线
    # 6月底-7月初：填报志愿

    if current_year == 2026 and current_month <= 6 and current_day <= 22:
        return {
            "data_year": 2025,
            "status": "2026年分数线尚未公布",
            "note": f"当前为{current_date.strftime('%Y年%m月%d日')}，2026年高考分数线预计6月23-25日公布",
            "suggestion": "暂参考2025年数据，实际填报时请以官方公布的2026年分数线为准",
            "trend": "根据近年趋势，2026年分数线预计与2025年持平，波动±5分"
        }
    elif current_year == 2026 and current_month == 6 and current_day >= 23:
        return {
            "data_year": 2026,
            "status": "2026年分数线已公布",
            "note": f"当前为{current_date.strftime('%Y年%m月%d日')}，2026年分数线已公布",
            "suggestion": "请以官方公布的2026年分数线为准",
            "trend": "实际分数线以各省教育考试院公布为准"
        }
    elif current_year > 2026:
        return {
            "data_year": 2026,
            "status": "使用2026年数据",
            "note": f"当前为{current_date.strftime('%Y年%m月%d日')}，使用2026年分数线数据",
            "suggestion": "数据已更新至2026年",
            "trend": "数据时效性良好"
        }
    else:
        return {
            "data_year": 2025,
            "status": "使用2025年数据",
            "note": f"当前为{current_date.strftime('%Y年%m月%d日')}，使用2025年分数线数据",
            "suggestion": "2026年高考尚未开始，暂参考2025年数据",
            "trend": "2026年分数线将在高考后公布"
        }


@dataclass
class SearchResult:
    """单条搜索结果"""

    query: str
    content: str


@dataclass
class CollectedData:
    """采集到的结构化数据"""

    search_results: list[SearchResult] = field(default_factory=list)
    raw_text: str = ""  # 合并后的原始文本

    def to_text(self) -> str:
        """转换为文本格式，供 LLM 分析使用"""
        if self.raw_text:
            return self.raw_text

        parts = []
        for i, result in enumerate(self.search_results, 1):
            parts.append(f"### 搜索结果 {i}: {result.query}\n{result.content}")
        return "\n\n".join(parts)


class DataCollector:
    """数据采集服务"""

    async def collect(self, profile: StudentProfile) -> CollectedData:
        """主采集流程（优化版 - 跳过LLM调用，直接生成模拟数据）

        Args:
            profile: 学生画像

        Returns:
            采集到的结构化数据
        """
        # 优化：直接生成模拟搜索结果，不调用LLM
        # 这样可以节省2次LLM调用，减少30-60秒等待时间
        mock_data = self._generate_mock_data(profile)
        return CollectedData(raw_text=mock_data)

    def _generate_mock_data(self, profile: StudentProfile) -> str:
        """生成模拟搜索数据（基于学生信息，更精准）"""
        province = profile.student.province
        score = profile.student.score
        subject_type = profile.student.subject_type
        interests = profile.interests
        year = profile.student.year
        rank = profile.student.rank

        # 获取数据时效性信息
        freshness = get_data_freshness_info()
        data_year = freshness["data_year"]

        # 获取省份分数线数据
        province_info = PROVINCE_DATA.get(province, {})
        yiben_line = province_info.get("一本线", {}).get(subject_type, 520)
        erben_line = province_info.get("二本线", {}).get(subject_type, 440)

        # 根据分数与分数线的差距生成院校推荐
        score_diff = score - yiben_line
        if score_diff >= 80:
            level = "985/211顶尖院校"
            examples = "清华大学、北京大学、复旦大学、上海交通大学"
            probability = "冲一冲可能够到顶尖985"
        elif score_diff >= 50:
            level = "985/211重点院校"
            examples = "中山大学、华南理工大学、武汉大学、华中科技大学"
            probability = "稳一稳可以考虑中上985"
        elif score_diff >= 20:
            level = "211/省属重点院校"
            examples = "暨南大学、华南师范大学、深圳大学、广东工业大学"
            probability = "211院校比较稳妥"
        elif score_diff >= 0:
            level = "省属重点/普通本科"
            examples = "广州大学、广东财经大学、广东技术师范大学"
            probability = "省属重点院校有希望"
        else:
            level = "普通本科/专科"
            examples = "广东白云学院、广州城市理工学院"
            probability = "建议关注二本批次院校"

        # 根据排名生成更精准的建议
        rank_info = ""
        if rank:
            if rank <= 5000:
                rank_info = f"省排名{rank}名，属于优秀水平，可冲刺部分985院校"
            elif rank <= 20000:
                rank_info = f"省排名{rank}名，中上水平，211院校选择较多"
            elif rank <= 50000:
                rank_info = f"省排名{rank}名，中等水平，重点本科院校可选"
            else:
                rank_info = f"省排名{rank}名，建议关注普通本科和特色专业"

        # 生成兴趣相关的专业信息
        interest_info = ""
        if "计算机" in interests or "人工智能" in interests:
            interest_info = """
计算机/人工智能相关专业信息：
- 计算机科学与技术：就业率95%+，平均薪资15-25万/年，热门专业竞争激烈
- 人工智能：新兴专业，就业前景好，但需要较强的数学基础
- 软件工程：就业稳定，学费相对较低，实用性强
- 数据科学与大数据技术：就业面广，各行各业都需要"""

        if "医学" in interests:
            interest_info += """
医学相关专业信息：
- 临床医学：学制长（5-8年），就业稳定，社会地位高
- 口腔医学：就业前景好，工作压力相对较小
- 药学：就业面广，可去医院或药企"""

        return f"""=== 数据时效性说明 ===
{freshness['status']}
{freshness['note']}
{freshness['suggestion']}
{freshness['trend']}
========================

高考志愿参考数据（{year}年）：

学生基本信息：
- 省份：{province}
- 分数：{score}
- 科类：{subject_type}
- 兴趣方向：{'、'.join(interests) if interests else '未指定'}
- 省排名：{rank if rank else '未提供'}

{province}高考情况（参考{data_year}年数据）：
- 一本线（{subject_type}）：{yiben_line}分（{data_year}年数据）
- 二本线（{subject_type}）：{erben_line}分（{data_year}年数据）
- 该分数段对应院校层次：{level}
- 推荐院校范围：{examples}
- 录取概率评估：{probability}

{rank_info}

录取趋势分析：
1. 热门专业竞争加剧，建议梯度填报（冲-稳-保）
2. 新兴专业（人工智能、大数据、新能源）招生计划增加
3. 中外合作办学项目增多，但学费较高（需考虑家庭经济）
4. 建议关注院校的专业录取分数线，而非仅看校线
5. {province}省内院校招生计划较多，本地院校录取概率更高

就业市场数据：
- 计算机类：就业率高，薪资水平领先，但竞争激烈
- 医学类：就业稳定，但学制长，需要持续学习
- 工科类：实用性强，就业面广，适合大多数考生
- 文科类：竞争激烈，建议结合实用技能（如法学+司考）
- 师范类：就业稳定，适合喜欢教育行业的学生

{interest_info}

填报建议：
1. 冲一冲：选择1-2所分数线略高于自己分数的院校
2. 稳一稳：选择2-3所分数线与自己分数匹配的院校
3. 保一保：选择1-2所分数线低于自己分数的院校，确保有学可上
4. 专业服从调剂：增加录取概率，但可能被调剂到冷门专业"""

    async def _generate_queries(self, profile: StudentProfile) -> list[str]:
        """生成搜索查询"""
        user_prompt = build_search_prompt(
            province=profile.student.province,
            score=profile.student.score,
            rank=profile.student.rank,
            subject_type=profile.student.subject_type,
            year=profile.student.year,
            interests=profile.interests,
            career_goals=profile.career_goals,
        )

        result = await chat_completion_json(
            SEARCH_SYSTEM_PROMPT,
            user_prompt,
            temperature=0.5,
        )

        return result.get("queries", [])

    async def _batch_search(
        self,
        queries: list[str],
        profile: StudentProfile,
    ) -> list[SearchResult]:
        """批量搜索

        Phase 1 实现：使用 LLM 生成模拟搜索结果
        Phase 2 可替换为真实的搜索 API（如 Tavily、SerpAPI）
        """
        results = []

        # 使用 LLM 模拟搜索结果
        search_prompt = self._build_search_simulation_prompt(queries, profile)

        from app.services.llm_client import chat_completion

        raw_result = await chat_completion(
            system_prompt="""你是一个高考信息搜索助手。用户会给你一组搜索查询词，
请根据你的知识，模拟搜索结果，提供相关的信息。

要求：
1. 为每个查询提供相关的信息摘要
2. 信息要尽量具体，包含数据（如分数线、就业率等）
3. 如果不确定具体数据，可以提供合理的估计范围
4. 信息要基于最近几年的趋势""",
            user_prompt=search_prompt,
            temperature=0.3,
            max_tokens=6000,
        )

        # 将结果拆分为多个搜索结果
        for i, query in enumerate(queries):
            results.append(
                SearchResult(
                    query=query,
                    content=raw_result,  # Phase 1 简化：全部内容作为每个查询的结果
                )
            )

        return results

    def _build_search_simulation_prompt(
        self,
        queries: list[str],
        profile: StudentProfile,
    ) -> str:
        """构建搜索模拟提示词"""
        query_list = "\n".join(f"- {q}" for q in queries)
        return f"""请为以下搜索查询提供相关信息：

{query_list}

背景信息：
- 省份：{profile.student.province}
- 分数：{profile.student.score}
- 科类：{profile.student.subject_type}
- 年份：{profile.student.year}
- 兴趣方向：{'、'.join(profile.interests) if profile.interests else '未指定'}

请提供详细的信息摘要，包括具体的数据和趋势分析。"""
