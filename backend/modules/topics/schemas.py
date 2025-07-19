# backend/modules/topics/schemas.py
"""Pydantic schemas for topics module"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, field_validator, ConfigDict


class TopicBase(BaseModel):
    """Base topic schema"""
    name: str
    description: Optional[str] = None
    color: str = '#3498db'
    parent_topic_id: Optional[UUID] = None
    sort_order: int = 0
    difficulty_level: int = 1
    priority_level: int = 3
    daily_study_goal_minutes: int = 30
    target_completion_date: Optional[datetime] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Topic name cannot be empty')
        if len(v.strip()) > 255:
            raise ValueError('Topic name must be 255 characters or less')
        return v.strip()
    
    @field_validator('color')
    @classmethod
    def validate_color(cls, v: str) -> str:
        if not v.startswith('#') or len(v) != 7:
            return '#3498db'
        try:
            int(v[1:], 16)
            return v
        except ValueError:
            return '#3498db'
    
    @field_validator('difficulty_level', 'priority_level')
    @classmethod
    def validate_levels(cls, v: int) -> int:
        return max(1, min(5, v or 1))


class TopicCreate(TopicBase):
    """Schema for creating a topic"""
    pass


class TopicUpdate(BaseModel):
    """Schema for updating a topic"""
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    parent_topic_id: Optional[UUID] = None
    sort_order: Optional[int] = None
    difficulty_level: Optional[int] = None
    priority_level: Optional[int] = None
    daily_study_goal_minutes: Optional[int] = None
    target_completion_date: Optional[datetime] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError('Topic name cannot be empty')
            if len(v.strip()) > 255:
                raise ValueError('Topic name must be 255 characters or less')
            return v.strip()
        return v


class TopicResponse(BaseModel):
    """Schema for topic response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    color: str
    parent_topic_id: Optional[UUID] = None
    sort_order: int
    total_pdfs: int
    total_exercises: int
    total_notes: int
    study_progress: Decimal
    total_study_time_minutes: int
    estimated_completion_hours: int
    is_active: bool
    is_completed: bool
    completed_at: Optional[datetime] = None
    target_completion_date: Optional[datetime] = None
    daily_study_goal_minutes: int
    difficulty_level: int
    priority_level: int
    created_at: datetime
    updated_at: datetime


class TopicWithStats(TopicResponse):
    """Topic with additional computed statistics"""
    estimated_remaining_hours: int
    completion_percentage: float
    is_overdue: bool
    has_subtopics: bool
    is_root_topic: bool


class TopicSummary(BaseModel):
    """Lightweight topic summary"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    color: str
    study_progress: Decimal
    is_completed: bool


# Goal schemas
class TopicGoalBase(BaseModel):
    """Base topic goal schema"""
    title: str
    description: Optional[str] = None
    goal_type: str  # 'study_time', 'completion', 'exercises', 'notes'
    target_value: Decimal
    target_date: Optional[datetime] = None


class TopicGoalCreate(TopicGoalBase):
    """Schema for creating a topic goal"""
    pass


class TopicGoalUpdate(BaseModel):
    """Schema for updating a topic goal"""
    title: Optional[str] = None
    description: Optional[str] = None
    target_value: Optional[Decimal] = None
    target_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class TopicGoalResponse(BaseModel):
    """Schema for topic goal response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    topic_id: UUID
    user_id: UUID
    title: str
    description: Optional[str] = None
    goal_type: str
    target_value: Decimal
    current_value: Decimal
    target_date: Optional[datetime] = None
    is_active: bool
    is_completed: bool
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    progress_percentage: float
    is_overdue: bool


# API Response schemas
class TopicApiResponse(BaseModel):
    """Topic API response wrapper"""
    success: bool
    message: str
    data: Optional[TopicResponse] = None


class TopicsListResponse(BaseModel):
    """Topics list API response"""
    success: bool
    message: str
    data: List[TopicResponse]
    total: int