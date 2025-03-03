from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.review import Review, ReviewCreate, ReviewResponse, ReviewUpdate
from datetime import datetime

def create_review(db: Session, review_data: ReviewCreate):
    try:
        now = datetime.now()
        db_review = Review(**review_data.model_dump(), created_at=now, updated_at=now)
        
        db.add(db_review)
        db.commit()
        db.refresh(db_review)

        return ReviewResponse.model_validate(db_review.__dict__) 
    except Exception as e:
        raise

def get_review(db: Session, review_id: int):
    return db.query(Review).filter(Review.id == review_id).first()


def update_review(db: Session, review_id: int, new_comment: ReviewUpdate):
    db_review = db.query(Review).filter(Review.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")

    for key, value in new_comment.model_dump(exclude_unset=True).items():
        setattr(db_review, key, value)

    db_review.updated_at = datetime.now()
    db.commit()
    db.refresh(db_review)
    return db_review