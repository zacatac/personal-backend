import os
import asyncio
from re import M
from typing import Optional
from uuid import uuid4

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import jwt
from jwt import PyJWKClient
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.ai import generate_chat
from app.crud import (
    get_bot,
    get_or_create_bot,
    get_or_create_user,
    get_user,
    persist_next_message,
)
from app.lib import async_tee, messages_from_context, tokens_for_context
import app.models as models
import app.schemas as schemas
from app.database import SessionLocal
from app.types import ChatCompletionUserMessageParamID

load_dotenv()

app = FastAPI()
security = HTTPBearer()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://app.zackeryfield.com",
        "https://zackeryfield.com",
        "https://api.zackeryfield.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ENV = os.getenv("ENV")
DEV_USER_ID = "user_2jfLb9a9wPGdc4vSPE1G3h8OVVI"
CLERK_JWT_ISSUER = os.getenv("CLERK_JWT_ISSUER")
CLERK_JWKS_URL = f"{CLERK_JWT_ISSUER}/.well-known/jwks.json"
MAX_TOKENS = 4096  # TODO: make sure this aligns with the frontend

if CLERK_JWT_ISSUER is None or CLERK_JWT_ISSUER == "":
    raise ValueError("Missing CLERK_JWT_ISSUER")

# Initialize the PyJWKClient
jwks_client = PyJWKClient(CLERK_JWKS_URL)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_signing_key(token):
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        return signing_key.key
    except jwt.exceptions.PyJWKClientError as error:
        raise HTTPException(status_code=401, detail=str(error))


async def optional_verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Optional[dict]:
    try:
        return await verify_token(credentials)
    except HTTPException as e:
        if ENV == "dev":
            return {
                "sub": DEV_USER_ID,
            }
        raise e


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        signing_key = get_signing_key(token)
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
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


@app.get("/me", response_model=schemas.User)
async def user(
    token_data: dict = Depends(optional_verify_token), db: Session = Depends(get_db)
):
    clerk_id = token_data["sub"]
    user = get_or_create_user(db=db, clerk_id=clerk_id)
    return user


@app.delete("/bot")
async def delete_bot(
    token_data: dict = Depends(optional_verify_token), db: Session = Depends(get_db)
):
    clerk_id = token_data["sub"]
    user = get_user(db=db, clerk_id=clerk_id)
    bot = get_bot(db=db, user_id=user.id)
    if bot:
        db.delete(bot)
        db.commit()
        return {"detail": "Bot deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Bot not found")


@app.get("/bot", response_model=schemas.Bot)
async def bot(
    token_data: dict = Depends(optional_verify_token), db: Session = Depends(get_db)
):
    clerk_id = token_data["sub"]
    user = get_or_create_user(db=db, clerk_id=clerk_id)
    bot = get_or_create_bot(db=db, user_id=user.id)
    if tokens_for_context(bot.context) >= MAX_TOKENS:
        name = bot.name
        db.delete(bot)
        db.commit()
        raise HTTPException(
            status_code=404, detail=f"Sorry, {name} is no longer with us."
        )
    return bot


@app.get("/chat", response_class=StreamingResponse)
async def stream_chat(
    message: str,
    token_data: dict = Depends(optional_verify_token),
    db: Session = Depends(get_db),
):
    clerk_id = token_data["sub"]
    user = db.query(models.User).filter_by(clerk_id=clerk_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    bot = get_or_create_bot(db=db, user_id=user.id)
    messages = []
    response_message_id = str(uuid4())
    if bot.context is not None:
        messages = messages_from_context(context=bot.context)
    messages.append(
        ChatCompletionUserMessageParamID(
            role="user",
            content=message,
            id=str(uuid4()),
        )
    )

    # Tee off the generating message to respond to the user and persist in parallel.
    accumulator, responder = await async_tee(generate_chat(messages))

    # Start the accumulator consumer in the background
    asyncio.create_task(
        persist_next_message(
            db=db,
            bot=bot,
            accumulator=accumulator,
            messages=messages,
            message_id=response_message_id,
        )
    )

    return StreamingResponse(responder, media_type="text/event-stream")
