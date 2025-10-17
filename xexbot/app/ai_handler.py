import os
import google.generativeai as genai
from openai import AsyncOpenAI
import httpx
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- AI Client Configurations ---
openrouter_client = None
try:
    # Configure Gemini
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        logger.warning("GEMINI_API_KEY not found. Gemini will be unavailable.")
    else:
        genai.configure(api_key=gemini_api_key)

    # Configure OpenRouter client
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        logger.warning("OPENROUTER_API_KEY not found. OpenRouter fallback will be unavailable.")
    else:
        # Explicitly create an httpx client to avoid internal proxy/state issues on Render
        http_client = httpx.AsyncClient()
        openrouter_client = AsyncOpenAI(
            api_key=openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            http_client=http_client,
        )
except Exception as e:
    logger.error(f"Error during AI client configuration: {e}")
    openrouter_client = None


async def generate_response(prompt: str) -> str:
    """
    Generates a response using Gemini, with a fallback to a different model via OpenRouter.

    Args:
        prompt: The input prompt for the AI model.

    Returns:
        The generated text response.
    """
    # --- Try Gemini First ---
    try:
        logger.info("Attempting to generate response with Gemini...")
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = await model.generate_content_async(prompt)
        logger.info("Successfully generated response with Gemini.")
        return response.text
    except Exception as e:
        logger.warning(f"Gemini API call failed: {e}. Falling back to OpenRouter.")

    # --- Fallback to Llama via OpenRouter ---
    if openrouter_client:
        try:
            logger.info("Attempting to generate response with Llama (OpenRouter)...")
            chat_completion = await openrouter_client.chat.completions.create(
                model="meta-llama/llama-3-8b-instruct",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            logger.info("Successfully generated response with Llama (OpenRouter).")
            return chat_completion.choices[0].message.content
        except Exception as e_fallback:
            logger.error(f"OpenRouter API call failed: {e_fallback}")
            return "Error: Both primary and fallback AI services failed."

    logger.error("All AI services are unavailable. Check API keys and configurations.")
    return "Error: AI services are not configured."