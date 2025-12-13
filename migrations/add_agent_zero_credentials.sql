-- Migration: add_agent_zero_credentials.sql
-- Adds Agent Zero username and encrypted password fields to account_users table

ALTER TABLE account_users 
ADD COLUMN agent_zero_username VARCHAR(255),
ADD COLUMN agent_zero_password_encrypted TEXT;

-- Index for faster lookups
CREATE INDEX idx_account_users_agent_zero_username ON account_users(agent_zero_username) WHERE agent_zero_username IS NOT NULL;
