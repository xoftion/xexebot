import tweepy
import os
import re
import logging
import asyncio
from .db import get_last_mention_id, set_last_mention_id, get_db_connection
from typing import Callable, Awaitable
from .ai_handler import extract_search_query
# The google_search tool is provided by the environment, but we can import it for clarity
# from .utils import google_search

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

async def post_strategic_content(generate_response_func: Callable[[str], Awaitable[str]]):
    """
    Generates and posts a new, original tweet based on the user's recent timeline.
    """
    if not client or not USER_ID:
        logger.warning("Cannot post strategic content: client or USER_ID not configured.")
        return

    logger.info("Fetching recent tweets for context...")
    try:
        recent_tweets_response = client.get_users_tweets(id=USER_ID, max_results=10)
        if not recent_tweets_response.data:
            logger.warning("No recent tweets found to generate context.")
            return

        # Create a context string from the recent tweets
        context = "\n".join([f"- \"{tweet.text}\"" for tweet in recent_tweets_response.data])

        prompt = (
            f"Analyze the style and topics of these recent tweets from @PiLord_officia:\n{context}\n\n"
            "Now, generate a new, short, and engaging tweet in the same style. The tweet should be a "
            "thought-provoking question or a sharp insight related to crypto, Pi Network, or market trends. "
            "Keep it under 260 characters. Do not use hashtags."
        )

        new_tweet_text = await generate_response_func(prompt)

        if "Error:" not in new_tweet_text:
            post_to_x(new_tweet_text)

    except tweepy.errors.TweepyException as e:
        logger.error(f"An error occurred while fetching user tweets: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in post_strategic_content: {e}")


def get_user_info(username: str):
    """Fetches profile information for a given X username."""
    if not client:
        return None
    try:
        # Using the v2 endpoint for users by username
        response = client.get_user(username=username, user_fields=["created_at", "description", "public_metrics"])
        if response.data:
            user = response.data
            return {
                "username": user.username,
                "name": user.name,
                "created_at": user.created_at.isoformat(),
                "followers_count": user.public_metrics.get("followers_count", 0),
                "tweet_count": user.public_metrics.get("tweet_count", 0),
                "description": user.description,
            }
    except tweepy.errors.TweepyException as e:
        logger.error(f"Could not fetch info for user @{username}: {e}")
    return None

async def check_mentions(generate_response_func: Callable[[str], Awaitable[str]]):
    """
    Checks for a new mention, researches any users mentioned within it for legitimacy,
    and then generates a safe, factual reply.
    """
    if not client or not USER_ID:
        logger.warning("Cannot check mentions: client or USER_ID not configured.")
        return

    last_mention_id = get_last_mention_id()
    logger.info(f"Checking for new mentions since tweet ID: {last_mention_id}")

    try:
        mentions_response = client.get_users_mentions(
            id=USER_ID, since_id=last_mention_id, max_results=1, tweet_fields=["author_id", "created_at"]
        )
        if not mentions_response.data:
            logger.info("No new mentions found.")
            return

        mention = mentions_response.data[0]
        logger.info(f"Found new mention {mention.id}: \"{mention.text}\"")

        # --- Research & Scam Detection Step ---
        # 1. Research mentioned user accounts
        mentioned_usernames = re.findall(r'@(\w+)', mention.text)
        research_data = "No other users were mentioned in the tweet."
        if mentioned_usernames:
            author_response = client.get_user(id=mention.author_id, user_fields=["username"])
            author_username = author_response.data.username if author_response.data else ""

            users_to_research = [u for u in mentioned_usernames if u.lower() not in [USER_ID.lower(), author_username.lower()]]

            if users_to_research:
                logger.info(f"Researching mentioned users: {users_to_research}")
                user_info_list = [get_user_info(u) for u in users_to_research]
                user_info_list = [u for u in user_info_list if u]
                if user_info_list:
                    research_data = "Research on mentioned X accounts:\n" + "\n".join([str(u) for u in user_info_list])

        # 2. Perform a web search for fact-checking
        search_query = await extract_search_query(mention.text)
        if search_query:
            logger.info(f"Performing web search for query: '{search_query}'")
            try:
                # This is where the actual google_search tool would be called
                # For this environment, we will simulate the call.
                # In a real environment, you would uncomment the following line:
                # search_results = google_search(query=search_query)
                search_results = "Web search results would appear here." # Placeholder
                research_data += f"\n\nWeb Search Results for '{search_query}':\n{search_results}"
            except Exception as e:
                logger.error(f"Web search failed: {e}")
                research_data += "\n\nWeb search could not be completed."

        # --- Multi-Step AI Prompt for Safe Reply Generation ---
        prompt = (
            "You are Xexbot, a highly intelligent crypto research assistant for the user @PiLord_officia. Your primary goal is to provide factual, safe, and helpful replies.\n\n"
            "**1. The Original Mention:**\n"
            f"```\n{mention.text}\n```\n\n"
            "**2. Your Internal Research Findings:**\n"
            f"```\n{research_data}\n```\n\n"
            "**3. Your Task:**\n"
            "Synthesize all the information above. First, form a conclusion about the validity of the claims in the tweet. Then, write a reply from the perspective of @PiLord_officia.\n"
            "- If your research (especially the web search) disproves the tweet's claim or suggests a scam, your reply **must** correct the misinformation and gently warn the user. Provide the correct, factual information.\n"
            "- If the tweet is a legitimate question or comment, provide a helpful and insightful answer.\n"
            "- The reply must be short, engaging, and under 280 characters."
        )

        reply_text = await generate_response_func(prompt)

        if "Error:" not in reply_text:
            reply_to_mention(mention.id, reply_text)

        set_last_mention_id(mention.id)

    except tweepy.errors.TooManyRequests:
        logger.warning("X API rate limit hit. Skipping this polling cycle.")
    except tweepy.errors.TweepyException as e:
        logger.error(f"An error occurred during the mention check process: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in check_mentions: {e}")