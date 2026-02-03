"""
用户认证模块 - 用户名密码注册登录
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
import jwt
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv

load_dotenv()

# JWT配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 数据库配置
DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)  # 用户名
    password_hash = Column(String, nullable=False)  # 密码哈希
    nickname = Column(String, nullable=True)  # 昵称（显示名称）
    email = Column(String, nullable=True)  # 邮箱（可选）
    avatar = Column(String, nullable=True)  # 头像URL
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)


# 创建数据库表
Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    """密码加密"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建JWT访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """验证JWT令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None


def create_user(db: Session, username: str, password: str, nickname: str = None, email: str = None) -> Tuple[Optional[User], Optional[str]]:
    """创建新用户"""
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        return None, "用户名已存在"
    
    # 检查邮箱是否已被使用（如果提供了邮箱）
    if email:
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            return None, "邮箱已被使用"
    
    # 创建新用户
    user = User(
        username=username,
        password_hash=hash_password(password),
        nickname=nickname or username,  # 如果没有昵称，使用用户名
        email=email
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, None


def authenticate_user(db: Session, username: str, password: str) -> Tuple[Optional[User], Optional[str]]:
    """验证用户登录"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None, "用户名或密码错误"
    
    if not verify_password(password, user.password_hash):
        return None, "用户名或密码错误"
    
    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user, None


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """根据ID获取用户"""
    return db.query(User).filter(User.id == user_id).first()
