from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def root():
    return {"message": "Welcome to Chiboohae!"}


@router.get("/health", status_code=200)
async def health_check():
    return {"message": "Success Health Check"}
