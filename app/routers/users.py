from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..models.database import get_db
from ..models.user import User
from ..schemas.auth import UserResponse
from ..schemas.user import UserProfileUpdate
from ..services.auth_service import get_current_user
from ..services.user_service import save_avatar, update_user_profile

router = APIRouter(prefix="/api", tags=["Utilisateur"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        profile_image=current_user.profile_image,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
    )


@router.put("/me", response_model=UserResponse)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user profile."""
    try:
        user = update_user_profile(
            db=db,
            user=current_user,
            first_name=profile_data.first_name,
            last_name=profile_data.last_name,
            email=profile_data.email,
            current_password=profile_data.current_password,
            new_password=profile_data.new_password,
        )
        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            profile_image=user.profile_image,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(..., description="Image de profil (PNG, JPG, GIF, WEBP)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload or update profile avatar."""
    try:
        filename = await save_avatar(current_user, file, db)
        return {
            "status": "success",
            "message": "Image de profil mise à jour",
            "profile_image": filename,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur upload: {str(e)}")
