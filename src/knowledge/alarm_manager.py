import json
import os
from datetime import datetime
from dateutil import parser

class AlarmManager:
    def __init__(self, alarms_file='data/user_data/alarms.json'):
        self.alarms_file = alarms_file
        self._ensure_alarms_file_exists()
        self.alarms = self._load_alarms()
        print(f"Alarm Manager initialized. Alarms will be saved to: {self.alarms_file}")

    def _ensure_alarms_file_exists(self):
        os.makedirs(os.path.dirname(self.alarms_file), exist_ok=True)
        if not os.path.exists(self.alarms_file):
            with open(self.alarms_file, 'w') as f:
                json.dump([], f)

    def _load_alarms(self):
        with open(self.alarms_file, 'r') as f:
            alarms_data = json.load(f)
        # Convert time strings back to datetime objects for easier comparison
        for alarm in alarms_data:
            if 'time_str' in alarm:
                try:
                    alarm['time'] = parser.parse(alarm['time_str'])
                except parser.ParserError:
                    alarm['time'] = None # Handle parsing errors
        return alarms_data

    def _save_alarms(self):
        # Convert datetime objects to string before saving
        alarms_to_save = []
        for alarm in self.alarms:
            alarm_copy = alarm.copy()
            if 'time' in alarm_copy and isinstance(alarm_copy['time'], datetime):
                alarm_copy['time_str'] = alarm_copy['time'].isoformat()
                del alarm_copy['time'] # Remove datetime object before saving
            alarms_to_save.append(alarm_copy)
        
        with open(self.alarms_file, 'w') as f:
            json.dump(alarms_to_save, f, indent=4)

    def add_alarm(self, alarm_time: datetime, message: str, file_path: str) -> bool:
        alarm_id = len(self.alarms) + 1 # Simple ID generation
        new_alarm = {
            "id": alarm_id,
            "time": alarm_time,
            "time_str": alarm_time.isoformat(), # Store string for display/saving
            "message": message,
            "file_path": file_path,
            "triggered": False
        }
        self.alarms.append(new_alarm)
        self._save_alarms()
        return True

    def get_due_alarms(self) -> list:
        now = datetime.now()
        due_alarms = []
        for alarm in self.alarms:
            if not alarm.get("triggered", False) and alarm.get("time") and alarm["time"] <= now:
                due_alarms.append(alarm)
        return due_alarms

    def mark_alarm_triggered(self, alarm_id: int):
        for alarm in self.alarms:
            if alarm["id"] == alarm_id:
                alarm["triggered"] = True
                break
        self._save_alarms()

    def get_all_alarms(self, include_triggered: bool = False) -> list:
        if include_triggered:
            return self.alarms
        return [alarm for alarm in self.alarms if not alarm.get("triggered", False)]

    def delete_all_alarms(self) -> bool:
        self.alarms = []
        self._save_alarms()
        return True
