"""
Unified LLM Manager for Emotion Therapy

Provides a unified interface that:
- Integrates with validator.py rules
- Adds safety guardrails
- Works with existing conversation.py
- Environment-based LLM provider selection
- Fallback mechanisms
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from enum import Enum

# Import models and validator
from .models import SessionState, ValidationResult, CommandType
from .validator import validate_command_from_raw, parse_command, get_available_commands

# Import existing conversation management
from .conversation import ConversationManager, create_conversation_manager, ConversationContext

# Import wheel for emotion normalization
from .wheel import normalize_text

# Optional LangChain imports
try:
    from langchain_openai import ChatOpenAI
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


class LLMProviderType(Enum):
    """Supported LLM provider types"""
    STUB = "stub"
    OPENAI = "openai"
    GEMINI = "gemini"


@dataclass
class LLMConfig:
    """Configuration for LLM manager"""
    provider: LLMProviderType
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 500
    api_key: Optional[str] = None
    fallback_to_stub: bool = True


class SafetyGuardrails:
    """Safety checks and content filtering"""
    
    CRISIS_KEYWORDS = [
        "suicide", "kill myself", "end it all", "want to die", "hurt myself",
        "self harm", "cutting", "overdose", "can't go on", "no point living",
        "better off dead", "not worth living", "kill me"
    ]
    
    INAPPROPRIATE_KEYWORDS = [
        "sexual", "porn", "naked", "drug dealer", "illegal drugs",
        "violence", "weapon", "bomb", "terrorist", "hate speech"
    ]
    
    @classmethod
    def check_crisis_indicators(cls, text: str) -> bool:
        """Check if text contains crisis indicators"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in cls.CRISIS_KEYWORDS)
    
    @classmethod
    def check_inappropriate_content(cls, text: str) -> bool:
        """Check if text contains inappropriate content"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in cls.INAPPROPRIATE_KEYWORDS)
    
    @classmethod
    def get_crisis_response(cls) -> str:
        """Standard crisis response"""
        return (
            "I'm concerned about what you're sharing. Your safety is important. "
            "Please reach out to a mental health professional, trusted friend, or crisis hotline immediately. "
            "In the US: 988 Suicide & Crisis Lifeline (call or text). "
            "You don't have to go through this alone."
        )
    
    @classmethod
    def get_inappropriate_response(cls) -> str:
        """Response for inappropriate content"""
        return (
            "I'm designed to help with emotional support and well-being. "
            "Let's focus on your feelings and healthy coping strategies. "
            "How are you feeling emotionally right now?"
        )


class EnhancedLLMProvider:
    """Enhanced LLM provider with guardrails and context awareness"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.llm = self._initialize_llm() if config.provider != LLMProviderType.STUB else None
    
    def _initialize_llm(self):
        """Initialize the appropriate LLM"""
        if not LANGCHAIN_AVAILABLE:
            return None
            
        if self.config.provider == LLMProviderType.OPENAI:
            api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                return None
            
            return ChatOpenAI(
                model=self.config.model or "gpt-3.5-turbo",
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                api_key=api_key
            )
        
        elif self.config.provider == LLMProviderType.GEMINI:
            api_key = self.config.api_key or os.getenv("GEMINI_API_KEY")
            if not api_key:
                return None
            
            return ChatGoogleGenerativeAI(
                model=self.config.model or "gemini-1.5-flash",
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens,
                google_api_key=api_key
            )
        
        return None
    
    async def enhance_response(self, base_response: str, context: ConversationContext, user_input: str) -> str:
        """Enhance response using LLM if available"""
        if not self.llm:
            return base_response
        
        try:
            system_prompt = self._build_enhancement_prompt(context, base_response)
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_input)
            ]
            
            result = await self.llm.ainvoke(messages)
            enhanced = getattr(result, "content", str(result))
            
            # Apply safety filters
            if SafetyGuardrails.check_crisis_indicators(enhanced):
                return SafetyGuardrails.get_crisis_response()
            
            if SafetyGuardrails.check_inappropriate_content(enhanced):
                return SafetyGuardrails.get_inappropriate_response()
            
            return enhanced
            
        except Exception:
            # Fallback to base response
            return base_response
    
    def _build_enhancement_prompt(self, context: ConversationContext, base_response: str) -> str:
        """Build prompt for response enhancement"""
        return f"""You are a compassionate emotion therapy assistant using Plutchik's Wheel of Emotions.

Current context:
- Session state: {context.session_state.value}
- User's emotion: {context.current_emotion or 'unknown'}
- Session goal: {context.session_goal or 'emotional support'}

Base response: {base_response}

Guidelines:
- Enhance the base response to be more empathetic and helpful
- Keep the core message but make it more personalized
- Be concise (2-3 sentences maximum)
- Stay focused on emotional well-being
- If you detect any crisis indicators, immediately direct to professional help
- You are NOT a licensed therapist

Enhanced response:"""


class UnifiedLLMManager:
    """Unified LLM manager that integrates validation, guardrails, and conversation management"""
    
    def __init__(self, session_manager: Any, config: Optional[LLMConfig] = None):
        self.session_manager = session_manager
        self.config = config or self._detect_config_from_env()
        
        # Use existing conversation manager
        use_langchain = self.config.provider != LLMProviderType.STUB
        self.conv_manager = create_conversation_manager(
            session_manager, 
            use_langchain=use_langchain,
            model_name=self.config.model or "gpt-3.5-turbo"
        )
        
        # Enhanced LLM provider for additional processing
        self.enhanced_provider = EnhancedLLMProvider(self.config)
    
    def _detect_config_from_env(self) -> LLMConfig:
        """Detect LLM configuration from environment variables"""
        use_langchain = os.getenv("THERAPY_USE_LANGCHAIN", "0").lower() in ("1", "true", "yes")
        
        if not use_langchain:
            return LLMConfig(provider=LLMProviderType.STUB)
        
        # Check available API keys
        openai_key = os.getenv("OPENAI_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")
        
        prefer_provider = os.getenv("THERAPY_LLM_PROVIDER", "").lower()
        
        if prefer_provider == "gemini" and gemini_key:
            return LLMConfig(provider=LLMProviderType.GEMINI, api_key=gemini_key)
        elif prefer_provider == "openai" and openai_key:
            return LLMConfig(provider=LLMProviderType.OPENAI, api_key=openai_key)
        elif openai_key:
            return LLMConfig(provider=LLMProviderType.OPENAI, api_key=openai_key)
        elif gemini_key:
            return LLMConfig(provider=LLMProviderType.GEMINI, api_key=gemini_key)
        else:
            return LLMConfig(provider=LLMProviderType.STUB)
    
    async def process_user_input_with_validation(
        self,
        user_id: str,
        raw_input: str,
        current_state: SessionState
    ) -> tuple[str, ValidationResult, Dict[str, Any]]:
        """
        Process user input with full validation, safety checks, and LLM interaction
        
        Returns:
            tuple of (response, validation_result, llm_context)
        """
        # Safety checks first
        if SafetyGuardrails.check_crisis_indicators(raw_input):
            # Trigger emergency state
            session = self.session_manager.get_session(user_id)
            session.state = SessionState.EMERGENCY
            self.session_manager.save_session(session)
            
            return SafetyGuardrails.get_crisis_response(), ValidationResult(
                is_valid=True,
                command_type=CommandType.EMERGENCY,
                current_state=current_state,
                next_state=SessionState.EMERGENCY,
                suggested_commands=["/sos", "/exit"]
            ), {"safety_alert": "crisis_detected"}
        
        if SafetyGuardrails.check_inappropriate_content(raw_input):
            return SafetyGuardrails.get_inappropriate_response(), ValidationResult(
                is_valid=False,
                command_type=CommandType.UNKNOWN,
                current_state=current_state,
                error_message="Inappropriate content detected"
            ), {"safety_alert": "inappropriate_content"}
        
        # Parse and validate command using validator
        validation_result = validate_command_from_raw(raw_input, current_state)
        
        if not validation_result.is_valid:
            return (
                validation_result.error_message or "Invalid command",
                validation_result,
                {}
            )
        
        # Update session state if validation suggests a state change
        if validation_result.next_state and validation_result.next_state != current_state:
            session = self.session_manager.get_session(user_id)
            session.state = validation_result.next_state
            
            # Update session context with LLM context from validation (e.g., emotion details)
            if validation_result.llm_context:
                if not hasattr(session, 'context') or session.context is None:
                    session.context = {}
                session.context.update(validation_result.llm_context)
                
                # Set current emotion if provided
                if 'current_emotion_primary' in validation_result.llm_context:
                    session.current_emotion = validation_result.llm_context['current_emotion_primary']
            
            self.session_manager.save_session(session)
        
        # Process with conversation manager
        command, parameter = parse_command(raw_input)
        base_response, llm_context = await self.conv_manager.process_with_llm(
            user_id, command, parameter, raw_input
        )
        
        # Enhance response if possible
        context = await self.conv_manager.get_conversation_context(user_id)
        enhanced_response = await self.enhanced_provider.enhance_response(
            base_response, context, raw_input
        )
        
        # Add conversation turn
        await self.conv_manager.add_turn(
            user_id=user_id,
            user_input=raw_input,
            command=command,
            parameter=parameter,
            system_response=enhanced_response,
            emotion_context=llm_context
        )
        
        # Merge LLM context with validation context
        final_context = {**llm_context}
        if validation_result.llm_context:
            final_context.update(validation_result.llm_context)
        
        return enhanced_response, validation_result, final_context
    
    async def get_available_commands(self, user_id: str) -> List[str]:
        """Get available commands for current session state"""
        session = self.session_manager.get_session(user_id)
        return get_available_commands(session.state)
    
    async def get_session_status(self, user_id: str) -> Dict[str, Any]:
        """Get current session status and context"""
        session = self.session_manager.get_session(user_id)
        available_commands = await self.get_available_commands(user_id)
        
        return {
            "user_id": user_id,
            "state": session.state.value,
            "current_emotion": getattr(session, 'current_emotion', None),
            "available_commands": available_commands,
            "context": getattr(session, 'context', {}),
            "history_length": len(getattr(session, 'history', []))
        }
    
    # Delegate other methods to conversation manager
    async def start_conversation(self, user_id: str) -> str:
        """Start a new conversation"""
        return await self.conv_manager.start_conversation(user_id)
    
    async def end_conversation(self, user_id: str) -> None:
        """End conversation"""
        await self.conv_manager.end_conversation(user_id)
    
    async def get_conversation_context(self, user_id: str) -> ConversationContext:
        """Get conversation context"""
        return await self.conv_manager.get_conversation_context(user_id)


def create_unified_llm_manager(
    session_manager: Any,
    config: Optional[LLMConfig] = None
) -> UnifiedLLMManager:
    """Factory function to create unified LLM manager"""
    return UnifiedLLMManager(session_manager, config)


def create_enhanced_manager_from_env(session_manager: Any) -> UnifiedLLMManager:
    """Create manager with environment-detected configuration"""
    return UnifiedLLMManager(session_manager)