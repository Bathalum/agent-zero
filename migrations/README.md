# Database Migrations

This directory contains SQL migration scripts for the Portal Backend database schema.

## Required Migrations

### 1. Add Agent Zero Fields (`add_agent_zero_fields_to_users.sql`)

Adds basic Agent Zero configuration fields to the `account_users` table.

**Run this migration first.**

### 2. Add Agent Zero Credentials (`add_agent_zero_credentials.sql`)

Adds username and encrypted password fields for Agent Zero authentication.

**Run this migration second.**

## How to Run Migrations

### Option 1: Supabase Dashboard (Recommended)

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Copy the contents of the migration file
4. Paste into the SQL Editor
5. Click **Run** to execute

### Option 2: Supabase CLI

```bash
# If you have Supabase CLI installed
supabase db push
```

### Option 3: Direct SQL Connection

If you have direct database access, you can run the SQL directly using `psql` or your preferred SQL client.

## Migration Order

**Important:** Run migrations in this order:

1. `add_agent_zero_fields_to_users.sql` - Adds API key and URL fields
2. `add_agent_zero_credentials.sql` - Adds username and encrypted password fields

## Verifying Migrations

After running migrations, verify the columns exist:

```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'account_users' 
AND column_name LIKE 'agent_zero%';
```

You should see:
- `agent_zero_api_key`
- `agent_zero_url`
- `agent_zero_api_key_retrieved_at`
- `agent_zero_instance_id`
- `agent_zero_username`
- `agent_zero_password_encrypted`

## Troubleshooting

### Error: "Could not find the 'agent_zero_password_encrypted' column"

This means the `add_agent_zero_credentials.sql` migration hasn't been run. Run it in your Supabase SQL Editor.

### Error: "Could not find the 'agent_zero_api_key' column"

This means the `add_agent_zero_fields_to_users.sql` migration hasn't been run. Run it first.

## Migration Files

- `add_agent_zero_fields_to_users.sql` - Basic Agent Zero fields
- `add_agent_zero_credentials.sql` - Credential storage fields
