from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from pathlib import Path
import csv
import os 

# === Step 1: Load email addresses from CSV ===
def load_emails_from_csv(csv_file):
    emails = []
    with open(csv_file, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('email', '').strip()
            if email:
                emails.append(email)
    return emails

creds_path = Path(os.environ.get("GOOGLE_CREDS_PATH", "."))
oauth2_creds_file = creds_path / 'calendar_token.json'

# Authenticate with OAuth2 (after setting up credentials)
creds = Credentials.from_authorized_user_file(oauth2_creds_file, ['https://www.googleapis.com/auth/calendar'])
service = build('calendar', 'v3', credentials=creds)

calendar_id = os.environ.get("GOOGLE_PTA_CALENDAR_ID", "your_calendar_id_here")
email_list = load_emails_from_csv('invitees.csv') # read in emails from CSV file


# Fetch upcoming events
# === Step 3: Get events and add attendees ===
events_result = service.events().list(
    calendarId=calendar_id,
    maxResults=300,
    singleEvents=True,
    orderBy='startTime'
).execute()
events = events_result.get('items', [])



if not events:
    print('No events found.')
else:
    for event in events:
        if event.get('status') == 'cancelled':
            continue

        if event['summary'] == 'PTA Budget 2025-26':
            print(f"Skipping event: {event['summary']} (Budget meeting)")
            continue
        attendees = event.get('attendees', [])
        existing_emails = [a['email'] for a in attendees]

        # Add new emails only if not already present
        added = False
        for email in email_list:
            if email not in existing_emails:
                attendees.append({'email': email})
                added = True

        if added:
            updated_event = service.events().patch(
                calendarId=calendar_id,
                eventId=event['id'],
                body={'attendees': attendees},
                sendUpdates='all'  # Change to 'none' for dry run
            ).execute()

            print(f"✅ Updated: {event['summary']} — added {len(email_list)} new attendees")
        else:
            print(f"⚠️ No new attendees added for: {event['summary']}")