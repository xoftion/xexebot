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
        # Create a more robust httpx client with custom transport and longer timeouts
        transport = httpx.AsyncHTTPTransport(retries=2)
        http_client = httpx.AsyncClient(transport=transport, timeout=30.0)

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
        # Use a standard, widely available model to avoid 404 errors.
        model = genai.GenerativeModel('gemini-1.0-pro')
        response = await model.generate_content_async(prompt)
        # Check if the response has content before returning
        if response.parts:
            logger.info("Successfully generated response with Gemini.")
            return response.text
        else:
            # This can happen if the model returns an empty response due to safety settings etc.
            logger.warning("Gemini returned an empty response. Falling back to OpenRouter.")
            raise ValueError("Empty response from Gemini")
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