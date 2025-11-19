from __future__ import annotations

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Subscription, User, WeeklyReport
from app.schemas import AdminUserPayload, AdminUserResponse
from app.services.email_formatter import format_weekly_report_email
from app.services.email_sender import MailerooService, serialize_email_status
from app.services.report_builder import build_weekly_report_payload
from app.services.scraping import scrape_all_user_leagues

router = APIRouter(prefix="/admin", tags=["admin"])


def _get_current_user(db: Session) -> Optional[User]:
    return db.query(User).order_by(User.created_at.desc()).first()


def _build_user_response(user: User, db: Session) -> AdminUserResponse:
    leagues: List[str] = [
        sub.league_code
        for sub in db.query(Subscription)
        .filter(Subscription.user_id == user.id, Subscription.is_active.is_(True))
        .all()
    ]
    return AdminUserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name or "",
        last_name=user.last_name or "",
        language=user.language,
        favorite_team=user.favorite_team,
        leagues=leagues,
    )


@router.post("/user", response_model=AdminUserResponse)
def upsert_admin_user(payload: AdminUserPayload, db: Session = Depends(get_db)) -> AdminUserResponse:
    user = db.query(User).filter(User.email == payload.email).first()

    if user:
        user.first_name = payload.first_name
        user.last_name = payload.last_name
        user.language = payload.language
        user.favorite_team = payload.favorite_team
        user.is_active = True
    else:
        user = User(
            email=payload.email,
            password_hash="",
            first_name=payload.first_name,
            last_name=payload.last_name,
            language=payload.language,
            favorite_team=payload.favorite_team,
            is_active=True,
        )
        db.add(user)
        db.flush()

    db.query(Subscription).filter(Subscription.user_id == user.id).delete(synchronize_session=False)

    for league_code in payload.leagues:
        if not league_code:
            continue
        sub = Subscription(user_id=user.id, league_code=league_code, is_active=True)
        db.add(sub)

    db.commit()
    db.refresh(user)
    return _build_user_response(user, db)


@router.get("/user", response_model=AdminUserResponse)
def get_admin_user(db: Session = Depends(get_db)) -> AdminUserResponse:
    user = _get_current_user(db)
    if not user:
        raise HTTPException(status_code=404, detail="No user configured yet.")
    return _build_user_response(user, db)


@router.post("/generate_report")
def generate_weekly_report(db: Session = Depends(get_db)) -> dict:
    user = _get_current_user(db)
    if not user:
        raise HTTPException(status_code=400, detail="No user configured yet.")

    scraped = scrape_all_user_leagues(user, db)
    if not scraped.get("leagues"):
        raise HTTPException(status_code=400, detail="No active leagues configured for this user.")

    payload = build_weekly_report_payload(scraped)
    serialized = json.dumps(payload, ensure_ascii=False)

    report = WeeklyReport(user_id=user.id, payload=serialized, email_sent=False, email_status=None)
    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "status": "ok",
        "report_id": report.id,
        "total_leagues": payload.get("total_articles", 0),
    }


@router.post("/send_latest_email")
def send_latest_email(db: Session = Depends(get_db)) -> dict:
    user = _get_current_user(db)
    if not user:
        raise HTTPException(status_code=400, detail="No user configured yet.")

    report = (
        db.query(WeeklyReport)
        .filter(WeeklyReport.user_id == user.id)
        .order_by(WeeklyReport.created_at.desc())
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="No weekly report generated yet.")

    try:
        payload = json.loads(report.payload)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail="Stored report payload is invalid JSON.") from exc

    subject, text_body, html_body = format_weekly_report_email(payload)
    mailer = MailerooService()
    send_result = mailer.send_weekly_email(
        to_email=user.email,
        to_name=user.first_name or user.last_name or user.email,
        subject=subject,
        html=html_body,
        text=text_body,
    )

    report.email_sent = bool(send_result.get("success"))
    report.email_status = serialize_email_status(send_result)
    db.add(report)
    db.commit()

    status = "sent" if send_result.get("success") else "error"
    details = send_result.get("error") or send_result.get("reference_id")
    return {"status": status, "email_sent": report.email_sent, "details": details}
