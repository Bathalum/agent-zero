-- Migration: add_agent_zero_fields_to_users.sql
-- Adds Agent Zero configuration fields to account_users table

ALTER TABLE account_users 
ADD COLUMN agent_zero_api_key VARCHAR(255),
ADD COLUMN agent_zero_url VARCHAR(255) DEFAULT 'http://localhost:8080',
ADD COLUMN agent_zero_api_key_retrieved_at TIMESTAMP,
ADD COLUMN agent_zero_instance_id VARCHAR(255);

-- Index for faster lookups
CREATE INDEX idx_account_users_agent_zero_api_key ON account_users(agent_zero_api_key) WHERE agent_zero_api_key IS NOT NULL;
