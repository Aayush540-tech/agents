# 🗣️ Conversational AI Agent with Dynamic Backchannel Filtering

## Project Overview

This project implements an advanced conversational AI agent using an **Intelligent Interrupt Handler**. The core feature is the use of a **dynamically updatable list of ignored words (backchannels)** to filter out common conversational fillers (like "yeah," "uh-huh") and prevent the agent from being unnecessarily interrupted. This significantly improves the natural flow of the full-duplex conversation and allows updating the ignored list at runtime without a restart.

## Key Components

### 1. The Agent (`my-ai-agent.py`)

This is the main entry point, containing the session setup and event handlers for managing the conversation flow.

### 2. Intelligent Interrupt Handler (`IntelligentInterruptHandler.py`)

This class contains the logic for distinguishing between a listener backchannel and a genuine interruption command. Key features:
  * **Dynamic Ignored Words:** The list of ignored words is **updatable at runtime**, not static.
  * **Command Handling:** Words like "STOP" are immediately processed if confidence is high.
  * **Confidence Threshold:** Filters out low-confidence, noisy transcriptions.
  * **Persistence:** The list is saved to disk (`ignored_words.json`) and automatically loaded on restart.
  * **Thread Safety:** Uses a thread-safe set with threading locks to allow dynamic updates from multiple asynchronous events.

## 🔄 Dynamic Interruption Filtering

### What Changed: 
  * **Dynamic Storage:** Instead of a static list in `config.py`, ignored words are stored in memory as a Python set.
  * **Persistence:** The set is written to and read from `ignored_words.json`. 
  * **API/Voice Command Support:** Ignored words can be added or removed live by voice command (e.g., “Add ignore uhhh”).
  * **Threading:** All access to the list/set is guarded by a `threading.Lock`, enabling safe live updates even when accessed by multiple concurrent event handlers.

### What Works:
  * **Live Backchannel Filtering:** The agent ignores any words currently in the in-memory dynamic list, which can be augmented or trimmed without restarts.
  * **Real-Time Updates:** Admins/users can safely add/remove ignored words at any time via supported commands.
  * **Persistence:** All updates are durable and survive process restarts.

### Known Issues:
  * **Phrase Matching:** Only exact matches are currently ignored (no partial/substring match for complex utterances, e.g., "Yeah, can you pause" is an interruption if not exactly "yeah").
  * **Concurrency:** Threading and async event-handling are used to ensure updates are never lost or corrupted but should be carefully maintained if extending internals.
  * **User Feedback:** Confirmation of changes is provided via voice output and logs.

### Steps to Test:
1. **Start the agent** using the instructions in the "Running the Agent" section below.
2. **Add Ignored Word:** While the agent is running, say: **"Add ignore uhhh"**.
    - *Expected Result:* The agent will confirm and `uhhh` will be ignored in real time.
3. **Remove Ignored Word:** Say: **"Remove ignore uhhh"**.
    - *Expected Result:* The agent will confirm and `uhhh` will again act as a valid interruption trigger.
4. **Persistence:** Restart the agent. Previously ignored words will be loaded from `ignored_words.json`.

### Environment Details:
  * **Python Version:** Python 3.8+
  * **Dependencies:** All required packages are listed in `requirements.txt`.
  * **Required External APIs:**
      * **Speech-to-Text (STT): Deepgram**
      * **Text-to-Speech (TTS): LiveKit In-Built TTS**
      * **Large Language Model (LLM): Grok API**

---

## Dynamic Configuration Example

The ignored word list is no longer set statically in `config.py`. Instead, it is managed at runtime, persisted to disk, and guarded for thread safety.
 
 ## To run AI-Agent

 python -m examples.my-ai-agent console

 ## THANK YOU
