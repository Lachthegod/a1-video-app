
# from fastapi import HTTPException, Depends
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from jose import jwt, jwk, JWTError
# from jose.utils import base64url_decode
# import requests
# import os

# COGNITO_REGION = os.environ.get("COGNITO_REGION", "ap-southeast-2")
# COGNITO_USERPOOL_ID = os.environ.get("COGNITO_USERPOOL_ID", "ap-southeast-2_KUuRLDBYK")
# COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID", "1nc5drgnphkq8i4d2rusnfoa36")

# JWKS_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USERPOOL_ID}/.well-known/jwks.json"
# ISSUER = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USERPOOL_ID}"
# jwks = requests.get(JWKS_URL).json()

# security = HTTPBearer()


# def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
#     if not credentials or credentials.scheme.lower() != "bearer":
#         raise HTTPException(status_code=401, detail="Unauthorized")

#     token = credentials.credentials
#     try:
#         # Get the key
#         unverified_headers = jwt.get_unverified_header(token)
#         kid = unverified_headers["kid"]
#         key_data = next((k for k in jwks["keys"] if k["kid"] == kid), None)
#         if not key_data:
#             raise HTTPException(status_code=401, detail="Invalid token key")

#         # Construct the public key
#         public_key = jwk.construct(key_data)

#         # Verify signature manually
#         message, encoded_sig = token.rsplit('.', 1)
#         decoded_sig = base64url_decode(encoded_sig.encode())
#         if not public_key.verify(message.encode(), decoded_sig):
#             raise HTTPException(status_code=401, detail="Invalid token signature")

#         # Decode claims
#         payload = jwt.get_unverified_claims(token)

#         username = payload.get("cognito:username") or payload.get("username")
#         groups = payload.get("cognito:groups", [])
#         sub = payload.get("sub")

#         if not username:
#             raise HTTPException(status_code=401, detail="Invalid token claims")

#         return {
#             "username": username,
#             "id": sub,
#             "role": groups[0] if groups else "user"
#         }

#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=401, detail="Token expired")
#     except JWTError as e:
#         raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError
import requests
import os

# -----------------------------
# Cognito Config
# -----------------------------
COGNITO_REGION = os.environ.get("COGNITO_REGION", "ap-southeast-2")
COGNITO_USERPOOL_ID = os.environ.get("COGNITO_USERPOOL_ID", "ap-southeast-2_KUuRLDBYK")
COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID", "1nc5drgnphkq8i4d2rusnfoa36")

JWKS_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USERPOOL_ID}/.well-known/jwks.json"
ISSUER = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USERPOOL_ID}"

jwks = requests.get(JWKS_URL).json()
security = HTTPBearer()


def verify_token(token: str):
    try:
        claims = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=COGNITO_CLIENT_ID,
            issuer=ISSUER,
        )
        return claims
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Unauthorized")

    claims = verify_token(credentials.credentials)

    username = claims.get("cognito:username") or claims.get("username")
    groups = claims.get("cognito:groups", [])
    sub = claims.get("sub")

    if not username:
        raise HTTPException(status_code=401, detail="Invalid token claims")

    return {
        "username": username,
        "id": sub,
        "role": groups[0] if groups else "user",
    }
