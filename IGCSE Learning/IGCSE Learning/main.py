from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from database import engine
import models
from dependencies import get_current_user

from routers import auth, admin, teacher, student

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(teacher.router)
app.include_router(student.router)

@app.get("/")
async def root(user: models.User = Depends(get_current_user)):
    if not user:
        return RedirectResponse("/login")
    if user.role == "admin":
        return RedirectResponse("/admin")
    elif user.role == "teacher":
        return RedirectResponse("/teacher")
    elif user.role == "student":
        return RedirectResponse("/student")
    return RedirectResponse("/login")