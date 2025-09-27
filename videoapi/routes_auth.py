
from fastapi import APIRouter, HTTPException, Body
from videoapi.cognito import (
    sign_up_user, confirm_user, authenticate_user, respond_to_mfa_challenge
)
import requests
import os
import jwt
from jose import jwk, jwt as jose_jwt, JWTError
from jose.utils import base64url_decode
from videoapi.pstore import load_parameters



router = APIRouter()

parameters = load_parameters()

COGNITO_REGION = parameters.get("awsregion", "ap-southeast-2")
COGNITO_USERPOOL_ID = parameters.get("cognitouserpoolid")


COGNITO_DOMAIN = f"https://{load_parameters().get('cognitouserpoolid')}.auth.{load_parameters().get('awsregion')}.amazoncognito.com"


# Load Cognito JWKS once
JWKS_URL = f"https://cognito-idp.{load_parameters().get('awsregion')}.amazonaws.com/{load_parameters().get('cognitouserpoolid')}/.well-known/jwks.json"
jwks = requests.get(JWKS_URL).json()


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
        return authenticate_user(username, password)

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))



@router.post("/mfa")
async def mfa(username: str = Body(...), session: str = Body(...), code: str = Body(...), challenge: str = Body(...)):

    try:
        return respond_to_mfa_challenge(username, session, code, challenge)
    
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


