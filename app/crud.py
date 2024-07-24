from sqlalchemy.orm import Session
from app import models


def get_or_create_user(db: Session, clerk_id: str):
    user = db.query(models.User).filter(models.User.clerk_id == clerk_id).first()
    if user is None:
        db_user = models.User(clerk_id=clerk_id)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        user = db_user
    return user
