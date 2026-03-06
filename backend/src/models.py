from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="pending")  # pending, in_progress, completed
    parent_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    assigned_agent = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    parent = relationship("Task", remote_side=[id], backref="subtasks")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    tool_calls = Column(Text, nullable=True)  # JSON string
    timestamp = Column(DateTime, default=datetime.utcnow)


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(500), nullable=False, unique=True)
    access_level = Column(String(50), nullable=False)  # read, write, execute
    granted_at = Column(DateTime, default=datetime.utcnow)


class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"

    id = Column(Integer, primary_key=True, index=True)
    cron_expression = Column(String(100), nullable=False)
    task_description = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True)
    last_run = Column(DateTime, nullable=True)


class ComputerUsePermission(Base):
    __tablename__ = "computer_use_permissions"

    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(String(50), nullable=False)  # screenshot, mouse, keyboard, app_launch
    granted = Column(Boolean, default=False)
    scope = Column(String(200), nullable=True)  # global or specific app
    granted_at = Column(DateTime, default=datetime.utcnow)
