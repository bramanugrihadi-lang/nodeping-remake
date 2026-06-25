from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from app.schemas import LoginRequest, LoginResponse, User, MessageResponse
from app.auth import verify_password, create_access_token, get_current_user, rate_limiter
from app.database import get_db
import aiosqlite

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(request: Request, data: LoginRequest, db=Depends(get_db)):
    """Login with username and password. Returns JWT token."""
    
    # Check rate limit
    client_ip = request.client.host if request.client else "unknown"
    if not await rate_limiter.check(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later."
        )
    
    cursor = await db.execute("SELECT * FROM users WHERE username = ?", (data.username,))
    user = await cursor.fetchone()
    
    if user is None or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    token = create_access_token(user["id"], user["role"])
    await rate_limiter.reset(client_ip)
    
    return LoginResponse(
        token=token,
        user=User(id=user["id"], username=user["username"], role=user["role"])
    )


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return current_user


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: User = Depends(get_current_user)):
    """Logout (stateless - client discards token)."""
    return MessageResponse(message="Logged out successfully")
