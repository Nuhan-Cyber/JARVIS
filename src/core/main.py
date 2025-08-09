# jarvis-ai/src/core/main.py

import os
import sys
import speech_recognition as sr
import time
import tempfile
import subprocess
import keyboard
import queue # For threading communication
import threading
import json
from dateutil import parser
from datetime import datetime, timedelta
import tkinter as tk # Import tkinter
import translators as ts # Import the translators library

# Import sub-modules
from src.tts.a4f_local import A4F
from src.nlp.processor import NLPProcessor
from src.knowledge.manager import KnowledgeManager
from src.tasks.executor import TaskExecutor
from src.knowledge.reminder_manager import ReminderManager
from src.knowledge.alarm_manager import AlarmManager # NEW: Import AlarmManager
from src.core.session_manager import SessionManager
from src.ui.email_gui import EmailGUI # Import EmailGUI
from config import settings

class JarvisCore:
    """The main orchestrator for Jarvis AI, now with god-like thinking power and unbreakable resilience."""
    def __init__(self):
        print("Initializing Jarvis Core...")
        self.user_id = os.getlogin().upper()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.a4f_client = A4F()
        # self.translator = translate.Client(api_key=settings.GOOGLE_TRANSLATE_API_KEY) # No longer needed
        self._initialize_sub_modules()
        
        # Calibrate microphone
        with self.microphone as source:
            print("Calibrating microphone... Please be quiet.")
            self.recognizer.adjust_for_ambient_noise(source, duration=1.5)
        print("Microphone calibrated. Jarvis is ready.")

        # Input mode and hotkey listener
        self.input_mode = 'voice'
        self.input_mode_lock = threading.Lock()
        self.stop_hotkey_listener = threading.Event()
        self.hotkey_thread = threading.Thread(target=self._hotkey_listener_thread, daemon=True)
        self.hotkey_thread.start()
        
        # NEW: Alarm checker thread
        self.stop_alarm_checker = threading.Event()
        self.alarm_checker_thread = threading.Thread(target=self._alarm_checker_thread, daemon=True)
        self.alarm_checker_thread.start()

        self.should_exit = False
        self.current_language = "en" # Default output language is English
        self.input_language = "en" # Default input language is English. "en" for English, "bn" for Bengali
        self.speak(f"Jarvis is online and ready. All systems nominal. How may I assist you, sir?")

    def _alarm_checker_thread(self):
        """Periodically checks for and triggers due alarms."""
        print("Alarm checker thread started.")
        while not self.stop_alarm_checker.is_set():
            due_alarms = self.alarm_manager.get_due_alarms()
            for alarm in due_alarms:
                self.speak(f"Sir, your time is up! {alarm.get('message', '')}")
                self.task_executor._play_sound_file(alarm['file_path'])
                self.alarm_manager.mark_alarm_triggered(alarm['id'])
            time.sleep(1) # Check every second

    def _initialize_sub_modules(self):
        """Initializes all sub-modules, including the new KnowledgeManager."""
        print("Initializing sub-modules...")
        self.session_manager = SessionManager(session_id=self.user_id)
        self.knowledge_manager = KnowledgeManager()
        self.nlp_processor = NLPProcessor()
        self.reminder_manager = ReminderManager()
        self.alarm_manager = AlarmManager() # NEW: Initialize AlarmManager
        self.task_executor = TaskExecutor()
        print("Sub-modules initialized.")
        if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your_groq_api_key_here":
            print("WARNING: Groq API Key not set. NLP capabilities will be limited.")
        print(f"Jarvis initialized for user: {self.user_id}")

    def speak(self, text: str):
        """Converts text to speech at the configured speed and plays it."""
        if not self.a4f_client:
            print(f"TTS client not initialized. Cannot speak: '{text}'")
            return
        
        # Translate text to Bangla if current_language is "bn"
        if self.current_language == "bn":
            try:
                translated_text = ts.translate_text(query_text=text, translator='bing', to_language='bn')
                print(f"Jarvis speaking (Bangla): '{translated_text}'")
                text_to_speak = translated_text
            except Exception as e:
                print(f"Error translating to Bangla: {e}. Speaking in English instead.")
                text_to_speak = text
        else:
            print(f"Jarvis speaking: '{text}'")
            text_to_speak = text

        try:
            # The A4F client uses the specified voice for the given text, regardless of language.
            audio_bytes = self.a4f_client.audio.speech.create(
                model=settings.A4F_TTS_MODEL, input=text_to_speak, voice=settings.A4F_TTS_VOICE
            )
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio_file:
                audio_file_path = temp_audio_file.name
                temp_audio_file.write(audio_bytes)
            playback_command = ["ffplay", "-nodisp", "-autoexit", "-af", f"atempo={settings.TTS_SPEED}", audio_file_path]
            subprocess.run(playback_command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.remove(audio_file_path)
        except Exception as e:
            print(f"An error occurred during speech synthesis: {e}")

    def listen(self):
        """Listens for a command using the microphone."""
        with self.microphone as source:
            print("Listening for your command...")
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                print("Processing audio...")
                if self.input_language == "bn":
                    # Attempt to recognize in Bengali
                    try:
                        return self.recognizer.recognize_google(audio, language="bn-BD").lower()
                    except sr.UnknownValueError:
                        print("Could not understand Bengali audio. Trying English...")
                        # Fallback to English if Bengali recognition fails
                        return self.recognizer.recognize_google(audio).lower()
                else:
                    return self.recognizer.recognize_google(audio).lower()
            except sr.WaitTimeoutError: return None
            except sr.UnknownValueError: print("Could not understand audio."); return None
            except sr.RequestError as e: print(f"Speech recognition service error; {e}"); return None

    def _hotkey_listener_thread(self):
        """Runs in a separate thread to listen for the F3 key press."""
        print("Hotkey listener started (Press F3 to toggle input mode).")
        while not self.stop_hotkey_listener.is_set():
            if keyboard.is_pressed('f3'):
                with self.input_mode_lock:
                    self.input_mode = 'text' if self.input_mode == 'voice' else 'voice'
                    print(f"\n[SYSTEM] Switched to {self.input_mode.upper()} input mode.")
                keyboard.wait('f3', suppress=True)
            time.sleep(0.05)

    def get_user_input(self, prompt: str) -> str:
        """Gets input from the user, respecting the current input mode."""
        self.speak(prompt)
        self.session_manager.append_message("assistant", prompt)
        user_response = None
        while user_response is None:
            with self.input_mode_lock: current_mode = self.input_mode
            if current_mode == 'voice':
                user_response = self.listen()
            else:
                user_response = input(f"[{current_mode.upper()}] {prompt}: ").strip() or None
        self.session_manager.append_message("user", user_response)
        return user_response

    def process_command(self, command: str):
        """
        THE ULTIMATE ALGORITHM: Get the plan from the thinker, then execute it with unbreakable error handling.
        """
        if not command: return
        print(f"\nJarvis received command: '{command}'")
        self.session_manager.append_message("user", command)

        try:
            # Step 1: Get the perfect action plan from the AI's "brain"
            action_plan_json = self.nlp_processor.create_action_plan(
                prompt=command,
                chat_history=self.session_manager.get_full_context(),
                knowledge_base=self.knowledge_manager.get_all_knowledge_as_string()
            )
            
            plan = json.loads(action_plan_json)
            action = plan.get("action")
            entities = plan.get("entities", {})
        # The NLP processor already has a broad exception handler, so we only need to catch specific ones here.
        except Exception as e:
            # THE "GOD-LIKE" RESILIENCE PROTOCOL
            print(f"CRITICAL NETWORK ERROR: Could not connect to Groq API. {e}")
            self.speak("Sir, my connection to my higher consciousness is temporarily unavailable. I will proceed with a basic command execution protocol.")
            action = "execute_cmd"
            entities = {"command_description": command}
        
        except json.JSONDecodeError:
            print("CRITICAL: Failed to decode the action plan. Defaulting to command execution.")
            self.speak("My apologies, sir. My thought process was corrupted. I will attempt a basic execution.")
            action = "execute_cmd"
            entities = {"command_description": command}

        # Step 2: Execute the plan
        self.execute_action_plan(action, entities, command)

    def execute_action_plan(self, action: str, entities: dict, original_command: str):
        """Dynamically executes the action specified in the plan with intelligent self-correction."""
        print(f"Executing Action: '{action}' with Entities: {entities}")

        # --- Self-Correction Safety Net ---
        if action == "get_image" and not entities.get("image_query"):
            entities["image_query"] = self.get_user_input("Of course. What image would you like me to find?")
        # NEW self-correction for QR code
        if action == "generate_qr_code" and not entities.get("data"):
            entities["data"] = self.get_user_input("Of course. What text or link should I encode in the QR code?")
        
        action_map = {
            "get_weather": lambda e: self.task_executor._get_weather(e.get("location")),
            "get_time": lambda e: f"The current time is {time.strftime('%I:%M %p')}.",
            "get_date": lambda e: f"Today's date is {time.strftime('%A, %B %d, %Y')}.",
            "get_news": lambda e: self.task_executor._get_news(e.get("topic")),
            "get_stock_price": lambda e: self.task_executor._get_stock_price(e.get("symbol")),
            "get_nasa_apod": lambda e: self.task_executor._get_nasa_apod(),
            "get_image": lambda e: self.task_executor._fetch_and_download_image(e.get("image_query"), e.get("count", 1)),
            "generate_qr_code": lambda e: self.task_executor._generate_qr_code(e.get("data")),
            # Music Controls
            "play_music": lambda e: self.task_executor._play_music(e.get("song_name")),
            "pause_music": lambda e: self.task_executor._pause_music(),
            "stop_music": lambda e: self.task_executor._stop_music(),
            "next_song": lambda e: self.task_executor._next_song(),
            "previous_song": lambda e: self.task_executor._previous_song(),
            # Window Management
            "close_current_tab": lambda e: self.task_executor._close_current_tab(),
            "switch_window": lambda e: self.task_executor._switch_window(),
            "minimize_window": lambda e: self.task_executor._minimize_window(),
            "maximize_window": lambda e: self.task_executor._maximize_window(),
            "new_tab": lambda e: self.task_executor._new_tab(),
        }

        if action in action_map:
            response = action_map[action](entities)
            self.session_manager.append_message("assistant", response)
            self.speak(response)
        elif action == "direct_answer":
            response = self.nlp_processor.generate_direct_answer(
                prompt=original_command,
                chat_history=self.session_manager.get_full_context(),
                knowledge_base=self.knowledge_manager.get_all_knowledge_as_string()
            )
            self.session_manager.append_message("assistant", response)
            self.speak(response)
        elif action == "search_and_answer":
            self.handle_search_and_answer(entities, original_command)
        elif action == "remember_fact":
            fact = entities.get("fact")
            if fact and self.knowledge_manager.add_fact(fact):
                self.speak(f"I have remembered that, sir: {fact}")
            else:
                self.speak("I'm sorry, I was unable to remember that.")
        elif action == "set_reminder":
             task = entities.get("task")
             reminder_time = entities.get("time")

             # If task is not explicitly provided, use the original command as the task
             if not task:
                 task = original_command
                 self.speak("I didn't catch a specific task for the reminder, so I'll use your original request as the task.")

             # If reminder_time is not explicitly provided, try to infer or use a default
             if not reminder_time:
                 # Attempt to extract time from original_command if not already done by Groq
                 # This is a basic attempt; more sophisticated NLP would be needed for complex cases
                 if "today" in original_command.lower():
                     reminder_time = datetime.now().strftime("%Y-%m-%d 00:00:00") # Start of today
                 elif "tomorrow" in original_command.lower():
                     reminder_time = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d 00:00:00") # Start of tomorrow
                 elif "now" in original_command.lower() or "immediately" in original_command.lower():
                     reminder_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                 else:
                     user_input_time = self.get_user_input("When would you like to be reminded?")
                     try:
                         # Try to parse user input into a datetime object
                         parsed_user_time = parser.parse(user_input_time, fuzzy=True)
                         reminder_time = parsed_user_time.strftime("%Y-%m-%d %H:%M:%S")
                     except parser.ParserError:
                         self.speak("I couldn't understand that time. Please try again with a clearer time.")
                         return # Exit if time cannot be parsed

             if task and reminder_time:
                 if self.reminder_manager.add_reminder(task, reminder_time):
                     response = self.nlp_processor.generate_reminder_confirmation(task, reminder_time)
                 else:
                     response = "I had trouble setting that reminder. Please try again."
             else:
                 response = "I still don't have enough information to set a reminder. Please provide a task and a time."
             self.session_manager.append_message("assistant", response)
             self.speak(response)
        elif action == "list_reminders":
            reminders = self.reminder_manager.get_all_reminders(include_completed=False)
            if reminders:
                response_parts = ["Here are your active reminders, sir:"]
                for i, r in enumerate(reminders):
                    task_display = r.get("task", "unknown task")
                    if not task_display or task_display.lower() == "none specified":
                        task_display = "an unspecified task"

                    time_display = r.get("reminder_time_str", "an unspecified time")
                    if not time_display or time_display.lower() == "none specified":
                        time_display = "an unspecified time"
                    else:
                        try:
                            # Try to parse and format for better display
                            parsed_time = parser.parse(time_display, fuzzy=True)
                            # Format based on whether it's today, tomorrow, or a specific date
                            if parsed_time.date() == datetime.now().date():
                                time_display = parsed_time.strftime("today at %I:%M %p")
                            elif parsed_time.date() == (datetime.now() + timedelta(days=1)).date():
                                time_display = parsed_time.strftime("tomorrow at %I:%M %p")
                            else:
                                time_display = parsed_time.strftime("%B %d, %Y at %I:%M %p")
                        except parser.ParserError:
                            # If parsing fails, keep the original string
                            pass

                    response_parts.append(f"{i+1}. To {task_display} for {time_display}.")
                response = " ".join(response_parts)
            else:
                response = "You have no active reminders, sir."
            self.session_manager.append_message("assistant", response)
            self.speak(response)
        elif action == "delete_all_reminders":
            if self.reminder_manager.delete_all_reminders():
                response = "All reminders have been cleared, sir."
            else:
                response = "I encountered an issue while trying to clear all reminders."
            self.session_manager.append_message("assistant", response)
            self.speak(response)
        elif action == "trigger_email_gui":
            recipient = entities.get("recipient", "")
            subject = entities.get("subject", "")
            body = entities.get("body", "")

            # Create a dummy Tkinter root window (hidden)
            root = tk.Tk()
            root.withdraw() 

            # Launch the Email GUI
            email_gui = EmailGUI(root, recipient, subject, body)
            root.mainloop() # Start the Tkinter event loop
            root.destroy() # Destroy the root window after mainloop exits

            self.speak("Email window opened, sir.")
        elif action == "send_email":
            self.handle_email_intent(entities)
        elif action == "write_notepad":
            self.handle_notepad_intent(entities)
        elif action == "execute_cmd":
            command_description = entities.get("command_description", original_command)
            self.handle_command_execution(command_description)
        elif action == "set_language":
            language_code = entities.get("language_code", "en") # Default to English if not specified
            self._set_language(language_code)
        elif action == "set_alarm":
            self._set_alarm(entities, original_command)
        elif action == "toggle_input_language":
            self._toggle_input_language()
        elif action == "set_all_language":
            target_language = entities.get("target_language", "en") # Default to English if not specified
            self._set_all_language(target_language)
        elif action == "summarize_file":
            file_path = entities.get("file_path")
            if not file_path:
                file_path = self.get_user_input("Of course sir, I will try my best for summarizing the txt file. Please provide the path of your txt file:")
            
            if file_path:
                response = self.task_executor.summarize_file(file_path)
            else:
                response = "My apologies, I cannot proceed without a file path."
            
            self.session_manager.append_message("assistant", response)
            self.speak(response)
        elif action == "exit":
            self.speak("As you wish, sir. Powering down.")
            self.should_exit = True
        else:
            self.speak(f"I'm sorry, my analysis resulted in an unknown action: '{action}'. I cannot proceed.")

    def _search_and_answer_worker(self, query: str, original_command: str, result_queue: queue.Queue):
        """
        Worker thread to perform web search and generate an answer without blocking.
        """
        try:
            # Step 1: Perform the web search.
            search_results = self.task_executor.search_the_web(query)
            
            # Step 2: Generate the final answer based on search context.
            response = self.nlp_processor.generate_direct_answer(
                prompt=original_command,
                chat_history=self.session_manager.get_full_context(),
                knowledge_base=self.knowledge_manager.get_all_knowledge_as_string(),
                search_context=search_results
            )
            result_queue.put(response)
        except Exception as e:
            print(f"Error in search worker thread: {e}")
            result_queue.put("I'm sorry, sir. I encountered an error while searching the web.")

    def handle_search_and_answer(self, entities: dict, original_command: str):
        """
        Handles the search_and_answer action with ultra-fast parallel processing.
        """
        query = entities.get("query", original_command)
        result_queue = queue.Queue()

        worker_thread = threading.Thread(target=self._search_and_answer_worker, args=(query, original_command, result_queue))
        worker_thread.start()

        self.speak(f"Consulting the web for '{query}'. One moment, sir.")

        final_response = result_queue.get()
        worker_thread.join()

        self.session_manager.append_message("assistant", final_response)
        self.speak(final_response)

    def handle_command_execution(self, command_description: str):
        # PERFECTED: This logic now flawlessly handles the 'answer' output type.
        initial_ack = self.nlp_processor.generate_initial_cmd_acknowledgment(command_description)
        self.speak(initial_ack)
        self.session_manager.append_message("assistant", initial_ack)
        
        plan_json = self.nlp_processor.generate_cmd_command(command_description)
        if not plan_json:
            self.speak("I'm sorry, I could not devise a command for that request.")
            return
        
        try:
            plan = json.loads(plan_json)
            command_sequence = plan.get('commands', '').split('&&')
            output_type = plan.get('output_type', 'task')
        except json.JSONDecodeError:
            self.speak("I devised a plan, but it was malformed. I cannot proceed.")
            return
            
        final_result = None
        for cmd in command_sequence:
            cmd = cmd.strip()
            if not cmd: continue
            exec_result = self.task_executor._execute_cmd_command(cmd)
            final_result = exec_result
            if not exec_result['success']:
                break
        
        if final_result and final_result['success']:
            if output_type == 'answer' and final_result.get('output'):
                # This is the corrected logic path
                response = self.nlp_processor.generate_answer_from_output(command_description, final_result['output'])
            else:
                response = self.nlp_processor.generate_cmd_success_message(command_description)
        elif final_result:
            response = self.nlp_processor.generate_cmd_failure_message(command_description, final_result['error'])
        else:
            response = "An unknown error occurred, and I was unable to execute the command plan."
            
        self.session_manager.append_message("assistant", response)
        self.speak(response)

    def handle_email_intent(self, entities):
        recipient = entities.get("recipient") or self.get_user_input("Whom should I send the email to?")
        subject = entities.get("subject") or self.get_user_input("What is the subject?")
        body = entities.get("body")
        if not body:
            choice = self.get_user_input("Should I generate the body, or will you provide it?")
            if "generate" in choice:
                formality = "informal" if "informal" in self.get_user_input("Formal or informal?") else "formal"
                body = self.nlp_processor.generate_email_body(subject, formality)
            else:
                body = self.get_user_input("Please tell me the body of the email.")
        response = self.task_executor._send_email(recipient, subject, body) if recipient and subject and body else "Email cancelled."
        self.session_manager.append_message("assistant", response)
        self.speak(response)

    def handle_notepad_intent(self, entities):
        content = entities.get("content") or self.get_user_input("Of course. What should I write?")
        response = self.task_executor._write_to_notepad(content) if content else "Notepad command cancelled."
        self.speak(response)

    def _set_alarm(self, entities: dict, original_command: str):
        alarm_time_str = entities.get("time")
        message = entities.get("message", "Alarm")
        file_path = "C:/Users/NUHAN_CYBER/Desktop/JARVIS 2.0/ALARM/alarm.wav" # Hardcoded path

        if not alarm_time_str:
            self.speak("I need a time to set the alarm, sir.")
            return

        try:
            alarm_time = parser.parse(alarm_time_str)
            if alarm_time < datetime.now():
                self.speak("I cannot set an alarm in the past, sir.")
                return
            
            if self.alarm_manager.add_alarm(alarm_time, message, file_path):
                self.speak(f"Alarm set for {alarm_time.strftime('%I:%M %p on %A, %B %d, %Y')}. I will play the alarm sound and tell you when the time is up.")
            else:
                self.speak("I had trouble setting that alarm. Please try again.")
        except parser.ParserError:
            self.speak("I couldn't understand the time you provided for the alarm.")
        except Exception as e:
            self.speak(f"An error occurred while setting the alarm: {e}")

    def _set_language(self, language_code: str):
        if language_code == "bn":
            self.current_language = "bn"
            self.speak("Now I will be redirected to Bangla language.") # Confirmation message
            # The actual "আমি এখন বাংলায় কথা বলব।" will be spoken after translation in speak()
        elif language_code == "en":
            self.current_language = "en"
            self.speak("I will now speak in English.")
        else:
            self.speak("I'm sorry, I don't support that language yet.")

    def _toggle_input_language(self):
        if self.input_language == "en":
            self.input_language = "bn"
            self.speak("বাংলা ইনপুট মোড সক্রিয় করা হয়েছে।") # Bangla input mode activated.
        else:
            self.input_language = "en"
            self.speak("English input mode activated.")

    def _set_all_language(self, target_language: str):
        if target_language == "en":
            self.current_language = "en"
            self.input_language = "en"
            self.speak("Everything set to English.")
        elif target_language == "bn":
            self.current_language = "bn"
            self.input_language = "bn"
            self.speak("সবকিছু বাংলায় সেট করা হয়েছে।") # Everything set to Bengali.
        else:
            self.speak("I'm sorry, I don't support that language yet.")

    def run(self):
        """Starts the Jarvis listening loop with graceful exit handling."""
        while not self.should_exit:
            try:
                with self.input_mode_lock: current_mode = self.input_mode
                if current_mode == 'voice':
                    print(f"\n[VOICE MODE] Listening...")
                    command = self.listen()
                else:
                    command = input(f"\n[TEXT MODE] Type your command: ").strip().lower()
                
                if command:
                    self.process_command(command)
                
                if self.should_exit:
                    break
                time.sleep(0.1)
            except KeyboardInterrupt:
                print("\nShutdown sequence initiated by user.")
                self.should_exit = True
        
        self.stop_hotkey_listener.set()
        self.hotkey_thread.join()
        # --- NEW: Explicitly clean up the session file on exit ---
        self.session_manager.cleanup_session()
        print("Jarvis has powered down. Goodbye.")


if __name__ == "__main__":
    jarvis = JarvisCore()
    jarvis.run()