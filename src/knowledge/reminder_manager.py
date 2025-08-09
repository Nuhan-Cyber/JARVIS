# jarvis-ai/src/knowledge/reminder_manager.py

import os
import sys
import json
from datetime import datetime
import shutil # Added for robust file deletion

# Add the project root to the system path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from config import settings

class ReminderManager:
    """
    Manages reminders using a JSON file.
    """
    def __init__(self):
        self.reminders_file = os.path.join(
            settings.DATA_DIR, "user_data", "reminders.json"
        )
        self.reminders = self._load_reminders()
        print(f"Initializing Reminder Manager. Reminders will be saved to: {self.reminders_file}")
        self._migrate_from_db_if_needed()

    def _load_reminders(self) -> list[dict]:
        if not os.path.exists(self.reminders_file) or os.path.getsize(self.reminders_file) == 0:
            return []
        try:
            with open(self.reminders_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {self.reminders_file}. Starting with empty reminders.")
            return []

    def _save_reminders(self):
        os.makedirs(os.path.dirname(self.reminders_file), exist_ok=True)
        with open(self.reminders_file, "w", encoding="utf-8") as f:
            json.dump(self.reminders, f, indent=4)

    def _get_next_id(self) -> int:
        return max([r["id"] for r in self.reminders]) + 1 if self.reminders else 1

    def _migrate_from_db_if_needed(self):
        old_db_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "reminders.db"
        )
        if os.path.exists(old_db_path) and not self.reminders:
            print(f"Attempting to migrate reminders from old database: {old_db_path}")
            try:
                from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
                from sqlalchemy.orm import sessionmaker, declarative_base
                from sqlalchemy.exc import SQLAlchemyError

                Base = declarative_base()

                class OldReminder(Base):
                    __tablename__ = 'reminders'
                    id = Column(Integer, primary_key=True)
                    task = Column(String, nullable=False)
                    reminder_time_str = Column(String, nullable=False)
                    created_at = Column(DateTime, default=datetime.now)
                    completed = Column(Boolean, default=False)

                engine = create_engine(f'sqlite:///{old_db_path}')
                OldSession = sessionmaker(bind=engine)
                old_session = OldSession()

                old_reminders = old_session.query(OldReminder).all()
                if old_reminders:
                    print(f"Found {len(old_reminders)} reminders in old database. Migrating...")
                    for r in old_reminders:
                        new_reminder = {
                            "id": self._get_next_id(),
                            "task": r.task,
                            "reminder_time_str": r.reminder_time_str,
                            "created_at": r.created_at.isoformat(),
                            "completed": r.completed,
                            "announced": False,
                            "announced_today": False
                        }
                        self.reminders.append(new_reminder)
                    self._save_reminders()
                    print("Migration complete. Attempting to remove old database file.")
                    old_session.close() # Explicitly close the session
                    try:
                        os.remove(old_db_path)
                        print(f"Successfully removed old database file: {old_db_path}")
                    except OSError as e:
                        print(f"Warning: Could not remove old database file {old_db_path}: {e}. Please delete it manually.")
                else:
                    print("No reminders found in old database.")

            except ImportError:
                print("SQLAlchemy not installed. Cannot migrate from old database.")
            except SQLAlchemyError as e:
                print(f"Error during database migration: {e}")
            except Exception as e:
                print(f"An unexpected error occurred during migration: {e}")


    def add_reminder(self, task: str, reminder_time_str: str) -> bool:
        """
        Adds a new reminder to the JSON file.
        """
        new_id = self._get_next_id()
        new_reminder = {
            "id": new_id,
            "task": task,
            "reminder_time_str": reminder_time_str,
            "created_at": datetime.now().isoformat(),
            "completed": False,
            "announced": False, # New field
            "announced_today": False # New field for daily reminders
        }
        self.reminders.append(new_reminder)
        self._save_reminders()
        print(f"Reminder added: Task: '{task}', Time: '{reminder_time_str}'")
        return True

    def mark_reminder_announced(self, reminder_id: int, announced_today: bool = False) -> bool:
        """
        Marks a specific reminder as announced in the JSON file.
        """
        for reminder in self.reminders:
            if reminder["id"] == reminder_id:
                reminder["announced"] = True
                if announced_today:
                    reminder["announced_today"] = True
                self._save_reminders()
                print(f"Reminder {reminder_id} marked as announced.")
                return True
        print(f"Reminder {reminder_id} not found.")
        return False

    def get_all_reminders(self, include_completed: bool = False) -> list[dict]:
        """
        Retrieves all reminders from the JSON file.
        """
        if include_completed:
            return self.reminders
        else:
            return [r for r in self.reminders if not r["completed"]]

    def mark_reminder_completed(self, reminder_id: int) -> bool:
        """
        Marks a specific reminder as completed in the JSON file.
        """
        for reminder in self.reminders:
            if reminder["id"] == reminder_id:
                reminder["completed"] = True
                reminder["announced"] = True # Mark as announced when completed
                self._save_reminders()
                print(f"Reminder {reminder_id} marked as completed.")
                return True
        print(f"Reminder {reminder_id} not found.")
        return False

    def delete_reminder(self, reminder_id: int) -> bool:
        """
        Deletes a reminder from the JSON file by its ID.
        """
        initial_len = len(self.reminders)
        self.reminders = [r for r in self.reminders if r["id"] != reminder_id]
        if len(self.reminders) < initial_len:
            self._save_reminders()
            print(f"Reminder {reminder_id} deleted.")
            return True
        print(f"Reminder {reminder_id} not found.")
        return False

    def get_due_reminders(self) -> list[dict]:
        """
        Retrieves reminders that are due soon (all non-completed for now).
        """
        return [r for r in self.reminders if not r["completed"]]

    def delete_all_reminders(self) -> bool:
        """
        Deletes all reminders from the JSON file.
        """
        self.reminders = []
        self._save_reminders()
        print("All reminders deleted.")
        return True


if __name__ == "__main__":
    print("--- Testing ReminderManager with JSON ---")

    # Ensure settings.py is accessible for DATA_DIR
    if not hasattr(settings, 'DATA_DIR'):
        settings.DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
        os.makedirs(os.path.join(settings.DATA_DIR, "user_data"), exist_ok=True)

    manager = ReminderManager()

    # Add some test reminders
    print("\n--- Adding test reminders ---")
    manager.add_reminder("Buy groceries", "tomorrow morning")
    manager.add_reminder("Send email to John", "2025-07-07 10:00 AM")
    manager.add_reminder("Workout", "every day at 6 PM")

    # Get and print all reminders
    print("\n--- Retrieving all active reminders ---")
    active_reminders = manager.get_all_reminders(include_completed=False)
    if active_reminders:
        for r in active_reminders:
            print(r)
    else:
        print("No active reminders found.")

    # Mark one as completed
    print("\n--- Marking a reminder as completed (ID 1) ---")
    if active_reminders:
        first_id = active_reminders[0]["id"]
        manager.mark_reminder_completed(first_id)
        print(f"Reminders after marking ID {first_id} complete:")
        for r in manager.get_all_reminders():
            print(r)
    else:
        print("No reminders to mark complete.")

    # Get due reminders (for now, same as active)
    print("\n--- Getting 'due' reminders (all active for now) ---")
    due_reminders = manager.get_due_reminders()
    if due_reminders:
        for r in due_reminders:
            print(r)
    else:
        print("No 'due' reminders found.")

    # Delete a reminder
    print("\n--- Deleting a reminder (ID 2) ---")
    if len(active_reminders) > 1: # Ensure there's a second reminder to delete
        second_id = active_reminders[1]["id"]
        manager.delete_reminder(second_id)
        print(f"Reminders after deleting ID {second_id}:")
        for r in manager.get_all_reminders():
            print(r)
    else:
        print("Not enough reminders to delete a second one.")
