from fastapi import APIRouter

router = APIRouter()

@router.head("/health/")
def check_health():
    return "OK"
