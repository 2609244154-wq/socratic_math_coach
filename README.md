# 🦉 苏格拉底式AI数学助教

基于AI的数学解题引导系统,通过苏格拉底式提问帮助学生自主解决数学问题。

## 功能特点
- 支持上传数学题目图片
- 自动识别题目内容
- 通过多轮引导式提问帮助学生思考
- 不直接给出答案,培养解题能力
- 支持多问题会话管理

## 技术栈
- 前端:Streamlit
- AI模型:智谱GLM/OpenAI API
- OCR:Tesseract
- 部署:Streamlit Cloud

## 本地运行

### 1. 环境准备
确保已安装 Python 3.8 或更高版本。

### 2. 克隆项目
```bash
git clone <your-repository-url>
cd socratic_math_coach
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置环境变量
在项目根目录创建 `.env` 文件,填入以下内容:
```env
API_KEY=your_api_key_here
BASE_URL=https://open.bigmodel.cn/api/paas/v4/
```

**获取 API Key:**
- 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
- 注册账号并获取 API Key
- 将 API Key 填入 `.env` 文件中的 `API_KEY`

### 5. 运行应用
```bash
streamlit run main_app.py
```

浏览器会自动打开 `http://localhost:8501`,即可开始使用!

---

## 🚀 部署到 Streamlit Cloud (推荐)

### 前置条件
1. 拥有 GitHub 账号
2. 拥有 Streamlit Cloud 账号(可用 GitHub 登录)

### 部署步骤

#### 第一步:推送代码到 GitHub
```bash
# 在 GitHub 上创建新仓库后,执行以下命令
git remote add origin https://github.com/<your-username>/socratic_math_coach.git
git branch -M main
git push -u origin main
```

#### 第二步:配置 Streamlit Cloud
1. 访问 [Streamlit Cloud](https://streamlit.io/cloud)
2. 点击 **"New app"**
3. 选择你的 GitHub 仓库 `socratic_math_coach`
4. 配置以下参数:
   - **Repository**: `<your-username>/socratic_math_coach`
   - **Branch**: `main`
   - **Main file path**: `main_app.py`
   
5. 点击 **"Advanced settings"**,添加环境变量:
   - `API_KEY`: 你的智谱AI API Key
   - `BASE_URL`: `https://open.bigmodel.cn/api/paas/v4/`

6. 点击 **"Deploy!"**

等待几分钟,应用就会自动部署完成!你会获得一个类似 `https://xxx.streamlit.app` 的在线访问地址。

### 注意事项
⚠️ **安全提示**: 
- 永远不要将 `.env` 文件提交到 GitHub(已在 `.gitignore` 中排除)
- API Key 只在 Streamlit Cloud 的环境变量中配置
- 定期检查 API 使用情况,避免超额消费

---

## 项目结构
```
socratic_math_coach/
├── main_app.py          # Streamlit 主应用入口
├── core_agent.py        # AI 代理核心逻辑(双Agent架构)
├── prompts.py           # 系统提示词模板
├── requirements.txt     # Python 依赖包
├── .env                 # 环境变量配置(不提交到Git)
├── .gitignore          # Git 忽略文件配置
├── .streamlit/
│   └── config.toml     # Streamlit 配置文件
└── README.md           # 项目说明文档
```

## 工作原理

本项目采用**双Agent架构**:

1. **Agent 1 (解题专家)**: 
   - 后台默默分析题目(支持图文双模态)
   - 提取知识点、生成详细解答步骤
   - 输出结构化 JSON 数据

2. **Agent 2 (苏格拉底教练)**:
   - 基于 Agent 1 的解答结果
   - 通过启发式提问引导学生思考
   - 绝不直接给出答案,培养独立解题能力

## 常见问题

### Q: 如何更换其他大模型?
A: 修改 `core_agent.py` 中的 `model` 参数,并确保调整 `BASE_URL` 和 `API_KEY`。

### Q: 支持哪些图片格式?
A: 支持 PNG、JPG、JPEG 格式。

### Q: 对话历史会保存吗?
A: 当前版本使用 Session State 保存在浏览器会话中,刷新页面后会丢失。如需持久化,可集成数据库存储。

## License
MIT License

## 贡献
欢迎提交 Issue 和 Pull Request!

---

**祝你学习愉快!🎓**