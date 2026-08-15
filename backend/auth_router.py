import os
import secrets
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from jose import jwt
import bcrypt
from datetime import datetime, timedelta
from authlib.integrations.starlette_client import OAuth
import httpx

from database import get_db
import models

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"]
)

# Cryptographic Context Configurations
SECRET_KEY = "AXON_SECURE_CLINICAL_SESSION_SIGNATURE_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

class UserAuthSchema(BaseModel):
    email: str
    password: str

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/register")
def register_user(credentials: UserAuthSchema, db: Session = Depends(get_db)):
    """
    POST /api/auth/register
    Creates a new user record in SQLite after hashing credentials securely.
    """
    # 1. Clean email formatting
    email_clean = credentials.email.strip().lower()
    
    # 2. Check if user already exists
    existing_user = db.query(models.User).filter(models.User.email == email_clean).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is already registered."
        )
        
    # 3. Create hashed password and user instance
    hashed_password = get_password_hash(credentials.password)
    new_user = models.User(
        email=email_clean,
        hashed_password=hashed_password
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"status": "success", "message": "User registered successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login")
def login_user(credentials: UserAuthSchema, db: Session = Depends(get_db)):
    """
    POST /api/auth/login
    Authenticates user, creates secure signed JWT session token, and returns user meta details.
    """
    email_clean = credentials.email.strip().lower()
    
    # 1. Retrieve user
    user = db.query(models.User).filter(models.User.email == email_clean).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
        
    # 2. Verify password hash
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
        
    # 3. Generate token payload
    token_payload = {
        "sub": user.email,
        "user_id": user.id,
        "is_onboarded": user.is_onboarded
    }
    
    access_token = create_access_token(token_payload)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "email": user.email,
        "created_at": user.created_at.isoformat(),
        "is_onboarded": user.is_onboarded
    }

# Google OAuth Client Configurations
oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID", ""),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET", ""),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    }
)

@router.get("/google/login")
async def google_login(request: Request):
    """
    GET /api/auth/google/login
    Generates Google OAuth login URL or redirects to mock callback in sandbox environments.
    """
    client_id = os.environ.get("GOOGLE_CLIENT_ID") or ""
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET") or ""
    is_mock = not client_id or not client_secret or "mock" in client_id.lower() or "mock" in client_secret.lower()
    
    if is_mock:
        print("Warning: Google OAuth client credentials missing. Executing mock redirect pathway.")
        callback_url = str(request.url_for("google_callback")) + "?code=mock_oauth_code&state=mock_state"
        return RedirectResponse(url=callback_url)
        
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback", name="google_callback")
async def google_callback(request: Request, code: Optional[str] = None, db: Session = Depends(get_db)):
    """
    GET /api/auth/google/callback
    Resolves the social email, provisions user records in SQLite if missing,
    generates secure AXON signed JWT, and redirects user back to dashboard.
    """
    client_id = os.environ.get("GOOGLE_CLIENT_ID") or ""
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET") or ""
    is_mock = not client_id or not client_secret or "mock" in client_id.lower() or "mock" in client_secret.lower()
    
    email = "google-user@axon.com"
    
    if is_mock:
        print("Warning: Handling mock Google OAuth callback.")
    else:
        try:
            token = await oauth.google.authorize_access_token(request)
            user_info = token.get("userinfo")
            if not user_info:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        "https://www.googleapis.com/oauth2/v3/userinfo",
                        headers={"Authorization": f"Bearer {token['access_token']}"}
                    )
                    user_info = resp.json()
            email = user_info.get("email")
            if not email:
                raise HTTPException(status_code=400, detail="Verified Google email not found.")
        except Exception as e:
            print(f"Error exchanging Google OAuth code: {e}")
            raise HTTPException(status_code=400, detail=f"Google authentication failed: {str(e)}")
            
    email_clean = email.strip().lower()
    
    # Retrieve or provision user record
    user = db.query(models.User).filter(models.User.email == email_clean).first()
    if not user:
        # Social logins provisioned with safe high-entropy random hashed passwords
        random_pass = secrets.token_hex(24)
        hashed_pass = get_password_hash(random_pass)
        user = models.User(
            email=email_clean,
            hashed_password=hashed_pass
        )
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Successfully provisioned social login profile for: {email_clean}")
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Profile provisioning failed: {str(e)}"
            )
            
    # Generate signed AXON JWT
    token_payload = {
        "sub": user.email,
        "user_id": user.id,
        "is_onboarded": user.is_onboarded
    }
    access_token = create_access_token(token_payload)
    
    # Redirect back to Next.js dashboard frame at the root route
    frontend_url = f"http://localhost:3000?token={access_token}"
    return RedirectResponse(url=frontend_url)
