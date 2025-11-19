import json
import os
import threading
from typing import List


class IntelligentInterruptHandler:
    """
    An extension layer to intelligently distinguish meaningful user interruptions
    from irrelevant fillers using ASR results, ensuring no changes to LiveKit's
    base VAD algorithm[cite: 7, 12].
    """

    def __init__(
        self,
        ignored_words: List[str],
        interruption_commands: List[str],
        confidence_threshold: float,
        persist_file: str = "ignored_words.json",
    ):
        self._lock = threading.Lock()
        self.persist_file = persist_file
        self.interruption_commands = set(w.lower() for w in interruption_commands)
        self.confidence_threshold = confidence_threshold

        loaded_words = self._load_ignored_words()
        if loaded_words is not None:
            self.ignored_words = loaded_words
        else:
            self.ignored_words = set(w.lower() for w in ignored_words)

        print(f"Ignored words loaded: {self.ignored_words}")

    def _load_ignored_words(self) -> set:
        try:
            with open(self.persist_file, "r") as f:
                words = json.load(f)
                return set(words)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def _save_ignored_words(self):
        try:
            os.makedirs(os.path.dirname(self.persist_file), exist_ok=True)
            with open(self.persist_file, "w") as f:
                json.dump(list(self.ignored_words), f)
            print(f"Successfully saved ignored words to {self.persist_file}")
        except Exception as e:
            print(f"Error saving ignored words file: {e}")

    def add_ignored_word(self, word: str) -> None:
        with self._lock:
            self.ignored_words.add(word.lower())
            self._save_ignored_words()
            print(f"Added and persisted '{word}' to ignored words list.")

    def remove_ignored_word(self, word: str) -> None:
        with self._lock:
            if word.lower() in self.ignored_words:
                self.ignored_words.remove(word.lower())
                self._save_ignored_words()
                print(f"Removed and persisted '{word}' from ignored words list.")
            else:
                print(f"'{word}' not in ignored words list.")

    def _get_clean_words(self, transcript: str) -> List[str]:
        return transcript.lower().split()

    def should_interrupt(self, transcript: str, confidence: float, agent_is_speaking: bool) -> bool:
        words = self._get_clean_words(transcript)

        if not words:
            return False

        if any(word in self.interruption_commands for word in words):
            print(f"**LOG: VALID COMMAND INTERRUPTION** - Command '{transcript}' detected.")
            return True

        if agent_is_speaking:
            if confidence < self.confidence_threshold:
                print(f"**LOG: IGNORED LOW CONFIDENCE** - Confidence {confidence:.2f} < Threshold.")
                return False

            with self._lock:
                is_filler_only = all(word in self.ignored_words for word in words)

            if is_filler_only:
                print(f"**LOG: IGNORED FILLER** - Agent speaking, ignoring filler: '{transcript}'.")
                return False

            print(f"**LOG: VALID SPEECH INTERRUPTION** - Agent speaking, stopping for meaningful speech: '{transcript}'.")
            return True
        else:
            print(f"**LOG: SPEECH EVENT** - Agent quiet, registering speech: '{transcript}'.")
            return True
