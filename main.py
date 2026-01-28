from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Literal, Dict
import os
from pathlib import Path
import requests
from dotenv import load_dotenv
import json
from datetime import datetime, date
from collections import defaultdict
import logging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="OpenChatBox API")

# Get the parent directory (project root)
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议配置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# IP限流存储：{date: {ip: count}}
ip_usage: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

def get_client_ip(request: Request) -> str:
    """获取客户端真实IP地址"""
    # 优先从代理头获取（如果使用了反向代理）
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 直接连接的IP
    return request.client.host if request.client else "unknown"

def check_ip_limit(ip: str, has_custom_key: bool) -> bool:
    """检查IP是否超过每日限制"""
    # 如果使用自定义key，不限制
    if has_custom_key:
        return True
    
    today = date.today().isoformat()
    daily_limit = int(os.getenv("DAILY_FREE_LIMIT", "10"))
    
    # 获取今天的使用记录
    if today not in ip_usage:
        # 清理旧数据
        ip_usage.clear()
        ip_usage[today] = defaultdict(int)
    
    current_usage = ip_usage[today][ip]
    return current_usage < daily_limit

def increment_ip_usage(ip: str, has_custom_key: bool):
    """增加IP使用计数"""
    # 如果使用自定义key，不计数
    if has_custom_key:
        return
    
    today = date.today().isoformat()
    if today not in ip_usage:
        ip_usage[today] = defaultdict(int)
    
    ip_usage[today][ip] += 1

def get_ip_usage(ip: str) -> dict:
    """获取IP使用情况"""
    today = date.today().isoformat()
    daily_limit = int(os.getenv("DAILY_FREE_LIMIT", "10"))
    
    if today not in ip_usage:
        return {"used": 0, "limit": daily_limit, "remaining": daily_limit}
    
    used = ip_usage[today].get(ip, 0)
    return {
        "used": used,
        "limit": daily_limit,
        "remaining": max(0, daily_limit - used)
    }

# 请求模型
class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = None  # 改为可选
    endpoint_url: Optional[str] = None  # 改为可选
    stream: bool = False
    max_tokens: Optional[int] = None
    temperature: Optional[float] = 0.7
    api_key: Optional[str] = None  # 改为可选

class ImageRequest(BaseModel):
    prompt: str
    model: Optional[str] = None  # 改为可选
    size: Optional[str] = None  # 改为可选
    n: int = 1
    api_key: Optional[str] = None  # 改为可选
    endpoint_url: Optional[str] = None  # 改为可选


class AgentRequest(BaseModel):
    input: dict
    parameters: Optional[dict] = {}
    api_key: Optional[str] = None

def get_default_config():
    """从环境变量获取默认配置"""
    return {
        "chat_endpoint": os.getenv("DEFAULT_CHAT_ENDPOINT", "https://api.openai.com/v1"),
        "chat_model": os.getenv("DEFAULT_CHAT_MODEL", "qwen-plus"),
        "chat_api_key": os.getenv("DEFAULT_CHAT_API_KEY", ""),
        "image_endpoint": os.getenv("DEFAULT_IMAGE_ENDPOINT", "https://api.openai.com/v1/images/generations"),
        "image_model": os.getenv("DEFAULT_IMAGE_MODEL", "dall-e-3"),
        "image_size": os.getenv("DEFAULT_IMAGE_SIZE", "1024x1024"),
        "image_api_key": os.getenv("DEFAULT_IMAGE_API_KEY", ""),
    }


def make_api_request(endpoint: str, data: dict, api_key: str):
    """发送HTTP请求到云平台API；如果 endpoint 是完整 URL 则直接使用，不再盲目拼接"""
    # 如果 endpoint 是完整 URL，直接使用
    if isinstance(endpoint, str) and endpoint.lower().startswith(("http://", "https://")):
        url = endpoint
    else:
        # 对于自定义 provider，可能需要处理
        url = endpoint

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"  # 直接使用传入的 api_key
    }
    
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=60)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Upstream request failed / 上游请求失败: {str(e)}")
    
    if resp.status_code >= 400:
        # 尝试解析错误信息
        try:
            error_data = resp.json()
            error_msg = error_data.get("error", {}).get("message", resp.text)
        except:
            error_msg = resp.text
        
        raise HTTPException(
            status_code=resp.status_code, 
            detail=f"API request failed / API请求失败: {error_msg[:200]}"
        )
    
    try:
        return resp.json()
    except ValueError:
        return {"raw_text": resp.text}

@app.get("/")
async def root():
    """Serve the main HTML page / 提供主页面"""
    return FileResponse(str(STATIC_DIR / "index.html"))

@app.get("/api/config")
async def get_config():
    """Get application configuration / 获取应用配置"""
    return {
        "appName": os.getenv("APP_NAME", "多云聊天平台"),
        "appNameEn": os.getenv("APP_NAME_EN", "Multi-Cloud Chat"),
        "dailyFreeLimit": int(os.getenv("DAILY_FREE_LIMIT", "10"))
    }

@app.get("/api/usage")
async def get_usage(req: Request):
    """Get current IP usage / 获取当前IP使用情况"""
    client_ip = get_client_ip(req)
    return get_ip_usage(client_ip)

@app.get("/api/models")
async def get_models():
    """Get supported model list / 获取支持的模型列表"""
    return {
        "aliyun": [
            {"id": "qwen-plus", "name": "Qwen Plus", "name_zh": "通义千问 Plus"},
            {"id": "qwen-turbo", "name": "Qwen Turbo", "name_zh": "通义千问 Turbo"},
            {"id": "qwen-max", "name": "Qwen Max", "name_zh": "通义千问 Max"},
            {"id": "qwen-long", "name": "Qwen Long", "name_zh": "通义千问 Long"}
        ],
        "openai": [
            {"id": "gpt-4", "name": "GPT-4"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"}
        ]
    }

@app.post("/api/chat")
async def chat(request: ChatRequest, req: Request):
    """Chat API / 聊天接口"""
    try:

        defaults = get_default_config()
        # 获取客户端IP
        client_ip = get_client_ip(req)
        has_custom_key = bool(request.api_key)
        
        # 检查IP限制
        if not check_ip_limit(client_ip, has_custom_key):
            usage = get_ip_usage(client_ip)
            raise HTTPException(
                status_code=429,
                detail=f"Daily free quota exceeded ({usage['used']}/{usage['limit']}). Please provide your own API key. / 每日免费配额已用完 ({usage['used']}/{usage['limit']})，请输入自己的 API Key。"
            )
        
        endpoint = request.endpoint_url or defaults["chat_endpoint"]
        api_key = request.api_key or defaults["chat_api_key"]
        model = request.model or defaults["chat_model"]

        if not endpoint:
            raise HTTPException(status_code=400, detail="API endpoint URL is required")
        
        if not api_key:
            raise HTTPException(status_code=400, detail="API key is required")
        
        # 转换消息格式
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # 构建请求参数
        data = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
        }
        
        print(f"前端传入model: {request.model}, 实际使用model: {model}")

        if request.max_tokens:
            data["max_tokens"] = request.max_tokens
        
        # 调用 API
        result = make_api_request(endpoint, data, api_key)
        
        # 增加IP使用计数
        if not has_custom_key:
            increment_ip_usage(client_ip, False)
        
        return {
            "message": {
                "role": "assistant",
                "content": result["choices"][0]["message"]["content"]
            },
            "usage": result.get("usage", {}),
            "model": result.get("model", request.model)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Request failed / 请求失败: {str(e)}")
    
@app.post("/api/generate-image")
async def generate_image(request: ImageRequest, req: Request):
    """Image generation API / 生成图片接口"""
    try:
        defaults = get_default_config()
        
        # 获取客户端IP
        client_ip = get_client_ip(req)
        has_custom_key = bool(request.api_key)
        
        # 检查IP限制
        if not check_ip_limit(client_ip, has_custom_key):
            usage = get_ip_usage(client_ip)
            raise HTTPException(
                status_code=429,
                detail=f"Daily free quota exceeded ({usage['used']}/{usage['limit']}). Please provide your own API key. / 每日免费配额已用完 ({usage['used']}/{usage['limit']})，请输入自己的 API Key。"
            )

        endpoint = request.endpoint_url or defaults["image_endpoint"]
        api_key = request.api_key or defaults["image_api_key"]
        model = request.model or defaults["image_model"]
        size = request.size or defaults["image_size"]
        
        if not endpoint:
            raise HTTPException(status_code=400, detail="API endpoint URL is required")
        
        if not api_key:
            raise HTTPException(status_code=400, detail="API key is required")
        
        print(f"调用阿里云图片生成API: {endpoint}")
        
        if "ali" in endpoint or "multimodal-generation" in endpoint:
            data = {
                "model": model,
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "text": request.prompt
                                }
                            ]
                        }
                    ]
                },
                "parameters": {
                    "size": size,
                    "n": request.n
                }
            }
        else:
            # 默认OpenAI格式
            data = {
                "model": model,
                "prompt": request.prompt,
                "size": size,
                "n": request.n
            }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        print(f"请求体: {data}")
        
        resp = requests.post(endpoint, headers=headers, json=data, timeout=60)
        
        print(f"响应状态: {resp.status_code}")
        print(f"响应内容: {resp.text}")
        
        if resp.status_code >= 400:
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"API请求失败: {resp.text}"
            )
        
        result = resp.json()
        
        # 增加IP使用计数
        if not has_custom_key:
            increment_ip_usage(client_ip, False)
        
        # 解析阿里云格式响应
        images = []
        if "output" in result and "choices" in result["output"]:
            for choice in result["output"]["choices"]:
                if "message" in choice and "content" in choice["message"]:
                    for content_item in choice["message"]["content"]:
                        if "image" in content_item:
                            images.append({"url": content_item["image"]})

        print(f"find image: {images}")
        return {"images": images}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片生成失败: {str(e)}")


@app.post("/api/agent-completion")
async def agent_completion(request: AgentRequest, req: Request):
    """Proxy endpoint for DashScope agent completion using AGENT_APP_ID and DEFAULT_AGENT_API_KEY"""
    try:
        defaults = get_default_config()

        client_ip = get_client_ip(req)
        has_custom_key = bool(request.api_key)

        # IP limit check
        if not check_ip_limit(client_ip, has_custom_key):
            usage = get_ip_usage(client_ip)
            raise HTTPException(
                status_code=429,
                detail=f"Daily free quota exceeded ({usage['used']}/{usage['limit']}). Please provide your own API key. / 每日免费配额已用完 ({usage['used']}/{usage['limit']})，请输入自己的 API Key。"
            )

        # Use provided api_key or default agent key from env
        api_key = request.api_key or os.getenv("DEFAULT_AGENT_API_KEY", "")
        app_id = os.getenv("AGENT_APP_ID", "")

        if not api_key:
            raise HTTPException(status_code=400, detail="Agent API key is required")
        if not app_id:
            raise HTTPException(status_code=400, detail="AGENT_APP_ID is not configured")

        endpoint = f"https://dashscope.aliyuncs.com/api/v1/apps/{app_id}/completion"

        data = {
            "input": request.input,
            "parameters": request.parameters or {},
            "debug": {}
        }

        # Call the upstream agent endpoint
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        resp = requests.post(endpoint, headers=headers, json=data, timeout=60)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=f"Agent API请求失败: {resp.text}")

        result = resp.json()

        # increase usage
        if not has_custom_key:
            increment_ip_usage(client_ip, False)

        # Try to extract assistant text (support multiple DashScope response formats)
        assistant_text = None
        try:
            if isinstance(result, dict):
                out = result.get("output")
                # Case 1: top-level 'choices' (OpenAI-like)
                if "choices" in result and isinstance(result["choices"], list) and len(result["choices"])>0:
                    choice0 = result["choices"][0]
                    # common pattern: choice.message.content is string
                    if isinstance(choice0, dict) and "message" in choice0 and isinstance(choice0["message"], dict):
                        msg = choice0["message"]
                        if "content" in msg and isinstance(msg["content"], str):
                            assistant_text = msg["content"]
                # Case 2: output is a dict with a direct "text" field
                if assistant_text is None and isinstance(out, dict) and isinstance(out.get("text"), str):
                    assistant_text = out.get("text")
                # Case 3: output contains choices with message.content array
                if assistant_text is None and isinstance(out, dict) and "choices" in out:
                    choice = out["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        contents = choice["message"]["content"]
                        for item in contents:
                            if isinstance(item, dict) and "text" in item:
                                assistant_text = item["text"]
                                break
                # Case 4: top-level 'text' field
                if assistant_text is None and isinstance(result.get("text"), str):
                    assistant_text = result.get("text")
        except Exception:
            assistant_text = None

        if assistant_text is None:
            # Fallback: try to stringify common readable fields, otherwise return raw JSON
            # prefer output.text if present
            try:
                if isinstance(result, dict):
                    out = result.get("output")
                    if isinstance(out, dict) and out.get("text"):
                        assistant_text = out.get("text")
            except Exception:
                assistant_text = None

        if assistant_text is None:
            return {"message": {"role": "assistant", "content": json.dumps(result, ensure_ascii=False)}, "raw": result}

        return {"message": {"role": "assistant", "content": assistant_text}}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent 请求失败: {str(e)}")
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
