"""搜索查询生成 Prompt 模板"""

SYSTEM_PROMPT = """你是一个高考志愿填报专家助手。你的任务是根据学生信息生成需要搜索的查询词列表。

要求：
1. 生成 5-10 个搜索查询词，覆盖以下方面：
   - 该省份当年的高考分数线和一分一段表
   - 适合该分数段的大学的录取分数线
   - 学生感兴趣专业的就业前景
   - 相关大学的基本信息（学费、位置、特色专业）
   - 当年的招生政策变化

2. 每个查询词应该具体、明确，适合搜索引擎查询
3. 考虑学生的省份、分数、选科、兴趣方向

请以 JSON 格式返回：
```json
{
  "queries": ["查询词1", "查询词2", ...]
}
```"""


def build_user_prompt(
    province: str,
    score: int,
    rank: int | None,
    subject_type: str,
    year: int,
    interests: list[str],
    career_goals: list[str],
) -> str:
    """构建用户提示词"""
    parts = [
        f"省份：{province}",
        f"分数：{score}",
        f"科类：{subject_type}",
        f"年份：{year}",
    ]

    if rank is not None:
        parts.append(f"排名：{rank}")

    if interests:
        parts.append(f"兴趣方向：{'、'.join(interests)}")

    if career_goals:
        parts.append(f"职业目标：{'、'.join(career_goals)}")

    return "\n".join(parts)
