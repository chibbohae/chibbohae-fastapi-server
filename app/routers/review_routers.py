from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.review import ReviewCreate, ReviewResponse, ReviewUpdate
from app.services.review_service import create_review, get_review, update_review
from app.dependencies.db import get_db

router = APIRouter(
    prefix="/reviews"
)

@router.post("/", status_code=201)
def create_review_handler(review_data: ReviewCreate, db: Session = Depends(get_db)) -> ReviewResponse:
    try:
        review = create_review(db, review_data)
        return review
    except Exception as e:
        db.rollback() 
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{review_id}", response_model=ReviewResponse)
def read_review(review_id: int, db: Session = Depends(get_db)):
    review = get_review(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review
    
@router.put("/{review_id}", response_model=ReviewResponse)
def update_review_handler(review_id: int, new_comment: ReviewUpdate, db: Session = Depends(get_db)):
    try:
        review = update_review(db, review_id, new_comment)
        return review
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
