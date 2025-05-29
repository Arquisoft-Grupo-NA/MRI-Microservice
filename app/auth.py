from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from app.templates import templates
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
CALLBACK_URL = os.getenv("AUTH0_CALLBACK_URL")
APP_URL = os.getenv("APP_URL")

router = APIRouter()

@router.get("/login")
async def login():
    return RedirectResponse(
        url=f"https://{AUTH0_DOMAIN}/authorize?"
            f"response_type=code&"
            f"client_id={CLIENT_ID}&"
            f"redirect_uri={CALLBACK_URL}&"
            f"scope=openid profile email"
    )

@router.get("/callback")
async def callback(request: Request, code: str = None):
    if not code:
        return HTMLResponse("Error: no code in callback", status_code=400)

    token_url = f"https://{AUTH0_DOMAIN}/oauth/token"
    headers = {"content-type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": CALLBACK_URL,
    }

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(token_url, data=data, headers=headers)
        token_resp.raise_for_status()
        tokens = token_resp.json()

        userinfo_url = f"https://{AUTH0_DOMAIN}/userinfo"
        userinfo_resp = await client.get(userinfo_url, headers={"Authorization": f"Bearer {tokens['access_token']}"})
        userinfo_resp.raise_for_status()
        userinfo = userinfo_resp.json()

    request.session["user"] = {
        "access_token": tokens["access_token"],
        "id_token": tokens.get("id_token"),
        "userinfo": userinfo,
    }

    return RedirectResponse(url=APP_URL)


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(
        url=f"https://{AUTH0_DOMAIN}/v2/logout?"
            f"client_id={CLIENT_ID}&"
            f"returnTo={APP_URL}"
    )

def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    return user

@router.get("/me", response_class=HTMLResponse)
async def read_me(request: Request, user=Depends(get_current_user)):
    userinfo = user.get("userinfo", {})
    nickname = userinfo.get("nickname", "Sin nickname")
    return templates.TemplateResponse("me.html", {"request": request, "nickname": nickname, "userinfo": userinfo})
