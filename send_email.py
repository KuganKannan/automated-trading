import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
from logging_config import setup_logging, get_logger

load_dotenv()

# Setup logging
setup_logging()
logger = get_logger(__name__)

class SendEmail:
    
    def sendEmail(self, subject, body):
        # Email configuration
        smtp_server = 'smtp.gmail.com'  # e.g., 'smtp.gmail.com'
        smtp_port = 587  # For TLS
        sender_email = 'simracinggenius@gmail.com'
        sender_password = os.environ.get("G_PASSWORD")
        recipients = ['simracinggenius@gmail.com', 'ramkicsebe@gmail.com','mskel73@gmail.com']

        print(f"📧 Preparing email: {subject}", flush=True)
        print(f"📧 Recipients: {recipients}", flush=True)
        
        # Create the email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            print("📧 Connecting to SMTP server...", flush=True)
            # Connect to the SMTP server
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            print("📧 Logging in...", flush=True)
            server.login(sender_email, sender_password)
            print("📧 Sending email...", flush=True)
            # Send the email
            server.sendmail(sender_email, recipients, msg.as_string())
            print("✅ Email sent successfully!", flush=True)
            logger.info('Email sent successfully!')
        except Exception as e:
            print(f"❌ Error sending email: {e}", flush=True)
            logger.error(f'Error sending email: {e}')
        finally:
            server.quit()
