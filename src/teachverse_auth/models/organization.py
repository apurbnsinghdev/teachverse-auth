# teachverse_auth/models/organization.py
from sqlmodel import SQLModel, Field, Column, JSON
from typing import Optional
from datetime import datetime
import enum

class OrganizationType(str, enum.Enum):
    UNIVERSITY = "university"
    COLLEGE = "college"
    SCHOOL = "school"
    COACHING_CENTER = "coaching_center"
    KINDERGARTEN = "kindergarten"
    ANGANWADI = "anganwadi"
    INDIVIDUAL = "individual"
    ART_STUDIO = "art_studio"
    ARTISAN = "artisan"
    SPORTS_ACADEMY = "sports_academy"
    CORPORATE = "corporate"
    OTHER = "other"

class Organization(SQLModel, table=True):
    __tablename__ = "organizations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, nullable=False)
    type: OrganizationType = Field(nullable=False)
    
    email: str = Field(nullable=False)
    phone: str = Field(nullable=False)
    address: str = Field(nullable=False)
    website: Optional[str] = Field(default=None)
    
    logo_url: Optional[str] = Field(default=None)
    banner_url: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    
    verified: bool = Field(default=False)
    verified_at: Optional[datetime] = Field(default=None)
    verification_documents: dict = Field(default={}, sa_column=Column(JSON))
    
    is_active: bool = Field(default=True)
    suspended_at: Optional[datetime] = Field(default=None)
    suspension_reason: Optional[str] = Field(default=None)
    
    org_metadata: dict = Field(default={}, sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class OrganizationSettings(SQLModel, table=True):
    __tablename__ = "organization_settings"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    organization_id: int = Field(foreign_key="organizations.id", unique=True)
    
    primary_color: Optional[str] = Field(default="#6366f1")
    secondary_color: Optional[str] = Field(default="#f97316")
    custom_domain: Optional[str] = Field(default=None)
    
    allow_public_courses: bool = Field(default=True)
    require_teacher_approval: bool = Field(default=True)
    allow_teacher_hiring: bool = Field(default=False)
    allow_certificates: bool = Field(default=True)
    
    enabled_features: dict = Field(default={}, sa_column=Column(JSON))
    disabled_features: dict = Field(default={}, sa_column=Column(JSON))
    
    webhook_url: Optional[str] = Field(default=None)
    api_key: Optional[str] = Field(default=None)
    api_secret: Optional[str] = Field(default=None)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)