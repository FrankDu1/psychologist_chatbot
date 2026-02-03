"""
用户认证模块 - 支持微信OAuth和JWT Token
"""
from datetime import datetime, timedelta
from typing import Optional
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
    openid = Column(String, unique=True, index=True, nullable=True)  # 微信OpenID
    unionid = Column(String, unique=True, index=True, nullable=True)  # 微信UnionID
    phone = Column(String, unique=True, index=True, nullable=True)  # 手机号
    email = Column(String, unique=True, index=True, nullable=True)  # 邮箱
    nickname = Column(String, nullable=True)  # 昵称
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


def get_or_create_user(db: Session, openid: str = None, unionid: str = None, 
                       phone: str = None, email: str = None, nickname: str = None, avatar: str = None) -> User:
    """获取或创建用户"""
    user = None
    
    # 先尝试通过各种ID查找用户
    if unionid:
        user = db.query(User).filter(User.unionid == unionid).first()
    if not user and openid:
        user = db.query(User).filter(User.openid == openid).first()
    if not user and phone:
        user = db.query(User).filter(User.phone == phone).first()
    if not user and email:
        user = db.query(User).filter(User.email == email).first()
    
    if user:
        # 更新用户信息
        if openid and not user.openid:
            user.openid = openid
        if unionid and not user.unionid:
            user.unionid = unionid
        if phone and not user.phone:
            user.phone = phone
        if email and not user.email:
            user.email = email
        if nickname:
            user.nickname = nickname
        if avatar:
            user.avatar = avatar
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)
    else:
        # 创建新用户
        user = User(
            openid=openid,
            unionid=unionid,
            phone=phone,
            email=email,
            nickname=nickname,
            avatar=avatar
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """通过ID获取用户"""
    return db.query(User).filter(User.id == user_id).first()
