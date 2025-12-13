"""
Diagnostic script for Portal Backend issues.

Run this to diagnose 500 errors and CORS issues.
"""

import os
import sys
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SupabaseDB
from app.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_environment():
    """Check required environment variables."""
    print("\n=== Environment Variables Check ===")
    required = [
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY',
        'SUPABASE_SERVICE_ROLE_KEY'
    ]
    
    missing = []
    for var in required:
        value = os.getenv(var)
        if not value:
            missing.append(var)
            print(f"❌ {var}: NOT SET")
        else:
            # Mask sensitive values
            masked = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {var}: {masked}")
    
    optional = [
        'SUPABASE_JWT_SECRET',
        'CORS_ORIGINS',
        'AGENT_ZERO_URL'
    ]
    
    for var in optional:
        value = os.getenv(var)
        if value:
            if 'SECRET' in var or 'KEY' in var:
                masked = value[:10] + "..." if len(value) > 10 else value
                print(f"✅ {var}: {masked}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: Not set (using default)")
    
    if missing:
        print(f"\n❌ Missing required variables: {', '.join(missing)}")
        return False
    
    return True


def check_database_connection():
    """Check Supabase database connection."""
    print("\n=== Database Connection Check ===")
    try:
        db = SupabaseDB.get_instance()
        print("✅ Supabase client initialized")
        
        # Try a simple query
        try:
            # Test query - get count (this should work even if table is empty)
            response = db.client.table('account_users').select('id', count='exact').limit(1).execute()
            print(f"✅ Database connection successful")
            print(f"   Table 'account_users' accessible")
            if hasattr(response, 'count'):
                print(f"   Total users: {response.count}")
            return True
        except Exception as e:
            print(f"❌ Database query failed: {e}")
            print(f"   Error type: {type(e).__name__}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to initialize Supabase client: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False


def check_cors_config():
    """Check CORS configuration."""
    print("\n=== CORS Configuration Check ===")
    cors_origins = Config.CORS_ORIGINS
    if cors_origins:
        print(f"✅ CORS origins configured: {', '.join(cors_origins)}")
    else:
        print("⚠️  CORS origins not configured (default: http://localhost:3000)")
    
    # Check if common dev origins are included
    common_origins = [
        'http://localhost:3000',
        'http://localhost:5173',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:5173'
    ]
    
    missing_common = [origin for origin in common_origins if origin not in cors_origins]
    if missing_common:
        print(f"⚠️  Common dev origins not whitelisted: {', '.join(missing_common)}")
    
    return True


def test_user_query(user_id: str = None):
    """Test querying a user."""
    print("\n=== User Query Test ===")
    if not user_id:
        print("⚠️  No user ID provided, skipping user query test")
        print("   To test: python -m app.diagnostics <user_id>")
        return True
    
    try:
        db = SupabaseDB.get_instance()
        user = db.get_user_by_id(user_id)
        
        if user:
            print(f"✅ User found: {user_id}")
            print(f"   Email: {user.get('email', 'N/A')}")
            print(f"   Has API key: {bool(user.get('agent_zero_api_key'))}")
            print(f"   Agent Zero URL: {user.get('agent_zero_url', 'N/A')}")
            return True
        else:
            print(f"⚠️  User not found: {user_id}")
            print("   This is normal if the user hasn't been created yet")
            return True
            
    except Exception as e:
        print(f"❌ Error querying user: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all diagnostics."""
    print("=" * 50)
    print("Portal Backend Diagnostics")
    print("=" * 50)
    
    results = []
    
    # Check environment
    results.append(("Environment", check_environment()))
    
    # Check database
    if results[0][1]:  # Only check DB if env vars are set
        results.append(("Database", check_database_connection()))
    else:
        print("\n⚠️  Skipping database check due to missing environment variables")
        results.append(("Database", False))
    
    # Check CORS
    results.append(("CORS", check_cors_config()))
    
    # Test user query if user ID provided
    user_id = sys.argv[1] if len(sys.argv) > 1 else None
    if user_id:
        results.append(("User Query", test_user_query(user_id)))
    
    # Summary
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n✅ All checks passed!")
    else:
        print("\n❌ Some checks failed. Review the output above.")
        print("\nCommon fixes:")
        print("1. Set missing environment variables")
        print("2. Verify Supabase credentials are correct")
        print("3. Check CORS_ORIGINS includes your frontend origin")
        print("4. Ensure database table 'account_users' exists")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
