# Problem
Send automated emails to users

# Solution
Execute the n8n email workflow via bridge:

```bash
python /a0/instruments/custom/n8n/bridge.py email_workflow \
  --recipient "user@example.com" \
  --template "welcome" \
  --data '{"name":"John","company":"Acme Inc"}'
```

## Parameters
- `recipient`: Email address of the recipient (required)
- `template`: Email template name (e.g., "welcome", "notification", "reminder")
- `data`: JSON string with template variables (optional)

## Expected Output
- Success: "✓ Send automated emails: Email sent successfully to user@example.com (ID: 12345)"
- Error: "✗ Send automated emails Error: Invalid recipient email address"

## Notes
- Make sure the recipient email is valid
- Template must exist in n8n workflow configuration
- Data should be valid JSON with variables needed by the template

