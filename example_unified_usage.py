"""
Example usage of the Unified LLM Manager

This shows how to use the new unified system that integrates:
- Validator rules and state transitions
- Safety guardrails 
- LLM provider selection based on environment
- Conversation history management
"""
import asyncio
import os
from emotion_therapy.session_store import get_redis_session_manager
from emotion_therapy.llm_manager import create_enhanced_manager_from_env
from emotion_therapy.models import SessionState


async def example_conversation():
    """Example conversation showing unified manager features"""
    
    # Set up environment for testing (optional)
    # os.environ["THERAPY_USE_LANGCHAIN"] = "1"
    # os.environ["OPENAI_API_KEY"] = "your-key-here"
    # os.environ["THERAPY_LLM_PROVIDER"] = "openai"
    
    # Create session manager and unified LLM manager
    session_mgr = get_redis_session_manager()
    unified_mgr = create_enhanced_manager_from_env(session_mgr)
    
    user_id = "test_user_123"
    
    print("🤖 Emotion Therapy Assistant with Unified LLM Manager")
    print("=" * 60)
    
    # Example 1: Start session
    print("\n1. Starting session...")
    response, validation, context = await unified_mgr.process_user_input_with_validation(
        user_id, "/start", SessionState.NO_SESSION
    )
    print(f"✅ Response: {response}")
    print(f"📋 Validation: {validation.is_valid}, Next State: {validation.next_state}")
    
    # Example 2: Identify emotion (triggers state transition + wheel normalization)
    print("\n2. Identifying emotion...")
    response, validation, context = await unified_mgr.process_user_input_with_validation(
        user_id, "/feel anxious about work", SessionState.SESSION_STARTED
    )
    print(f"✅ Response: {response}")
    print(f"📋 Validation: {validation.is_valid}, Next State: {validation.next_state}")
    print(f"🧠 LLM Context: {context}")
    
    # Example 3: Ask for diagnostic questions
    print("\n3. Getting diagnostic questions...")
    response, validation, context = await unified_mgr.process_user_input_with_validation(
        user_id, "/why", SessionState.EMOTION_IDENTIFIED
    )
    print(f"✅ Response: {response}")
    print(f"📋 Next State: {validation.next_state}")
    
    # Example 4: Get remedies
    print("\n4. Getting remedies...")
    response, validation, context = await unified_mgr.process_user_input_with_validation(
        user_id, "/remedy", SessionState.DIAGNOSTIC_COMPLETE
    )
    print(f"✅ Response: {response}")
    
    # Example 5: Safety guardrails - crisis detection
    print("\n5. Testing safety guardrails...")
    response, validation, context = await unified_mgr.process_user_input_with_validation(
        user_id, "I want to hurt myself", SessionState.REMEDY_PROVIDED
    )
    print(f"🚨 Crisis Response: {response}")
    print(f"📋 Safety Alert: {context.get('safety_alert')}")
    print(f"📋 Emergency State: {validation.next_state}")
    
    # Example 6: Invalid command (shows validator integration)
    print("\n6. Testing invalid command...")
    response, validation, context = await unified_mgr.process_user_input_with_validation(
        user_id, "/remedy", SessionState.NO_SESSION  # Invalid state for remedy
    )
    print(f"❌ Invalid Command Response: {response}")
    print(f"📋 Validation: {validation.is_valid}")
    print(f"💡 Suggestions: {validation.suggested_commands}")
    
    # Example 7: Get session status
    print("\n7. Session status...")
    status = await unified_mgr.get_session_status(user_id)
    print(f"📊 Session Status: {status}")


async def example_environment_detection():
    """Show how the manager detects LLM provider from environment"""
    print("\n🔍 Environment Detection Example")
    print("=" * 40)
    
    session_mgr = get_redis_session_manager()
    
    # Test different environment configurations
    configs = [
        {"THERAPY_USE_LANGCHAIN": "0"},  # Stub only
        {"THERAPY_USE_LANGCHAIN": "1", "OPENAI_API_KEY": "test-key"},  # OpenAI
        {"THERAPY_USE_LANGCHAIN": "1", "GEMINI_API_KEY": "test-key"},  # Gemini  
        {"THERAPY_USE_LANGCHAIN": "1", "THERAPY_LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "test-key"},  # Prefer Gemini
    ]
    
    for i, config in enumerate(configs, 1):
        print(f"\n{i}. Testing config: {config}")
        
        # Temporarily set environment
        original_env = {}
        for key, value in config.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value
        
        try:
            mgr = create_enhanced_manager_from_env(session_mgr)
            print(f"   Provider: {mgr.config.provider.value}")
            print(f"   Model: {mgr.config.model or 'default'}")
            print(f"   Fallback enabled: {mgr.config.fallback_to_stub}")
        except Exception as e:
            print(f"   Error: {e}")
        finally:
            # Restore environment
            for key in config.keys():
                if original_env[key] is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_env[key]


if __name__ == "__main__":
    print("🚀 Running Unified LLM Manager Examples\n")
    
    # Run examples
    asyncio.run(example_conversation())
    asyncio.run(example_environment_detection())
    
    print("\n✨ Examples completed!")
    print("\nEnvironment Variables for Configuration:")
    print("- THERAPY_USE_ENHANCED_MANAGER=1    # Enable unified manager (default)")
    print("- THERAPY_USE_LANGCHAIN=1           # Use LangChain providers")  
    print("- THERAPY_LLM_PROVIDER=openai|gemini # Prefer specific provider")
    print("- OPENAI_API_KEY=your-key           # OpenAI API key")
    print("- GEMINI_API_KEY=your-key           # Gemini API key")