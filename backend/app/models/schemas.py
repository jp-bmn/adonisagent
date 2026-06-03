"""
Pydantic schemas for all Adonis entities.
Request/response models for every API endpoint are defined here.
"""
from datetime import date, datetime
from typing import Literal, Optional
from pydantic import BaseModel, HttpUrl, field_validator
import uuid


# ---------------------------------------------------------------------------
# Enums / literals
# ---------------------------------------------------------------------------

SignalType = Literal[
    "leadership_change",
    "rcm_hiring_spike",
    "epic_go_live",
    "post_golive_friction",
    "ma_acquisition",
    "vendor_change",
    "vendor_dispute",
    "restructuring",
    "new_hospital_launch",
    "financial_event",
    "ai_adoption_outside_rcm",
    "automation_proof",
    "named_automation_owner",
    "thought_leadership",
    "filtered_out",
]

TierType = Literal["urgent", "worth_knowing", "filtered_out"]
ReviewStatusType = Literal["pending", "approved", "dismissed"]


# ---------------------------------------------------------------------------
# Hospital
# ---------------------------------------------------------------------------

class HospitalBase(BaseModel):
    name: str
    website_url: Optional[str] = None
    division_note: Optional[str] = None


class HospitalCreate(HospitalBase):
    pass


class Hospital(HospitalBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class HospitalWithAEs(Hospital):
    ae_users: list["AEUserBrief"] = []


# ---------------------------------------------------------------------------
# AE User
# ---------------------------------------------------------------------------

class AEUserBrief(BaseModel):
    id: uuid.UUID
    name: str
    is_admin: bool = False

    class Config:
        from_attributes = True


class AEUser(BaseModel):
    id: uuid.UUID
    name: str
    slack_user_id: Optional[str] = None
    is_admin: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class AEUserWithStats(AEUser):
    hospitals: list[Hospital] = []
    new_signals_this_week: int = 0
    last_viewed_digest: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Signal
# ---------------------------------------------------------------------------

class SignalCreate(BaseModel):
    hospital_id: uuid.UUID
    signal_type: SignalType
    tier: TierType
    confidence_score: float = 0.0
    title: Optional[str] = None
    summary: Optional[str] = None
    source_url: Optional[HttpUrl] = None
    source_name: Optional[str] = None
    published_date: Optional[date] = None

    # Validation
    @field_validator("title")
    @classmethod
    def title_max_length(cls, v):
        if v and len(v) > 200:
            raise ValueError("title must be 200 characters or fewer")
        return v

    @field_validator("summary")
    @classmethod
    def summary_max_length(cls, v):
        if v and len(v) > 1000:
            raise ValueError("summary must be 1000 characters or fewer")
        return v


class Signal(BaseModel):
    id: uuid.UUID
    hospital_id: uuid.UUID
    signal_type: str
    tier: TierType
    confidence_score: float
    review_status: Optional[ReviewStatusType] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    source_url: Optional[str] = None
    source_name: Optional[str] = None
    published_date: Optional[date] = None
    created_at: datetime
    included_in_digest: bool = False
    urgent_sent: bool = False

    class Config:
        from_attributes = True


class SignalWithHospital(Signal):
    hospital_name: Optional[str] = None


class SignalReviewRequest(BaseModel):
    action: Literal["approved", "dismissed"]
    reviewer_id: str


# ---------------------------------------------------------------------------
# Contact
# ---------------------------------------------------------------------------

class ContactCreate(BaseModel):
    hospital_id: uuid.UUID
    full_name: str
    role: Optional[str] = None
    prior_employer: Optional[str] = None
    linkedin_url: Optional[str] = None
    linkedin_verified: bool = False

    @field_validator("full_name")
    @classmethod
    def name_max_length(cls, v):
        if len(v) > 200:
            raise ValueError("full_name must be 200 characters or fewer")
        return v


class ContactUpdate(BaseModel):
    role: Optional[str] = None
    prior_employer: Optional[str] = None
    linkedin_url: Optional[str] = None
    linkedin_verified: Optional[bool] = None
    is_active: Optional[bool] = None


class ContactLinkedInVerify(BaseModel):
    linkedin_url: str


class Contact(BaseModel):
    id: uuid.UUID
    hospital_id: uuid.UUID
    full_name: str
    role: Optional[str] = None
    prior_employer: Optional[str] = None
    linkedin_url: Optional[str] = None
    linkedin_verified: bool = False
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Digest
# ---------------------------------------------------------------------------

class Digest(BaseModel):
    id: uuid.UUID
    ae_id: Optional[uuid.UUID] = None
    sent_at: Optional[datetime] = None
    slack_message_ts: Optional[str] = None
    week_start: Optional[date] = None
    week_end: Optional[date] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Digest View
# ---------------------------------------------------------------------------

class DigestViewCreate(BaseModel):
    digest_id: uuid.UUID
    ae_id: uuid.UUID
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None


class DigestViewResponse(BaseModel):
    recorded: bool


# ---------------------------------------------------------------------------
# Agent Run
# ---------------------------------------------------------------------------

class AgentRun(BaseModel):
    id: uuid.UUID
    run_at: datetime
    hospitals_checked: int = 0
    signals_found: int = 0
    signals_new: int = 0
    rules_engine_hits: int = 0
    errors: Optional[dict] = None
    duration_ms: Optional[int] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Hospital-AE Assignment
# ---------------------------------------------------------------------------

class HospitalAEAssignment(BaseModel):
    hospital_id: uuid.UUID
    ae_id: uuid.UUID


# ---------------------------------------------------------------------------
# Classify
# ---------------------------------------------------------------------------

class ClassifyRequest(BaseModel):
    article_text: str
    hospital_name: str
    source_name: str
    signal_type_hint: Optional[SignalType] = None


class ClassifyResponse(BaseModel):
    signal_type: str
    tier: TierType
    confidence_score: float
    title: str
    summary: str
    why_relevant: str
    classification_source: Literal["rules_engine", "claude_api", "error"]


# ---------------------------------------------------------------------------
# Status / Health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    service: str


class StatusResponse(BaseModel):
    api_version: str
    last_scraper_run: Optional[datetime] = None
    next_scraper_run: Optional[datetime] = None
    total_signals_stored: int
    total_hospitals_monitored: int
    pending_review_count: int


# Forward refs
HospitalWithAEs.model_rebuild()
