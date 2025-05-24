# routers/agent.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
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
import re

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
    },
    {
        "type": "function",
        "function": {
            "name": "get_meetings_on_date",
            "description": "Get all meetings for the user on a specific date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "format": "date"}
                },
                "required": ["date"]
            }
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_meeting",
            "description": "Delete a meeting by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "meeting_id": {"type": "integer"}
                },
                "required": ["meeting_id"]
            }
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_meeting",
            "description": "Update a meeting's title, start time, or end time by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "meeting_id": {"type": "integer"},
                    "title": {"type": "string"},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"}
                },
                "required": ["meeting_id"]
            }
        },
    },
]

tools += [
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a task for the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"},
                    "description": {"type": "string"},
                    "priority": {"type": "string"}
                },
                "required": ["title"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_tasks_on_date",
            "description": "Get all tasks for the user on a specific date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "format": "date"}
                },
                "required": ["date"]
            }
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Delete a task by its ID or by title/date/time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer"},
                    "title": {"type": "string"},
                    "date": {"type": "string"},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"}
                },
                "required": []
            }
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": "Update a task's title, start time, end time, description, or priority by its ID or by title/date/time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer"},
                    "title": {"type": "string"},
                    "date": {"type": "string"},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"},
                    "new_title": {"type": "string"},
                    "new_start_time": {"type": "string"},
                    "new_end_time": {"type": "string"},
                    "new_description": {"type": "string"},
                    "new_priority": {"type": "string"}
                },
                "required": []
            }
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_free_time_for_task",
            "description": "Get available time slots for the user to schedule a task",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "format": "date"},
                    "duration_minutes": {"type": "integer"}
                },
                "required": ["date", "duration_minutes"]
            }
        },
    },
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
        overlap = any(s < candidate_end and e >
                      current_time for s, e in busy_slots)
        if not overlap:
            free_slots.append(
                {"start": current_time.isoformat(), "end": candidate_end.isoformat()})
        current_time += timedelta(minutes=30)

    return {"free_slots": free_slots}


def get_meetings_on_date_backend(user_id: int, date: str, db: Session):
    try:
        parsed_date = datetime.fromisoformat(date)
    except Exception:
        parsed_date = dateparser.parse(
            date, settings={"RELATIVE_BASE": datetime.now()})
    if not parsed_date:
        raise ValueError(f"Could not parse date: {date}")
    day_start = parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = parsed_date.replace(
        hour=23, minute=59, second=59, microsecond=999999)
    print("Getting meetings for date:", day_start, day_end)
    meetings = db.query(Meeting).filter(
        Meeting.user_id == user_id,
        Meeting.start_time >= day_start,
        Meeting.start_time <= day_end
    ).all()
    return [
        {
            "id": m.id,
            "title": m.title,
            "start_time": m.start_time.isoformat(),
            "end_time": m.end_time.isoformat(),
            "location": m.location,
            "description": m.description
        } for m in meetings
    ]


def delete_meeting_backend(user_id: int, meeting_id: int, db: Session):
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id, Meeting.user_id == user_id).first()
    if not meeting:
        return {"error": "Meeting not found"}
    db.delete(meeting)
    db.commit()
    return {"status": "Meeting deleted"}


def find_meetings(user_id: int, db: Session, title: str = None, date: str = None, start_time: str = None, end_time: str = None):
    query = db.query(Meeting).filter(Meeting.user_id == user_id)
    print(
        f"find_meetings called with title={title}, date={date}, start_time={start_time}, end_time={end_time}")
    parsed_date = dateparser.parse(
        date, settings={"RELATIVE_BASE": datetime.now()}) if date else None
    parsed_start = dateparser.parse(
        start_time, settings={"RELATIVE_BASE": datetime.now()}) if start_time else None
    parsed_end = dateparser.parse(
        end_time, settings={"RELATIVE_BASE": datetime.now()}) if end_time else None
    print(
        f"parsed_date={parsed_date}, parsed_start={parsed_start}, parsed_end={parsed_end}")
    if title:
        query = query.filter(Meeting.title.ilike(f"%{title}%"))
    if parsed_date:
        day_start = parsed_date.replace(
            hour=0, minute=0, second=0, microsecond=0)
        day_end = parsed_date.replace(
            hour=23, minute=59, second=59, microsecond=999999)
        print(f"Filtering by day_start={day_start}, day_end={day_end}")
        query = query.filter(Meeting.start_time >= day_start,
                             Meeting.start_time <= day_end)
    if parsed_start:
        if parsed_date:
            print(
                f"Filtering by start_time: {parsed_start.hour}:{parsed_start.minute} on {parsed_date.date()}")
            query = query.filter(
                Meeting.start_time.year == parsed_date.year,
                Meeting.start_time.month == parsed_date.month,
                Meeting.start_time.day == parsed_date.day,
                Meeting.start_time.hour == parsed_start.hour,
                Meeting.start_time.minute == parsed_start.minute
            )
        else:
            print(
                f"Filtering by start_time: {parsed_start.hour}:{parsed_start.minute}")
            query = query.filter(Meeting.start_time.hour == parsed_start.hour,
                                 Meeting.start_time.minute == parsed_start.minute)
    if parsed_end:
        if parsed_date:
            print(
                f"Filtering by end_time: {parsed_end.hour}:{parsed_end.minute} on {parsed_date.date()}")
            query = query.filter(
                Meeting.end_time.year == parsed_date.year,
                Meeting.end_time.month == parsed_date.month,
                Meeting.end_time.day == parsed_date.day,
                Meeting.end_time.hour == parsed_end.hour,
                Meeting.end_time.minute == parsed_end.minute
            )
        else:
            print(
                f"Filtering by end_time: {parsed_end.hour}:{parsed_end.minute}")
            query = query.filter(Meeting.end_time.hour == parsed_end.hour,
                                 Meeting.end_time.minute == parsed_end.minute)
    meetings = query.all()
    print(f"Found meetings: {[m.start_time for m in meetings]}")
    return meetings


def delete_meeting_backend(user_id: int, db: Session, title: str = None, date: str = None, start_time: str = None, end_time: str = None, meeting_id: int = None):
    meetings = []
    if meeting_id:
        meeting = db.query(Meeting).filter(
            Meeting.id == meeting_id, Meeting.user_id == user_id).first()
        if meeting:
            meetings = [meeting]
    else:
        meetings = find_meetings(
            user_id, db, title, date, start_time, end_time)
    if not meetings:
        return {"error": "No matching meetings found"}
    for m in meetings:
        db.delete(m)
    db.commit()
    return {"status": f"Deleted {len(meetings)} meeting(s)", "deleted_ids": [m.id for m in meetings]}


def is_time_slot_available(user_id: int, db: Session, new_start: datetime, new_end: datetime, exclude_meeting_id: int = None):
    q = db.query(Meeting).filter(Meeting.user_id == user_id)
    if exclude_meeting_id:
        q = q.filter(Meeting.id != exclude_meeting_id)
    q = q.filter(
        (Meeting.start_time < new_end) & (Meeting.end_time > new_start)
    )
    return not q.first()


def suggest_next_available_slot(user_id: int, db: Session, duration_minutes: int, after: datetime):
    for day in range(0, 7):
        day_start = (after + timedelta(days=day)).replace(hour=9,
                                                          minute=0, second=0, microsecond=0)
        for i in range(0, 16):
            slot_start = day_start + timedelta(minutes=30 * i)
            slot_end = slot_start + timedelta(minutes=duration_minutes)
            if is_time_slot_available(user_id, db, slot_start, slot_end):
                return slot_start, slot_end
    return None, None


def update_meeting_backend(user_id: int, db: Session, title: str = None, date: str = None, start_time: str = None, end_time: str = None, meeting_id: int = None, new_title: str = None, new_start_time: str = None, new_end_time: str = None):
    meetings = []
    if meeting_id:
        meeting = db.query(Meeting).filter(
            Meeting.id == meeting_id, Meeting.user_id == user_id).first()
        if meeting:
            meetings = [meeting]
    else:
        meetings = find_meetings(
            user_id, db, title, date, start_time, end_time)
    if not meetings:
        return {"error": "No matching meetings found"}
    updated = []
    for m in meetings:
        ns = None
        ne = None
        if new_start_time:
            ns = datetime.fromisoformat(new_start_time)
        elif start_time:
            ns = dateparser.parse(start_time, settings={
                                  "RELATIVE_BASE": m.start_time})
        else:
            ns = m.start_time
        if new_end_time:
            ne = datetime.fromisoformat(new_end_time)
        elif end_time:
            ne = dateparser.parse(end_time, settings={
                                  "RELATIVE_BASE": m.end_time})
        else:
            ne = m.end_time
        if not is_time_slot_available(user_id, db, ns, ne, exclude_meeting_id=m.id):
            slot_start, slot_end = suggest_next_available_slot(
                user_id, db, int((ne-ns).total_seconds()//60), ns)
            return {"error": "Time slot not available", "suggested_start": slot_start.isoformat() if slot_start else None, "suggested_end": slot_end.isoformat() if slot_end else None}
        if new_title:
            m.title = new_title
        m.start_time = ns
        m.end_time = ne
        db.commit()
        db.refresh(m)
        updated.append(m.id)
    return {"status": f"Updated {len(updated)} meeting(s)", "updated_ids": updated}


def extract_date_from_message(message: str):
    parsed = dateparser.parse(
        message, settings={"RELATIVE_BASE": datetime.now()})
    return parsed.date().isoformat() if parsed else None


def set_last_context_meeting(user_id: int, db: Session, title: str = None, date: str = None):
    db.query(ChatMessage).filter(ChatMessage.user_id == user_id,
                                 ChatMessage.role == "context_meeting").delete()
    ctx = {"type": "meeting"}
    if title:
        ctx["title"] = title
    if date:
        ctx["date"] = date
    db.add(ChatMessage(user_id=user_id,
           role="context_meeting", content=json.dumps(ctx)))
    db.commit()


def get_last_context_meeting(user_id: int, db: Session):
    last_ctx = db.query(ChatMessage).filter(ChatMessage.user_id == user_id,
                                            ChatMessage.role == "context_meeting").order_by(desc(ChatMessage.id)).first()
    if last_ctx:
        try:
            ctx = json.loads(last_ctx.content)
            return ctx.get("title"), ctx.get("date")
        except Exception:
            return None, None
    return None, None


def set_last_context_task(user_id: int, db: Session, title: str = None, date: str = None):
    db.query(ChatMessage).filter(ChatMessage.user_id == user_id,
                                 ChatMessage.role == "context_task").delete()
    ctx = {"type": "task"}
    if title:
        ctx["title"] = title
    if date:
        ctx["date"] = date
    db.add(ChatMessage(user_id=user_id, role="context_task", content=json.dumps(ctx)))
    db.commit()


def get_last_context_task(user_id: int, db: Session):
    last_ctx = db.query(ChatMessage).filter(ChatMessage.user_id == user_id,
                                            ChatMessage.role == "context_task").order_by(desc(ChatMessage.id)).first()
    if last_ctx:
        try:
            ctx = json.loads(last_ctx.content)
            return ctx.get("title"), ctx.get("date")
        except Exception:
            return None, None
    return None, None


def set_pending_meeting(user_id: int, db: Session, meeting_data: dict):
    db.query(ChatMessage).filter(ChatMessage.user_id == user_id,
                                 ChatMessage.role == "pending_meeting").delete()
    db.add(ChatMessage(user_id=user_id, role="pending_meeting",
           content=json.dumps(meeting_data)))
    db.commit()


def get_pending_meeting(user_id: int, db: Session):
    last_ctx = db.query(ChatMessage).filter(ChatMessage.user_id == user_id,
                                            ChatMessage.role == "pending_meeting").order_by(desc(ChatMessage.id)).first()
    if last_ctx:
        try:
            return json.loads(last_ctx.content)
        except Exception:
            return None
    return None


def clear_pending_meeting(user_id: int, db: Session):
    db.query(ChatMessage).filter(ChatMessage.user_id == user_id,
                                 ChatMessage.role == "pending_meeting").delete()
    db.commit()


def set_pending_task(user_id: int, db: Session, task_data: dict):
    db.query(ChatMessage).filter(ChatMessage.user_id == user_id,
                                 ChatMessage.role == "pending_task").delete()
    db.add(ChatMessage(user_id=user_id, role="pending_task",
           content=json.dumps(task_data)))
    db.commit()


def get_pending_task(user_id: int, db: Session):
    last_ctx = db.query(ChatMessage).filter(ChatMessage.user_id == user_id,
                                            ChatMessage.role == "pending_task").order_by(desc(ChatMessage.id)).first()
    if last_ctx:
        try:
            return json.loads(last_ctx.content)
        except Exception:
            return None
    return None


def clear_pending_task(user_id: int, db: Session):
    db.query(ChatMessage).filter(ChatMessage.user_id == user_id,
                                 ChatMessage.role == "pending_task").delete()
    db.commit()


def get_recent_chat_history(user_id: int, db: Session, n: int = 10):
    return db.query(ChatMessage).filter(ChatMessage.user_id == user_id).order_by(desc(ChatMessage.id)).limit(n).all()[::-1]


def infer_context_from_history(history):
    last_title = None
    last_date = None
    for msg in reversed(history):
        match = re.search(r'(?:meeting|Meeting) ([\w\s]+)', msg.content)
        if match and not last_title:
            last_title = match.group(1).strip()
        date = extract_date_from_message(msg.content)
        if date and not last_date:
            last_date = date
        if last_title and last_date:
            break
    return last_title, last_date

# --- TASKS BACKEND LOGIC ---


def create_task_backend(user_id: int, title: str, start_time: str = None, end_time: str = None, description: str = None, priority: str = None, db: Session = None):
    from app.models.task import Task, TaskPriority
    # Map 'normal' to 'medium' and validate priority
    if priority:
        priority_lower = priority.lower()
        if priority_lower == "normal":
            priority_enum = TaskPriority.medium
        elif priority_lower in TaskPriority.__members__:
            priority_enum = TaskPriority[priority_lower]
        elif priority_lower in [p.value for p in TaskPriority]:
            priority_enum = TaskPriority(priority_lower)
        else:
            priority_enum = TaskPriority.medium
    else:
        priority_enum = TaskPriority.medium
    task = Task(
        user_id=user_id,
        title=title,
        start_time=datetime.fromisoformat(start_time) if start_time else None,
        end_time=datetime.fromisoformat(end_time) if end_time else None,
        description=description,
        priority=priority_enum
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"status": "Task created", "task_id": task.id}


def get_tasks_on_date_backend(user_id: int, date: str, db: Session):
    from app.models.task import Task
    try:
        parsed_date = datetime.fromisoformat(date)
    except Exception:
        import dateparser
        parsed_date = dateparser.parse(
            date, settings={"RELATIVE_BASE": datetime.now()})
    if not parsed_date:
        raise ValueError(f"Could not parse date: {date}")
    day_start = parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = parsed_date.replace(
        hour=23, minute=59, second=59, microsecond=999999)
    tasks = db.query(Task).filter(
        Task.user_id == user_id,
        Task.start_time >= day_start,
        Task.start_time <= day_end
    ).all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "start_time": t.start_time.isoformat() if t.start_time else None,
            "end_time": t.end_time.isoformat() if t.end_time else None,
            "description": t.description,
            "priority": t.priority.value
        } for t in tasks
    ]


def find_tasks(user_id: int, db: Session, title: str = None, date: str = None, start_time: str = None, end_time: str = None):
    from app.models.task import Task
    import dateparser
    query = db.query(Task).filter(Task.user_id == user_id)
    parsed_date = dateparser.parse(
        date, settings={"RELATIVE_BASE": datetime.now()}) if date else None
    parsed_start = dateparser.parse(
        start_time, settings={"RELATIVE_BASE": datetime.now()}) if start_time else None
    parsed_end = dateparser.parse(
        end_time, settings={"RELATIVE_BASE": datetime.now()}) if end_time else None
    if title:
        query = query.filter(Task.title.ilike(f"%{title}%"))
    if parsed_date:
        day_start = parsed_date.replace(
            hour=0, minute=0, second=0, microsecond=0)
        day_end = parsed_date.replace(
            hour=23, minute=59, second=59, microsecond=999999)
        query = query.filter(Task.start_time >= day_start,
                             Task.start_time <= day_end)
    if parsed_start:
        query = query.filter(Task.start_time >= parsed_start)
    if parsed_end:
        query = query.filter(Task.end_time <= parsed_end)
    return query.all()


def delete_task_backend(user_id: int, db: Session, title: str = None, date: str = None, start_time: str = None, end_time: str = None, task_id: int = None):
    from app.models.task import Task
    tasks = []
    if task_id:
        task = db.query(Task).filter(Task.id == task_id,
                                     Task.user_id == user_id).first()
        if task:
            tasks = [task]
    else:
        tasks = find_tasks(user_id, db, title, date, start_time, end_time)
    if not tasks:
        return {"error": "No matching tasks found"}
    for t in tasks:
        db.delete(t)
    db.commit()
    return {"status": f"Deleted {len(tasks)} task(s)", "deleted_ids": [t.id for t in tasks]}


def update_task_backend(user_id: int, db: Session, title: str = None, date: str = None, start_time: str = None, end_time: str = None, task_id: int = None, new_title: str = None, new_start_time: str = None, new_end_time: str = None, new_description: str = None, new_priority: str = None):
    from app.models.task import Task, TaskPriority
    tasks = []
    if task_id:
        task = db.query(Task).filter(Task.id == task_id,
                                     Task.user_id == user_id).first()
        if task:
            tasks = [task]
    else:
        tasks = find_tasks(user_id, db, title, date, start_time, end_time)
    if not tasks:
        return {"error": "No matching tasks found"}
    updated = []
    for t in tasks:
        if new_title:
            t.title = new_title
        if new_start_time:
            t.start_time = datetime.fromisoformat(new_start_time)
        elif start_time:
            import dateparser
            t.start_time = dateparser.parse(
                start_time, settings={"RELATIVE_BASE": t.start_time or datetime.now()})
        if new_end_time:
            t.end_time = datetime.fromisoformat(new_end_time)
        elif end_time:
            import dateparser
            t.end_time = dateparser.parse(
                end_time, settings={"RELATIVE_BASE": t.end_time or datetime.now()})
        if new_description:
            t.description = new_description
        if new_priority:
            t.priority = TaskPriority(new_priority)
        db.commit()
        db.refresh(t)
        updated.append(t.id)
    return {"status": f"Updated {len(updated)} task(s)", "updated_ids": updated}


def is_task_time_slot_available(user_id: int, db: Session, new_start: datetime, new_end: datetime, exclude_task_id: int = None):
    from app.models.task import Task
    q = db.query(Task).filter(Task.user_id == user_id)
    if exclude_task_id:
        q = q.filter(Task.id != exclude_task_id)
    q = q.filter((Task.start_time < new_end) & (Task.end_time > new_start))
    return not q.first()


def get_free_time_for_task_backend(user_id: int, date: str, duration_minutes: int, db: Session):
    from app.models.task import Task
    day_start = datetime.fromisoformat(date + "T09:00:00")
    day_end = datetime.fromisoformat(date + "T17:00:00")
    tasks = db.query(Task).filter(
        Task.user_id == user_id,
        Task.start_time >= day_start,
        Task.end_time <= day_end
    ).all()
    busy_slots = [(t.start_time, t.end_time) for t in tasks]
    free_slots = []
    current_time = day_start
    while current_time + timedelta(minutes=duration_minutes) <= day_end:
        candidate_end = current_time + timedelta(minutes=duration_minutes)
        overlap = any(s < candidate_end and e >
                      current_time for s, e in busy_slots)
        if not overlap:
            free_slots.append(
                {"start": current_time.isoformat(), "end": candidate_end.isoformat()})
        current_time += timedelta(minutes=30)
    return {"free_slots": free_slots}


def is_relevant_query(message: str) -> bool:
    """
    Determines if a message is relevant to time management by checking for:
    1. Intent keywords related to calendar/task management
    2. Question patterns about schedule/tasks
    3. Time-related expressions
    4. Action verbs related to calendar management
    """
    # Core intent keywords indicating time management purpose
    intent_keywords = {
        "meeting", "task", "schedule", "appointment", "event",
        "todo", "reminder", "deadline", "calendar", "agenda",
        "slot", "availability", "busy", "free"
    }

    # Action verbs specific to calendar/task management
    action_verbs = {
        "create", "schedule", "set", "plan", "book",
        "cancel", "delete", "remove", "reschedule", "move",
        "update", "change", "check", "show", "list", "find",
        "complete", "finish", "have", "add", "organize"
    }

    # Time-related expressions
    time_expressions = {
        "today", "tomorrow", "yesterday", "week",
        "month", "morning", "afternoon", "evening",
        "time", "date", "day", "hour", "minute",
        "available", "free", "busy", "now", "later",
        "daily", "weekly", "monthly", "am", "pm",
        "next", "previous", "upcoming", "soon"
    }

    # Question words and patterns that indicate schedule queries
    question_patterns = {
        "what", "when", "how", "any", "is", "are",
        "do", "does", "did", "will", "would", "can",
        "could", "should", "tell", "show", "list"
    }

    message_lower = message.lower().split()
    message_set = set(message_lower)

    # Different valid patterns for a relevant query:
    has_intent = any(word in message_set for word in intent_keywords)
    has_action = any(word in message_set for word in action_verbs)
    has_time = any(word in message_set for word in time_expressions)
    has_question = any(word in message_set for word in question_patterns)

    # A query is relevant if it matches any of these patterns:
    # 1. Contains an intent keyword (meeting, task, etc.)
    # 2. Contains both an action verb AND a time expression
    # 3. Contains both a question word AND a time expression
    return has_intent or (has_action and has_time) or (has_question and has_time)


@router.post("/chat")
# Check if the message is relevant to time management
def chat_with_agent(message: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not is_relevant_query(message):
        return {"reply": "I am your time management assistant. I can help you with:\n- Scheduling meetings and appointments\n- Managing tasks and reminders\n- Checking your calendar and availability\n- Setting deadlines and priorities\n\nPlease ask me something related to these topics."}

    from openai.types.chat import ChatCompletionMessage

    today = datetime.now().strftime('%Y-%m-%d')
    now_time = datetime.now().strftime('%H:%M')

    history = get_recent_chat_history(current_user.id, db, n=10)
    inferred_title, inferred_date = infer_context_from_history(history)

    def extract_title_from_message(msg):
        msg = re.sub(r'\b(make|create|schedule|add|set up|organize|plan|update|change|move|delete|remove)\b',
                     '', msg, flags=re.IGNORECASE)
        match = re.search(r'"([^"]+)"', msg)
        if match:
            return match.group(1).strip()
        match = re.search(
            r'(?:the |a )?([\w\s]+? Meeting)', msg, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        match = re.search(
            r'(?:the |a )?([\w\s]+?)(?= (meeting|event|call|appointment))', msg, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        match = re.search(r'(?:the |a )?([A-Z][\w]+)', msg)
        if match:
            return match.group(1).strip()
        return None

    referenced_title = extract_title_from_message(message) or inferred_title
    referenced_date = extract_date_from_message(message) or inferred_date

    # Determine if this is a meeting or task intent (simple heuristic)
    is_task = any(kw in message.lower() for kw in ["task", "todo", "remind", "reminder"]) and not any(
        kw in message.lower() for kw in ["meeting", "call", "appointment", "event"])
    is_meeting = any(kw in message.lower() for kw in [
                     "meeting", "call", "appointment", "event"]) and not is_task

    # Only update context if the message is not a confirmation
    confirmation_words = ["yes", "ok", "confirm",
                          "do it", "schedule it", "that time"]
    is_confirmation = any(word in message.lower()
                          for word in confirmation_words)

    if not is_confirmation and (referenced_title or referenced_date):
        # Only update the relevant context
        if is_task:
            set_last_context_task(current_user.id, db,
                                  referenced_title, referenced_date)
        elif is_meeting:
            set_last_context_meeting(
                current_user.id, db, referenced_title, referenced_date)
        else:
            # fallback: set both only if truly ambiguous
            set_last_context_task(current_user.id, db,
                                  referenced_title, referenced_date)
            set_last_context_meeting(
                current_user.id, db, referenced_title, referenced_date)

    ctx_title_meeting, ctx_date_meeting = get_last_context_meeting(
        current_user.id, db)
    ctx_title_task, ctx_date_task = get_last_context_task(current_user.id, db)

    context_line = ""
    if ctx_date_meeting or ctx_title_meeting:
        context_line = "Current context: "
        if ctx_title_meeting:
            context_line += f"meeting '{ctx_title_meeting}'"
        if ctx_date_meeting:
            context_line += f" on {ctx_date_meeting}"
        context_line += "."
    if ctx_date_task or ctx_title_task:
        context_line += " "
        if ctx_title_task:
            context_line += f"task '{ctx_title_task}'"
        if ctx_date_task:
            context_line += f" on {ctx_date_task}"
        context_line += "."

    messages: list[dict] = [
        {"role": "system",
            "content": f"You are a smart assistant that helps users manage their calendar, tasks, and meetings. Today's date is {today} and the current time is {now_time}. Always use this date and time as the reference for any relative date or time (such as 'today', 'tomorrow', 'next week', etc.). {context_line}"},
        {"role": "user", "content": message},
    ]

    db.add(ChatMessage(user_id=current_user.id, role="user", content=message))
    db.commit()

    def propose_alternative_slots(user_id, db, date, duration_minutes, meeting_data=None):
        free = get_free_time_backend(user_id, date, duration_minutes, db)[
            "free_slots"]
        if free:
            if meeting_data:
                meeting_data = meeting_data.copy()
                meeting_data["proposed_start"] = free[0]["start"]
                meeting_data["proposed_end"] = free[0]["end"]
                set_pending_meeting(user_id, db, meeting_data)
            return f"Available slots on {date}: " + ", ".join([f'{slot["start"]} to {slot["end"]}' for slot in free])
        for i in range(1, 7):
            next_date = (datetime.fromisoformat(date) +
                         timedelta(days=i)).date().isoformat()
            free = get_free_time_backend(user_id, next_date, duration_minutes, db)[
                "free_slots"]
            if free:
                if meeting_data:
                    meeting_data = meeting_data.copy()
                    meeting_data["proposed_start"] = free[0]["start"]
                    meeting_data["proposed_end"] = free[0]["end"]
                    set_pending_meeting(user_id, db, meeting_data)
                return f"No slots available on {date}. Next available on {next_date}: " + ", ".join([f'{slot["start"]} to {slot["end"]}' for slot in free])
        return "No available slots in the next week."

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
            user_message = message.lower()
            if any(kw in user_message for kw in confirmation_words):
                pending_meeting = get_pending_meeting(current_user.id, db)
                pending_task = get_pending_task(current_user.id, db)
                # --- Fix: Only check for task slot conflicts when confirming a task ---
                if pending_task and "start_time" in pending_task and "end_time" in pending_task:
                    start_dt = datetime.fromisoformat(
                        pending_task["start_time"])
                    end_dt = datetime.fromisoformat(pending_task["end_time"])
                    if is_task_time_slot_available(current_user.id, db, start_dt, end_dt):
                        result = create_task_backend(
                            user_id=current_user.id,
                            title=pending_task.get(
                                "title", ctx_title_task or "Untitled Task"),
                            start_time=pending_task["start_time"],
                            end_time=pending_task["end_time"],
                            description=pending_task.get("description"),
                            priority=pending_task.get("priority"),
                            db=db
                        )
                        clear_pending_task(current_user.id, db)
                        db.add(ChatMessage(user_id=current_user.id, role="assistant",
                               content=f"The task '{pending_task.get('title', ctx_title_task or 'Untitled Task')}' has been scheduled for {pending_task['start_time']} to {pending_task['end_time']}!"))
                        db.commit()
                        return {"reply": f"The task '{pending_task.get('title', ctx_title_task or 'Untitled Task')}' has been scheduled for {pending_task['start_time']} to {pending_task['end_time']}!"}
                    else:
                        # Suggest alternative task slots
                        duration = int(
                            (end_dt - start_dt).total_seconds() // 60)
                        alt = get_free_time_for_task_backend(
                            current_user.id, start_dt.date().isoformat(), duration, db)["free_slots"]
                        alt_str = "\n".join([
                            f"- {slot['start'][11:16]} - {slot['end'][11:16]}" for slot in alt
                        ]) if alt else "No available slots."
                        db.add(ChatMessage(user_id=current_user.id, role="assistant",
                               content=f"The time you requested for the task '{pending_task.get('title', ctx_title_task or 'Untitled Task')}' is not available. Here are some available slots for your task:\n{alt_str}"))
                        db.commit()
                        return {"reply": f"The time you requested for the task '{pending_task.get('title', ctx_title_task or 'Untitled Task')}' is not available. Here are some available slots for your task:\n{alt_str}"}
                elif pending_meeting and "proposed_start" in pending_meeting and "proposed_end" in pending_meeting:
                    start_dt = datetime.fromisoformat(
                        pending_meeting["proposed_start"])
                    end_dt = datetime.fromisoformat(
                        pending_meeting["proposed_end"])
                    if is_time_slot_available(current_user.id, db, start_dt, end_dt):
                        result = create_meeting_backend(
                            user_id=current_user.id,
                            title=pending_meeting.get(
                                "title", ctx_title_meeting or "Untitled Meeting"),
                            start_time=pending_meeting["proposed_start"],
                            end_time=pending_meeting["proposed_end"],
                            location=pending_meeting.get("location"),
                            description=pending_meeting.get("description"),
                            db=db
                        )
                        clear_pending_meeting(current_user.id, db)
                        db.add(ChatMessage(user_id=current_user.id, role="assistant",
                               content=f"The meeting '{pending_meeting.get('title', ctx_title_meeting or 'Untitled Meeting')}' has been scheduled for {pending_meeting['proposed_start']} to {pending_meeting['proposed_end']}!"))
                        db.commit()
                        return {"reply": f"The meeting '{pending_meeting.get('title', ctx_title_meeting or 'Untitled Meeting')}' has been scheduled for {pending_meeting['proposed_start']} to {pending_meeting['proposed_end']}!"}
                    else:
                        # Suggest alternative meeting slots
                        duration = int(
                            (end_dt - start_dt).total_seconds() // 60)
                        alt = get_free_time_backend(
                            current_user.id, start_dt.date().isoformat(), duration, db)["free_slots"]
                        alt_str = "\n".join([
                            f"- {slot['start'][11:16]} - {slot['end'][11:16]}" for slot in alt
                        ]) if alt else "No available slots."
                        db.add(ChatMessage(user_id=current_user.id, role="assistant",
                               content=f"The time you requested for the meeting '{pending_meeting.get('title', ctx_title_meeting or 'Untitled Meeting')}' is not available. Here are some available slots for your meeting:\n{alt_str}"))
                        db.commit()
                        return {"reply": f"The time you requested for the meeting '{pending_meeting.get('title', ctx_title_meeting or 'Untitled Meeting')}' is not available. Here are some available slots for your meeting:\n{alt_str}"}
            db.add(ChatMessage(user_id=current_user.id,
                   role="assistant", content=reply.content))
            db.commit()
            return {"reply": reply.content}

        tool_outputs = []
        for tool_call in reply.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            # Use correct context for meetings and tasks
            if name in ["update_meeting", "delete_meeting"]:
                if ("date" not in args or not args["date"]) and ctx_date_meeting:
                    args["date"] = ctx_date_meeting
                if ("title" not in args or not args["title"]) and ctx_title_meeting:
                    args["title"] = ctx_title_meeting
            if name in ["update_task", "delete_task"]:
                if ("date" not in args or not args["date"]) and ctx_date_task:
                    args["date"] = ctx_date_task
                if ("title" not in args or not args["title"]) and ctx_title_task:
                    args["title"] = ctx_title_task

            if name in ["create_meeting", "update_meeting", "create_task", "update_task"]:
                start = args.get("start_time") or args.get("new_start_time")
                end = args.get("end_time") or args.get("new_end_time")
                now_dt = datetime.now()
                start_dt = dateparser.parse(
                    start, settings={"RELATIVE_BASE": now_dt}) if start else None
                if start_dt and start_dt < now_dt:
                    # Instead of auto-rescheduling, prompt the user for confirmation
                    tomorrow_same_time = (now_dt + timedelta(days=1)).replace(
                        hour=start_dt.hour, minute=start_dt.minute, second=0, microsecond=0)
                    # Store pending intent for confirmation
                    if name in ["create_task", "update_task"]:
                        task_data = {
                            "title": args.get("title", ctx_title_task),
                            "description": args.get("description"),
                            "start_time": tomorrow_same_time.isoformat(),
                            "end_time": (tomorrow_same_time + timedelta(minutes=20)).isoformat(),
                            "priority": args.get("priority")
                        }
                        set_pending_task(current_user.id, db, task_data)
                        tool_outputs.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": name,
                            "content": json.dumps({
                                "error": "The requested start time is in the past.",
                                "suggestion": f"Would you like to schedule the task '{args.get('title', ctx_title_task)}' for tomorrow at {tomorrow_same_time.strftime('%H:%M')} instead?"
                            })
                        })
                        continue
                    elif name in ["create_meeting", "update_meeting"]:
                        meeting_data = {
                            "title": args.get("title", ctx_title_meeting),
                            "description": args.get("description"),
                            "location": args.get("location"),
                            "start_time": tomorrow_same_time.isoformat(),
                            "end_time": (tomorrow_same_time + timedelta(minutes=20)).isoformat()
                        }
                        set_pending_meeting(current_user.id, db, meeting_data)
                        tool_outputs.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": name,
                            "content": json.dumps({
                                "error": "The requested start time is in the past.",
                                "suggestion": f"Would you like to schedule the meeting '{args.get('title', ctx_title_meeting)}' for tomorrow at {tomorrow_same_time.strftime('%H:%M')} instead?"
                            })
                        })
                        continue

                if start_dt:
                    if not end:
                        end_dt = start_dt + timedelta(minutes=20)
                        if "end_time" in args:
                            args["end_time"] = end_dt.isoformat()
                        if "new_end_time" in args:
                            args["new_end_time"] = end_dt.isoformat()
                    else:
                        end_dt = dateparser.parse(
                            end, settings={"RELATIVE_BASE": now_dt})
                        if not end_dt or end_dt <= start_dt:
                            end_dt = start_dt + timedelta(minutes=20)
                            if "end_time" in args:
                                args["end_time"] = end_dt.isoformat()
                            if "new_end_time" in args:
                                args["new_end_time"] = end_dt.isoformat()
                if start_dt and end_dt:
                    if name in ["create_meeting", "update_meeting"]:
                        if not is_time_slot_available(current_user.id, db, start_dt, end_dt, exclude_meeting_id=args.get("meeting_id")):
                            duration = int(
                                (end_dt - start_dt).total_seconds() // 60)
                            meeting_data = {
                                "title": args.get("title", ctx_title_meeting),
                                "description": args.get("description"),
                                "location": args.get("location"),
                                "start_time": start_dt.isoformat(),
                                "end_time": end_dt.isoformat()
                            }
                            alt = propose_alternative_slots(
                                current_user.id, db, start_dt.date().isoformat(), duration, meeting_data)
                            tool_outputs.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": name,
                                "content": json.dumps({"error": "Time slot not available", "alternatives": alt})
                            })
                            # Store as pending meeting
                            set_pending_meeting(
                                current_user.id, db, meeting_data)
                            continue
                    elif name in ["create_task", "update_task"]:
                        if not is_task_time_slot_available(current_user.id, db, start_dt, end_dt, exclude_task_id=args.get("task_id")):
                            duration = int(
                                (end_dt - start_dt).total_seconds() // 60)
                            task_data = {
                                "title": args.get("title", ctx_title_task),
                                "description": args.get("description"),
                                "start_time": start_dt.isoformat(),
                                "end_time": end_dt.isoformat(),
                                "priority": args.get("priority")
                            }
                            alt = propose_alternative_slots(
                                current_user.id, db, start_dt.date().isoformat(), duration, task_data)
                            tool_outputs.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": name,
                                "content": json.dumps({"error": "Time slot not available", "alternatives": alt})
                            })
                            # Store as pending task
                            set_pending_task(current_user.id, db, task_data)
                            continue

            if "start_time" in args:
                start_raw = args["start_time"].lower()
                parsed_start = dateparser.parse(args["start_time"], settings={
                                                "RELATIVE_BASE": datetime.now()})
                now = datetime.now()
                if "tomorrow" in start_raw:
                    tomorrow = now + timedelta(days=1)
                    if parsed_start:
                        parsed_start = parsed_start.replace(
                            year=tomorrow.year, month=tomorrow.month, day=tomorrow.day)
                elif re.match(r"^\d{1,2}:\d{2}", start_raw) or re.match(r"^\d{1,2}(:\d{2})?\s*(am|pm)?$", start_raw):
                    if parsed_start:
                        if parsed_start < now:
                            parsed_start = now + timedelta(days=1)
                        parsed_start = parsed_start.replace(
                            year=now.year, month=now.month, day=now.day)
                elif parsed_start and parsed_start < now:
                    parsed_start = now + timedelta(days=1)
                args["start_time"] = parsed_start.isoformat(
                ) if parsed_start else args["start_time"]

            if "end_time" in args:
                end_raw = args["end_time"].lower()
                parsed_end = dateparser.parse(args["end_time"], settings={
                                              "RELATIVE_BASE": datetime.now()})
                now = datetime.now()
                if "tomorrow" in end_raw:
                    tomorrow = now + timedelta(days=1)
                    if parsed_end:
                        parsed_end = parsed_end.replace(
                            year=tomorrow.year, month=tomorrow.month, day=tomorrow.day)
                elif re.match(r"^\d{1,2}:\d{2}", end_raw) or re.match(r"^\d{1,2}(:\d{2})?\s*(am|pm)?$", end_raw):
                    if parsed_end:
                        if parsed_end < now:
                            parsed_end = now + timedelta(days=1)
                        parsed_end = parsed_end.replace(
                            year=now.year, month=now.month, day=now.day)
                elif parsed_end and parsed_end < now:
                    parsed_end = now + timedelta(days=1)
                args["end_time"] = parsed_end.isoformat(
                ) if parsed_end else args["end_time"]

            if "date" in args:
                parsed_date = dateparser.parse(args["date"], settings={
                                               "RELATIVE_BASE": datetime.now()})
                args["date"] = parsed_date.date().isoformat(
                ) if parsed_date else args["date"]

            if name == "create_meeting":
                result = create_meeting_backend(
                    user_id=current_user.id, db=db, **args)
            elif name == "get_free_time":
                result = get_free_time_backend(
                    user_id=current_user.id, db=db, **args)
            elif name == "get_meetings_on_date":
                result = get_meetings_on_date_backend(
                    user_id=current_user.id, db=db, **args)
            elif name == "delete_meeting":
                result = delete_meeting_backend(
                    user_id=current_user.id, db=db, **args)
            elif name == "update_meeting":
                result = update_meeting_backend(
                    user_id=current_user.id, db=db, **args)
            elif name == "create_task":
                result = create_task_backend(
                    user_id=current_user.id, db=db, **args)
            elif name == "get_tasks_on_date":
                result = get_tasks_on_date_backend(
                    user_id=current_user.id, db=db, **args)
            elif name == "delete_task":
                result = delete_task_backend(
                    user_id=current_user.id, db=db, **args)
            elif name == "update_task":
                result = update_task_backend(
                    user_id=current_user.id, db=db, **args)
            elif name == "get_free_time_for_task":
                result = get_free_time_for_task_backend(
                    user_id=current_user.id, db=db, **args)
            else:
                result = {"error": f"Unknown function: {name}"}

            tool_outputs.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": name,
                "content": json.dumps(result)
            })

        messages.extend(tool_outputs)
