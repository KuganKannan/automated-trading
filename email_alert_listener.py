import imaplib
import email
import time
import subprocess
import os
from dotenv import load_dotenv  


# Gmail IMAP settings
IMAP_SERVER = 'imap.gmail.com'
EMAIL_ACCOUNT = 'simracinggenius@gmail.com'
EMAIL_PASSWORD = os.environ.get("G_PASSWORD")  # Use your Gmail App Password
TRADINGVIEW_SENDER = 'ramkicsebe@gmail.com'

# How often to check for new emails (in seconds)
CHECK_INTERVAL = 10

def check_for_alerts():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    mail.select('inbox')
    result, data = mail.search(None, f'(UNSEEN FROM "{TRADINGVIEW_SENDER}")')
    if result == 'OK':
        for num in data[0].split():
            result, msg_data = mail.fetch(num, '(RFC822)')
            if result == 'OK':
                msg = email.message_from_bytes(msg_data[0][1])
                subject = msg['subject']
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == 'text/plain':
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = msg.get_payload(decode=True).decode()
                print(f'Received TradingView alert: {subject}\n{body}')
                # Call send_email.py with the alert body
                try:
                    subprocess.run(['python', 'send_email.py', body], check=True)
                    print('send_email.py executed successfully!')
                except Exception as e:
                    print(f'Error running send_email.py: {e}')
                # Mark email as seen
                mail.store(num, '+FLAGS', '\\Seen')
    mail.logout()

def main():
    print('Listening for TradingView alert emails...')
    while True:
        check_for_alerts()
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    main()

