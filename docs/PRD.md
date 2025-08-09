# 📄 Project Summary: WhatsApp-Based Emotion Therapy Bot using Wheel of Emotions

## 1. 🎯 Objective

Build a MCP Server that acts as a therapist assistant to:

- Help users identify emotions using the Wheel of Emotions
- Ask tailored diagnostic questions based on emotion category
- Provide coping mechanisms and resources as emotional remedies
- Maintain user context, provide daily check-ins, and ensure privacy

## 2. 🧑‍💼 Target User Persona

- **Name:** Riya Sharma  
- **Age:** 27  
- **Behavior:** Uses WhatsApp daily, prefers text-based emotional support, seeks emotional clarity without a therapist

**Primary Needs:**
- Identify her emotional state
- Understand triggers
- Get relief or actionable suggestions

## 3. 💬 Supported Commands

| Command                | Purpose                          |
|------------------------|----------------------------------|
| `/start`               | Start/reset conversation         |
| `/feel <emotion>`      | Direct input of emotional state  |
| `/ask <text>`          | Free-form message                |
| `/why`                 | Diagnostic questions             |
| `/remedy`              | Coping strategies                |
| `/exit`                | End session and clear context    |

## 4. 🧠 Conversation & Session Model
- Conversations are session-scoped. LLM calls only occur after `/start`.
- Structured `history` per session keeps recent N turns for context.
- A Conversation Manager mediates tools/validator ↔ LLM and supports pluggable backends (stub or LangChain).

## 5. 🔁 Backends
- Default: deterministic stub (no network).
- Optional: LangChain provider controlled by `THERAPY_USE_LANGCHAIN=1` and OpenAI credentials.
