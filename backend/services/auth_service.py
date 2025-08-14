"""
Authentication service with JWT and OAuth support
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from models import User
import os
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
import logging

logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth setup
config = Config('.env')
oauth = OAuth(config)

# Configure OAuth providers
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

oauth.register(
    name='github',
    client_id=os.getenv('GITHUB_CLIENT_ID'),
    client_secret=os.getenv('GITHUB_CLIENT_SECRET'),
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params=None,
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
)


class AuthService:
    """Service for authentication and authorization"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create a JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    async def authenticate_user(username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password"""
        user = await User.find_one(User.username == username)
        if not user:
            user = await User.find_one(User.email == username)
        if not user:
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        return user
    
    @staticmethod
    async def create_user(
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None
    ) -> User:
        """Create a new user"""
        hashed_password = AuthService.get_password_hash(password)
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            created_at=datetime.utcnow()
        )
        await user.insert()
        return user
    
    @staticmethod
    async def get_user_from_token(token: str) -> Optional[User]:
        """Get user from JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "access":
                return None
            username: str = payload.get("sub")
            if username is None:
                return None
            user = await User.find_one(User.username == username)
            return user
        except JWTError:
            return None
    
    @staticmethod
    async def refresh_access_token(refresh_token: str) -> Optional[str]:
        """Refresh an access token using a refresh token"""
        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "refresh":
                return None
            username: str = payload.get("sub")
            if username is None:
                return None
            
            # Create new access token
            access_token = AuthService.create_access_token(
                data={"sub": username}
            )
            return access_token
        except JWTError:
            return None
    
    @staticmethod
    async def create_oauth_user(
        provider: str,
        oauth_id: str,
        email: str,
        full_name: Optional[str] = None
    ) -> User:
        """Create or get a user from OAuth provider"""
        # Check if user already exists
        user = await User.find_one(
            User.oauth_provider == provider,
            User.oauth_id == oauth_id
        )
        
        if user:
            # Update last login
            user.last_login = datetime.utcnow()
            await user.save()
            return user
        
        # Check if email already exists
        user = await User.find_one(User.email == email)
        if user:
            # Link OAuth to existing user
            user.oauth_provider = provider
            user.oauth_id = oauth_id
            user.last_login = datetime.utcnow()
            await user.save()
            return user
        
        # Create new user
        username = email.split('@')[0]
        # Ensure unique username
        counter = 1
        while await User.find_one(User.username == username):
            username = f"{email.split('@')[0]}{counter}"
            counter += 1
        
        user = User(
            username=username,
            email=email,
            hashed_password="",  # No password for OAuth users
            full_name=full_name,
            oauth_provider=provider,
            oauth_id=oauth_id,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        await user.insert()
        return user
    
    @staticmethod
    def create_tokens(user: User) -> Dict[str, str]:
        """Create access and refresh tokens for a user"""
        access_token = AuthService.create_access_token(
            data={"sub": user.username}
        )
        refresh_token = AuthService.create_refresh_token(
            data={"sub": user.username}
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }


# Create auth service instance
auth_service = AuthService()
