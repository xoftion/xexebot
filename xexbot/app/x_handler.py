import tweepy
import os
import logging
import asyncio
from .db import get_last_mention_id, set_last_mention_id, get_db_connection
from typing import Callable, Awaitable

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Tweepy Client Initialization ---
try:
    bearer_token = os.getenv("X_BEARER_TOKEN")
    consumer_key = os.getenv("X_CONSUMER_KEY")
    consumer_secret = os.getenv("X_CONSUMER_SECRET")
    access_token = os.getenv("X_ACCESS_TOKEN")
    access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")

    if not all([bearer_token, consumer_key, consumer_secret, access_token, access_token_secret]):
        logger.warning("One or more X API credentials are not set. X functionality will be disabled.")
        client = None
    else:
        client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        logger.info("Tweepy client initialized successfully.")
except Exception as e:
    logger.error(f"Error initializing Tweepy client: {e}")
    client = None

USER_ID = os.getenv("USER_ID")

def post_to_x(text: str):
    """Posts a tweet to the configured X account."""
    if not client:
        logger.error("Cannot post to X: client not initialized.")
        return
    try:
        logger.info(f"Posting tweet: {text}")
        client.create_tweet(text=text)
        logger.info("Tweet posted successfully.")
    except tweepy.errors.TweepyException as e:
        logger.error(f"Error posting tweet: {e}")

def reply_to_mention(mention_id: int, reply_text: str):
    """Replies to a specific mention."""
    if not client:
        logger.error(f"Cannot reply to mention: client not initialized.")
        return
    try:
        logger.info(f"Replying to mention {mention_id} with: {reply_text}")
        client.create_tweet(text=reply_text, in_reply_to_tweet_id=mention_id)
        logger.info(f"Successfully replied to mention {mention_id}.")
    except tweepy.errors.TweepyException as e:
        logger.error(f"Error replying to mention {mention_id}: {e}")

async def check_mentions(generate_response_func: Callable[[str], Awaitable[str]]):
    """
    Checks for new mentions since the last processed one, generates a reply,
    and posts it. Runs asynchronously.
    """
    if not client or not USER_ID:
        logger.warning("Cannot check mentions: client or USER_ID not configured.")
        return

    last_mention_id = get_last_mention_id()
    logger.info(f"Checking for new mentions since tweet ID: {last_mention_id}")

    try:
        mentions_response = client.get_users_mentions(
            id=USER_ID,
            since_id=last_mention_id,
            max_results=20,
            tweet_fields=["author_id", "created_at"]
        )

        if not mentions_response.data:
            logger.info("No new mentions found.")
            return

        new_mentions = sorted(mentions_response.data, key=lambda m: m.created_at)
        logger.info(f"Found {len(new_mentions)} new mentions.")

        tasks = []
        for mention in new_mentions:
            prompt = (
                f"You are a crypto expert named Xexbot. Your persona is like @PiLord_officia on X. "
                f"Provide a human-like, insightful, and trustworthy reply to the following tweet. "
                f"Use emojis and relevant slang where appropriate. Keep it concise (under 280 chars).\n\n"
                f"Tweet: \"{mention.text}\""
            )
            tasks.append(generate_response_func(prompt))

        replies = await asyncio.gather(*tasks)

        conn = get_db_connection()
        cursor = conn.cursor()
        for mention, reply_text in zip(new_mentions, replies):
            try:
                if "Error:" not in reply_text:
                    reply_to_mention(mention.id, reply_text)
                    cursor.execute(
                        "INSERT OR IGNORE INTO conversation_history (tweet_id, author_id, text, response) VALUES (?, ?, ?, ?)",
                        (mention.id, mention.author_id, mention.text, reply_text)
                    )
                    conn.commit()
            except Exception as e:
                logger.error(f"Failed to process and reply to mention {mention.id}: {e}")
                continue
        conn.close()

        latest_mention_id = new_mentions[-1].id
        set_last_mention_id(latest_mention_id)

    except tweepy.errors.TooManyRequests:
        logger.warning("X API rate limit hit. Skipping this polling cycle.")
    except tweepy.errors.TweepyException as e:
        logger.error(f"An error occurred while fetching mentions: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in check_mentions: {e}")