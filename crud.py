"""خدمات CRUD موحدة للتطبيق"""
from typing import Optional

from sqlalchemy.orm import Session

from database import EmailLog, JobListing, Subscriber
from schemas import (
    JobListingCreate,
    SubscriberCreate,
    SubscriberUpdate,
)


class SubscriberCRUD:
    """عمليات CRUD للمشتركين"""

    @staticmethod
    def create(session: Session, subscriber: SubscriberCreate) -> Subscriber:
        db_subscriber = Subscriber(
            email=subscriber.email,
            preferred_country=subscriber.preferred_country,
            active=True,
        )
        session.add(db_subscriber)
        session.commit()
        session.refresh(db_subscriber)
        return db_subscriber

    @staticmethod
    def get_by_email(session: Session, email: str) -> Optional[Subscriber]:
        return session.query(Subscriber).filter(Subscriber.email == email).first()

    @staticmethod
    def get_by_id(session: Session, subscriber_id: int) -> Optional[Subscriber]:
        return (
            session.query(Subscriber)
            .filter(Subscriber.id == subscriber_id)
            .first()
        )

    @staticmethod
    def get_all(session: Session, active_only: bool = True) -> list[Subscriber]:
        query = session.query(Subscriber)
        if active_only:
            query = query.filter(Subscriber.active == True)
        return query.order_by(Subscriber.created_at.desc()).all()

    @staticmethod
    def update(session: Session, subscriber_id: int, update: SubscriberUpdate) -> Optional[Subscriber]:
        subscriber = session.query(Subscriber).filter(Subscriber.id == subscriber_id).first()
        if not subscriber:
            return None
        if update.preferred_country:
            subscriber.preferred_country = update.preferred_country
        if update.active is not None:
            subscriber.active = update.active
        session.commit()
        session.refresh(subscriber)
        return subscriber

    @staticmethod
    def toggle_active(session: Session, subscriber_id: int) -> Optional[Subscriber]:
        subscriber = session.query(Subscriber).filter(Subscriber.id == subscriber_id).first()
        if not subscriber:
            return None
        subscriber.active = not subscriber.active
        session.commit()
        session.refresh(subscriber)
        return subscriber

    @staticmethod
    def get_by_country(session: Session, country: str) -> list[Subscriber]:
        return (
            session.query(Subscriber)
            .filter(
                (Subscriber.preferred_country == country)
                | (Subscriber.preferred_country == "International")
            )
            .filter(Subscriber.active == True)
            .all()
        )


class JobListingCRUD:
    """عمليات CRUD لعروض العمل"""

    @staticmethod
    def create(session: Session, job: JobListingCreate) -> JobListing:
        db_job = JobListing(**job.model_dump())
        session.add(db_job)
        session.commit()
        session.refresh(db_job)
        return db_job

    @staticmethod
    def get_by_id(session: Session, job_id: int) -> Optional[JobListing]:
        return session.query(JobListing).filter(JobListing.id == job_id).first()

    @staticmethod
    def get_unnotified(session: Session, limit: int = 100) -> list[JobListing]:
        return (
            session.query(JobListing)
            .filter(JobListing.notified == False)
            .order_by(JobListing.created_at.asc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_all(
        session: Session,
        country: Optional[str] = None,
        limit: int = 50,
    ) -> list[JobListing]:
        query = session.query(JobListing)
        if country:
            query = query.filter(JobListing.country == country)
        return query.order_by(JobListing.created_at.desc()).limit(limit).all()

    @staticmethod
    def mark_notified(session: Session, job_id: int) -> Optional[JobListing]:
        job = session.query(JobListing).filter(JobListing.id == job_id).first()
        if not job:
            return None
        job.notified = True
        from datetime import datetime
        job.processed_at = datetime.utcnow()
        session.commit()
        session.refresh(job)
        return job

    @staticmethod
    def check_duplicate(
        session: Session,
        title: str,
        country: str,
    ) -> bool:
        return (
            session.query(JobListing)
            .filter(
                JobListing.title == title,
                JobListing.country == country,
            )
            .first()
            is not None
        )

    @staticmethod
    def get_distinct_countries(session: Session) -> list[str]:
        return [
            row[0]
            for row in session.query(JobListing.country)
            .distinct()
            .order_by(JobListing.country)
            .all()
        ]


class EmailLogCRUD:
    """عمليات CRUD لسجل البريد"""

    @staticmethod
    def create(
        session: Session,
        recipient: str,
        job_id: int,
        status: str,
        error_message: Optional[str] = None,
    ) -> EmailLog:
        log = EmailLog(
            recipient=recipient,
            job_id=job_id,
            status=status,
            error_message=error_message,
        )
        session.add(log)
        session.commit()
        session.refresh(log)
        return log

    @staticmethod
    def get_recent(session: Session, hours: int = 24, limit: int = 50) -> list[EmailLog]:
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return (
            session.query(EmailLog)
            .filter(EmailLog.sent_at >= cutoff)
            .order_by(EmailLog.sent_at.desc())
            .limit(limit)
            .all()
        )
