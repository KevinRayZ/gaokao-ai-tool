# 高考志愿填报AI分析工具

基于人工智能的五维度分析，为高考考生提供个性化的志愿填报建议。

## 功能特点

- **五维度分析**：就业导向、经济理性、个人匹配、政策环境、趋势前瞻
- **省份适配**：支持 15 个省份的分数线数据
- **时效性说明**：智能判断数据年份，明确标注参考信息
- **实时进度**：SSE 推送分析进度，用户体验友好
- **一键下载**：分析报告支持 Markdown 格式下载

## 技术栈

- **前端**：HTML5 + Tailwind CSS + Alpine.js + Marked.js
- **后端**：FastAPI + Uvicorn
- **AI 引擎**：小米 MiMo API（mimo-v2.5-pro）
- **模板引擎**：Jinja2

## 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API 密钥

# 启动服务
python run.py
```

访问 http://localhost:8000

## 部署到 Railway

详见 [RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md)

## 项目结构

```
├── app/
│   ├── api/          # API 路由
│   ├── models/       # 数据模型
│   ├── prompts/      # Prompt 模板
│   ├── services/     # 业务逻辑
│   ├── static/       # 前端静态文件
│   └── templates/    # 报告模板
├── .env.example      # 环境变量示例
├── Procfile          # Railway 启动命令
├── railway.json      # Railway 配置
└── requirements.txt  # Python 依赖
```

## 使用说明

1. 填写学生信息（省份、分数、排名、科类等）
2. 可选填写家庭背景、兴趣方向、职业目标
3. 点击"开始AI分析"
4. 等待 1-2 分钟，查看分析报告
5. 可下载 Markdown 格式报告

## 注意事项

- AI 分析仅供参考，请结合实际情况综合判断
- 分数线数据基于往年信息，实际填报请以官方公布为准
- 建议咨询学校老师和有经验的学长学姐

## 许可证

MIT License
