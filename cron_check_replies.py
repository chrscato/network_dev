#!/usr/bin/env python3
"""
Simple cron job to check for email replies.
Run this every hour or few hours to automatically detect replies.

Usage: python cron_check_replies.py
"""

import os
import sys
import logging
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/reply_checker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main cron job function."""
    logger.info("=== Starting Reply Check Job ===")
    
    try:
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Import and run the reply checker
        from utils.check_replies import check_all_recent_outreach
        
        logger.info("Checking for replies in the last 7 days...")
        check_all_recent_outreach(days_back=7)
        
        logger.info("Reply check job completed successfully")
        
    except Exception as e:
        logger.error(f"Error in reply check job: {str(e)}", exc_info=True)
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("✅ Reply check completed")
    else:
        print("❌ Reply check failed")
        sys.exit(1) 