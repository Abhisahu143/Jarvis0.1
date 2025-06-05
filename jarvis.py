import os
import speech_recognition as sr
import datetime
import webbrowser
import wikipedia
import google.generativeai as genai
import logging
import json
import sys
from config import GEMINI_API_KEY

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jarvis.log'),
        logging.StreamHandler()
    ]
)

class JarvisAssistant:
    def __init__(self):
        try:
            self.recognizer = sr.Recognizer()
            # Configure Gemini
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-pro')
            logging.info("Jarvis Assistant initialized successfully")
            
            # Initialize system info
            self.system_info = {
                'battery': self.get_battery_status(),
                'disk': self.get_disk_usage(),
                'cpu': self.get_cpu_usage()
            }
            
        except Exception as e:
            logging.error(f"Failed to initialize Jarvis: {e}")
            print(f"Error: {e}")
            sys.exit(1)

    def get_battery_status(self):
        """Get system battery status."""
        try:
            import psutil
            battery = psutil.sensors_battery()
            if battery:
                return f"Battery: {battery.percent}% {'Charging' if battery.power_plugged else 'Discharging'}"
            return "Battery status not available"
        except:
            return "Battery status not available"

    def get_disk_usage(self):
        """Get disk usage information."""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            return f"Disk Usage: {disk.percent}% used ({disk.total/1024/1024/1024:.1f}GB total)"
        except:
            return "Disk usage not available"

    def get_cpu_usage(self):
        """Get CPU usage information."""
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=1)
            return f"CPU Usage: {cpu}%"
        except:
            return "CPU usage not available"

    def speak(self, text):
        """Converts text to speech using pyttsx3."""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)  # Speed of speech
            engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)
            print(f"Jarvis: {text}")
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            logging.error(f"TTS error: {e}")
            print(f"Error speaking: {e}")

    def listen(self):
        """Listens for command from the user and converts it to text."""
        try:
            with sr.Microphone() as source:
                print("Listening...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                print("Recognizing...")
                query = self.recognizer.recognize_google(audio, language='en-in')
                print(f"User: {query}")
                return query.lower()
        except sr.WaitTimeoutError:
            print("No speech detected")
            return ""
        except sr.UnknownValueError:
            print("Could not understand audio")
            return ""
        except sr.RequestError as e:
            print(f"Speech recognition service error: {e}")
            return ""
        except Exception as e:
            logging.error(f"Listening error: {e}")
            print(f"Error listening: {e}")
            return ""

    def ask_gemini(self, query):
        """Get response from Gemini AI."""
        try:
            response = self.model.generate_content(query)
            if response.text:
                return response.text
            else:
                return "I couldn't generate a response. Please try rephrasing your question."
        except Exception as e:
            logging.error(f"Gemini error: {e}")
            return f"Sorry, I encountered an error with Gemini: {str(e)}"

    def process_command(self, command):
        """Processes the command and performs an action."""
        if not command:
            return True

        # Check for exit commands first
        if any(word in command for word in ['exit', 'quit', 'bye', 'bye bye', 'tata']):
            self.speak("Goodbye!")
            return False

        # Handle system info commands
        if any(word in command for word in ['system info', 'info', 'status']):
            info = []
            info.append(self.system_info['battery'])
            info.append(self.system_info['disk'])
            info.append(self.system_info['cpu'])
            self.speak("System Information:")
            for item in info:
                self.speak(item)
            return True

        # Handle clipboard commands
        if "clipboard" in command:
            if "get" in command:
                try:
                    import pyperclip
                    content = pyperclip.paste()
                    self.speak(f"Clipboard content: {content}")
                except:
                    self.speak("Could not access clipboard")
                return True
            elif "set" in command:
                try:
                    import pyperclip
                    text = command.split("set", 1)[1].strip()
                    pyperclip.copy(text)
                    self.speak("Text copied to clipboard")
                except:
                    self.speak("Could not copy to clipboard")
                return True

        # Handle app opening commands
        app_commands = {
            'chrome': 'com.google.android.apps.chrome.Main',
            'whatsapp': '.Main',
            'camera': '.Camera',
            'settings': '.Settings',
            'browser': 'com.android.browser',
            'calculator': 'com.android.calculator2'
        }
        
        for app, activity in app_commands.items():
            # Check for both 'open [app]' and '[app]'
            if f'open {app}' in command or app in command:
                try:
                    # Windows-specific app handling
                    if app == 'chrome' or app == 'browser':
                        webbrowser.open('https://www.google.com')
                        self.speak("Opening browser...")
                    elif app == 'whatsapp':
                        webbrowser.open('https://web.whatsapp.com')
                        self.speak("Opening WhatsApp Web...")
                    elif app == 'settings':
                        os.system('start ms-settings:')
                        self.speak("Opening Windows Settings...")
                    elif app == 'camera':
                        os.system('start microsoft.windows.camera:')
                        self.speak("Opening Camera...")
                    elif app == 'calculator':
                        os.system('start calculator:')
                        self.speak("Opening Calculator...")
                    return True
                except Exception as e:
                    self.speak(f"Could not open {app}. Error: {e}")
                    return True

        # Handle camera commands
        if any(word in command for word in ['take photo', 'click picture', 'take picture', 'camera click']):
            try:
                os.system('start microsoft.windows.camera:')
                self.speak("Opening camera for you...")
                return True
            except Exception as e:
                self.speak(f"Could not open camera. Error: {e}")
                return True

        # Handle clipboard commands with more variations
        if any(word in command for word in ['copy', 'paste', 'clipboard']):
            try:
                import pyperclip
                if "copy" in command:
                    if "text" in command or "this" in command:
                        text = command.split("copy", 1)[1].strip()
                        pyperclip.copy(text)
                        self.speak("Text copied to clipboard")
                    else:
                        content = pyperclip.paste()
                        self.speak(f"Clipboard content: {content}")
                elif "paste" in command:
                    content = pyperclip.paste()
                    self.speak(f"Clipboard content: {content}")
                return True
            except Exception as e:
                self.speak(f"Could not access clipboard. Error: {e}")
                return True

        # Handle website opening commands
        website_commands = {
            'youtube': 'https://www.youtube.com',
            'google': 'https://www.google.com',
            'facebook': 'https://www.facebook.com',
            'instagram': 'https://www.instagram.com',
            'twitter': 'https://www.twitter.com',
            'whatsapp': 'https://web.whatsapp.com',
            'gmail': 'https://mail.google.com'
        }
        
        for site, url in website_commands.items():
            if site in command or f'open {site}' in command:
                self.speak(f"Opening {site}...")
                webbrowser.open(url)
                return True

        # Handle time commands in English and Hindi
        time_commands = ['what time is it', 'time', 'time batao', 'samay kya hai']
        if any(word in command for word in time_commands):
            now = datetime.datetime.now()
            current_time = now.strftime("%I:%M %p")
            self.speak(f"The current time is {current_time}")
            return True

        # Handle date commands in English and Hindi
        date_commands = ['what date is it', 'date', 'date kitna hai', 'din kya hai']
        if any(word in command for word in date_commands):
            now = datetime.datetime.now()
            current_date = now.strftime("%B %d, %Y")
            self.speak(f"Today's date is {current_date}")
            return True

        # Handle basic greetings
        greetings = ['hello', 'hai', 'namaste', 'hi']
        if any(word in command for word in greetings):
            self.speak("Hello! How can I help you today?")
            return True

        # Handle Gemini queries
        if command.startswith("ask gemini"):
            query = command.replace("ask gemini", "").strip()
            if query:
                response = self.ask_gemini(query)
                self.speak(response)
            else:
                self.speak("What would you like to ask Gemini?")
            return True

        # Handle search commands
        if "search for" in command or "search" in command:
            search_query = command.replace("search for", "").replace("search", "").strip()
            if search_query:
                url = f"https://www.google.com/search?q={search_query}"
                self.speak(f"Searching for {search_query} on Google.")
                try:
                    webbrowser.open(url)
                except Exception as e:
                    self.speak(f"Could not open browser. Error: {e}")
            else:
                self.speak("What would you like me to search for?")
            return True

        # Handle Wikipedia commands
        if "wikipedia" in command or "wiki" in command:
            query = command.replace("wikipedia", "").replace("wiki", "").strip()
            if query:
                try:
                    result = wikipedia.summary(query, sentences=2)
                    self.speak(f"According to Wikipedia: {result}")
                except wikipedia.exceptions.DisambiguationError:
                    self.speak("There are multiple results for this query. Please be more specific.")
                except wikipedia.exceptions.PageError:
                    self.speak("I couldn't find information about that topic.")
            return True

        # Handle general commands
        if "jarvis" in command.lower():
            self.speak("Yes, I'm here. How can I assist you?")
            return True

        # If no commands matched
        self.speak("Sorry, I don't know how to do that yet.")
        return True

    def run(self):
        """Main loop to listen for commands and process them."""
        self.speak("Jarvis assistant activated. How can I assist you?")
        
        # Update system info periodically
        while True:
            try:
                command = self.listen()
                if not self.process_command(command):
                    break
                
                # Update system info every 30 seconds
                self.update_system_info()
            except KeyboardInterrupt:
                self.speak("Goodbye!")
                break
            except Exception as e:
                logging.error(f"Error in run loop: {e}")
                self.speak("Sorry, I encountered an error.")
                # Still try to update system info even if there's an error
                self.update_system_info()

    def update_system_info(self):
        """Update system information periodically."""
        try:
            self.system_info = {
                'battery': self.get_battery_status(),
                'disk': self.get_disk_usage(),
                'cpu': self.get_cpu_usage()
            }
        except:
            pass  # Silently fail if we can't update info

    def speak(self, text):
        """Converts text to speech using pyttsx3."""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)  # Speed of speech
            engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)
            print(f"Jarvis: {text}")
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            logging.error(f"TTS error: {e}")
            print(f"Error speaking: {e}")

if __name__ == "__main__":
    try:
        assistant = JarvisAssistant()
        assistant.run()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print(f"Fatal error: {e}")
        sys.exit(1)
