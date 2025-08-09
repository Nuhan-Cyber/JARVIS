# jarvis-ai/src/tasks/executor.py

import os
import sys
import requests
import json
from datetime import datetime
import subprocess # For executing CMD commands
import pyautogui # For GUI automation
import time # For delays
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import webbrowser

# Add the project root to the system path to allow imports from config, src, etc.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from config import settings
from src.tools.qr_code_generator import generate_qr_code
from src.tools.music_player import MusicPlayer
from src.nlp.processor import NLPProcessor # Import NLPProcessor

class TaskExecutor:
    """
    Executes various tasks based on identified intents and extracted entities.
    This includes making API calls to external services and running system commands.
    """
    def __init__(self):
        print("Initializing Task Executor...")
        # API keys are loaded from settings
        self.news_api_key = settings.NEWS_API_KEY
        self.nasa_api_key = settings.NASA_API_KEY
        self.alpha_vantage_api_key = settings.ALPHA_VANTAGE_API_KEY
        self.google_cse_api_key = settings.GOOGLE_CSE_API_KEY
        self.google_cse_id = settings.GOOGLE_CSE_CX_ID
        self.openweathermap_api_key = settings.OPENWEATHERMAP_API_KEY
        self.unsplash_access_key = settings.UNSPLASH_ACCESS_KEY
        self.nlp_processor = NLPProcessor() # Initialize the NLP Processor
        self.music_player = MusicPlayer() # Initialize the Music Player
        self.serper_dev_api_key = settings.SERPER_DEV_API_KEY # NEW
        
        # Ensure download directory exists
        os.makedirs(settings.IMAGE_DOWNLOAD_PATH, exist_ok=True)


    def execute_task(self, intent: str, entities: dict) -> str:
        """
        Executes a specific task based on the detected intent and entities.
        """
        print(f"Task Executor received intent: '{intent}' with entities: {entities}")
        response = "I'm sorry, I don't know how to perform that specific task yet."

        if intent == "get_weather":
            location = entities.get("location")
            response = self._get_weather(location)
        elif intent == "get_news":
            topic = entities.get("topic")
            response = self._get_news(topic)
        elif intent == "get_stock_price":
            symbol = entities.get("symbol")
            response = self._get_stock_price(symbol)
        elif intent == "get_nasa_apod":
            response = self._get_nasa_apod()
        elif intent == "search_web": # Old search, kept for compatibility if needed
            query = entities.get("query")
            response = self._legacy_search_web(query)
        elif intent == "get_image":
            image_query = entities.get("image_query")
            count = entities.get("count", 1) # Default to 1 image if not specified
            response = self._fetch_and_download_image(image_query, count)
        elif intent == "write_notepad":
            content = entities.get("content")
            response = self._write_to_notepad(content)
        elif intent == "send_email":
            recipient = entities.get("recipient")
            subject = entities.get("subject")
            body = entities.get("body")
            response = self._send_email(recipient, subject, body)
        return response

    def _get_weather(self, location: str = None) -> str:
        """Fetches live weather information using OpenWeatherMap API."""
        if not self.openweathermap_api_key:
            return "My OpenWeatherMap API key is not configured."

        if not location:
            return "Please specify a city to get the weather."

        api_url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={self.openweathermap_api_key}&units=metric"
        try:
            res = requests.get(api_url)
            res.raise_for_status()
            data = res.json()
            if data.get("cod") != 200:
                return f"Sorry, I couldn't find the weather for {location}."
            return f"The weather in {data['name']} is {data['weather'][0]['description']} with a temperature of {data['main']['temp']:.1f}°C."
        except Exception as e:
            return f"Sorry, I couldn't get the weather due to an error: {e}"

    def _get_news(self, topic: str = None) -> str:
        """Fetches top news headlines using News API."""
        if not self.news_api_key:
            return "My News API key is not configured."
        query_param = f"q={topic}" if topic else "country=us"
        url = f"https://newsapi.org/v2/top-headlines?{query_param}&apiKey={self.news_api_key}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            articles = response.json().get("articles", [])
            if not articles:
                return f"I couldn't find any news on '{topic}'."
            headlines = [f"{i+1}. {a['title']}" for i, a in enumerate(articles[:3])]
            return f"Here are the top headlines on {topic if topic else 'general news'}: " + " ".join(headlines)
        except Exception as e:
            return f"I encountered an error fetching news: {e}"

    def _get_stock_price(self, symbol: str) -> str:
        """Fetches stock price using Alpha Vantage API."""
        if not self.alpha_vantage_api_key:
            return "My Alpha Vantage API key is not configured."
        if not symbol:
            return "Please specify a stock symbol."
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.alpha_vantage_api_key}"
        try:
            data = requests.get(url).json()
            quote = data.get("Global Quote", {})
            if not quote:
                return f"Could not find stock info for {symbol.upper()}."
            return f"The price for {symbol.upper()} is ${quote.get('05. price')}."
        except Exception as e:
            return f"I encountered an error fetching the stock price: {e}"

    def _get_nasa_apod(self) -> str:
        """Fetches NASA Astronomy Picture of the Day (APOD)."""
        if not self.nasa_api_key:
            return "My NASA API key is not configured."
        url = f"https://api.nasa.gov/planetary/apod?api_key={self.nasa_api_key}"
        try:
            data = requests.get(url).json()
            return f"Today's NASA Picture of the Day is '{data['title']}'. {data['explanation'][:150]}..."
        except Exception as e:
            return f"I couldn't fetch the NASA picture: {e}"

    def _fetch_and_download_image(self, query: str, count: int = 1) -> str:
        """
        Fetches a specified number of images from Unsplash, saves, and opens them.
        """
        if not self.unsplash_access_key:
            return "Sir, my Unsplash API key is not configured. I cannot fetch images."
        if not query:
            return "Please tell me what image you would like me to find."

        print(f"Fetching {count} image(s) for query: '{query}' from Unsplash.")
        url = f"https://api.unsplash.com/search/photos?page=1&per_page={count}&query={query}&client_id={self.unsplash_access_key}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            results = data.get("results")
            if not results:
                return f"I'm sorry, sir, but I couldn't find any images for '{query}'."

            downloaded_files = 0
            for i, image_data in enumerate(results):
                image_url = image_data['urls']['regular']
                
                print(f"Downloading image {i+1} from: {image_url}")
                image_response = requests.get(image_url, stream=True)
                image_response.raise_for_status()

                file_path = os.path.join(settings.IMAGE_DOWNLOAD_PATH, f"{query.replace(' ', '_')}_{i+1}.jpg")
                with open(file_path, 'wb') as f:
                    for chunk in image_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"Image saved to: {file_path}")
                if sys.platform == "win32":
                    os.startfile(file_path)
                else: # macOS and Linux
                    subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", file_path])
                downloaded_files += 1

            return f"Sir, I have downloaded and opened {downloaded_files} image(s) of '{query}' for you."

        except requests.exceptions.HTTPError as http_err:
            return f"I encountered a network error while fetching the image: {http_err}"
        except Exception as e:
            return f"I'm sorry, sir. A critical error occurred while getting the image: {e}"

    def _generate_qr_code(self, data: str) -> str:
        """
        Generates a QR code, saves it, opens it, and returns a status message.
        """
        if not data:
            return "I need some text or a link to create a QR code."

        file_path = generate_qr_code(data)

        if "Error:" in file_path:
            return f"I'm sorry, sir. I encountered an error: {file_path}"
        
        try:
            # Open the generated QR code for the user to see
            if sys.platform == "win32":
                os.startfile(file_path)
            else: # macOS and Linux
                subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", file_path])
            return "I have generated the QR code for you, sir. It should be on your screen now."
        except Exception as e:
            # Generate a more natural response using the NLP processor
            return self.nlp_processor.generate_qr_code_confirmation(data)

    # --- Music Player Controls ---
    def _play_music(self, song_name: str = None) -> str:
        """Calls the music player to play a song."""
        return self.music_player.play(song_name)

    def _pause_music(self) -> str:
        """Calls the music player to pause the music."""
        return self.music_player.pause()

    def _stop_music(self) -> str:
        """Calls the music player to stop the music."""
        return self.music_player.stop()

    def _next_song(self) -> str:
        """Calls the music player to play the next song."""
        return self.music_player.next_song()

    def _previous_song(self) -> str:
        """Calls the music player to play the previous song."""
        return self.music_player.previous_song()

    # --- Window Management ---
    def _close_current_tab(self) -> str:
        """Closes the current active tab using keyboard shortcuts."""
        try:
            pyautogui.hotkey('ctrl', 'w')
            time.sleep(0.5) # Give a moment for the action to complete
            return "Current tab closed, sir."
        except Exception as e:
            return f"I encountered an error trying to close the tab: {e}"

    def _switch_window(self) -> str:
        """Switches to the next window using Alt+Tab."""
        try:
            pyautogui.hotkey('alt', 'tab')
            return "Switched window."
        except Exception as e:
            return f"I encountered an error trying to switch windows: {e}"

    def _minimize_window(self) -> str:
        """Minimizes the current active window."""
        try:
            pyautogui.hotkey('win', 'down')
            return "Window minimized."
        except Exception as e:
            return f"I encountered an error trying to minimize the window: {e}"

    def _maximize_window(self) -> str:
        """Maximizes the current active window."""
        try:
            pyautogui.hotkey('win', 'up')
            return "Window maximized."
        except Exception as e:
            return f"I encountered an error trying to maximize the window: {e}"

    def _new_tab(self) -> str:
        """Opens a new tab in the current application."""
        try:
            pyautogui.hotkey('ctrl', 't')
            return "New tab opened."
        except Exception as e:
            return f"I encountered an error trying to open a new tab: {e}"

    def _send_email(self, recipient: str, subject: str, body: str) -> str:
        """Sends an email using the configured credentials."""
        if not settings.EMAIL_ADDRESS or not settings.EMAIL_PASSWORD:
            return "My email sending capabilities are not configured."
        if not recipient or not subject or not body:
            return "I am missing information to send the email."
        try:
            msg = MIMEMultipart()
            msg['From'] = settings.EMAIL_ADDRESS
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(settings.EMAIL_ADDRESS, settings.EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            return "Email sent successfully, sir."
        except Exception as e:
            return f"I encountered an error sending the email: {e}"

    def _legacy_search_web(self, query: str) -> str:
        """Performs a web search by opening the browser."""
        if not query:
            return "Please tell me what to search for."
        try:
            webbrowser.open(f"http://googleusercontent.com/search?q={query}")
            return f"I am searching the web for '{query}' for you now, sir."
        except Exception as e:
            return f"I encountered an error trying to open the web browser: {e}"

    def search_the_web(self, query: str) -> str:
        """
        NEW: Autonomously searches the web using Serper.dev API and returns a digest of results.
        """
        if not self.serper_dev_api_key:
            return "Search failed: My Serper.dev API key is not configured."
        
        print(f"Performing autonomous web search for: '{query}' using Serper.dev")
        search_url = "https://google.serper.dev/search"
        headers = {
            'X-API-KEY': self.serper_dev_api_key,
            'Content-Type': 'application/json'
        }
        data = json.dumps({"q": query})

        try:
            response = requests.post(search_url, headers=headers, data=data, timeout=10) # Added timeout
            response.raise_for_status()
            search_results = response.json() # Renamed to search_results as in real.py
            
            organic_results = search_results.get("organic", []) # Serper.dev uses "organic" not "organic_results"
            
            if not organic_results:
                return "Search failed: I found no relevant results on the web for that query."

            # ULTRA-FAST: Compile a concise digest from only the top 3 results.
            digest = f"Web search results for '{query}':\n"
            for i, item in enumerate(organic_results[:3]):
                title = item.get("title", "No Title")
                snippet = item.get("snippet", "No snippet available.").replace("\n", "")
                # Link is omitted to keep context for the next LLM call short and fast.
                digest += f"Source {i+1}: {title} - Snippet: {snippet}\n"
            
            return digest

        except requests.exceptions.Timeout:
            return "Search failed: The web search request timed out."
        except requests.exceptions.HTTPError as http_err:
            if http_err.response.status_code == 404:
                return "Search failed: The requested resource was not found (404 error). This might mean the search query was invalid or no results exist."
            else:
                return f"Search failed: A network error occurred. {http_err}"
        except Exception as e:
            return f"Search failed: An unexpected error occurred: {e}"


    def _execute_cmd_command(self, command_string: str) -> dict:
        """
        Executes a command in a clean PowerShell environment and returns detailed results.
        """
        if not command_string:
            return {'success': False, 'output': '', 'error': 'No command was provided.'}
        print(f"Executing command in clean PowerShell: '{command_string}'")
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", command_string],
                capture_output=True, text=True, check=False, encoding='utf-8'
            )
            if result.returncode == 0:
                return {'success': True, 'output': result.stdout.strip(), 'error': ''}
            else:
                return {'success': False, 'output': result.stdout.strip(), 'error': result.stderr.strip() or "Command failed with no specific error."}
        except Exception as e:
            return {'success': False, 'output': '', 'error': f"An exception occurred: {e}"}

    def _write_to_notepad(self, content: str) -> str:
        """Opens Notepad and writes content."""
        if not content:
            return "There is no content to write."
        try:
            subprocess.Popen(["notepad.exe"])
            time.sleep(2)
            pyautogui.write(content, interval=0.01)
            return "I have written the content in Notepad for you."
        except Exception as e:
            return f"I encountered an error writing to Notepad: {e}"

    def _play_sound_file(self, file_path: str) -> str:
        """Plays a sound file using ffplay."""
        if not os.path.exists(file_path):
            return f"Error: Sound file not found at {file_path}"
        try:
            # Use ffplay to play the sound file
            playback_command = ["ffplay", "-nodisp", "-autoexit", file_path]
            subprocess.run(playback_command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Playing sound from {file_path}"
        except Exception as e:
            return f"Error playing sound file: {e}"

    def _read_text_file(self, file_path: str) -> str:
        """Reads the content of a text file."""
        if not os.path.exists(file_path):
            return f"Error: File not found at {file_path}"
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            return f"Error reading file: {e}"

    def summarize_file(self, file_path: str) -> str:
        """Summarizes the text file at the given path."""
        content = self._read_text_file(file_path)
        if content.startswith("Error:"):
            return content

        from src.nlp.processor import NLPProcessor
        nlp_processor = NLPProcessor()
        summary = nlp_processor.generate_summary(content)
        return f"I have summarized the file, {os.path.basename(file_path)}. Here is the summary: {summary}"