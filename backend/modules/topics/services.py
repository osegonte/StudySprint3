# backend/modules/topics/services.py
"""Topics service for business logic and database operations"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from common.errors import ResourceNotFoundError, ValidationError, BusinessLogicError
from .models import Topic, TopicGoal
from .schemas import TopicCreate, TopicUpdate, TopicGoalCreate, TopicGoalUpdate


class TopicService:
    """Service for topic management operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_topic(self, user_id: UUID, topic_data: TopicCreate) -> Topic:
        """Create a new topic"""
        
        # Check if parent topic exists and belongs to user
        if topic_data.parent_topic_id:
            parent = await self.get_topic_by_id(topic_data.parent_topic_id, user_id)
            if not parent:
                raise ResourceNotFoundError("Parent topic", str(topic_data.parent_topic_id))
        
        # Create topic
        topic = Topic(
            user_id=user_id,
            name=topic_data.name,
            description=topic_data.description,
            color=topic_data.color,
            parent_topic_id=topic_data.parent_topic_id,
            sort_order=topic_data.sort_order,
            difficulty_level=topic_data.difficulty_level,
            priority_level=topic_data.priority_level,
            daily_study_goal_minutes=topic_data.daily_study_goal_minutes,
            target_completion_date=topic_data.target_completion_date
        )
        
        self.db.add(topic)
        await self.db.commit()
        await self.db.refresh(topic)
        
        return topic
    
    async def get_topic_by_id(self, topic_id: UUID, user_id: UUID) -> Optional[Topic]:
        """Get topic by ID and verify ownership"""
        query = select(Topic).where(
            and_(Topic.id == topic_id, Topic.user_id == user_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_topic_with_subtopics(self, topic_id: UUID, user_id: UUID) -> Optional[Topic]:
        """Get topic with loaded subtopics"""
        query = select(Topic).options(
            selectinload(Topic.subtopics)
        ).where(
            and_(Topic.id == topic_id, Topic.user_id == user_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def has_subtopics(self, topic_id: UUID, user_id: UUID) -> bool:
        """Check if topic has subtopics without loading them"""
        query = select(Topic.id).where(
            and_(Topic.parent_topic_id == topic_id, Topic.user_id == user_id)
        ).limit(1)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def get_user_topics(
        self, 
        user_id: UUID,
        parent_id: Optional[UUID] = None,
        include_completed: bool = True,
        sort_by: str = "sort_order"
    ) -> List[Topic]:
        """Get all topics for a user"""
        query = select(Topic).where(Topic.user_id == user_id)
        
        # Filter by parent
        if parent_id is not None:
            query = query.where(Topic.parent_topic_id == parent_id)
        else:
            # Get root topics only
            query = query.where(Topic.parent_topic_id.is_(None))
        
        # Filter completed
        if not include_completed:
            query = query.where(Topic.is_completed == False)
        
        # Sort
        if sort_by == "name":
            query = query.order_by(asc(Topic.name))
        elif sort_by == "created_at":
            query = query.order_by(desc(Topic.created_at))
        elif sort_by == "progress":
            query = query.order_by(desc(Topic.study_progress))
        else:  # sort_order
            query = query.order_by(asc(Topic.sort_order), asc(Topic.name))
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update_topic(self, topic_id: UUID, user_id: UUID, topic_data: TopicUpdate) -> Topic:
        """Update topic"""
        topic = await self.get_topic_by_id(topic_id, user_id)
        if not topic:
            raise ResourceNotFoundError("Topic", str(topic_id))
        
        # Check if parent topic exists and isn't the topic itself
        if topic_data.parent_topic_id:
            if topic_data.parent_topic_id == topic_id:
                raise ValidationError("Topic cannot be its own parent")
            
            parent = await self.get_topic_by_id(topic_data.parent_topic_id, user_id)
            if not parent:
                raise ResourceNotFoundError("Parent topic", str(topic_data.parent_topic_id))
        
        # Update fields
        update_data = topic_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(topic, field) and value is not None:
                setattr(topic, field, value)
        
        topic.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(topic)
        
        return topic
    
    async def delete_topic(self, topic_id: UUID, user_id: UUID) -> bool:
        """Delete topic and all subtopics"""
        topic = await self.get_topic_by_id(topic_id, user_id)
        if not topic:
            raise ResourceNotFoundError("Topic", str(topic_id))
        
        # Check if topic has content that prevents deletion
        if topic.total_pdfs > 0 or topic.total_exercises > 0 or topic.total_notes > 0:
            raise BusinessLogicError(
                "Cannot delete topic with existing content. Please move or delete content first."
            )
        
        await self.db.delete(topic)
        await self.db.commit()
        
        return True
    
    async def toggle_topic_completion(self, topic_id: UUID, user_id: UUID) -> Topic:
        """Toggle topic completion status"""
        topic = await self.get_topic_by_id(topic_id, user_id)
        if not topic:
            raise ResourceNotFoundError("Topic", str(topic_id))
        
        if topic.is_completed:
            topic.mark_incomplete()
        else:
            topic.mark_completed()
        
        await self.db.commit()
        await self.db.refresh(topic)
        
        return topic
    
    async def update_topic_statistics(self, topic_id: UUID) -> Topic:
        """Update topic statistics (will be called when content changes)"""
        # This is a placeholder for when we integrate with other modules
        # For now, just update the timestamp
        query = select(Topic).where(Topic.id == topic_id)
        result = await self.db.execute(query)
        topic = result.scalar_one_or_none()
        
        if topic:
            topic.update_statistics()
            await self.db.commit()
            await self.db.refresh(topic)
        
        return topic
    
    async def search_topics(self, user_id: UUID, search_term: str) -> List[Topic]:
        """Search topics by name or description"""
        query = select(Topic).where(
            and_(
                Topic.user_id == user_id,
                or_(
                    Topic.name.ilike(f"%{search_term}%"),
                    Topic.description.ilike(f"%{search_term}%")
                )
            )
        ).order_by(asc(Topic.name))
        
        result = await self.db.execute(query)
        return result.scalars().all()


class TopicGoalService:
    """Service for topic goal management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_goal(self, topic_id: UUID, user_id: UUID, goal_data: TopicGoalCreate) -> TopicGoal:
        """Create a new topic goal"""
        
        # Verify topic exists and belongs to user
        topic_service = TopicService(self.db)
        topic = await topic_service.get_topic_by_id(topic_id, user_id)
        if not topic:
            raise ResourceNotFoundError("Topic", str(topic_id))
        
        goal = TopicGoal(
            topic_id=topic_id,
            user_id=user_id,
            title=goal_data.title,
            description=goal_data.description,
            goal_type=goal_data.goal_type,
            target_value=goal_data.target_value,
            target_date=goal_data.target_date
        )
        
        self.db.add(goal)
        await self.db.commit()
        await self.db.refresh(goal)
        
        return goal
    
    async def get_topic_goals(self, topic_id: UUID, user_id: UUID, active_only: bool = True) -> List[TopicGoal]:
        """Get all goals for a topic"""
        query = select(TopicGoal).where(
            and_(TopicGoal.topic_id == topic_id, TopicGoal.user_id == user_id)
        )
        
        if active_only:
            query = query.where(TopicGoal.is_active == True)
        
        query = query.order_by(desc(TopicGoal.created_at))
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update_goal_progress(self, goal_id: UUID, user_id: UUID, new_value: float) -> TopicGoal:
        """Update goal progress"""
        query = select(TopicGoal).where(
            and_(TopicGoal.id == goal_id, TopicGoal.user_id == user_id)
        )
        result = await self.db.execute(query)
        goal = result.scalar_one_or_none()
        
        if not goal:
            raise ResourceNotFoundError("Goal", str(goal_id))
        
        goal.update_progress(new_value)
        await self.db.commit()
        await self.db.refresh(goal)
        
        return goal