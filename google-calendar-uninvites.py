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
                emails.append(email.lower())
    return emails

# === Step 2: Setup credentials and service ===
creds_path = Path(os.environ.get("GOOGLE_CREDS_PATH", "."))
oauth2_creds_file = creds_path / 'calendar_token.json'

creds = Credentials.from_authorized_user_file(oauth2_creds_file, ['https://www.googleapis.com/auth/calendar'])
service = build('calendar', 'v3', credentials=creds)

calendar_id = os.environ.get("GOOGLE_PTA_CALENDAR_ID", "your_calendar_id_here")
email_list = load_emails_from_csv('un-invitees.csv')

# === Step 3: Fetch events ===
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

        original_attendees = event.get('attendees', [])
        updated_attendees = [a for a in original_attendees if a['email'].lower() not in email_list]

        if len(updated_attendees) < len(original_attendees):
            updated_event = service.events().patch(
                calendarId=calendar_id,
                eventId=event['id'],
                body={'attendees': updated_attendees},
                sendUpdates='all'  # Change to 'none' to avoid sending removal notifications
            ).execute()
            removed = len(original_attendees) - len(updated_attendees)
            print(f"❌ Updated: {event['summary']} — removed {removed} attendee(s)")
        else:
            print(f"✅ No matching attendees to remove for: {event['summary']}")
