import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base, get_db
from src.models import Task, Message, Permission, ScheduledJob, ComputerUsePermission


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_create_task(db_session):
    task = Task(
        description="Test task",
        status="pending",
        assigned_agent="main"
    )
    db_session.add(task)
    db_session.commit()

    assert task.id is not None
    assert task.description == "Test task"
    assert task.status == "pending"
