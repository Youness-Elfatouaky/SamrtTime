from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas import meeting as schemas
from app.models import meeting as models
from app.database import get_db
from app.auth.auth_bearer import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=schemas.MeetingOut)
def create_meeting(meeting: schemas.MeetingCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_meeting = models.Meeting(**meeting.dict(), user_id=current_user.id)
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    return db_meeting

# @router.get("/", response_model=list[schemas.MeetingOut])
# def get_meetings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     return db.query(models.Meeting).filter(models.Meeting.user_id == current_user.id).all()
@router.get("/", response_model=list[schemas.MeetingOut])
def get_meetings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(models.Meeting).filter(
        models.Meeting.user_id == current_user.id
    ).order_by(models.Meeting.start_time.desc()).all()

@router.get("/{meeting_id}", response_model=schemas.MeetingOut)
def get_meeting(meeting_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    meeting = db.query(models.Meeting).filter(models.Meeting.id == meeting_id, models.Meeting.user_id == current_user.id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting

@router.put("/{meeting_id}", response_model=schemas.MeetingOut)
def update_meeting(meeting_id: int, update: schemas.MeetingUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    meeting = db.query(models.Meeting).filter(models.Meeting.id == meeting_id, models.Meeting.user_id == current_user.id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    for key, value in update.dict(exclude_unset=True).items():
        setattr(meeting, key, value)
    db.commit()
    db.refresh(meeting)
    return meeting

@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(meeting_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    meeting = db.query(models.Meeting).filter(models.Meeting.id == meeting_id, models.Meeting.user_id == current_user.id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    db.delete(meeting)
    db.commit()
    return
