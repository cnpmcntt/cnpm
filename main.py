from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse
from database import engine
import models
from routers import auth, admin, manager, teacher, student, parent, profile

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(manager.router)
app.include_router(teacher.router)
app.include_router(student.router)
app.include_router(parent.router)
app.include_router(profile.router)

@app.get("/")
async def root():
    return RedirectResponse("/login")