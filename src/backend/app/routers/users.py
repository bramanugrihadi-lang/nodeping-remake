from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas import User, UserCreate, MessageResponse
from app.auth import get_current_user, require_admin, hash_password
from app.database import get_db
import aiosqlite

router = APIRouter(prefix="/api", tags=["users"])


@router.get("/users", response_model=list[User])
async def get_users(
    db=Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all users (admin only)."""
    await require_admin(current_user)
    
    cursor = await db.execute("SELECT id, username, role FROM users ORDER BY id")
    rows = await cursor.fetchall()
    
    return [User(id=row["id"], username=row["username"], role=row["role"]) for row in rows]


@router.post("/users", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db=Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new user (admin only)."""
    await require_admin(current_user)
    
    # Check if username exists
    cursor = await db.execute("SELECT id FROM users WHERE username = ?", (user.username,))
    if await cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Hash password
    password_hash = hash_password(user.password)
    
    # Insert user
    cursor = await db.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        (user.username, password_hash, user.role)
    )
    await db.commit()
    
    return User(
        id=cursor.lastrowid,
        username=user.username,
        role=user.role
    )


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    db=Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a user (admin only). Cannot delete self."""
    await require_admin(current_user)
    
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete your own account"
        )
    
    # Check if user exists
    cursor = await db.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if await cursor.fetchone() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    await db.commit()
    
    return MessageResponse(message="User deleted successfully")
