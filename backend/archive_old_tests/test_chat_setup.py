#!/usr/bin/env python3
"""
Simple test script to verify chat setup without full server startup
"""
import os
import sys
sys.path.append('.')

from app.utils.config import get_settings

def test_config():
    """Test configuration loading"""
    print("🔧 Testing configuration...")
    settings = get_settings()
    
    print(f"✅ Supabase URL: {settings.supabase_url[:20]}...")
    print(f"✅ OpenAI API Key: {'***' + settings.openai_api_key[-4:] if settings.openai_api_key else 'NOT SET'}")
    print(f"✅ OpenAI Model: {settings.openai_model}")
    
    # Check for DATABASE_URL
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        print(f"✅ DATABASE_URL: {db_url[:20]}...")
    else:
        print("⚠️  DATABASE_URL not set - will need manual configuration")
    
    return True

def test_imports():
    """Test that all required packages can be imported"""
    print("\n📦 Testing package imports...")
    
    try:
        from langchain_openai import ChatOpenAI
        print("✅ langchain-openai")
    except ImportError as e:
        print(f"❌ langchain-openai: {e}")
        return False
    
    try:
        from langchain_community.agent_toolkits import SQLDatabaseToolkit
        from langchain_community.utilities import SQLDatabase
        print("✅ langchain-community")
    except ImportError as e:
        print(f"❌ langchain-community: {e}")
        return False
    
    try:
        from langchain.agents import create_sql_agent
        print("✅ langchain")
    except ImportError as e:
        print(f"❌ langchain: {e}")
        return False
    
    return True

def main():
    print("🤖 Testing Chat Setup\n")
    
    config_ok = test_config()
    imports_ok = test_imports()
    
    if config_ok and imports_ok:
        print("\n✅ Basic setup looks good!")
        print("\n📝 Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set DATABASE_URL environment variable")
        print("3. Start the server: python main.py")
        print("4. Test the chat endpoint")
    else:
        print("\n❌ Setup has issues - please fix before proceeding")

if __name__ == "__main__":
    main()