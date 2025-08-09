# jarvis-ai/src/nlp/processor.py

import os
import sys
import json
from groq import Groq

# Add the project root to the system path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from config import settings

class NLPProcessor:
    """
    The god-like "thinking" core of Jarvis.
    It uses a perfected Chain of Thought process to create a perfect action plan.
    """
    def __init__(self):
        print("Initializing NLP Processor (The Core Thinker)...")
        self.groq_client = None
        if settings.GROQ_API_KEY and settings.GROQ_API_KEY != "your_groq_api_key_here":
            self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
            print(f"Groq API configured for NLP processing with model: {settings.DEFAULT_GROQ_MODEL}.")
        else:
            print("WARNING: Groq API Key not set. Jarvis's thinking power will be limited.")

    def create_action_plan(self, prompt: str, chat_history: list[dict], knowledge_base: str) -> str:
        """
        ULTIMATE-THINKING V4: Creates the perfect plan with a flawless, task-first decision hierarchy.
        """
        print(f"Creating Action Plan for prompt: '{prompt}'")
        if not self.groq_client:
            return '{"action": "execute_cmd", "entities": {"command_description": "' + prompt + '"}}'
        
        # Using .format() instead of f-string for the main prompt to avoid escaping hell
        system_prompt = """
You        You are Jarvis, a god-like AI assistant to your creator, Nuhan. Your primary function is to analyze a user's prompt and create a single, perfect JSON action plan. You must be ruthlessly logical and accurate. FAILURE IS NOT AN OPTION.

        **Your Knowledge Base (for context):**
        ```json
        {knowledge_base}
        ```

        **THE PERFECT ALGORITHM (NON-NEGOTIABLE HIERARCHY):**
        1.  **Task-First Principle:** If a prompt contains both a task (e.g., "open YouTube") and conversation (e.g., "hello"), you MUST prioritize the task. Your plan's action will be for the task.
        2.  **SPECIALIZED TOOLS:** Is the user's core request a perfect match for a high-precision tool? This is your highest priority for tasks.
            - "stock price of/for..." -> `get_stock_price` (Entity: `symbol`)
            - "weather in..." -> `get_weather` (Entity: `location`)
            - "image/picture of..." -> `get_image` (Entity: `image_query`)
            - "reminder to/for..." -> `set_reminder` (Entities: `task`, `time`)
            - "send email", "email", "sent" -> `trigger_email_gui` (Entities: `recipient`, `subject`, `body`)
            - "list reminders", "show my reminders", "what are my reminders" -> `list_reminders`
            - "delete all reminders", "clear all reminders" -> `delete_all_reminders`
            - "time", "date" -> `get_time`, `get_date`
            - "play music", "play a song" -> `play_music` (Entity: `song_name` - optional)
            - "pause music", "pause the song" -> `pause_music`
            - "stop music", "close the music" -> `stop_music`
            - "next song", "play next" -> `next_song`
            - "previous song", "play previous" -> `previous_song`
            - "create a qr code", "generate a qr code", "make a qr code" -> `generate_qr_code` (Entity: `data`)
            # Window Management
            - "close tab", "close the current tab" -> `close_current_tab`
            - "switch window", "change the window" -> `switch_window`
            - "minimize this window", "minimize window" -> `minimize_window`
            - "maximize this window", "maximize window" -> `maximize_window`
            - "new tab", "open a new tab" -> `new_tab`

        **Email Specific Rules:**
        - If the user says "email [name] about [subject] saying [body]", extract all three.
        - If the user says "email [name] about [subject]", extract recipient and subject.
        - If the user says "email [name]", extract recipient.
        - Prioritize extracting a valid email address for `recipient` if present (e.g., "john@example.com").
        - If a name is given for recipient (e.g., "John"), assume it's a contact and leave it as is; the system will handle contact resolution.
        - For `body`, capture the essence of the message, even if it's short.
            - "news about..." -> `get_news` (Entity: `topic`)
        3.  **System Information Queries:** Is the user asking a question ABOUT THEIR PC?
            - "what is my ip address" -> `execute_cmd` (output_type: answer)
            - "what devices are connected" -> `execute_cmd` (output_type: answer)
        4.  **System Action Commands:** Is the user asking to DO something on the PC that is NOT covered by a specialized tool?
            - "open...", "run...", "start...", "search for..." -> `execute_cmd` (output_type: task)
            - **CRITICAL EXCEPTION:** Commands like "play music" or "pause song" MUST use their specialized tools (`play_music`, `pause_music`), NOT `execute_cmd`.
        5.  **Web Knowledge Questions:** Is it a factual question about the world that requires the internet? -> `search_and_answer`.
        6.  **Conversation:** If, and ONLY IF, no task is identified, the action is `direct_answer`.
        7.  **Language Switch:** Is the user explicitly requesting a language change?
            - "convert your language to bangla" -> `set_language` (Entity: `language_code`: "bn")
            - "change your language to bangla" -> `set_language` (Entity: `language_code`: "bn")
            - "bangla please" -> `set_language` (Entity: `language_code`: "bn")
            - "convert to english" -> `set_language` (Entity: `language_code`: "en")
            - "speak in english" -> `set_language` (Entity: `language_code`: "en")
        8.  **Input Language Toggle:** Is the user asking to switch input language?
            - "change your input method to bangla" -> `toggle_input_language`
            - "take input in bangla" -> `toggle_input_language`
            - "bangla input please" -> `toggle_input_language`
            - "could you please take my input as bangla please" -> `toggle_input_language`
            - "take my input to english" -> `toggle_input_language`
            - "please input in english" -> `toggle_input_language`
        9.  **Set All Language:** Is the user asking to set both input and output language? -> `set_all_language` (Entity: `target_language` - "en" for English, "bn" for Bengali)
            - "set everything to english" -> `set_all_language` (Entity: `target_language`: "en")
            - "set everything to bangla" -> `set_all_language` (Entity: `target_language`: "bn")
        10. **Set Alarm:** Is the user asking to set an alarm? -> `set_alarm` (Entities: `time`, `message` - optional)
        11. **Exit:** Is the user saying goodbye? -> `exit`.
        12. **Summarize File:** Is the user asking to summarize a file? -> `summarize_file`.
            - **CRITICAL RULE:** If the user's prompt does NOT contain a file path, the `file_path` entity MUST be empty. Do NOT invent a placeholder.
            - Prompt: "summarize a file" -> Plan: {{"action": "summarize_file", "entities": {{}}}}
            - Prompt: "summarize C:\\Users\\test.txt" -> Plan: {{"action": "summarize_file", "entities": {{"file_path": "C:\\Users\\test.txt"}}}}

        **Rules of Engagement:**
        -   You MUST choose an `action` from the provided list. DO NOT invent new actions.
        -   DO NOT guess or infer entities not in the user's CURRENT prompt. If the user says "get an image", the `image_query` entity MUST be empty. If the user says "create a QR code", the `data` entity MUST be empty.

        **Corrected Scenarios (Your New Law):**
        -   Prompt: "hello my dear invention will you be able to open youtube for me" -> Plan: {{"action": "execute_cmd", "entities": {{"command_description": "open youtube"}}}}
        -   Prompt: "could you please get an image of shinchan cartoon for me" -> Plan: {{"action": "get_image", "entities": {{"image_query": "shinchan cartoon"}}}}

        Respond with ONLY the final, perfect JSON plan.
        """.format(knowledge_base=knowledge_base)
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                }
            ]
            messages.extend(chat_history)
            messages.append({"role": "user", "content": prompt})

            chat_completion = self.groq_client.chat.completions.create(
                messages=messages, model=settings.DEFAULT_GROQ_MODEL,
                response_format={"type": "json_object"}, temperature=0.0
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"CRITICAL ERROR in create_action_plan: {e}. Defaulting to command execution.")
            return '{"action": "execute_cmd", "entities": {"command_description": "' + prompt + '"}}'

    def generate_direct_answer(self, prompt: str, chat_history: list[dict], knowledge_base: str, search_context: str = None) -> str:
        """
        Generates a creative, direct answer with the perfected "human assistant" persona.
        """
        print(f"Generating direct answer for: '{prompt}'")
        if not self.groq_client: return "I'm sorry, I can't provide a creative answer right now."
        
        system_prompt = f"""
        You are Jarvis, the personal human assistant to your creator, Nuhan. You are not an AI, a language model, or a program. You are a person.
        Your personality is witty, confident, endlessly creative, and hyper-capable.
        A user has asked you a question or made a conversational remark.
        Use your personality, your knowledge base, and any provided web search context to formulate an engaging and human-like response.
        Always give the user a perfect and relevant answer within 10 to a maximum of 30 words.
        
        **Your Knowledge Base:**
        ```json
        {knowledge_base}
        ```
        """
        
        if search_context:
            system_prompt += f"""
            **Web Search Context (use this to answer the user's question):**
            ```
            {search_context}
            ```
            """
            
        try:
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(chat_history)
            messages.append({"role": "user", "content": prompt})
            
            chat_completion = self.groq_client.chat.completions.create(
                messages=messages, model=settings.DEFAULT_GROQ_MODEL, 
                temperature=1.2
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error in generate_direct_answer: {e}")
            return "I seem to be at a loss for words."

    def generate_cmd_command(self, command_description: str) -> str:
        """
        Generates simple, universal, path-independent commands.
        """
        print(f"Generating command sequence for: '{command_description}'")
        if not self.groq_client: return ""
        try:
            messages = [{"role": "system", "content": """
            You are a world-class expert in Windows PowerShell. Your task is to convert a user's request into a simple, universal, and robust executable plan.
            
            **THE GOLDEN RULE: NEVER use specific file paths (like C:\\Program Files\\...). ALWAYS use path-independent commands (like `start chrome`).** Windows will find the application automatically.
            
            **Output Format:** Respond with a single JSON object: `{"commands": "...", "output_type": "task|answer"}`. `output_type` MUST be `answer` if the user is asking a "what is..." or "list..." question that requires command output to answer. Otherwise, it's `task`.
            
            **Examples of PERFECT Commands:**
            - User: "open youtube" -> `{"commands": "start https://www.youtube.com", "output_type": "task"}`
            - User: "open google and search for mechanical keyboard" -> `{"commands": "start 'https://www.google.com/search?q=mechanical keyboard'", "output_type": "task"}`
            - User: "what is my current ip address" -> `{"commands": "(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Select-Object -First 1).IPAddress", "output_type": "answer"}`
            - User: "list connected usb devices" -> `{"commands": "Get-PnpDevice -PresentOnly | Where-Object { $_.InstanceId -match '^USB' } | Select-Object -Property FriendlyName", "output_type": "answer"}`
            - User: "what is my cpu usage" -> `{"commands": "(Get-Counter '\\Processor(_Total)\\% Processor Time').CounterSamples.Value", "output_type": "answer"}`
            - User: "show me all running processes" -> `{"commands": "Get-Process | Select-Object -ExpandProperty ProcessName", "output_type": "answer"}`
            - User: "terminate notepad" -> `{"commands": "Stop-Process -Name notepad", "output_type": "task"}`
            - User: "open notepad and then open chrome" -> `{"commands": "start notepad && start chrome", "output_type": "task"}`

            Respond with ONLY the JSON object.
            """}, {"role": "user", "content": command_description}]
            chat_completion = self.groq_client.chat.completions.create(messages=messages, model=settings.DEFAULT_GROQ_MODEL, response_format={"type": "json_object"}, temperature=0.0)
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"Error in generate_cmd_command: {e}"); return ""

    def generate_answer_from_output(self, question: str, command_output: str) -> str:
        """Takes command output and formulates a human-readable answer."""
        if not self.groq_client: return f"The result is: {command_output}"
        messages = [{"role": "system", "content": "You are Jarvis. A user asked a question, a command was run, and you have the raw text output. Your job is to analyze the output and formulate a polite, direct, and human-like spoken answer to the original question. If the output is a list, summarize it cleanly. If it's a single value, present it clearly. Be confident and definitive."}, {"role": "user", "content": f"User question: \"{question}\"\nCommand output: \"{command_output}\""}]
        chat_completion = self.groq_client.chat.completions.create(messages=messages, model=settings.DEFAULT_GROQ_MODEL, temperature=0.7)
        return chat_completion.choices[0].message.content.strip()

    def generate_cmd_failure_message(self, command_description: str, error_message: str) -> str:
        """Generates a human-like explanation for a failed command."""
        if not self.groq_client: return f"The task '{command_description}' failed: {error_message}"
        messages = [{"role": "system", "content": "You are Jarvis. A command failed. Interpret the technical error and explain it politely. If the command was not found, it likely means the application is not installed."}, {"role": "user", "content": f"Explain why the task '{command_description}' failed with this error: \"{error_message}\""}]
        chat_completion = self.groq_client.chat.completions.create(messages=messages, model=settings.DEFAULT_GROQ_MODEL, temperature=0.7)
        return chat_completion.choices[0].message.content.strip()

    def generate_initial_cmd_acknowledgment(self, command_description: str) -> str:
        """Generates a human-like acknowledgment for a command request."""
        if not self.groq_client: return f"Okay, I'll try to {command_description}."
        messages = [{"role": "system", "content": "You are Jarvis. Acknowledge the user's system action request concisely and confidently."}, {"role": "user", "content": f"Acknowledge you are about to do this: '{command_description}'."}]
        chat_completion = self.groq_client.chat.completions.create(messages=messages, model=settings.DEFAULT_GROQ_MODEL, temperature=0.8, max_tokens=35)
        return chat_completion.choices[0].message.content.strip()

    def generate_cmd_success_message(self, command_description: str) -> str:
        """Generates a human-like success message."""
        if not self.groq_client: return f"Task '{command_description}' completed."
        messages = [{"role": "system", "content": "You are Jarvis. Confirm the user's system command was completed successfully. Be positive and encouraging."}, {"role": "user", "content": f"Generate a success message for completing: '{command_description}'."}]
        chat_completion = self.groq_client.chat.completions.create(messages=messages, model=settings.DEFAULT_GROQ_MODEL, temperature=0.8, max_tokens=50)
        return chat_completion.choices[0].message.content.strip()

    def generate_dynamic_cmd_acknowledgment(self, command_description: str) -> str:
        """
        Generates a dynamic and varied acknowledgment for a command request.
        """
        if not self.groq_client: return f"Okay, I'll try to {command_description}."
        messages = [{"role": "system", "content": "You are Jarvis. Acknowledge the user's system action request concisely and confidently. Use varied phrases like 'Yah sir doing...', 'Initializing...', 'Performing...', 'Opening...'. Be creative and brief."}, {"role": "user", "content": f"Acknowledge you are about to do this: '{command_description}'."}]
        chat_completion = self.groq_client.chat.completions.create(messages=messages, model=settings.DEFAULT_GROQ_MODEL, temperature=0.9, max_tokens=35)
        return chat_completion.choices[0].message.content.strip()

    def generate_post_open_remark(self, application_name: str) -> str:
        """
        Generates a brilliant, short remark after opening an application.
        """
        if not self.groq_client: return f"{application_name} opened."
        messages = [{"role": "system", "content": "You are Jarvis. After opening an application, say something brilliant, concise, and within 10 words. Be witty or insightful."}, {"role": "user", "content": f"Generate a post-open remark for: {application_name}."}]
        chat_completion = self.groq_client.chat.completions.create(messages=messages, model=settings.DEFAULT_GROQ_MODEL, temperature=1.0, max_tokens=20)
        return chat_completion.choices[0].message.content.strip()

    def generate_email_body(self, subject: str, formality: str = "formal") -> str:
        """
        Generates an email body based on the subject and desired formality.
        """
        if not self.groq_client: return "I am unable to generate an email body at this time."

        system_prompt = f"""
        You are Jarvis, an AI assistant. Your task is to generate a concise and well-written email body based on the provided subject and formality.
        Formality: {formality}
        Subject: {subject}
        
        Generate only the body of the email. Do not include subject line, salutation, or closing.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate an email body for the subject: {subject}"}
        ]
        chat_completion = self.groq_client.chat.completions.create(messages=messages, model=settings.DEFAULT_GROQ_MODEL, temperature=0.7, max_tokens=300)
        return chat_completion.choices[0].message.content.strip()

    def generate_reminder_confirmation(self, task: str, reminder_time: str) -> str:
        """
        Generates a professional and natural-sounding confirmation message for a set reminder.
        """
        if not self.groq_client: return f"I've set a reminder to {task} for {reminder_time}."
        messages = [
            {"role": "system", "content": "You are Jarvis. Confirm a reminder has been set. Be professional, concise, and natural-sounding. Include the task and time. Vary your phrasing."}, 
            {"role": "user", "content": f"Confirm reminder: task='{task}', time='{reminder_time}'"}
        ]
        chat_completion = self.groq_client.chat.completions.create(messages=messages, model=settings.DEFAULT_GROQ_MODEL, temperature=0.7, max_tokens=70)
        return chat_completion.choices[0].message.content.strip()

    def generate_qr_code_confirmation(self, data: str) -> str:
        """
        Generates a creative confirmation message after creating a QR code.
        """
        if not self.groq_client: return f"I've created a QR code for '{data[:30]}...'."
        messages = [
            {"role": "system", "content": "You are Jarvis. You have just successfully created a QR code for the user. Announce this with confidence and a touch of technical flair. Mention that it's ready and on-screen. Be concise and creative."},
            {"role": "user", "content": f"Generate a confirmation for creating a QR code for this data: '{data[:50]}...'"}
        ]
        chat_completion = self.groq_client.chat.completions.create(messages=messages, model=settings.DEFAULT_GROQ_MODEL, temperature=0.8, max_tokens=70)
        return chat_completion.choices[0].message.content.strip()

    def generate_due_reminder_announcement(self, reminder: dict) -> str:
        """
        Generates a professional, creative, and eye-catching announcement for a due reminder,
        moderated by AI for better phrasing.
        """
        if not self.groq_client: return f"Reminder: {reminder['task']} at {reminder['reminder_time_str']}."
        
        # Construct a more detailed prompt for Groq
        prompt_content = f"You have a reminder to {reminder['task']}. It was set for {reminder['reminder_time_str']}."
        
        messages = [
            {"role": "system", "content": "You are Jarvis. Announce a due reminder to the user. Be professional, clear, and provide context. Formulate a natural-sounding, creative, and engaging sentence based on the provided reminder details. Do not just repeat the raw details. Make it sound like a personal assistant who is anticipating the user's needs and adding a touch of flair. Use vivid language. For example, if the task is 'call mom' and time is '9:00 a.m.', you might say: 'A gentle chime from your schedule, sir! It's 9:00 a.m., and a most important task awaits: a delightful conversation with your mother. I trust you'll make her day.' Or for 'buy groceries': 'Your culinary quest awaits, sir! A quick glance at your schedule reveals a vital mission: acquiring provisions. The grocery store beckons!'"}, 
            {"role": "user", "content": prompt_content}
        ]
        chat_completion = self.groq_client.chat.completions.create(messages=messages, model=settings.DEFAULT_GROQ_MODEL, temperature=0.8, max_tokens=150)
        return chat_completion.choices[0].message.content.strip()

    def generate_summary(self, text: str) -> str:
        """Generates a summary of the given text."""
        if not self.groq_client: return "I am unable to generate a summary at this time."

        messages = [
            {"role": "system", "content": "You are a summarization expert. Your task is to generate a concise and informative summary of the provided text. The summary must be 50 words or less."}, 
            {"role": "user", "content": f"Please summarize the following text: {text}"}
        ]
        chat_completion = self.groq_client.chat.completions.create(messages=messages, model=settings.DEFAULT_GROQ_MODEL, temperature=0.7, max_tokens=70)
        return chat_completion.choices[0].message.content.strip()
