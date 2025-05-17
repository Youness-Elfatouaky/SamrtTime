from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth.auth_bearer import get_current_user
from app.auth.auth_handler import decode_access_token
from app.models.user import User, UserUpdate
from app.schemas.user import UserOut
from app.database import get_db

router = APIRouter()


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "fulll_name": current_user.full_name,
        "email": current_user.email
    }


@router.put("/update")
def update_user_info(
    update_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if update_data.full_name:
        user.full_name = update_data.full_name
    if update_data.email:
        user.email = update_data.email
    if update_data.username:
        user.username = update_data.username
    db.commit()
    db.refresh(user)
    return {"message": "User updated successfully"}
# @router.get("/me", response_model=UserOut, dependencies=[Depends(JWTBearer())])
# def get_me(token: str = Depends(JWTBearer()), db: Session = Depends(get_db)):
#     payload = decode_access_token(token)
#     user_id = payload.get("sub")
#     user = db.query(User).filter(User.id == int(user_id)).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user
