# 🔄 Command Flow DAG

## Entry Points
```
[User Input] → /start (Required for new session)
```

## Main Flow Paths

### Path 1: Direct Emotion Input
```
/start → /feel <emotion> → /why → /remedy → [Self-help tools] or /exit
```

### Path 2: Free-form Conversation
```
/start → /ask <text> → [NLP Analysis] → /wheel (if emotion unclear) → /feel <emotion> → /why → /remedy
```

### Path 3: Exploration Mode
```
/start → /wheel → /feel <emotion> → /why → /remedy
```

## Command Dependencies & Rules

### 🚪 **Session Management**
- **`/start`** - Required before any other command (except `/sos`)
- **`/exit`** - Can be used at any time to end session

### 🎯 **Emotion Identification Phase**
- **`/ask <text>`** - Available after `/start` for free-form input
- **`/wheel`** - Can follow `/start` or `/ask` when emotion is unclear
- **`/feel <emotion>`** - Can follow `/start`, `/ask`, or `/wheel`

### 🔍 **Diagnostic Phase**
- **`/why`** - Only available after emotion is identified via `/feel`
- Prerequisite: User must have used `/feel <emotion>`

### 💡 **Remedy Phase**
- **`/remedy`** - Available after `/why` or directly after `/feel`
- Prerequisite: Emotion must be identified

### 🛠️ **Self-Help Tools** (Available anytime after `/start`)
- **`/breathe`** - Immediate breathing exercise
- **`/quote`** - Motivational quote
- **`/journal`** - Journaling prompt
- **`/audio`** - Meditation audio

### 📊 **Tracking & Monitoring**
- **`/checkin`** - Daily check-in (can start new session)
- **`/moodlog`** - View mood history (requires active session)

### 🚨 **Emergency**
- **`/sos`** - Available at ANY time, bypasses all flows

## Flow States

### State 1: No Active Session
```
Available: /start, /sos, /checkin
```

### State 2: Session Started, No Emotion Identified
```
Available: /ask, /wheel, /feel, /breathe, /quote, /journal, /audio, /exit, /sos
```

### State 3: Emotion Identified
```
Available: /why, /remedy, /breathe, /quote, /journal, /audio, /moodlog, /exit, /sos
```

### State 4: Diagnostic Complete
```
Available: /remedy, /breathe, /quote, /journal, /audio, /moodlog, /exit, /sos
```

### State 5: Remedy Provided
```
Available: /ask (new issue), /checkin, /moodlog, /breathe, /quote, /journal, /audio, /exit, /sos
```

## Visual Flow

### Complete Flow Diagram

```plantuml
@startuml EmotionTherapyBotFlow
!theme plain
skinparam backgroundColor white
skinparam roundcorner 10
skinparam shadowing false

title WhatsApp Emotion Therapy Bot - Command Flow

start

:User Input;

if (Active Session?) then (No)
  :Execute /start;
  note right: Required for new users\nor session reset
  :Session Started;
else (Yes)
  :Continue with existing session;
endif

partition "Emergency Override" #lightcoral {
  if (/sos command?) then (Yes)
    :Emergency Protocol;
    :Crisis Resources;
    :Contact Emergency Services;
    stop
  else (No)
    :Continue normal flow;
  endif
}

if (Exit requested?) then (Yes)
  :Execute /exit;
  :End Session;
  stop
else (No)
  :Continue;
endif

partition "Emotion Identification Phase" #lightblue {
  if (Emotion already identified?) then (No)
    if (User input type?) then (/ask text)
      :Process free-form text;
      :NLP Analysis;
      if (Emotion clear from text?) then (No)
        :Show /wheel;
        :Display emotion categories;
        :User selects emotion;
      else (Yes)
        :Extract emotion;
      endif
    elseif (Direct emotion input) then (/feel emotion)
      :Record emotion directly;
    elseif (Need guidance) then (/wheel)
      :Display Plutchik's Wheel;
      :User browses categories;
      :User executes /feel;
    endif
    :Emotion Identified ✓;
  else (Yes)
    :Use existing emotion;
  endif
}

partition "Diagnostic Phase" #lightyellow {
  if (/why command or auto-trigger?) then (Yes)
    :Ask 2-3 probing questions;
    :Based on emotion category;
    :Collect context responses;
    :Infer triggers (work/family/self/trauma);
    :Context Analysis Complete ✓;
  else (Skip)
    :Use basic emotion data;
  endif
}

partition "Remedy Phase" #lightgreen {
  :Execute /remedy;
  :Based on emotion + context;
  
  if (Remedy type needed?) then (Breathing)
    :Breathing exercises;
  elseif (Meditation) then (Audio)
    :Meditation audio;
  elseif (Reflection) then (Journal)
    :Journaling prompts;
  elseif (Inspiration) then (Quote)
    :Motivational quotes;
  elseif (Multiple) then (Combined)
    :Multiple coping strategies;
  endif
  
  :Remedy Provided ✓;
}

partition "Self-Help Tools (Available Anytime)" #lavender {
  note right
    /breathe - Immediate breathing exercise
    /quote - Daily motivation
    /journal - Reflection prompts  
    /audio - Meditation sounds
  end note
}

partition "Tracking & Continuity" #lightcyan {
  if (Daily engagement?) then (/checkin)
    :Daily mood check-in;
    :Update mood log;
  elseif (View history) then (/moodlog)
    :Display mood trends;
    :Show progress;
  endif
}

if (Continue session?) then (Yes)
  :Return to emotion identification;
  note left: User can report new emotion\nor ask follow-up questions
else (No)
  if (Auto check-in scheduled?) then (Yes)
    :Schedule next /checkin;
  endif
  :Session Complete;
endif

stop

@enduml
```

### State Transition Diagram

```plantuml
@startuml EmotionTherapyBotStates
!theme plain

title WhatsApp Emotion Therapy Bot - State Transitions

[*] --> NoSession : User first contact

state NoSession {
  NoSession : Available: /start, /sos, /checkin
}

state ActiveSession {
  state EmotionUnknown {
    EmotionUnknown : Available: /ask, /wheel, /feel
    EmotionUnknown : Self-help: /breathe, /quote, /journal, /audio
  }
  
  state EmotionIdentified {
    EmotionIdentified : Available: /why, /remedy
    EmotionIdentified : Self-help tools available
  }
  
  state DiagnosticComplete {
    DiagnosticComplete : Available: /remedy
    DiagnosticComplete : Context gathered
  }
  
  state RemedyProvided {
    RemedyProvided : Available: /ask (new issue), /moodlog
    RemedyProvided : Can start new emotion cycle
  }
}

state Emergency {
  Emergency : Crisis protocol activated
  Emergency : External resources provided
}

NoSession --> ActiveSession : /start
NoSession --> ActiveSession : /checkin
NoSession --> Emergency : /sos

ActiveSession --> EmotionUnknown : Session started
EmotionUnknown --> EmotionIdentified : /feel or emotion extracted from /ask
EmotionUnknown --> EmotionUnknown : /wheel (guidance)
EmotionIdentified --> DiagnosticComplete : /why (optional)
EmotionIdentified --> RemedyProvided : /remedy (direct)
DiagnosticComplete --> RemedyProvided : /remedy
RemedyProvided --> EmotionUnknown : /ask (new emotion cycle)

ActiveSession --> [*] : /exit
ActiveSession --> Emergency : /sos
Emergency --> [*] : Crisis resolved

note right of Emergency
  /sos available from 
  ANY state at ANY time
end note

note bottom of ActiveSession
  Self-help tools (/breathe, /quote, 
  /journal, /audio) available in 
  all active session states
end note

@enduml
```

## Command Priority Rules

1. **`/sos`** - Highest priority, interrupts any flow
2. **`/exit`** - Second priority, can end any session
3. **`/start`** - Required before other commands (session gate)
4. **Flow commands** - Must follow logical sequence
5. **Self-help tools** - Available as support at any active session state

## Implementation Notes

- **Session State**: Track current user state (NoSession, EmotionUnknown, EmotionIdentified, etc.)
- **Command Validation**: Validate commands against current state before execution
- **Emergency Override**: `/sos` should bypass all validation and state checks
- **Context Preservation**: Maintain emotion and diagnostic data throughout session
- **Graceful Degradation**: Allow users to skip diagnostic phase if desired
- **Cyclical Flow**: Users can identify multiple emotions in one session
