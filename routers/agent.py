from fastapi import APIRouter, Request, Depends, Body, BackgroundTasks
from utils.limiter import limiter
from controllers import agent_controller
from models.api_models import AgentStartRequest, AgentStartResponse

router = APIRouter(prefix="/agent", tags=["Agent"])

@router.post("/start", response_model=AgentStartResponse)
@limiter.limit("1/minute")
async def start_agent(
    request: Request, 
    background_tasks: BackgroundTasks, # <-- Add BackgroundTasks
    body: AgentStartRequest = Body(...)
):
    """
    Starts the LinkedIn browsing agent.
    The agent run is processed in the background.
    Live updates are sent via WebSocket to /ws.
    """
    print("Agent /start endpoint triggered.")
    
    # Add the long-running task to the background
    background_tasks.add_task(agent_controller.run_linkedin_agent, request=body)
    
    # Return an immediate response
    return AgentStartResponse(
        status="Started",
        message="Agent run queued. Check the dashboard for live updates."
    )