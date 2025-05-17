from fastapi import FastAPI
from app.database import Base, engine
from app.models import user, task, meeting, chat_message, notification
from app.routes import auth, users, tasks, meetings, agent, notifications

app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)

# Routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
app.include_router(meetings.router, prefix="/meetings", tags=["Meetings"])
app.include_router(agent.router, prefix="/agent", tags=["AI Agent"])
app.include_router(notifications.router, prefix="/notifications")

@app.get("/")
def root():
    return {"message": "Smart Time Manager API is running!"}
