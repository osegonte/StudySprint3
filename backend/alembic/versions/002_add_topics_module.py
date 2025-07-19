# backend/alembic/versions/002_add_topics_module.py
"""Add topics module

Revision ID: 002_add_topics_module
Revises: 001_add_users_module
Create Date: 2024-07-19 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002_add_topics_module'
down_revision = '001_add_users_module'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create topics module tables"""
    
    # Create topics table
    op.create_table('topics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=False),
        sa.Column('parent_topic_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('total_pdfs', sa.Integer(), nullable=False),
        sa.Column('total_exercises', sa.Integer(), nullable=False),
        sa.Column('total_notes', sa.Integer(), nullable=False),
        sa.Column('study_progress', sa.Numeric(5,2), nullable=False),
        sa.Column('total_study_time_minutes', sa.Integer(), nullable=False),
        sa.Column('estimated_completion_hours', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('target_completion_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('daily_study_goal_minutes', sa.Integer(), nullable=False),
        sa.Column('difficulty_level', sa.Integer(), nullable=False),
        sa.Column('priority_level', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_topic_id'], ['topics.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for topics table
    op.create_index('idx_topics_user_id', 'topics', ['user_id'])
    op.create_index('idx_topics_parent_id', 'topics', ['parent_topic_id'])
    op.create_index('idx_topics_user_active', 'topics', ['user_id', 'is_active'])
    op.create_index('idx_topics_user_sort', 'topics', ['user_id', 'sort_order'])
    op.create_index('idx_topics_completion', 'topics', ['is_completed', 'completed_at'])
    
    # Create topic_goals table
    op.create_table('topic_goals',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('goal_type', sa.String(length=50), nullable=False),
        sa.Column('target_value', sa.Numeric(10,2), nullable=False),
        sa.Column('current_value', sa.Numeric(10,2), nullable=False),
        sa.Column('target_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for topic_goals table
    op.create_index('idx_topic_goals_topic', 'topic_goals', ['topic_id'])
    op.create_index('idx_topic_goals_user', 'topic_goals', ['user_id'])
    op.create_index('idx_topic_goals_active', 'topic_goals', ['is_active', 'target_date'])
    
    # Set default values
    op.execute("""
        ALTER TABLE topics ALTER COLUMN color SET DEFAULT '#3498db';
        ALTER TABLE topics ALTER COLUMN sort_order SET DEFAULT 0;
        ALTER TABLE topics ALTER COLUMN total_pdfs SET DEFAULT 0;
        ALTER TABLE topics ALTER COLUMN total_exercises SET DEFAULT 0;
        ALTER TABLE topics ALTER COLUMN total_notes SET DEFAULT 0;
        ALTER TABLE topics ALTER COLUMN study_progress SET DEFAULT 0.0;
        ALTER TABLE topics ALTER COLUMN total_study_time_minutes SET DEFAULT 0;
        ALTER TABLE topics ALTER COLUMN estimated_completion_hours SET DEFAULT 0;
        ALTER TABLE topics ALTER COLUMN is_active SET DEFAULT true;
        ALTER TABLE topics ALTER COLUMN is_completed SET DEFAULT false;
        ALTER TABLE topics ALTER COLUMN daily_study_goal_minutes SET DEFAULT 30;
        ALTER TABLE topics ALTER COLUMN difficulty_level SET DEFAULT 1;
        ALTER TABLE topics ALTER COLUMN priority_level SET DEFAULT 3;
        
        ALTER TABLE topic_goals ALTER COLUMN current_value SET DEFAULT 0.0;
        ALTER TABLE topic_goals ALTER COLUMN is_active SET DEFAULT true;
        ALTER TABLE topic_goals ALTER COLUMN is_completed SET DEFAULT false;
    """)


def downgrade() -> None:
    """Drop topics module tables"""
    op.drop_table('topic_goals')
    op.drop_table('topics')