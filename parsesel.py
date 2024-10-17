import threading
import time
import os
import tkinter as tk
from tkinter import ttk, filedialog  # For file select dialog
import websocket
import requests
import json  # For handling JSON payloads
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import psutil  # For killing Chrome processes
from playsound import playsound  # To play sound files

# Function to kill all Chrome processes
def close_all_chrome_windows():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == 'chrome.exe':
            proc.kill()

# Function to launch Chrome browser with the user-selected chromedriver file and access the target tab
def setup_browser(chromedriver_path):
    chrome_options = Options()
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    user_directory = os.path.expanduser("~")
    chrome_profile_path = os.path.join(user_directory, "AppData", "Local", "Google", "Chrome", "User Data")
    chrome_options.add_argument(f"--user-data-dir={chrome_profile_path}")
    chrome_options.add_argument(r"--profile-directory=Default")

    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# Function to track and parse all text in the entire page
def track_and_parse_all_text(driver, target_url, gui):
    driver.get(target_url)
    old_filtered_text = ""
    time.sleep(3)
    wait = WebDriverWait(driver, 15)

    while True:
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            page_content = driver.find_element(By.TAG_NAME, "body")
            raw_new_text = page_content.text
            filtered_new_text = gui.filter_text(raw_new_text)
            delta_text = filtered_new_text.replace(old_filtered_text, "").strip()

            if delta_text:
                gui.update_text(delta_text)
                gui.check_keywords_and_send_requests(delta_text)
                old_filtered_text = filtered_new_text

            time.sleep(5)

        except Exception as e:
            gui.update_status(f"Error: {e}")
            break

    driver.quit()

# GUI Class to Handle UI Operations
class TextTrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RRC - Replika Remote Control")

        self.websocket_url = tk.StringVar(value="ws://192.168.178.40:80")
        self.target_url = tk.StringVar(value="https://my.replika.com")
        self.chromedriver_path = tk.StringVar(value=r"")
        self.character_keyword = tk.StringVar(value="Replika name")

        self.create_url_inputs()

        self.text_area = tk.Text(self.root, wrap=tk.WORD, height=5, width=80)
        self.text_area.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.status_label = tk.Label(self.root, text="Status: Waiting for updates...", relief=tk.SUNKEN, anchor='w')
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)

        self.keyword_entries = []
        self.payload_entries = []
        self.action_types = []
        self.file_buttons = []
        self.counters = []  # For storing counters
        self.create_keyword_payload_action_inputs()

        # Start button and note
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=5)

        self.start_button = tk.Button(button_frame, text="Start Tracking", command=self.start_tracking)
        self.start_button.pack(side=tk.LEFT, padx=5)

        # Note added next to the Start Tracking button
        note_label = tk.Label(button_frame, text="Start first - then enter keywords. Starting will close all open Chrome browser windows and open a new one.", fg="red")
        note_label.pack(side=tk.LEFT, padx=5)

    def create_url_inputs(self):
        url_frame = tk.Frame(self.root)
        url_frame.pack(pady=5, padx=10)

        websocket_label = tk.Label(url_frame, text="WebSocket URL:")
        websocket_label.pack(side=tk.LEFT, padx=5)
        websocket_entry = tk.Entry(url_frame, textvariable=self.websocket_url, width=40)
        websocket_entry.pack(side=tk.LEFT, padx=5)

        chromedriver_label = tk.Label(url_frame, text="ChromeDriver File:")
        chromedriver_label.pack(side=tk.LEFT, padx=5)
        chromedriver_entry = tk.Entry(url_frame, textvariable=self.chromedriver_path, width=50)
        chromedriver_entry.pack(side=tk.LEFT, padx=5)
        file_select_button = tk.Button(url_frame, text="Browse", command=self.browse_chromedriver_file)
        file_select_button.pack(side=tk.LEFT, padx=5)

        target_label = tk.Label(url_frame, text="Target URL:")
        target_label.pack(side=tk.LEFT, padx=5)
        target_entry = tk.Entry(url_frame, textvariable=self.target_url, width=40)
        target_entry.pack(side=tk.LEFT, padx=5)

        character_label = tk.Label(url_frame, text="Character name:")
        character_label.pack(side=tk.LEFT, padx=5)
        character_entry = tk.Entry(url_frame, textvariable=self.character_keyword, width=20)
        character_entry.pack(side=tk.LEFT, padx=5)

    def browse_chromedriver_file(self):
        file_path = filedialog.askopenfilename(title="Select ChromeDriver File", filetypes=[("Executable Files", "*.exe")])
        if file_path:
            self.chromedriver_path.set(file_path)

    def create_keyword_payload_action_inputs(self):
        for i in range(10):
            frame = tk.Frame(self.root)
            frame.pack(pady=2)

            keyword_label = tk.Label(frame, text=f"Keyword {i+1}:")
            keyword_label.pack(side=tk.LEFT, padx=5)

            keyword_entry = tk.Entry(frame, width=20)
            keyword_entry.pack(side=tk.LEFT)
            self.keyword_entries.append(keyword_entry)

            payload_entry = tk.Entry(frame, width=50)
            payload_entry.pack(side=tk.LEFT)
            self.payload_entries.append(payload_entry)

            action_type = tk.StringVar()
            action_type.set("WebSocket")
            self.action_types.append(action_type)
            dropdown = ttk.OptionMenu(frame, action_type, "WebSocket", "WebSocket", "Webhook", "API", "Play Sound", command=lambda value, idx=i: self.handle_dropdown_change(value, idx))
            dropdown.pack(side=tk.LEFT, padx=5)

            file_button = tk.Button(frame, text="Browse File", command=lambda idx=i: self.browse_audio_file(idx), state=tk.DISABLED)
            file_button.pack(side=tk.LEFT, padx=5)
            self.file_buttons.append(file_button)

            # Add counter label next to each row
            counter_label = tk.Label(frame, text="0", width=5)  # Initialize counter to 0
            counter_label.pack(side=tk.LEFT, padx=5)
            self.counters.append(counter_label)

    def handle_dropdown_change(self, value, index):
        payload_entry = self.payload_entries[index]
        file_button = self.file_buttons[index]
        payload_entry.delete(0, tk.END)

        if value == "Play Sound":
            file_button.config(state=tk.NORMAL)
        else:
            file_button.config(state=tk.DISABLED)

    def browse_audio_file(self, index):
        file_path = filedialog.askopenfilename(title="Select Audio File", filetypes=[("Audio Files", "*.wav *.mp3")])
        if file_path:
            self.payload_entries[index].delete(0, tk.END)
            self.payload_entries[index].insert(0, file_path)

    def filter_text(self, text):
        lines = text.splitlines()
        filtered_lines = []
        character_keyword = self.character_keyword.get().strip()

        for i in range(len(lines) - 1):
            if lines[i + 1].strip() == character_keyword:
                filtered_lines.append(lines[i].strip())

        return "\n".join(filtered_lines)

    def update_text(self, text):
        if text:
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, text)
            self.update_status("New text detected and displayed.")

    def update_status(self, message):
        self.status_label.config(text=f"Status: {message}")
        self.root.update_idletasks()

    def check_keywords_and_send_requests(self, newly_added_text):
        for index, (keyword_entry, payload_entry, action_type) in enumerate(zip(self.keyword_entries, self.payload_entries, self.action_types)):
            keyword = keyword_entry.get().strip().lower()
            payload = payload_entry.get().strip()
            action = action_type.get()

            if keyword and keyword in newly_added_text.lower():
                # Increment the counter when the action is triggered
                current_count = int(self.counters[index].cget("text"))
                self.counters[index].config(text=str(current_count + 1))

                # Run the action in a separate thread
                threading.Thread(target=self.execute_action, args=(action, payload, keyword)).start()

    def execute_action(self, action, payload, keyword):
        """Execute the action (WebSocket, Webhook, API, Play Sound) in a separate thread."""
        if action == "WebSocket":
            self.send_websocket_payload(payload)
            self.update_status(f"WebSocket payload sent for keyword '{keyword}'.")
        elif action == "Webhook":
            self.send_http_webhook(payload)
            self.update_status(f"Webhook payload sent for keyword '{keyword}'.")
        elif action == "API":
            self.send_api_request(payload)
            self.update_status(f"API request sent for keyword '{keyword}'.")
        elif action == "Play Sound":
            self.play_audio_file(payload)
            self.update_status(f"Sound played for keyword '{keyword}'.")

    def send_websocket_payload(self, payload):
        try:
            ws = websocket.WebSocket()
            ws.connect(self.websocket_url.get())
            ws.send(payload)
            ws.close()
        except Exception as e:
            self.update_status(f"WebSocket Error: {e}")

    def send_http_webhook(self, curl_payload):
        try:
            if "-X POST" in curl_payload and "-H" in curl_payload and "-d" in curl_payload:
                url = curl_payload.split()[2].strip()
                data_start = curl_payload.index("-d") + 2
                json_data = curl_payload[data_start:].strip().strip("'")
                headers = {'Content-Type': 'application/json'}
                response = requests.post(url, data=json_data, headers=headers)
                self.update_status(f"Webhook sent! Response: {response.status_code} {response.text}")
            else:
                self.update_status("Invalid curl command format for Webhook.")
        except Exception as e:
            self.update_status(f"Webhook Error: {e}")

    def send_api_request(self, curl_payload):
        try:
            if "-d" in curl_payload and "-H" in curl_payload:
                data_start = curl_payload.index("-d") + 2
                header_start = curl_payload.index("-H")
                json_data = curl_payload[data_start:header_start].strip().strip("'")
                url = curl_payload.split()[-1].strip()
                headers = {'Content-Type': 'application/json'}
                response = requests.post(url, data=json_data, headers=headers)
                self.update_status(f"API request sent! Response: {response.status_code} {response.text}")
            else:
                self.update_status("Invalid curl command format.")
        except Exception as e:
            self.update_status(f"API Request Error: {e}")

    def play_audio_file(self, file_path):
        try:
            playsound(file_path)
        except Exception as e:
            self.update_status(f"Error playing sound: {e}")

    def start_tracking(self):
        self.update_status("Closing all Chrome windows...")
        
        try:
            close_all_chrome_windows()
        except Exception as e:
            self.update_status(f"No open chrome windows")

        self.update_status("Starting text tracking...")
        self.driver = setup_browser(self.chromedriver_path.get())

        target_url = self.target_url.get()

        self.tracking_thread = threading.Thread(target=track_and_parse_all_text, args=(self.driver, target_url, self))
        self.tracking_thread.daemon = True
        self.tracking_thread.start()

# Main function to run the GUI application
def main():
    root = tk.Tk()
    gui = TextTrackerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
