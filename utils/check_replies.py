import os
import sys
import requests
import json
from datetime import datetime, timedelta, timezone

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db
from models.outreach import Outreach
from utils.mailers.graph_emailer import get_access_token

def check_conversation_for_replies(conversation_id, original_outreach_date):
    """
    Check a specific conversation for new replies using a different approach.
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
        
        # Instead of filtering by conversationId, get recent messages and filter client-side
        endpoint = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages"
        params = {
            '$select': 'id,subject,from,receivedDateTime,conversationId',
            '$orderby': 'receivedDateTime desc',
            '$top': 50  # Get last 50 messages and filter client-side
        }
        
        response = requests.get(endpoint, headers=headers, params=params)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            all_messages = response.json().get('value', [])
            print(f"Retrieved {len(all_messages)} recent messages")
            
            # Filter for messages in our conversation
            conversation_messages = [
                msg for msg in all_messages 
                if msg.get('conversationId') == conversation_id
            ]
            
            print(f"Found {len(conversation_messages)} messages in our conversation")
            
            # Filter for replies (not from us, received after our outreach)
            replies = []
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
                
                print(f"    Found reply!")
                replies.append({
                    'message_id': message.get('id'),
                    'subject': message.get('subject'),
                    'from_email': from_email,
                    'received_date': received_date
                })
            
            return replies
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
    Check all recent outreach for replies.
    """
    with app.app_context():
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
                outreach.created_at
            )
            
            if replies:
                print(f"  ✅ Found {len(replies)} replies!")
                for reply in replies:
                    print(f"    Reply from {reply['from_email']}: {reply['subject']}")
                
                # Update outreach record
                outreach.notes = f"{outreach.notes}\n\nReply received: {replies[0]['received_date']}"
                replies_found += 1
            else:
                print(f"  No replies found.")
        
        if replies_found > 0:
            db.session.commit()
            print(f"\n🎉 Total replies found: {replies_found}")
        else:
            print(f"\n📭 No replies found.")

if __name__ == "__main__":
    check_all_recent_outreach(days_back=7) 