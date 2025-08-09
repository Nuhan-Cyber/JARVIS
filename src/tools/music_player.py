# jarvis-ai/src/tools/music_player.py

import os
import sys
import glob

# Add the project root to the system path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# The user-specified path for music files
MUSIC_DIRECTORY = os.path.normpath("C:/Users/NUHAN_CYBER/Downloads/Video")

class MusicPlayer:
    """
    A class to handle music playback by launching media files in the default player.
    Manages a sequential playlist of MP4 files.
    """
    def __init__(self):
        print("Initializing Music Player (CMD/File Launch Mode)...")
        self.playlist = []
        self.current_song_index = -1
        self._load_playlist()
        self.is_initialized = True # Assume success unless playlist is empty

    def _load_playlist(self):
        """
        Scans the music directory for 'audio (*.mp4' files and sorts them numerically.
        """
        if not os.path.isdir(MUSIC_DIRECTORY):
            print(f"Warning: Music directory not found at '{MUSIC_DIRECTORY}'")
            return

        # Find all .mp4 files matching the pattern 'audio (number).mp4'
        files = glob.glob(os.path.join(MUSIC_DIRECTORY, "audio (*.mp4"))
        
        # Define a sort key to order files numerically based on the number in parentheses
        def sort_key(file_path):
            try:
                # Extract the number from '.../audio (5).mp4' -> '5'
                basename = os.path.basename(file_path)
                num_str = basename[basename.find('(')+1 : basename.find(')')]
                return int(num_str)
            except (ValueError, IndexError):
                # If parsing fails, place it at the end
                return float('inf')

        self.playlist = sorted(files, key=sort_key)
        
        if not self.playlist:
            print(f"No music files found in '{MUSIC_DIRECTORY}' matching the pattern 'audio (*.mp4'.")
        else:
            print(f"Loaded {len(self.playlist)} MP4 songs into the sequential playlist.")
            self.current_song_index = 0

    def play(self, song_name: str = None) -> str:
        """
        Plays a song by launching it with the default media player.
        If song_name is provided, it searches for that song. Otherwise, it plays the current one.
        """
        if not self.playlist:
            return "The music playlist is empty. I can't play anything."

        # If a specific song is requested
        if song_name:
            found = False
            for i, song_path in enumerate(self.playlist):
                if song_name.lower() in os.path.basename(song_path).lower():
                    self.current_song_index = i
                    found = True
                    break
            if not found:
                return f"I couldn't find a song named '{song_name}' in the playlist."

        try:
            song_to_play = self.playlist[self.current_song_index]
            print(f"Launching music file via CMD: {song_to_play}")
            
            # os.startfile is the standard way to open a file with its default application on Windows
            os.startfile(song_to_play)
            
            current_song_name = os.path.basename(song_to_play)
            return f"Now playing: {current_song_name}."
        except IndexError:
            return "Could not find a song to play. The playlist might be empty or the index is out of range."
        except Exception as e:
            return f"I encountered an error trying to play the music file: {e}"

    def pause(self) -> str:
        """Pausing is not directly supported; instructs the user."""
        return "I cannot pause the music directly. Please use the controls in the media player window that I've opened."

    def stop(self) -> str:
        """Stopping is not directly supported; instructs the user."""
        # A more advanced implementation could use taskkill, but it's risky.
        # This is a safer and more user-friendly approach.
        return "To stop the music, please close the media player window."

    def next_song(self) -> str:
        """Plays the next song in the sequential playlist."""
        if not self.playlist: 
            return "The playlist is empty."
        
        # Increment index, wrapping around to the beginning if at the end
        self.current_song_index = (self.current_song_index + 1) % len(self.playlist)
        
        return self.play()

    def previous_song(self) -> str:
        """Plays the previous song in the sequential playlist."""
        if not self.playlist: 
            return "The playlist is empty."
            
        # Decrement index, wrapping around to the end if at the beginning
        self.current_song_index = (self.current_song_index - 1) % len(self.playlist)
        
        return self.play()