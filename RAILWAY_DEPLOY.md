# Railway 部署指南

## 前置条件
- [ ] GitHub 账号
- [ ] Railway 账号（可用 GitHub 登录）

---

## 第一步：创建 GitHub 仓库

### 1.1 在 GitHub 上创建新仓库
1. 打开 https://github.com/new
2. 仓库名：`gaokao-zhiyuan`（或你喜欢的名字）
3. 选择 **Public**（免费方案需要公开仓库）
4. **不要**勾选 "Add a README file"
5. 点击 "Create repository"

### 1.2 推送代码到 GitHub
在项目目录下执行以下命令：

```bash
# 初始化 git 仓库
git init

# 添加所有文件（.gitignore 会自动排除敏感文件）
git add .

# 提交
git commit -m "Initial commit: 高考志愿填报AI分析工具"

# 添加远程仓库（替换 YOUR_USERNAME 为你的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/gaokao-zhiyuan.git

# 推送
git branch -M main
git push -u origin main
```

---

## 第二步：在 Railway 部署

### 2.1 登录 Railway
1. 打开 https://railway.app
2. 点击 "Login" → "Login with GitHub"

### 2.2 创建新项目
1. 点击 "New Project"
2. 选择 "Deploy from GitHub repo"
3. 选择刚才创建的 `gaokao-zhiyuan` 仓库
4. Railway 会自动检测到 Python 项目并开始部署

### 2.3 配置环境变量
在项目设置中添加以下环境变量：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `LLM_API_BASE_URL` | `https://token-plan-cn.xiaomimimo.com/v1` | LLM API 地址 |
| `LLM_API_KEY` | `你的API密钥` | 从 .env 文件中复制 |
| `LLM_MODEL` | `mimo-v2.5-pro` | 模型名称 |
| `LLM_TEMPERATURE` | `0.3` | 生成温度 |
| `LLM_MAX_TOKENS` | `8000` | 最大 token 数 |
| `DEBUG` | `false` | 关闭调试模式 |

**添加环境变量步骤**：
1. 点击项目中的服务
2. 点击 "Variables" 标签
3. 点击 "New Variable"
4. 逐个添加上述变量

### 2.4 获取公网域名
1. 点击 "Settings" 标签
2. 找到 "Public Networking" 部分
3. 点击 "Generate Domain"
4. 获得类似 `gaokao-zhiyuan.up.railway.app` 的域名

---

## 第三步：分享给亲戚朋友

将获得的域名分享给亲戚朋友即可访问！

格式：`https://gaokao-zhiyuan.up.railway.app`

---

## 常见问题

### Q: 部署失败怎么办？
A: 检查 "Deployments" 标签中的日志，通常是环境变量配置错误。

### Q: 免费额度够用吗？
A: Railway 免费方案提供 $5/月 的额度，约 500 小时运行时间，临时用一个月足够。

### Q: 如何更新代码？
A: 推送到 GitHub 后，Railway 会自动重新部署：
```bash
git add .
git commit -m "Update: 描述修改内容"
git push
```

### Q: 如何查看日志？
A: 在 Railway 项目中点击 "Deployments" → 选择最新的部署 → 查看 "Build Logs" 或 "Deploy Logs"

---

## 费用说明

| 项目 | 费用 |
|------|------|
| Railway 免费额度 | $5/月 |
| GitHub 公开仓库 | 免费 |
| 域名 | 免费（.up.railway.app） |
| API 调用 | 根据小米 MiMo 计费 |

**预计总费用**：$0-5/月（Railway 免费额度内）

---

## 部署完成后

1. 测试网站功能是否正常
2. 分享域名给亲戚朋友
3. 提醒他们：分析需要 1-2 分钟，请耐心等待

---

**需要帮助？** 如果在部署过程中遇到问题，随时告诉我！
