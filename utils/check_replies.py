import os
import sys
import requests
import json
from datetime import datetime, timedelta, timezone
import re
from flask import current_app

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import db
from models.outreach import Outreach
from utils.mailers.graph_emailer import get_access_token

def extract_email_body_preview(message_id):
    """
    Get the full message content and extract a clean preview.
    """
    try:
        access_token = get_access_token()
        user_email = os.getenv("MS_GRAPH_USER_EMAIL")
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Get the full message content
        endpoint = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages/{message_id}"
        params = {
            '$select': 'body,bodyPreview'
        }
        
        response = requests.get(endpoint, headers=headers, params=params)
        
        if response.status_code == 200:
            message_data = response.json()
            
            # Try to get clean text from body
            body = message_data.get('body', {})
            body_content = body.get('content', '')
            body_preview = message_data.get('bodyPreview', '')
            
            # If we have HTML body content, try to extract text
            if body_content and body.get('contentType') == 'html':
                # Simple HTML tag removal (you could use BeautifulSoup for better parsing)
                clean_text = re.sub(r'<[^>]+>', '', body_content)
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                
                # Remove common email signatures and footers
                clean_text = re.split(r'(Sent from|Get Outlook|From:.*On:.*Wrote:)', clean_text)[0]
                
                return clean_text[:300] if clean_text else body_preview
            
            # Fallback to bodyPreview
            return body_preview[:300] if body_preview else "No preview available"
            
        else:
            print(f"Error getting message body: {response.status_code}")
            return "Preview not available"
            
    except Exception as e:
        print(f"Exception getting message preview: {str(e)}")
        return "Preview not available"

def check_conversation_for_replies(conversation_id, original_outreach_date, outreach_record):
    """
    Check a specific conversation for new replies and update the database.
    """
    try:
        access_token = get_access_token()
        user_email = os.getenv("MS_GRAPH_USER_EMAIL")
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        print(f"Checking conversation: {conversation_id}")
        
        # Convert original_outreach_date to timezone-aware if it's naive
        if original_outreach_date.tzinfo is None:
            original_outreach_date = original_outreach_date.replace(tzinfo=timezone.utc)
        
        # Get messages specifically from this conversation
        endpoint = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages"
        params = {
            '$select': 'id,subject,from,receivedDateTime,conversationId,bodyPreview',
            '$orderby': 'receivedDateTime desc',
            '$filter': f"conversationId eq '{conversation_id}'",
            '$top': 100  # Increased from 50 to 100
        }
        
        response = requests.get(endpoint, headers=headers, params=params)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            conversation_messages = response.json().get('value', [])
            print(f"Retrieved {len(conversation_messages)} messages in conversation")
            
            # Filter for replies (not from us, received after our outreach)
            new_replies = []
            for message in conversation_messages:
                from_email = message.get('from', {}).get('emailAddress', {}).get('address', '')
                received_date_str = message.get('receivedDateTime', '')
                
                if received_date_str:
                    # Handle timezone properly
                    if received_date_str.endswith('Z'):
                        received_date = datetime.fromisoformat(received_date_str.replace('Z', '+00:00'))
                    else:
                        received_date = datetime.fromisoformat(received_date_str)
                else:
                    continue
                
                print(f"  Message from {from_email} at {received_date}")
                
                # Skip our own messages
                if from_email.lower() == user_email.lower():
                    print(f"    Skipping - our own message")
                    continue
                
                # Skip weird Exchange system messages
                if '/O=EXCHANGELABS/' in from_email:
                    print(f"    Skipping - Exchange system message")
                    continue
                
                # Skip messages received before our outreach
                if received_date <= original_outreach_date:
                    print(f"    Skipping - before outreach date ({original_outreach_date})")
                    continue
                
                # Skip if we already processed this reply
                if outreach_record.last_reply_date and received_date <= outreach_record.last_reply_date.replace(tzinfo=timezone.utc):
                    print(f"    Skipping - already processed")
                    continue
                
                print(f"    Found NEW reply!")
                
                # Get detailed preview
                preview_text = extract_email_body_preview(message.get('id'))
                
                new_replies.append({
                    'message_id': message.get('id'),
                    'subject': message.get('subject'),
                    'from_email': from_email,
                    'received_date': received_date,
                    'preview': preview_text
                })
            
            # Update database with new replies
            if new_replies:
                # Sort by date to get the latest reply
                new_replies.sort(key=lambda x: x['received_date'], reverse=True)
                latest_reply = new_replies[0]
                
                print(f"📧 Updating database with {len(new_replies)} new replies")
                print(f"  Latest reply from: {latest_reply['from_email']}")
                print(f"  Subject: {latest_reply['subject']}")
                print(f"  Preview: {latest_reply['preview'][:100]}...")
                
                # Update the outreach record
                outreach_record.mark_reply_received(
                    sender_email=latest_reply['from_email'],
                    reply_preview_text=latest_reply['preview'],
                    reply_date=latest_reply['received_date']
                )
                
                # If there were multiple new replies, increment the count
                if len(new_replies) > 1:
                    outreach_record.reply_count += len(new_replies) - 1
                    db.session.commit()
                
                print(f"✅ Updated outreach {outreach_record.id}")
                return new_replies
            
            return []
            
        else:
            print(f"Error getting messages: {response.status_code}")
            print(f"Error details: {response.text}")
            return []
            
    except Exception as e:
        print(f"Exception checking conversation {conversation_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def check_all_recent_outreach(days_back=7):
    """
    Check all recent outreach for replies and update the database.
    """
    # Get outreach records with conversation IDs from the last N days
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    outreach_records = Outreach.query.filter(
        Outreach.conversation_id.isnot(None),
        Outreach.created_at >= cutoff_date,
        Outreach.method == 'email'
    ).all()
    
    print(f"Checking {len(outreach_records)} outreach records for replies...")
    
    replies_found = 0
    
    for outreach in outreach_records:
        print(f"\nChecking outreach {outreach.id} created at {outreach.created_at}")
        
        replies = check_conversation_for_replies(
            outreach.conversation_id, 
            outreach.created_at,
            outreach  # Pass the outreach record for database updates
        )
        
        if replies:
            print(f"  ✅ Found {len(replies)} new replies!")
            for reply in replies:
                print(f"    Reply from {reply['from_email']}: {reply['subject'][:50]}...")
            
            replies_found += 1
        else:
            print(f"  📭 No new replies found.")
    
    print(f"\n🎉 Total outreach records with new replies: {replies_found}")
    return replies_found

if __name__ == "__main__":
    # Create a Flask app context for running the script directly
    from flask import Flask
    app = Flask(__name__)
    app.config.from_object('config.Config')
    with app.app_context():
        check_all_recent_outreach(days_back=7) 