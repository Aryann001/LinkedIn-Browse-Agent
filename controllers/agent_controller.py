from utils.workflow import get_workflow, AgentState
from models.api_models import AgentStartRequest, AgentStartResponse

async def run_linkedin_agent(
    request: AgentStartRequest
) -> AgentStartResponse:
    
    workflow = get_workflow()
    
    initial_state: AgentState = {
        "auto_comment": request.auto_comment,
        "auto_like": request.auto_like,
        "max_posts": request.max_posts_to_process,
        "cookie_json": request.cookie_json, # <-- PASS COOKIES
        "user_voice_prompt": "",
        "scraped_posts": [],
        "final_logs": [],
        "summary": "Process did not complete.",
        "error": None
    }
    
    # We run this in the background so the HTTP request can return immediately
    # Note: This uses FastAPI's background tasks. For heavy production,
    # you'd use Celery or ARQ.
    await workflow.ainvoke(initial_state)
    
    # Return an immediate response to the client
    return AgentStartResponse(
        status="Success",
        message="Agent run started successfully. Check the dashboard for live updates."
    )