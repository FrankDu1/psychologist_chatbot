# 多云聊天平台 / Multi-Cloud Chat Platform

一个支持阿里云通义千问和 OpenAI GPT 的现代化聊天应用。

**✨ 纯 Python + 原生 HTML/JS，无需 npm，无需构建！**

![功能演示](openchatbox_demo_gif_git.gif)

## 功能特性 / Features

- 多云平台支持：阿里云通义千问（Qwen Plus/Turbo/Max/Long）、OpenAI GPT 系列（GPT-4/GPT-3.5）
- **用户认证：微信OAuth登录、手机号登录（可选开启强制认证）**
- 聊天功能：实时对话、Markdown 渲染、多模型切换、聊天历史、Token 使用统计
- 图片生成：DALL-E 3（OpenAI）、通义万相（阿里云）
- 免费配额限制（无需API Key可体验，超限后需自填Key）
- 多语言支持：中文/English，动态切换
- 现代化UI：深色/浅色主题，响应式设计
- 零前端依赖：无需 Node.js、npm、React、Vite

## 项目结构 / Project Structure

```
openchatbox/
├── main.py            # FastAPI 后端主程序
├── auth.py            # 用户认证模块（JWT、数据库）
├── requirements.txt   # Python依赖
├── .env               # 环境变量配置（API Key等）
├── users.db           # SQLite用户数据库（运行后自动生成）
├── Dockerfile         # Docker 构建文件
├── docker-compose.yml # Docker编排（推荐）
├── static/            # 前端静态资源
│   ├── index.html     # 主页面
│   ├── app.js         # 前端逻辑
│   ├── i18n.js        # 多语言
│   ├── style.css      # 样式
│   └── ...            # 其它资源
└── README.md
```

## 快速开始 / Quick Start

### 1. 本地运行（无需 Docker）

```sh
# 推荐使用虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env   # 或手动创建 .env
# 编辑 .env，填入你的 API Key

# 启动服务
python main.py
# 默认运行在 http://localhost:8000
```

### 2. Docker 一键部署

```sh
# 构建镜像（如需自定义）
docker build -t openchatbox .

# 推荐使用 docker-compose
# 编辑 .env，填入你的 API Key
# 启动所有服务（含nginx反向代理）
docker-compose up -d

# 或单独运行主服务
# docker run --env-file .env -p 8000:8000 openchatbox
```

- 默认端口：8000
- 前端访问：http://你的服务器:8000 或 nginx 代理后的路径

### 3. API Key 和认证配置

编辑 `.env` 文件：

**基础配置：**
- 阿里云 DashScope：设置 `DEFAULT_CHAT_API_KEY` 和 `DEFAULT_IMAGE_API_KEY`
- OpenAI：设置 `OPENAI_API_KEY`
- 免费配额用完后，前端设置页可自填 Key

**认证配置（可选）：**
- `REQUIRE_AUTH=false` - 不强制登录（默认）
- `REQUIRE_AUTH=true` - 强制要求登录才能使用

**微信登录配置：**
1. 前往 [微信开放平台](https://open.weixin.qq.com/) 注册账号
2. 创建网站应用，获取 AppID 和 AppSecret
3. 在 `.env` 中配置：
   ```
   WECHAT_APP_ID=你的AppID
   WECHAT_APP_SECRET=你的AppSecret
   ```
4. 在微信开放平台配置回调域名：`你的域名/wechat-callback`

**手机号登录配置：**
- 测试环境使用默认验证码 `123456`
- 生产环境需接入真实短信服务（修改 [main.py](main.py#L150) 中的短信验证逻辑）

**JWT安全配置：**
- 修改 `JWT_SECRET_KEY` 为随机字符串（生产环境必须）

## API接口 / API Endpoints

**公开接口：**
- 获取模型列表：`GET /api/models`
- 获取配置：`GET /api/config`
- 配额查询：`GET /api/usage`

**认证接口：**
- 微信登录：`POST /api/auth/wechat`
- 手机号登录：`POST /api/auth/phone`
- 获取当前用户：`GET /api/auth/me`

**业务接口（需要认证或API Key）：**
- 聊天：`POST /api/chat`
- 图片生成：`POST /api/generate-image`
- Agent对话：`POST /api/agent-completion`

## 生产部署建议

- 推荐使用 Docker + docker-compose
- 生产环境请配置 CORS 域名和 HTTPS
- 不要将 API Key 提交到 Git
- **修改 `JWT_SECRET_KEY` 为强随机密钥**
- 使用环境变量或密钥管理服务存储敏感信息
- 配置真实的短信服务（替换测试验证码）
- 定期备份 `users.db` 用户数据库
- 启用 REQUIRE_AUTH 来保护API资源

## License

MIT
