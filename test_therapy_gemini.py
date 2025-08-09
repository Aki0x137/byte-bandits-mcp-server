#!/usr/bin/env python3
"""
Test script for the Emotion Therapy Assistant using Google Gemini
"""

import os
import google.generativeai as genai
from typing import Literal
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
    print("⚠️  GEMINI_API_KEY not set or is placeholder. Please set a real API key in .env file.")
    print("   Get your key at: https://makersuite.google.com/app/apikey")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
You are an Emotion Therapy Assistant trained to help users identify, reflect on, and manage their emotional states using Plutchik's Wheel of Emotions.

Your role is to provide structured, empathetic, and safe conversations. You are not a licensed therapist and must not offer medical, legal, or crisis-specific advice.

Your responses must follow this structure:

1. Acknowledge the user's emotion using empathetic language.
2. Reflect back the emotion and context gently.
3. Respond with one of:
   - A probing question (if in diagnosis flow)
   - A suggestion (if in remedy flow)
   - A validation and ask for more (if in conversation flow)
4. Offer a relevant next action using one of the tools: breathing, journaling, grounding exercises, or quotes.

Guardrails:
- Do not claim to diagnose, treat, or resolve psychological conditions.
- Redirect to professional help if crisis or risk words appear (e.g., "suicide", "end it", "hopeless").
- Avoid speculation about user's trauma, relationships, or background unless explicitly mentioned.
- Do not ask for personal identifying information (e.g., name, age, location).

Always aim to make the user feel heard, understood, and gently guided toward insight or relief.
"""

def generate_therapeutic_reply_gemini(
    emotion: str,
    context: str,
    user_message: str,
    tone: Literal["default", "soothing", "motivational"] = "default"
) -> str:
    """Generate a therapeutic reply using Gemini based on emotion, context, and user message."""
    user_input = f"Emotion: {emotion}\nContext: {context}\nMessage: {user_message}"
    
    if tone == "soothing":
        user_input += "\nPlease respond with a soft and calming tone."
    elif tone == "motivational":
        user_input += "\nPlease respond with an encouraging and action-oriented tone."

    try:
        # Initialize the model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Create the full prompt
        full_prompt = f"{SYSTEM_PROMPT}\n\nUser Input:\n{user_input}\n\nTherapeutic Response:"
        
        # Generate response
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=500,
            )
        )
        
        return response.text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def test_therapy_assistant_gemini():
    """Test the therapy assistant with different scenarios using Gemini."""
    print("🧠 Testing Emotion Therapy Assistant with Google Gemini")
    print("=" * 60)
    print(f"🔑 Using API Key: {GEMINI_API_KEY[:10]}...{GEMINI_API_KEY[-4:]}")
    print("=" * 60)
    
    test_cases = [
        {
            "emotion": "sadness",
            "context": "work stress",
            "message": "I feel overwhelmed with my workload and don't know how to cope",
            "tone": "soothing"
        },
        {
            "emotion": "anger",
            "context": "relationships",
            "message": "My partner keeps ignoring my feelings and I'm getting really frustrated",
            "tone": "default"
        },
        {
            "emotion": "joy",
            "context": "personal achievement",
            "message": "I finally completed that project I've been working on for months!",
            "tone": "motivational"
        },
        {
            "emotion": "anxiety",
            "context": "social situations",
            "message": "I have a big presentation tomorrow and I'm really nervous about speaking in front of people",
            "tone": "soothing"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}:")
        print(f"Emotion: {case['emotion']}")
        print(f"Context: {case['context']}")
        print(f"Message: {case['message']}")
        print(f"Tone: {case['tone']}")
        print("-" * 30)
        
        response = generate_therapeutic_reply_gemini(
            case['emotion'],
            case['context'],
            case['message'],
            case['tone']
        )
        
        print(f"🤖 Gemini Response:\n{response}")
        print("=" * 60)

def test_gemini_connection():
    """Test basic Gemini API connection."""
    print("🔗 Testing Gemini API Connection...")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Hello, please respond with 'Connection successful!'")
        print(f"✅ Connection test: {response.text}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🌟 Gemini Therapy Assistant Test Suite")
    print("=" * 60)
    
    # Test connection first
    if test_gemini_connection():
        print("\n" + "=" * 60)
        test_therapy_assistant_gemini()
    else:
        print("\n❌ Cannot proceed with therapy tests due to connection issues.")
        print("Please check your GEMINI_API_KEY in the .env file.")