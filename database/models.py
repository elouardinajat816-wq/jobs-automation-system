from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class JobListing(Base):
    __tablename__ = "jobs_feed"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    country = Column(String(100), nullable=False, index=True)
    details = Column(Text, nullable=False)
    contact_link = Column(String(500), nullable=True)
    source_email = Column(String(255), nullable=True)
    notified = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)


class Subscriber(Base):
    __tablename__ = "subscribers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    preferred_country = Column(String(100), nullable=False)
    active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    recipient = Column(String(255), nullable=False, index=True)
    job_id = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow, index=True)
