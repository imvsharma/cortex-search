from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/")
def create_user(user):
    # Create user logic to be implemented
    return {"message": "User created successfully"}
