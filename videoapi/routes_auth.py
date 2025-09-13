# videoapi/routes_auth.py
from fastapi import APIRouter, Body, HTTPException
from videoapi.cognito import sign_up_user, confirm_user, authenticate_user  # functions to call Cognito APIs

router = APIRouter()

@router.post("/signup")
async def signup(username: str = Body(...), password: str = Body(...), email: str = Body(...)):
    try:
        result = sign_up_user(username, password, email)
        return {"message": "User signed up", "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/confirm")
async def confirm(username: str = Body(...), code: str = Body(...)):
    try:
        result = confirm_user(username, code)
        return {"message": "User confirmed", "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(username: str = Body(...), password: str = Body(...)):
    try:
        tokens = authenticate_user(username, password)
        return tokens
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
