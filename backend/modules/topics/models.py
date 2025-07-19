# backend/modules/topics/models.py
"""Topic models for StudySprint 3.0"""

from datetime import datetime
from typing import List, Optional
from decimal import Decimal

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Decimal as SQLDecimal
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
import uuid

from common.database import Base


class Topic(Base):
    """Topic model for organizing study materials"""
    __tablename__ = "topics"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # User relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Topic details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), default='#3498db', nullable=False)  # Hex color code
    
    # Organization and hierarchy
    parent_topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=True, index=True)
    sort_order = Column(Integer, default=0, nullable=False)
    
    # Statistics (auto-calculated from related content)
    total_pdfs = Column(Integer, default=0, nullable=False, server_default='0')
    total_exercises = Column(Integer, default=0, nullable=False, server_default='0')
    total_notes = Column(Integer, default=0, nullable=False, server_default='0')
    study_progress = Column(SQLDecimal(5,2), default=0.0, nullable=False, server_default='0.0')  # Percentage 0-100
    
    # Time tracking
    total_study_time_minutes = Column(Integer, default=0, nullable=False, server_default='0')
    estimated_completion_hours = Column(Integer, default=0, nullable=False, server_default='0')
    
    # Status and completion
    is_active = Column(Boolean, default=True, nullable=False, server_default='true')
    is_completed = Column(Boolean, default=False, nullable=False, server_default='false')
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Goal tracking
    target_completion_date = Column(DateTime(timezone=True), nullable=True)
    daily_study_goal_minutes = Column(Integer, default=30, nullable=False, server_default='30')
    
    # Learning metadata
    difficulty_level = Column(Integer, default=1, nullable=False, server_default='1')  # 1-5 scale
    priority_level = Column(Integer, default=3, nullable=False, server_default='3')    # 1-5 scale
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="topics")
    parent_topic = relationship("Topic", remote_side=[id], back_populates="subtopics")
    subtopics = relationship("Topic", back_populates="parent_topic", cascade="all, delete-orphan")
    
    # Future relationships (will be added when modules are built)
    # pdfs = relationship("PDF", back_populates="topic", cascade="all, delete-orphan")
    # exercises = relationship("Exercise", back_populates="topic")
    # notes = relationship("Note", back_populates="topic")
    # study_sessions = relationship("StudySession", back_populates="topic")
    
    def __repr__(self):
        return f"<Topic(id={self.id}, name={self.name}, user_id={self.user_id})>"
    
    @validates('color')
    def validate_color(self, key, color):
        """Validate hex color format"""
        if not color.startswith('#') or len(color) != 7:
            return '#3498db'  # Default blue
        try:
            int(color[1:], 16)  # Validate hex
            return color
        except ValueError:
            return '#3498db'
    
    @validates('difficulty_level')
    def validate_difficulty(self, key, difficulty):
        """Validate difficulty level is 1-5"""
        return max(1, min(5, difficulty or 1))
    
    @validates('priority_level')
    def validate_priority(self, key, priority):
        """Validate priority level is 1-5"""
        return max(1, min(5, priority or 3))
    
    @validates('study_progress')
    def validate_progress(self, key, progress):
        """Validate progress is 0-100"""
        if progress is None:
            return 0.0
        return max(0.0, min(100.0, float(progress)))
    
    @property
    def is_root_topic(self) -> bool:
        """Check if this is a root topic (no parent)"""
        return self.parent_topic_id is None
    
    @property
    def has_subtopics(self) -> bool:
        """Check if topic has subtopics"""
        return len(self.subtopics) > 0
    
    @property
    def total_content_items(self) -> int:
        """Get total number of content items across all types"""
        return self.total_pdfs + self.total_exercises + self.total_notes
    
    @property
    def completion_percentage(self) -> float:
        """Get completion percentage as float"""
        return float(self.study_progress)
    
    @property
    def is_overdue(self) -> bool:
        """Check if topic is overdue based on target completion date"""
        if not self.target_completion_date or self.is_completed:
            return False
        return datetime.utcnow() > self.target_completion_date
    
    @property
    def estimated_remaining_hours(self) -> int:
        """Calculate estimated remaining study hours"""
        if self.is_completed:
            return 0
        
        completed_hours = (self.total_study_time_minutes / 60) if self.total_study_time_minutes else 0
        remaining_percentage = (100 - self.completion_percentage) / 100
        
        if self.estimated_completion_hours > completed_hours:
            return int((self.estimated_completion_hours - completed_hours) * remaining_percentage)
        else:
            # Estimate based on current progress
            if self.completion_percentage > 0:
                total_estimated = completed_hours / (self.completion_percentage / 100)
                return int(total_estimated - completed_hours)
            return self.estimated_completion_hours
    
    def update_statistics(self):
        """Update topic statistics (will be called when related content changes)"""
        # This method will be expanded when we add relationships to other modules
        # For now, it's a placeholder for future functionality
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self):
        """Mark topic as completed"""
        self.is_completed = True
        self.completed_at = datetime.utcnow()
        self.study_progress = 100.0
        self.updated_at = datetime.utcnow()
    
    def mark_incomplete(self):
        """Mark topic as incomplete"""
        self.is_completed = False
        self.completed_at = None
        self.updated_at = datetime.utcnow()


class TopicGoal(Base):
    """Topic-specific goals and milestones"""
    __tablename__ = "topic_goals"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Relationships
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Goal details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    goal_type = Column(String(50), nullable=False)  # 'study_time', 'completion', 'exercises', 'notes'
    
    # Target and progress
    target_value = Column(SQLDecimal(10,2), nullable=False)
    current_value = Column(SQLDecimal(10,2), default=0.0, nullable=False, server_default='0.0')
    target_date = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, server_default='true')
    is_completed = Column(Boolean, default=False, nullable=False, server_default='false')
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    topic = relationship("Topic")
    user = relationship("User")
    
    def __repr__(self):
        return f"<TopicGoal(id={self.id}, title={self.title}, topic_id={self.topic_id})>"
    
    @property
    def progress_percentage(self) -> float:
        """Calculate goal completion percentage"""
        if self.target_value <= 0:
            return 0.0
        return min(100.0, (float(self.current_value) / float(self.target_value)) * 100)
    
    @property
    def is_overdue(self) -> bool:
        """Check if goal is overdue"""
        if not self.target_date or self.is_completed:
            return False
        return datetime.utcnow() > self.target_date
    
    def update_progress(self, new_value: float):
        """Update goal progress"""
        self.current_value = new_value
        self.updated_at = datetime.utcnow()
        
        # Check if goal is completed
        if self.current_value >= self.target_value and not self.is_completed:
            self.is_completed = True
            self.completed_at = datetime.utcnow()


# Database indexes for performance
"""
-- Performance indexes to be created in migration:
CREATE INDEX idx_topics_user_id ON topics(user_id);
CREATE INDEX idx_topics_parent_id ON topics(parent_topic_id);
CREATE INDEX idx_topics_user_active ON topics(user_id, is_active);
CREATE INDEX idx_topics_user_sort ON topics(user_id, sort_order);
CREATE INDEX idx_topics_completion ON topics(is_completed, completed_at);

CREATE INDEX idx_topic_goals_topic ON topic_goals(topic_id);
CREATE INDEX idx_topic_goals_user ON topic_goals(user_id);
CREATE INDEX idx_topic_goals_active ON topic_goals(is_active, target_date);
"""