import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import subprocess
from dotenv import load_dotenv

load_dotenv()
import os
# Email configuration
smtp_server = 'smtp.gmail.com'  # e.g., 'smtp.gmail.com'
smtp_port = 587  # For TLS
sender_email = 'simracinggenius@gmail.com'
sender_password = os.environ.get("G_PASSWORD")
recipients = ['simracinggenius@gmail.com', 'ramkicsebe@gmail.com']

# Get Dhan positions by running dhan_connecting.py and capturing output
try:
    result = subprocess.run([r'trading/Scripts/python.exe', 'dhan_connecting.py'], capture_output=True, text=True, check=True)
    dhan_output = result.stdout.strip()
except Exception as e:
    dhan_output = f'Error: {e}'

subject = 'Test Email'
body = f'This is a test email sent to two people.\nThis is the output from dhan_connecting.py:\n{dhan_output}'

# Create the email
msg = MIMEMultipart()
msg['From'] = sender_email
msg['To'] = ', '.join(recipients)
msg['Subject'] = subject
msg.attach(MIMEText(body, 'plain'))

try:
    # Connect to the SMTP server
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(sender_email, sender_password)
    # Send the email
    server.sendmail(sender_email, recipients, msg.as_string())
    print('Email sent successfully!')
except Exception as e:
    print(f'Error sending email: {e}')
finally:
    server.quit()
