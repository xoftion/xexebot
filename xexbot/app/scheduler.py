import schedule
import requests
import time
import os
import logging
import threading
import asyncio
from .x_handler import check_mentions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ping_self():
    """Pings the deployed application to keep it from sleeping."""
    url = os.getenv("DEPLOYED_URL")
    if not url:
        logger.warning("DEPLOYED_URL not set. Cannot perform keep-alive ping.")
        return

    try:
        logger.info(f"Pinging self at {url}...")
        response = requests.get(url)
        logger.info(f"Ping response: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to ping self: {e}")

def poll_x_sync():
    """Synchronous wrapper to run the async check_mentions function."""
    logger.info("Polling X for new mentions...")
    asyncio.run(check_mentions())

def run_scheduler():
    """The main loop for the scheduler, running pending jobs."""
    schedule.every(10).minutes.do(ping_self)
    schedule.every(15).minutes.do(poll_x_sync)

    logger.info("Scheduler started. Waiting for scheduled jobs...")

    # Initial run to avoid waiting for the first interval
    ping_self()
    poll_x_sync()

    while True:
        schedule.run_pending()
        time.sleep(1)

def start_scheduler():
    """Starts the scheduler in a background thread."""
    logger.info("Initializing scheduler thread...")
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("Scheduler thread started.")