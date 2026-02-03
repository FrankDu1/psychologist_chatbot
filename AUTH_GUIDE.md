# 用户认证系统使用指南

## 认证功能概述

本系统支持两种认证方式：
1. **微信OAuth登录** - 扫码登录，获取微信用户信息
2. **手机号验证码登录** - 通过手机验证码验证身份

## 配置说明

### 1. 基础配置

在 `.env` 文件中配置：

```bash
# 是否强制要求认证（默认false，用户可选择登录）
REQUIRE_AUTH=false

# JWT密钥（生产环境必须修改为随机字符串）
JWT_SECRET_KEY=your-secret-key-change-this-in-production
```

### 2. 微信登录配置

#### 步骤1：注册微信开放平台

1. 访问 [微信开放平台](https://open.weixin.qq.com/)
2. 注册开发者账号
3. 完成开发者资质认证（需要营业执照）

#### 步骤2：创建网站应用

1. 在开放平台控制台，点击"创建网站应用"
2. 填写应用信息：
   - 应用名称：你的应用名称
   - 应用简介：应用描述
   - 应用官网：你的网站地址
   - 授权回调域：你的域名（不含http://和路径，如：example.com）
3. 提交审核，等待通过

#### 步骤3：配置环境变量

审核通过后，获取 AppID 和 AppSecret，在 `.env` 中配置：

```bash
WECHAT_APP_ID=你的AppID
WECHAT_APP_SECRET=你的AppSecret
```

#### 步骤4：配置回调URL

在微信开放平台应用设置中，配置授权回调域名为：
```
你的域名/wechat-callback
```

例如：`https://example.com/wechat-callback`

### 3. 手机号登录配置

#### 测试环境

默认使用固定验证码 `123456`：

```bash
TEST_SMS_CODE=123456
```

#### 生产环境

需要接入真实短信服务商（阿里云、腾讯云等）：

1. 注册短信服务商账号
2. 获取 AccessKey 和 SecretKey
3. 修改 `main.py` 中的 `phone_login` 函数：

```python
@app.post("/api/auth/phone")
async def phone_login(request: PhoneLoginRequest, db: Session = Depends(get_db)):
    # 调用短信服务商API验证验证码
    sms_service = SMSService(access_key, secret_key)
    is_valid = sms_service.verify_code(request.phone, request.code)
    
    if not is_valid:
        raise HTTPException(status_code=400, detail="验证码错误")
    
    # ... 其余逻辑
```

## 使用方式

### 用户登录流程

1. **访问应用** - 打开网站
2. **选择登录方式**：
   - 微信登录：点击"微信登录"，扫码授权
   - 手机号登录：输入手机号，点击"发送验证码"，输入收到的验证码，点击"登录"
3. **登录成功** - 自动跳转到聊天界面，侧边栏显示用户信息

### 强制认证模式

设置 `REQUIRE_AUTH=true` 后：
- 用户必须登录才能使用聊天、图片生成等功能
- 未登录用户会自动弹出登录窗口
- 登录状态通过 JWT Token 保存，7天内有效

### 可选认证模式

设置 `REQUIRE_AUTH=false` 时（默认）：
- 用户可以不登录直接使用（受IP配额限制）
- 登录后可以享受更多权益（可自定义）
- 提供自定义 API Key 时不受配额限制

## 数据存储

用户信息存储在 SQLite 数据库 `users.db` 中，包含：
- 用户ID
- 微信 OpenID / UnionID
- 手机号
- 昵称、头像
- 创建时间、最后登录时间

## 安全建议

1. **JWT密钥** - 生产环境务必修改 `JWT_SECRET_KEY` 为强随机字符串
2. **HTTPS** - 生产环境必须使用 HTTPS
3. **数据库备份** - 定期备份 `users.db`
4. **敏感信息** - 不要将 `.env` 文件提交到 Git
5. **短信服务** - 生产环境接入正规短信服务，添加防刷机制
6. **CORS配置** - 限制允许的域名，不要使用 `*`

## API端点

### 认证相关

- `POST /api/auth/wechat` - 微信登录
  ```json
  {
    "code": "微信授权码"
  }
  ```

- `POST /api/auth/phone` - 手机号登录
  ```json
  {
    "phone": "13800138000",
    "code": "123456"
  }
  ```

- `GET /api/auth/me` - 获取当前用户信息
  - Headers: `Authorization: Bearer <token>`

### 业务接口

所有业务接口（chat、generate-image、agent-completion）在 `REQUIRE_AUTH=true` 时需要添加 Header：
```
Authorization: Bearer <jwt_token>
```

## 故障排查

### 微信登录失败

1. 检查 `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET` 是否正确
2. 确认回调域名已在微信开放平台配置
3. 查看后端日志中的错误信息

### 手机号登录失败

1. 测试环境检查验证码是否为 `123456`
2. 生产环境检查短信服务配置是否正确
3. 查看后端日志中的错误信息

### Token过期

Token默认7天有效，过期后需要重新登录。可以在 `auth.py` 中修改：
```python
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天
```

## 扩展开发

### 添加其他登录方式

1. 在 `main.py` 中添加新的登录端点
2. 在前端 `index.html` 和 `app.js` 中添加登录按钮和处理逻辑
3. 更新用户数据库模型（如需要）

### 添加用户权限控制

1. 在 `User` 模型中添加 `role` 字段
2. 创建权限检查装饰器
3. 在需要权限控制的端点上应用装饰器

### 集成第三方服务

可以集成：
- 短信服务（阿里云、腾讯云）
- 邮箱验证
- GitHub/Google OAuth
- 企业微信登录
