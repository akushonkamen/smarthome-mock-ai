# SmartHome Mock AI - Development Roadmap

## Phase 1: Foundation (✅ Completed)
- [x] Initialize Project & Poetry Structure
- [x] Set up GitHub Actions (CI/CD) with Ruff & Pytest
- [x] Implement Virtual Device Simulator (In-Memory)
- [x] Implement Agent with Function Calling
- [x] Build CLI Interface (Main Loop)

## Phase 2: Persistence Layer (✅ Completed)
- [x] **Infrastructure**: Add `sqlite3` support. Create `src/smarthome_mock_ai/persistence.py` to handle database connections.
- [x] **State Management**: Modify `HomeSimulator` to save/load device states (on/off, temp, etc.) to `data/devices.json` or SQLite on every change.
- [x] **Interaction Logging**: Create a DB table `logs` to store `timestamp`, `user_input`, `agent_action`, and `device_state_snapshot`.

## Phase 3: Voice Interface (✅ Completed)
- [x] **Dependencies**: Add `SpeechRecognition`, `pyaudio`, and `openai-whisper` (or API client) to `pyproject.toml`.
- [x] **Voice Module**: Implement `VoiceListener` class in `src/smarthome_mock_ai/voice.py` with silence detection.
- [x] **Integration**: Update `main.py` to add a "Press 'V' to Speak" mode that transcribes audio and feeds it to the Agent.

## Phase 4: Reinforcement Learning (✅ Completed)
- [x] **Feedback Mechanism**: Update CLI to ask user "Was this action correct? (y/n)" after execution. Log the result (+1/-1) to the DB.
- [x] **Preference Model**: Create `src/smarthome_mock_ai/learning.py`. Implement a simple Contextual Bandit or Frequency Table (e.g., "If 8pm + 'hot', user prefers 24°C").
- [x] **Intervention Logic**: Modify Agent to query the Preference Model *before* executing tools. If confidence is high, override the LLM's default parameter.

## Phase 5: Final Polish (✨ Release)
- [x] **Full Regression Test**: Ensure Voice, Persistence, and RL work together without crashing.
- [x] **Documentation**: Update `README.md` with new features and usage guide.
