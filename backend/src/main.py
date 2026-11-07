import os
from uuid import UUID
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal
load_dotenv()
app = FastAPI(title="Flowboard API")
# Build CORS from runtime bindings on Workers and local environment during development.
from starlette.responses import Response
@app.middleware("http")
async def runtime_cors(request, call_next):
    env=request.scope.get("env")
    origins=(getattr(env,"ALLOWED_ORIGINS",None) if env else None) or os.getenv("ALLOWED_ORIGINS","http://localhost:5173")
    origin=request.headers.get("origin")
    allowed=origin in [x.strip() for x in origins.split(",")]
    if request.method=="OPTIONS":
        response=Response(status_code=204 if allowed else 403)
    else:
        response=await call_next(request)
    if allowed:
        response.headers["Access-Control-Allow-Origin"]=origin
        response.headers["Vary"]="Origin"
        response.headers["Access-Control-Allow-Methods"]="GET, POST, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"]="Authorization, Content-Type"
    return response

class Title(BaseModel):
    title: str = Field(min_length=1, max_length=200, pattern=r".*\S.*")
class CardInput(Title):
    status: Literal["todo","doing","done"] = "todo"
class Move(BaseModel):
    status: Literal["todo","doing","done"]
class Member(BaseModel):
    user_id: UUID
class UserState(BaseModel):
    suspended: bool

def config(request: Request):
    env = request.scope.get("env")
    def get(k):
        return getattr(env,k,None) if env else os.getenv(k)
    url,key=get("SUPABASE_URL"),get("SUPABASE_PUBLISHABLE_KEY")
    if not url or not key: raise HTTPException(503,"Database configuration missing")
    return url.rstrip("/"),key
async def session(request: Request):
    token=request.headers.get("Authorization", "")
    if not token.startswith("Bearer "): raise HTTPException(401,"Sign in required")
    url,key=config(request)
    headers={"apikey":key,"Authorization":token,"Content-Type":"application/json","Prefer":"return=representation"}
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            result=await c.get(url+"/auth/v1/user",headers=headers)
    except httpx.RequestError:
        raise HTTPException(503,"Authentication unavailable; try again")
    if result.status_code!=200: raise HTTPException(401,"Session expired; sign in again")
    return url,headers,result.json()
async def db(s,method,path,body=None):
    url,headers,_=s
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            response=await c.request(method,url+"/rest/v1/"+path,headers=headers,json=body)
    except httpx.RequestError:
        raise HTTPException(503,"Database unavailable; try again")
    if response.status_code>=400:
        raise HTTPException(403 if response.status_code in (401,403) else 400,"Action denied or invalid data")
    return response.json() if response.content else None
@app.get("/health")
def health(): return {"status":"ok"}
@app.get("/me")
async def me(s=Depends(session)):
    profiles=await db(s,"GET","kb_profiles?user_id=eq."+s[2]["id"])
    return {"id":s[2]["id"],"email":s[2].get("email"),"profile":profiles[0] if profiles else None}
@app.get("/boards")
async def boards(s=Depends(session)): return await db(s,"GET","kb_boards?order=created_at.asc")
@app.post("/boards",status_code=201)
async def create_board(data:Title,s=Depends(session)):
    return (await db(s,"POST","kb_boards",{"title":data.title.strip(),"owner_id":s[2]["id"]}))[0]
@app.get("/boards/{board_id}/cards")
async def cards(board_id:UUID,s=Depends(session)):
    return await db(s,"GET",f"kb_cards?board_id=eq.{board_id}&order=created_at.asc")
@app.post("/boards/{board_id}/cards",status_code=201)
async def create_card(board_id:UUID,data:CardInput,s=Depends(session)):
    return (await db(s,"POST","kb_cards",{**data.model_dump(),"title":data.title.strip(),"board_id":str(board_id)}))[0]
@app.patch("/cards/{card_id}")
async def move(card_id:UUID,data:Move,s=Depends(session)):
    rows=await db(s,"PATCH",f"kb_cards?id=eq.{card_id}",data.model_dump())
    if not rows: raise HTTPException(404,"Card not found")
    return rows[0]
@app.delete("/cards/{card_id}",status_code=204)
async def delete(card_id:UUID,s=Depends(session)):
    if not await db(s,"DELETE",f"kb_cards?id=eq.{card_id}"): raise HTTPException(404,"Card not found")
@app.get("/boards/{board_id}/members")
async def members(board_id:UUID,s=Depends(session)):
    return await db(s,"GET",f"kb_members?board_id=eq.{board_id}")
@app.post("/boards/{board_id}/members",status_code=201)
async def share(board_id:UUID,data:Member,s=Depends(session)):
    return (await db(s,"POST","kb_members",{"board_id":str(board_id),"user_id":str(data.user_id)}))[0]
@app.delete("/boards/{board_id}/members/{user_id}",status_code=204)
async def unshare(board_id:UUID,user_id:UUID,s=Depends(session)):
    await db(s,"DELETE",f"kb_members?board_id=eq.{board_id}&user_id=eq.{user_id}")
@app.get("/admin/users")
async def users(s=Depends(session)):
    return await db(s,"POST","rpc/kb_admin_users",{})
@app.patch("/admin/users/{user_id}")
async def user_state(user_id:UUID,data:UserState,s=Depends(session)):
    return await db(s,"POST","rpc/kb_set_suspended",{"target":str(user_id),"value":data.suspended})
