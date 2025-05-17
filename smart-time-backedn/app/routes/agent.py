# routers/agent.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.auth_bearer import get_current_user
from app.models.user import User
from app.models.chat_message import ChatMessage
from app.ai_config import OPENAI_API_KEY, GPT_MODEL
from app.models.task import Task
from app.models.meeting import Meeting
from datetime import datetime, timedelta
from openai import OpenAI
import json
import os
import dateparser

router = APIRouter()

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

tools = [
    {
        "type": "function",
        "function": {
            "name": "create_meeting",
            "description": "Schedule a meeting for the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"},
                    "location": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["title", "start_time", "end_time"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_free_time",
            "description": "Get available time slots for the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "format": "date"},
                    "duration_minutes": {"type": "integer"},
                },
                "required": ["date", "duration_minutes"]
            }
        },
    }
]

def create_meeting_backend(user_id: int, title: str, start_time: str, end_time: str, location: str = None, description: str = None, db: Session = None):
    meeting = Meeting(
        user_id=user_id,
        title=title,
        start_time=datetime.fromisoformat(start_time),
        end_time=datetime.fromisoformat(end_time),
        location=location,
        description=description,
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return {"status": "Meeting created", "meeting_id": meeting.id}

def get_free_time_backend(user_id: int, date: str, duration_minutes: int, db: Session):
    day_start = datetime.fromisoformat(date + "T09:00:00")
    day_end = datetime.fromisoformat(date + "T17:00:00")

    meetings = db.query(Meeting).filter(
        Meeting.user_id == user_id,
        Meeting.start_time >= day_start,
        Meeting.end_time <= day_end
    ).all()

    busy_slots = [(m.start_time, m.end_time) for m in meetings]

    free_slots = []
    current_time = day_start
    while current_time + timedelta(minutes=duration_minutes) <= day_end:
        candidate_end = current_time + timedelta(minutes=duration_minutes)
        overlap = any(s < candidate_end and e > current_time for s, e in busy_slots)
        if not overlap:
            free_slots.append({"start": current_time.isoformat(), "end": candidate_end.isoformat()})
        current_time += timedelta(minutes=30)

    return {"free_slots": free_slots}

@router.post("/chat")
def chat_with_agent(message: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from openai.types.chat import ChatCompletionMessage

    # Start conversation history
    messages: list[dict] = [
        {"role": "system", "content": "You are a smart assistant that helps users manage their calendar, tasks, and meetings."},
        {"role": "user", "content": message},
    ]

    # Save initial user message
    db.add(ChatMessage(user_id=current_user.id, role="user", content=message))
    db.commit()

    while True:
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        reply: ChatCompletionMessage = response.choices[0].message
        messages.append(reply)

        if not reply.tool_calls:
            # Assistant replied directly, store and return
            db.add(ChatMessage(user_id=current_user.id, role="assistant", content=reply.content))
            db.commit()
            return {"reply": reply.content}

        # One or more tool calls
        tool_outputs = []
        for tool_call in reply.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            # Natural language date parsing
            if "start_time" in args:
                parsed_start = dateparser.parse(args["start_time"], settings={"RELATIVE_BASE": datetime.now()})
                args["start_time"] = parsed_start.isoformat() if parsed_start else args["start_time"]

            if "end_time" in args:
                parsed_end = dateparser.parse(args["end_time"], settings={"RELATIVE_BASE": datetime.now()})
                args["end_time"] = parsed_end.isoformat() if parsed_end else args["end_time"]

            if "date" in args:
                parsed_date = dateparser.parse(args["date"], settings={"RELATIVE_BASE": datetime.now()})
                args["date"] = parsed_date.date().isoformat() if parsed_date else args["date"]

            # Call the backend function
            if name == "create_meeting":
                result = create_meeting_backend(user_id=current_user.id, db=db, **args)
            elif name == "get_free_time":
                result = get_free_time_backend(user_id=current_user.id, db=db, **args)
            else:
                result = {"error": f"Unknown function: {name}"}

            tool_outputs.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": name,
                "content": json.dumps(result)
            })

        # Append tool results and loop again
        messages.extend(tool_outputs)
