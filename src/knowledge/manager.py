# jarvis-ai/src/knowledge/manager.py

import os
import json
from config import settings

class KnowledgeManager:
    """
    Manages Jarvis's persistent knowledge base (self-learning).
    It reads from and writes to a JSON file to remember facts across sessions.
    """
    def __init__(self):
        # Define the path to the knowledge file in the project's data directory
        self.knowledge_file_path = os.path.join(settings.DATA_DIR, 'knowledge.json')
        self.knowledge = self._load_knowledge()

    def _load_knowledge(self) -> dict:
        """Loads knowledge from the JSON file. Creates it if it doesn't exist."""
        if os.path.exists(self.knowledge_file_path):
            try:
                with open(self.knowledge_file_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("Warning: Knowledge file is corrupted. Starting with a fresh one.")
                return self._create_default_knowledge()
        else:
            return self._create_default_knowledge()

    def _create_default_knowledge(self) -> dict:
        """Creates a default knowledge structure."""
        default_data = {
            "creator": "Nuhan Cyber",
            "user_profile": {
                "name": os.getlogin().upper()
            },
            "facts": [],
            "preferences": {}
        }
        self.save_knowledge(default_data)
        return default_data

    def save_knowledge(self, data: dict = None):
        """Saves the current knowledge base to the JSON file."""
        if data is None:
            data = self.knowledge
        with open(self.knowledge_file_path, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Knowledge base saved to {self.knowledge_file_path}")

    def add_fact(self, fact: str):
        """Adds a new fact to the knowledge base."""
        if 'facts' not in self.knowledge:
            self.knowledge['facts'] = []
        
        if fact not in self.knowledge['facts']:
            self.knowledge['facts'].append(fact)
            self.save_knowledge()
            print(f"New fact learned and saved: '{fact}'")
            return True
        return False

    def update_user_profile(self, key: str, value: str):
        """Updates a key in the user's profile."""
        if 'user_profile' not in self.knowledge:
            self.knowledge['user_profile'] = {}
        self.knowledge['user_profile'][key] = value
        self.save_knowledge()

    def get_all_knowledge_as_string(self) -> str:
        """Returns the entire knowledge base as a formatted string for the AI's context."""
        return json.dumps(self.knowledge, indent=2)