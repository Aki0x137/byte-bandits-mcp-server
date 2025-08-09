"""
Generic LLM Handler with Chain of Thoughts support using Langchain
"""
from __future__ import annotations

import os
from enum import Enum
from typing import Dict, Any, Optional, List, Literal
from dataclasses import dataclass

from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser

# Import provider-specific LLMs
try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    GEMINI = "gemini"


@dataclass
class LLMConfig:
    """Configuration for LLM handler"""
    provider: LLMProvider
    model: str
    temperature: float = 0.7
    max_tokens: int = 500
    api_key: Optional[str] = None


class ChainOfThoughtsPrompts:
    """Structured prompts for chain of thoughts reasoning"""
    
    EMOTION_ANALYSIS_COT = """You are an emotion analysis expert using Plutchik's Wheel of Emotions.

Let's think step by step:

1. IDENTIFY: Read the user's text and identify emotional keywords and context clues
2. CLASSIFY: Map these to primary emotions (anger, fear, sadness, joy, trust, disgust, surprise, anticipation)
3. ASSESS: Determine intensity (low, medium, high) and any emotion blends
4. CONTEXTUALIZE: Consider the situation and what might be driving this emotion

User text: "{text}"

Step 1 - IDENTIFY emotional keywords and context:
Let me look for emotional indicators...

Step 2 - CLASSIFY primary emotion(s):
Based on the keywords, the primary emotion appears to be...

Step 3 - ASSESS intensity and blends:
The intensity seems to be... because...

Step 4 - CONTEXTUALIZE:
Given the context, this emotion likely stems from...

FINAL ANALYSIS:
Primary Emotion: [emotion]
Intensity: [low/medium/high]
Confidence: [0.0-1.0]
Context: [brief context]
Reasoning: [brief explanation of why this emotion was identified]"""

    THERAPEUTIC_RESPONSE_COT = """You are an Emotion Therapy Assistant using Plutchik's Wheel of Emotions.

Let's approach this therapeutically step by step:

1. ACKNOWLEDGE: Validate the user's emotional experience
2. REFLECT: Mirror back what they're experiencing with empathy
3. EXPLORE: Ask or suggest based on the flow type (diagnosis/remedy/conversation)
4. GUIDE: Offer a specific next action or coping strategy

Context:
- Primary Emotion: {emotion}
- Situation Context: {context}
- User Message: {user_message}
- Response Tone: {tone}

Step 1 - ACKNOWLEDGE the emotion:
I want to first validate that...

Step 2 - REFLECT their experience:
It sounds like you're experiencing...

Step 3 - EXPLORE based on therapeutic flow:
To help you move forward...

Step 4 - GUIDE with specific action:
A helpful next step might be...

THERAPEUTIC RESPONSE:
[Provide the final, cohesive therapeutic response that incorporates all steps above]

Remember: You are not a licensed therapist. Redirect to professional help for crisis situations."""

    REMEDY_SUGGESTION_COT = """You are a therapeutic coping strategy specialist.

Let's think through appropriate remedies step by step:

1. UNDERSTAND: What is the core emotional need?
2. MATCH: What coping strategies align with this emotion type?
3. PERSONALIZE: How can we tailor this to the specific context?
4. PRIORITIZE: What's most immediately helpful?

Emotion: {emotion}
Context: {context}
Intensity: {intensity}

Step 1 - UNDERSTAND the core need:
For {emotion}, the underlying need is typically...

Step 2 - MATCH appropriate strategies:
Research-backed approaches for {emotion} include...

Step 3 - PERSONALIZE for context:
Given the context of {context}, I should emphasize...

Step 4 - PRIORITIZE immediate help:
The most helpful immediate action would be...

REMEDY SUGGESTIONS:
[Provide 3-5 specific, actionable coping strategies]"""


class LLMHandler:
    """Generic LLM handler supporting multiple providers with chain of thoughts"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.llm = self._initialize_llm()
        
    def _initialize_llm(self):
        """Initialize the appropriate LLM based on provider"""
        if self.config.provider == LLMProvider.OPENAI:
            if not OPENAI_AVAILABLE:
                raise ImportError("OpenAI langchain package not available")
            api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key required")
            
            return ChatOpenAI(
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                api_key=api_key
            )
            
        elif self.config.provider == LLMProvider.GEMINI:
            if not GEMINI_AVAILABLE:
                raise ImportError("Gemini langchain package not available")
            api_key = self.config.api_key or os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("Gemini API key required")
                
            return ChatGoogleGenerativeAI(
                model=self.config.model,
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens,
                google_api_key=api_key
            )
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")

    def analyze_emotion_with_cot(self, text: str) -> Dict[str, Any]:
        """Analyze emotion using chain of thoughts reasoning"""
        prompt = PromptTemplate(
            input_variables=["text"],
            template=ChainOfThoughtsPrompts.EMOTION_ANALYSIS_COT
        )
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            response = chain.invoke({"text": text})
            return self._parse_emotion_analysis(response)
        except Exception as e:
            return {
                "emotion": "UNKNOWN",
                "intensity": "low",
                "confidence": 0.1,
                "context": "Error in analysis",
                "reasoning": f"Error: {str(e)}",
                "raw_response": ""
            }

    def generate_therapeutic_response_with_cot(
        self,
        emotion: str,
        context: str,
        user_message: str,
        tone: Literal["default", "soothing", "motivational"] = "default"
    ) -> str:
        """Generate therapeutic response using chain of thoughts"""
        prompt = PromptTemplate(
            input_variables=["emotion", "context", "user_message", "tone"],
            template=ChainOfThoughtsPrompts.THERAPEUTIC_RESPONSE_COT
        )
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            response = chain.invoke({
                "emotion": emotion,
                "context": context,
                "user_message": user_message,
                "tone": tone
            })
            return self._extract_final_response(response, "THERAPEUTIC RESPONSE:")
        except Exception as e:
            return f"I understand you're experiencing {emotion}. I'm having trouble processing right now, but I want you to know your feelings are valid. Consider reaching out to a trusted friend or professional if you need immediate support."

    def suggest_remedies_with_cot(
        self,
        emotion: str,
        context: str = "",
        intensity: str = "medium"
    ) -> List[str]:
        """Suggest remedies using chain of thoughts reasoning"""
        prompt = PromptTemplate(
            input_variables=["emotion", "context", "intensity"],
            template=ChainOfThoughtsPrompts.REMEDY_SUGGESTION_COT
        )
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            response = chain.invoke({
                "emotion": emotion,
                "context": context,
                "intensity": intensity
            })
            return self._parse_remedy_suggestions(response)
        except Exception as e:
            # Fallback to basic suggestions
            return [
                "Take 5 deep breaths",
                "Step away from the situation briefly",
                "Write down 3 things you're grateful for",
                "Reach out to someone you trust"
            ]

    def _parse_emotion_analysis(self, response: str) -> Dict[str, Any]:
        """Parse the emotion analysis response"""
        lines = response.split('\n')
        result = {
            "emotion": "UNKNOWN",
            "intensity": "medium",
            "confidence": 0.5,
            "context": "",
            "reasoning": "",
            "raw_response": response
        }
        
        for line in lines:
            line = line.strip()
            if line.startswith("Primary Emotion:"):
                result["emotion"] = line.split(":", 1)[1].strip().strip("[]")
            elif line.startswith("Intensity:"):
                result["intensity"] = line.split(":", 1)[1].strip().strip("[]")
            elif line.startswith("Confidence:"):
                try:
                    conf_str = line.split(":", 1)[1].strip().strip("[]")
                    result["confidence"] = float(conf_str)
                except (ValueError, IndexError):
                    pass
            elif line.startswith("Context:"):
                result["context"] = line.split(":", 1)[1].strip().strip("[]")
            elif line.startswith("Reasoning:"):
                result["reasoning"] = line.split(":", 1)[1].strip().strip("[]")
                
        return result

    def _extract_final_response(self, response: str, marker: str) -> str:
        """Extract the final response after a marker"""
        if marker in response:
            parts = response.split(marker, 1)
            if len(parts) > 1:
                return parts[1].strip()
        return response.strip()

    def _parse_remedy_suggestions(self, response: str) -> List[str]:
        """Parse remedy suggestions from response"""
        if "REMEDY SUGGESTIONS:" in response:
            suggestions_text = response.split("REMEDY SUGGESTIONS:", 1)[1].strip()
        else:
            suggestions_text = response
            
        # Look for numbered or bulleted lists
        lines = suggestions_text.split('\n')
        remedies = []
        
        for line in lines:
            line = line.strip()
            # Skip empty lines and headers
            if not line or line.startswith('Step') or line.startswith('['):
                continue
            # Remove numbering/bullets
            if line[0].isdigit() or line.startswith('•') or line.startswith('-'):
                line = line[1:].strip()
                if line.startswith('.') or line.startswith(')'):
                    line = line[1:].strip()
            
            if line and len(line) > 5:  # Basic sanity check
                remedies.append(line)
                
        return remedies[:5] if remedies else ["Take a few deep breaths and pause"]


# Factory functions for common configurations
def create_openai_handler(
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.7,
    max_tokens: int = 500,
    api_key: Optional[str] = None
) -> LLMHandler:
    """Create an OpenAI LLM handler"""
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=api_key
    )
    return LLMHandler(config)


def create_gemini_handler(
    model: str = "gemini-1.5-flash",
    temperature: float = 0.7,
    max_tokens: int = 500,
    api_key: Optional[str] = None
) -> LLMHandler:
    """Create a Gemini LLM handler"""
    config = LLMConfig(
        provider=LLMProvider.GEMINI,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=api_key
    )
    return LLMHandler(config)


def create_handler_from_env(
    prefer_provider: Optional[str] = None
) -> Optional[LLMHandler]:
    """Create handler based on available environment variables"""
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if prefer_provider == "openai" and openai_key:
        return create_openai_handler(api_key=openai_key)
    elif prefer_provider == "gemini" and gemini_key:
        return create_gemini_handler(api_key=gemini_key)
    elif openai_key:
        return create_openai_handler(api_key=openai_key)
    elif gemini_key:
        return create_gemini_handler(api_key=gemini_key)
    
    return None