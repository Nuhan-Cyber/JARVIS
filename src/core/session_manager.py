# jarvis-ai/src/core/session_manager.py

import os
import tempfile
from datetime import datetime
import json # For serializing/deserializing messages to/from file

class SessionManager:
    """
    Manages the conversational context for a single session, storing it in a temporary file.
    It handles appending messages, retrieving the full context, trimming context for LLM limits,
    and cleaning up the session file.
    """
    # Maximum number of lines/messages to keep in context.
    # This is a simple line-based truncation. For more advanced, consider token counting.
    MAX_CONTEXT_LINES = 50 

    def __init__(self, session_id: str = None):
        # If no session_id is provided, generate a unique one using timestamp
        self.session_id = session_id if session_id else datetime.now().strftime("%Y%m%d%H%M%S%f")
        
        # Create a temporary directory for session files to keep them organized
        # This directory will be within the system's temp folder.
        self.session_dir = os.path.join(tempfile.gettempdir(), "jarvis_sessions")
        os.makedirs(self.session_dir, exist_ok=True) # Ensure the directory exists

        # Define the path for this session's context file
        self.context_file_path = os.path.join(self.session_dir, f"session_{self.session_id}.jsonl")

        # Ensure a fresh session by deleting any old context file from a previous run.
        if os.path.exists(self.context_file_path):
            try:
                os.remove(self.context_file_path)
            except OSError as e:
                print(f"Warning: Could not remove pre-existing session file: {e}")

        print(f"Session Manager initialized for a new session. Context will be stored in: {self.context_file_path}")

        # Internal list to hold messages as dictionaries, e.g., [{"role": "user", "content": "..."}]
        self.messages = []

    def _save_context_to_file(self):
        """Saves the current self.messages list back to the context file."""
        try:
            with open(self.context_file_path, 'w', encoding='utf-8') as f:
                for message in self.messages:
                    f.write(json.dumps(message) + '\n') # Write each message as a JSON line
            print(f"Saved {len(self.messages)} messages to context file.")
        except Exception as e:
            print(f"Error saving context to file: {e}")

    def _trim_context(self):
        """
        Trims the self.messages list to ensure it doesn't exceed MAX_CONTEXT_LINES.
        Keeps the most recent messages.
        """
        if len(self.messages) > self.MAX_CONTEXT_LINES:
            # Keep only the latest MAX_CONTEXT_LINES messages
            self.messages = self.messages[-self.MAX_CONTEXT_LINES:]
            print(f"Context trimmed. Keeping last {self.MAX_CONTEXT_LINES} messages.")

    def append_message(self, role: str, content: str):
        """
        Appends a new message (user or AI) to the session context.
        Role can be "user" or "assistant".
        """
        new_message = {"role": role, "content": content}
        self.messages.append(new_message)
        self._trim_context() # Trim after adding the new message
        self._save_context_to_file() # Save the updated (and trimmed) context to file
        print(f"Appended to context: {role}: {content[:50]}...") # Log first 50 chars

    def get_full_context(self) -> list[dict]:
        """
        Returns the current full conversational context as a list of message dictionaries.
        This list is already trimmed and up-to-date.
        """
        return self.messages

    def cleanup_session(self):
        """
        Deletes the temporary session context file.
        """
        try:
            if os.path.exists(self.context_file_path):
                os.remove(self.context_file_path)
                print(f"Session context file '{self.context_file_path}' deleted.")
            else:
                print(f"No context file found to delete for session {self.session_id}.")
        except Exception as e:
            print(f"Error deleting context file: {e}")

    def __del__(self):
        """Ensures cleanup is attempted when the object is garbage collected."""
        # This is a fallback; explicit cleanup_session() is preferred.
        # It's important to call cleanup_session() explicitly in main.py's run loop.
        self.cleanup_session()

if __name__ == "__main__":
    # Test the Advanced SessionManager
    print("--- Testing Advanced SessionManager ---")
    
    # Create a session
    session_mgr = SessionManager(session_id="advanced_test_session_123")

    # Append some messages
    session_mgr.append_message("user", "Hello Jarvis, how are you?")
    session_mgr.append_message("assistant", "I'm doing great, thank you! How can I help?")
    session_mgr.append_message("user", "What is the capital of Japan?")
    session_mgr.append_message("assistant", "The capital of Japan is Tokyo.")
    
    # Test trimming by adding many messages
    print("\n--- Testing Context Trimming ---")
    for i in range(SessionManager.MAX_CONTEXT_LINES + 5):
        session_mgr.append_message("user", f"Test message {i}")
        session_mgr.append_message("assistant", f"Response {i}")

    # Get full context (should be trimmed)
    print("\n--- Full Context (Trimmed) ---")
    full_context = session_mgr.get_full_context()
    for msg in full_context:
        print(f"{msg['role']}: {msg['content']}")
    print(f"Total messages in context: {len(full_context)}")
    assert len(full_context) <= SessionManager.MAX_CONTEXT_LINES, "Context not trimmed correctly!"

    # Clean up the session file
    print("\n--- Cleaning up session ---")
    session_mgr.cleanup_session()

    # Verify file is deleted
    if not os.path.exists(session_mgr.context_file_path):
        print("Test file successfully deleted.")
    else:
        print("Test file NOT deleted.")

    # Test loading from existing file (if any was left from a previous run)
    print("\n--- Testing Session Reload ---")
    session_mgr_reload = SessionManager(session_id="advanced_test_session_reload")
    session_mgr_reload.append_message("user", "This is a reloaded session message.")
    print(f"Reloaded session context: {session_mgr_reload.get_full_context()}")
    session_mgr_reload.cleanup_session()
