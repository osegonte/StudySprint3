# backend/alembic/versions/001_add_users_module.py
"""Add users module

Revision ID: 001_add_users_module
Revises: 
Create Date: 2024-07-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_add_users_module'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create users module tables"""
    
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('subscription_tier', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('email_verification_token', sa.String(length=255), nullable=True),
        sa.Column('email_verification_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_reset_token', sa.String(length=255), nullable=True),
        sa.Column('password_reset_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for users table
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_username', 'users', ['username'], unique=True)
    op.create_index('idx_users_email_active', 'users', ['email'], 
                   postgresql_where=sa.text('is_active = true'))
    op.create_index('idx_users_username_active', 'users', ['username'], 
                   postgresql_where=sa.text('is_active = true'))
    
    # Create user_sessions table
    op.create_table('user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_token', sa.String(length=255), nullable=False),
        sa.Column('refresh_token', sa.String(length=255), nullable=True),
        sa.Column('device_info', sa.String(length=500), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('refresh_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revocation_reason', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for user_sessions table
    op.create_index('idx_user_sessions_token', 'user_sessions', ['session_token'], unique=True)
    op.create_index('idx_user_sessions_refresh_token', 'user_sessions', ['refresh_token'], unique=True)
    op.create_index('idx_user_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_index('idx_user_sessions_user_active', 'user_sessions', ['user_id'], 
                   postgresql_where=sa.text('is_active = true'))
    op.create_index('idx_user_sessions_expires', 'user_sessions', ['expires_at'], 
                   postgresql_where=sa.text('is_active = true'))
    
    # Create user_preferences table
    op.create_table('user_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('theme', sa.String(length=20), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('timezone', sa.String(length=50), nullable=False),
        sa.Column('default_study_duration', sa.Integer(), nullable=False),
        sa.Column('default_break_duration', sa.Integer(), nullable=False),
        sa.Column('auto_start_timer', sa.Boolean(), nullable=False),
        sa.Column('daily_study_goal_minutes', sa.Integer(), nullable=False),
        sa.Column('notification_settings', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('study_preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('privacy_settings', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create unique index for user_preferences
    op.create_index('idx_user_preferences_user_id', 'user_preferences', ['user_id'], unique=True)
    
    # Set default values
    op.execute("""
        ALTER TABLE users ALTER COLUMN is_active SET DEFAULT true;
        ALTER TABLE users ALTER COLUMN is_verified SET DEFAULT false;
        ALTER TABLE users ALTER COLUMN is_superuser SET DEFAULT false;
        ALTER TABLE users ALTER COLUMN subscription_tier SET DEFAULT 'free';
        
        ALTER TABLE user_sessions ALTER COLUMN is_active SET DEFAULT true;
        
        ALTER TABLE user_preferences ALTER COLUMN theme SET DEFAULT 'light';
        ALTER TABLE user_preferences ALTER COLUMN language SET DEFAULT 'en';
        ALTER TABLE user_preferences ALTER COLUMN timezone SET DEFAULT 'UTC';
        ALTER TABLE user_preferences ALTER COLUMN default_study_duration SET DEFAULT 25;
        ALTER TABLE user_preferences ALTER COLUMN default_break_duration SET DEFAULT 5;
        ALTER TABLE user_preferences ALTER COLUMN auto_start_timer SET DEFAULT false;
        ALTER TABLE user_preferences ALTER COLUMN daily_study_goal_minutes SET DEFAULT 120;
        ALTER TABLE user_preferences ALTER COLUMN notification_settings SET DEFAULT '{}';
        ALTER TABLE user_preferences ALTER COLUMN study_preferences SET DEFAULT '{}';
        ALTER TABLE user_preferences ALTER COLUMN privacy_settings SET DEFAULT '{}';
    """)


def downgrade() -> None:
    """Drop users module tables"""
    op.drop_table('user_preferences')
    op.drop_table('user_sessions')
    op.drop_table('users')