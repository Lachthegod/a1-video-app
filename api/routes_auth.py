from fastapi import APIRouter, HTTPException, Body
from api.cognito import (
    sign_up_user,
    confirm_user,
    authenticate_user,
    respond_to_mfa_challenge,
)
import requests
from parameter_store import load_parameters


router = APIRouter()

parameters = load_parameters()

COGNITO_REGION = parameters.get("awsregion", "ap-southeast-2")
COGNITO_USERPOOL_ID = parameters.get("cognitouserpoolid")


JWKS_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USERPOOL_ID}/.well-known/jwks.json"
jwks = requests.get(JWKS_URL).json()


@router.post("/signup")
async def signup(
    username: str = Body(...), password: str = Body(...), email: str = Body(...)
):
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
        return authenticate_user(username, password)

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/mfa")
async def mfa(
    username: str = Body(...),
    session: str = Body(...),
    code: str = Body(...),
    challenge: str = Body(...),
):

    try:
        return respond_to_mfa_challenge(username, session, code, challenge)

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
