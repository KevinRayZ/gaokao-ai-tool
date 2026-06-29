# -*- coding: utf-8 -*-
"""生成高考志愿填报工具的分享海报（流程图）"""
from PIL import Image, ImageDraw, ImageFont


def create_poster():
    W, H = 1200, 1800
    img = Image.new("RGB", (W, H), "#ffffff")
    draw = ImageDraw.Draw(img)

    # Fonts
    font_title = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 48)
    font_subtitle = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 28)
    font_section = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 24)
    font_body = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 20)
    font_small = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 17)
    font_tag = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 15)

    # Colors
    INDIGO = "#4338CA"
    BLUE = "#4F46E5"
    LIGHT_BLUE = "#818CF8"
    DARK = "#1E293B"
    GRAY = "#64748B"
    LIGHT_GRAY = "#F1F5F9"
    WHITE = "#FFFFFF"
    GREEN = "#059669"
    ORANGE = "#D97706"
    RED = "#DC2626"
    PURPLE = "#7C3AED"
    CYAN = "#0891B2"
    PINK = "#DB2777"
    TEAL = "#0D9488"

    # ---- Header Background ----
    draw.rectangle([(0, 0), (W, 220)], fill=INDIGO)

    # Title
    title = "AI 高考志愿填报分析工具"
    draw.text((W // 2, 55), title, fill=WHITE, font=font_title, anchor="mt")
    subtitle = "五维度智能分析 | 融合多位名师方法论 | AI驱动"
    draw.text((W // 2, 130), subtitle, fill="#C7D2FE", font=font_subtitle, anchor="mt")
    tagline = "输入学生信息，1-2分钟生成个性化志愿填报分析报告"
    draw.text((W // 2, 175), tagline, fill="#A5B4FC", font=font_small, anchor="mt")

    # ---- Section: Analysis Flow ----
    y = 260
    draw.text((60, y), "分析流程", fill=DARK, font=font_section, anchor="lt")

    # Flow boxes
    flow_steps = [
        ("1", "输入学生信息", "分数、省份、选科\n兴趣、家庭背景", BLUE),
        ("2", "数据智能采集", "搜索院校/专业\n就业/政策数据", CYAN),
        ("3", "五维度分析", "就业导向 | 经济理性\n个人匹配 | 政策环境 | 趋势前瞻", PURPLE),
        ("4", "院校推荐", "冲 - 稳 - 保\n梯度策略匹配", GREEN),
        ("5", "风险评估", "天坑预警 | 滑档风险\nAI冲击评估", ORANGE),
        ("6", "生成报告", "评分表 + 策略建议\n风险提示 + 时间线", RED),
    ]

    box_w = 320
    box_h = 100
    gap_x = 40
    gap_y = 30
    start_x = 60
    start_y = y + 50

    for i, (num, title, desc, color) in enumerate(flow_steps):
        col = i % 3
        row = i // 3
        x = start_x + col * (box_w + gap_x)
        yb = start_y + row * (box_h + gap_y + 20)

        # Box background
        draw.rounded_rectangle(
            [(x, yb), (x + box_w, yb + box_h)],
            radius=12,
            fill=WHITE,
            outline=color,
            width=2,
        )

        # Number circle
        circle_r = 18
        cx, cy = x + 30, yb + 30
        draw.ellipse(
            [(cx - circle_r, cy - circle_r), (cx + circle_r, cy + circle_r)],
            fill=color,
        )
        draw.text((cx, cy), num, fill=WHITE, font=font_body, anchor="mm")

        # Title
        draw.text((x + 58, yb + 14), title, fill=DARK, font=font_section, anchor="lt")

        # Description
        lines = desc.split("\n")
        for li, line in enumerate(lines):
            draw.text(
                (x + 58, yb + 48 + li * 22),
                line,
                fill=GRAY,
                font=font_small,
                anchor="lt",
            )

        # Arrow between boxes (same row)
        if col < 2 and i < 5:
            ax = x + box_w + 8
            ay = yb + box_h // 2
            draw.polygon(
                [(ax, ay - 6), (ax + 18, ay), (ax, ay + 6)],
                fill=LIGHT_BLUE,
            )

    # Vertical arrow between rows
    arrow_x = start_x + box_w + gap_x // 2
    arrow_y1 = start_y + box_h
    arrow_y2 = start_y + box_h + gap_y + 8
    draw.line(
        [(arrow_x, arrow_y1 + 5), (arrow_x, arrow_y2)],
        fill=LIGHT_BLUE,
        width=2,
    )
    draw.polygon(
        [(arrow_x - 6, arrow_y2), (arrow_x + 6, arrow_y2), (arrow_x, arrow_y2 + 12)],
        fill=LIGHT_BLUE,
    )

    # ---- Section: Five Dimensions ----
    y = start_y + 2 * (box_h + gap_y + 20) + 40
    draw.text((60, y), "五维度分析模型", fill=DARK, font=font_section, anchor="lt")
    draw.text((250, y + 4), "融合洪向阳、张雪峰、张勋等名师思维框架", fill=GRAY, font=font_small, anchor="lt")

    y += 45
    dims = [
        ("就业导向", "25%", "就业率、薪资、行业需求、\n不可替代性", BLUE),
        ("经济理性", "20%", "学费、投入产出比、\n试错成本", CYAN),
        ("个人匹配", "25%", "兴趣、能力、性格、\n家庭背景适配", PURPLE),
        ("政策环境", "15%", "招生政策、录取趋势、\n新高考选科限制", GREEN),
        ("趋势前瞻", "15%", "AI冲击评估、行业趋势、\n专业热度变化", ORANGE),
    ]

    dim_w = 190
    dim_h = 105
    dim_gap = 25
    dim_start_x = 60

    for i, (name, weight, desc, color) in enumerate(dims):
        x = dim_start_x + i * (dim_w + dim_gap)

        # Card
        draw.rounded_rectangle(
            [(x, y), (x + dim_w, y + dim_h)],
            radius=10,
            fill=WHITE,
            outline="#E2E8F0",
            width=1,
        )

        # Top color bar
        draw.rounded_rectangle(
            [(x, y), (x + dim_w, y + 6)],
            radius=3,
            fill=color,
        )

        # Dimension name
        draw.text((x + dim_w // 2, y + 22), name, fill=DARK, font=font_body, anchor="mt")

        # Weight badge
        badge_w = 48
        badge_x = x + dim_w // 2 - badge_w // 2
        draw.rounded_rectangle(
            [(badge_x, y + 48), (badge_x + badge_w, y + 66)],
            radius=10,
            fill=color,
        )
        draw.text(
            (x + dim_w // 2, y + 57),
            weight,
            fill=WHITE,
            font=font_tag,
            anchor="mm",
        )

        # Description
        lines = desc.split("\n")
        for li, line in enumerate(lines):
            draw.text(
                (x + dim_w // 2, y + 74 + li * 18),
                line,
                fill=GRAY,
                font=font_small,
                anchor="mt",
            )

    # ---- Section: Zhang Xuefeng Framework ----
    y += dim_h + 50
    draw.text((60, y), "名师思维框架（核心方法论）", fill=DARK, font=font_section, anchor="lt")
    y += 45

    principles = [
        ("就业倒推法", "从就业数据倒推专业选择，看中位数而非顶尖案例"),
        ("不可替代性", "有技术壁垒的专业（理工科）优于\"谁都能干\"的专业"),
        ("阶层现实主义", "普通家庭追求确定性，有试错成本的家庭追求热爱"),
        ("城市优先", "发达城市资源/实习/视野差距远大于学校排名差距"),
        ("学校vs专业", "理工科选专业（技术壁垒），文科选学校（平台效应）"),
        ("天坑专业警示", "生化环材等除非读到博士，否则明确就业风险预警"),
        ("10年压迫测试", "这个组合10年后能不能比同分段其他选择过得更好？"),
    ]

    for i, (title, desc) in enumerate(principles):
        row = i // 2
        col = i % 2
        x = 60 + col * 555
        yb = y + row * 48

        # Bullet dot
        draw.ellipse([(x, yb + 7), (x + 8, yb + 15)], fill=BLUE)
        draw.text((x + 16, yb), title, fill=DARK, font=font_body, anchor="lt")
        desc_w = 500
        draw.text((x + 16, yb + 25), desc, fill=GRAY, font=font_small, anchor="lt")

    # ---- Section: Key Advantages ----
    y += 4 * 48 + 40
    draw.text((60, y), "核心优势", fill=DARK, font=font_section, anchor="lt")
    y += 45

    advantages = [
        ("AI驱动", "联网采集最新数据，AI深度分析，报告量身定制", BLUE),
        ("五维度评估", "不只是看分数，就业/经济/匹配/政策/趋势全覆盖", PURPLE),
        ("名师框架", "融合多位名师实战方法论，普通家庭也能做出聪明选择", INDIGO),
        ("冲稳保策略", "梯度式推荐，每个层次都有明确理由和风险提示", GREEN),
    ]

    adv_w = 540
    adv_h = 55
    adv_gap = 15

    for i, (title, desc, color) in enumerate(advantages):
        x = 60 + (i % 2) * (adv_w + adv_gap)
        yb = y + (i // 2) * (adv_h + adv_gap)

        draw.rounded_rectangle(
            [(x, yb), (x + adv_w, yb + adv_h)],
            radius=8,
            fill=LIGHT_GRAY,
        )

        # Left color bar
        draw.rounded_rectangle(
            [(x, yb), (x + 4, yb + adv_h)],
            radius=2,
            fill=color,
        )

        draw.text((x + 18, yb + 10), title, fill=DARK, font=font_body, anchor="lt")
        draw.text((x + 18, yb + 33), desc, fill=GRAY, font=font_small, anchor="lt")

    # ---- Footer ----
    footer_y = H - 60
    draw.rectangle([(0, footer_y - 20), (W, H)], fill=LIGHT_GRAY)
    draw.text(
        (W // 2, footer_y),
        "免费使用 | 输入信息即可获取分析报告 | 仅供志愿填报参考",
        fill=GRAY,
        font=font_small,
        anchor="mt",
    )

    # Save
    output = "C:/Users/robot01/Desktop/AI高考志愿填报工具-分享海报.png"
    img.save(output, "PNG", quality=95, dpi=(150, 150))
    print(f"Saved: {output}")
    return output


if __name__ == "__main__":
    create_poster()
