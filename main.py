from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import jwt
from jwt import PyJWKClient
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
security = HTTPBearer()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://personal-backend-production.up.railway.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CLERK_JWT_ISSUER = os.getenv("CLERK_JWT_ISSUER")
CLERK_JWKS_URL = f"{CLERK_JWT_ISSUER}/.well-known/jwks.json"

if CLERK_JWT_ISSUER is None or CLERK_JWT_ISSUER == "":
    raise ValueError("Missing CLERK_JWT_ISSUER")

# Initialize the PyJWKClient
jwks_client = PyJWKClient(CLERK_JWKS_URL)


def get_signing_key(token):
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        return signing_key.key
    except jwt.exceptions.PyJWKClientError as error:
        raise HTTPException(status_code=401, detail=str(error))


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        signing_key = get_signing_key(token)
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            # audience="your-audience",  # Set this to your application's audience
            issuer=CLERK_JWT_ISSUER,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": True,
                "verify_iss": True,
            },
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidAudienceError:
        raise HTTPException(status_code=401, detail="Invalid audience")
    except jwt.InvalidIssuerError:
        raise HTTPException(status_code=401, detail="Invalid issuer")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


async def not_so_protected_route():
    return {"message": f"Hello anon!"}


@app.get("/api/protected")
async def protected_route(token_data: dict = Depends(verify_token)):
    return {"message": f"Hello, user {token_data['sub']}!"}
