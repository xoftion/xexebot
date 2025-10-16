import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel

# Load environment variables from .env file at the very beginning
load_dotenv()

from .ai_handler import generate_response
from .x_handler import post_to_x
from .scheduler import start_scheduler
from .db import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FastAPI Application Setup ---
app = FastAPI(
    title="Xexbot",
    description="An AI-powered bot for human-like X automation.",
    version="1.0.0"
)

# --- Pydantic Models for Request Bodies ---
class PostRequest(BaseModel):
    topic: str

# --- Event Handlers ---
@app.on_event("startup")
async def startup_event():
    """
    Actions to perform on application startup.
    - Initializes the database.
    - Starts the background scheduler.
    """
    logger.info("Application starting up...")
    init_db()
    start_scheduler()
    logger.info("Application startup complete.")

# --- API Endpoints ---
@app.get("/ping", summary="Check if the service is alive")
def ping():
    """A simple endpoint to confirm the service is running."""
    return {"status": "Alive!"}

@app.post("/generate-post", summary="Generate and post a tweet on a topic")
async def gen_post(post_request: PostRequest, background_tasks: BackgroundTasks):
    """
    Generates a human-like X post on a given topic and queues it for posting.
    """
    logger.info(f"Received request to generate post on topic: {post_request.topic}")

    # Define a detailed prompt for the AI
    prompt = (
        f"You are a crypto expert named Xexbot, with a persona like @PiLord_officia on X. "
        f"Create a human-like, insightful, and trustworthy X post about '{post_request.topic}'. "
        f"Use relevant emojis, slang (like 'DYOR', 'fam'), and keep it under 280 characters."
    )

    # Generate the response content asynchronously
    try:
        response_text = await generate_response(prompt)
    except Exception as e:
        logger.error(f"Failed to generate AI response: {e}")
        raise HTTPException(status_code=500, detail="AI response generation failed.")

    if "Error:" in response_text:
        logger.error(f"AI service returned an error: {response_text}")
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {response_text}")

    # Add the posting task to the background
    background_tasks.add_task(post_to_x, response_text)

    logger.info(f"Queued post for topic '{post_request.topic}': {response_text}")

    return {
        "message": "Post generation has been queued.",
        "topic": post_request.topic,
        "generated_text_preview": response_text[:75] + "..."
    }

# --- Main entry point for running with uvicorn ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)