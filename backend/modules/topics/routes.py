# backend/modules/topics/routes.py
"""API routes for topics module"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from common.database import get_async_db
from common.errors import StudySprintException
from modules.users.routes import get_current_user
from modules.users.models import User
from .models import Topic
from .schemas import (
    TopicCreate, TopicUpdate, TopicResponse, TopicWithStats, TopicSummary,
    TopicGoalCreate, TopicGoalUpdate, TopicGoalResponse,
    TopicApiResponse, TopicsListResponse
)
from .services import TopicService, TopicGoalService

router = APIRouter()


# Topic CRUD endpoints
@router.post("", response_model=TopicApiResponse, status_code=status.HTTP_201_CREATED)
async def create_topic(
    topic_data: TopicCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new topic"""
    try:
        topic_service = TopicService(db)
        topic = await topic_service.create_topic(current_user.id, topic_data)
        
        return TopicApiResponse(
            success=True,
            message="Topic created successfully",
            data=TopicResponse.model_validate(topic)
        )
    except StudySprintException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create topic"
        )


@router.get("", response_model=TopicsListResponse)
async def get_topics(
    parent_id: Optional[UUID] = Query(None, description="Filter by parent topic ID"),
    include_completed: bool = Query(True, description="Include completed topics"),
    sort_by: str = Query("sort_order", description="Sort by: sort_order, name, created_at, progress"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get all topics for current user"""
    try:
        topic_service = TopicService(db)
        topics = await topic_service.get_user_topics(
            user_id=current_user.id,
            parent_id=parent_id,
            include_completed=include_completed,
            sort_by=sort_by
        )
        
        topic_responses = [TopicResponse.model_validate(topic) for topic in topics]
        
        return TopicsListResponse(
            success=True,
            message="Topics retrieved successfully",
            data=topic_responses,
            total=len(topic_responses)
        )
    except StudySprintException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve topics"
        )


@router.get("/search")
async def search_topics(
    q: str = Query(..., min_length=1, description="Search term"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Search topics by name or description"""
    try:
        topic_service = TopicService(db)
        topics = await topic_service.search_topics(current_user.id, q)
        
        return TopicsListResponse(
            success=True,
            message=f"Found {len(topics)} topics",
            data=[TopicSummary.model_validate(topic) for topic in topics],
            total=len(topics)
        )
    except StudySprintException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


@router.get("/{topic_id}", response_model=TopicApiResponse)
async def get_topic(
    topic_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get specific topic with statistics"""
    try:
        topic_service = TopicService(db)
        topic = await topic_service.get_topic_by_id(topic_id, current_user.id)
        
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found"
            )
        
        # Convert to response with computed stats
        topic_data = TopicResponse.model_validate(topic)
        has_subtopics = await topic_service.has_subtopics(topic_id, current_user.id)
        
        topic_with_stats = TopicWithStats(
            **topic_data.model_dump(),
            estimated_remaining_hours=topic.estimated_remaining_hours,
            completion_percentage=topic.completion_percentage,
            is_overdue=topic.is_overdue,
            has_subtopics=has_subtopics,
            is_root_topic=topic.is_root_topic
        )
        
        return TopicApiResponse(
            success=True,
            message="Topic retrieved successfully",
            data=topic_with_stats
        )
    except StudySprintException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve topic"
        )


@router.put("/{topic_id}", response_model=TopicApiResponse)
async def update_topic(
    topic_id: UUID,
    topic_data: TopicUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Update topic"""
    try:
        topic_service = TopicService(db)
        topic = await topic_service.update_topic(topic_id, current_user.id, topic_data)
        
        return TopicApiResponse(
            success=True,
            message="Topic updated successfully",
            data=TopicResponse.model_validate(topic)
        )
    except StudySprintException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update topic"
        )


@router.delete("/{topic_id}")
async def delete_topic(
    topic_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Delete topic"""
    try:
        topic_service = TopicService(db)
        success = await topic_service.delete_topic(topic_id, current_user.id)
        
        return {
            "success": success,
            "message": "Topic deleted successfully"
        }
    except StudySprintException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete topic"
        )


@router.post("/{topic_id}/toggle-completion", response_model=TopicApiResponse)
async def toggle_topic_completion(
    topic_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Toggle topic completion status"""
    try:
        topic_service = TopicService(db)
        topic = await topic_service.toggle_topic_completion(topic_id, current_user.id)
        
        action = "completed" if topic.is_completed else "marked as incomplete"
        
        return TopicApiResponse(
            success=True,
            message=f"Topic {action} successfully",
            data=TopicResponse.model_validate(topic)
        )
    except StudySprintException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update topic completion"
        )


# Topic Goal endpoints
@router.post("/{topic_id}/goals", response_model=TopicGoalResponse, status_code=status.HTTP_201_CREATED)
async def create_topic_goal(
    topic_id: UUID,
    goal_data: TopicGoalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new topic goal"""
    try:
        goal_service = TopicGoalService(db)
        goal = await goal_service.create_goal(topic_id, current_user.id, goal_data)
        
        # Add computed properties
        goal_response = TopicGoalResponse.model_validate(goal)
        goal_response.progress_percentage = goal.progress_percentage
        goal_response.is_overdue = goal.is_overdue
        
        return goal_response
    except StudySprintException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create goal"
        )


@router.get("/{topic_id}/goals", response_model=List[TopicGoalResponse])
async def get_topic_goals(
    topic_id: UUID,
    active_only: bool = Query(True, description="Show only active goals"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get all goals for a topic"""
    try:
        goal_service = TopicGoalService(db)
        goals = await goal_service.get_topic_goals(topic_id, current_user.id, active_only)
        
        # Add computed properties to each goal
        goal_responses = []
        for goal in goals:
            goal_response = TopicGoalResponse.model_validate(goal)
            goal_response.progress_percentage = goal.progress_percentage
            goal_response.is_overdue = goal.is_overdue
            goal_responses.append(goal_response)
        
        return goal_responses
    except StudySprintException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve goals"
        )


@router.put("/goals/{goal_id}/progress")
async def update_goal_progress(
    goal_id: UUID,
    progress_data: dict,  # {"value": float}
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Update goal progress"""
    try:
        goal_service = TopicGoalService(db)
        goal = await goal_service.update_goal_progress(
            goal_id, 
            current_user.id, 
            progress_data.get("value", 0)
        )
        
        goal_response = TopicGoalResponse.model_validate(goal)
        goal_response.progress_percentage = goal.progress_percentage
        goal_response.is_overdue = goal.is_overdue
        
        return {
            "success": True,
            "message": "Goal progress updated successfully",
            "data": goal_response
        }
    except StudySprintException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update goal progress"
        )


# Statistics endpoints
@router.get("/{topic_id}/stats")
async def get_topic_statistics(
    topic_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get detailed topic statistics"""
    try:
        topic_service = TopicService(db)
        topic = await topic_service.get_topic_by_id(topic_id, current_user.id)
        
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found"
            )
        
        # Get goals for this topic
        goal_service = TopicGoalService(db)
        goals = await goal_service.get_topic_goals(topic_id, current_user.id)
        
        stats = {
            "topic_id": topic_id,
            "total_content_items": topic.total_content_items,
            "completion_percentage": topic.completion_percentage,
            "estimated_remaining_hours": topic.estimated_remaining_hours,
            "is_overdue": topic.is_overdue,
            "study_time_minutes": topic.total_study_time_minutes,
            "active_goals": len([g for g in goals if g.is_active]),
            "completed_goals": len([g for g in goals if g.is_completed]),
            "has_subtopics": topic.has_subtopics,
            "difficulty_level": topic.difficulty_level,
            "priority_level": topic.priority_level
        }
        
        return {
            "success": True,
            "message": "Topic statistics retrieved successfully",
            "data": stats
        }
    except StudySprintException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve topic statistics"
        )