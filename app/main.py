from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_

from database import db, JobListing, Subscriber

app = FastAPI(title="Job Automation Dashboard", version="1.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
def dashboard(request: Request, country: str | None = None):
    session = db.get_session()
    try:
        query = session.query(JobListing)
        if country:
            query = query.filter(JobListing.country == country)

        jobs = query.order_by(JobListing.created_at.desc()).limit(50).all()
        countries = [row[0] for row in session.query(JobListing.country).distinct().order_by(JobListing.country).all()]

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "jobs": jobs,
                "countries": countries,
                "selected_country": country,
            },
        )
    finally:
        session.close()


@app.get("/subscribers")
def subscribers(request: Request):
    session = db.get_session()
    try:
        subs = session.query(Subscriber).order_by(Subscriber.created_at.desc()).all()
        return templates.TemplateResponse(
            "subscribers.html",
            {
                "request": request,
                "subscribers": subs,
            },
        )
    finally:
        session.close()


@app.post("/subscribers")
def add_subscriber(
    email: str = Form(...),
    preferred_country: str = Form(...),
):
    session = db.get_session()
    try:
        existing = session.query(Subscriber).filter(Subscriber.email == email).first()
        if existing:
            existing.preferred_country = preferred_country
            existing.active = True
        else:
            session.add(Subscriber(email=email, preferred_country=preferred_country, active=True))
        session.commit()
    finally:
        session.close()

    return RedirectResponse(url="/subscribers", status_code=303)


@app.post("/subscribers/{subscriber_id}/toggle")
def toggle_subscriber(subscriber_id: int):
    session = db.get_session()
    try:
        sub = session.query(Subscriber).filter(Subscriber.id == subscriber_id).first()
        if sub:
            sub.active = not sub.active
            session.commit()
    finally:
        session.close()

    return RedirectResponse(url="/subscribers", status_code=303)


@app.get("/health")
def health():
    return {"status": "ok"}
