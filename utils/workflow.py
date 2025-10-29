from dotenv import load_dotenv
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import settings
from utils.automation import LinkedInAutomator
from models.comment_log import CommentLog
from utils.connection_manager import manager
import random
import asyncio

load_dotenv()

# --- 1. Define State ---
class AgentState(TypedDict):
    auto_comment: bool
    auto_like: bool
    max_posts: int
    user_voice_prompt: str
    cookie_json: str
    
    scraped_posts: List[Dict[str, Any]]
    final_logs: List[Dict[str, Any]]
    summary: str
    error: Optional[str]

# --- 2. Define LLM ---
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", 
    temperature=0.7,
    google_api_key=settings.GEMINI_API_KEY
)

# --- 3. Define System Prompts ---
def get_comment_system_prompt(voice_prompt: str) -> str:
    return f"""
    You are a professional social media engagement assistant. Your goal is to write a short, genuine, and human-sounding comment for a LinkedIn post.
    IMPORTANT: Follow this user's defined "voice" and tone:
    --- USER VOICE ---
    {voice_prompt}
    --- END USER VOICE ---
    You will be given the post's author and content.
    - If the post is not insightful (e.g., "Hiring!", "Happy work anniversary!"), just output the single word: [SKIP]
    - Otherwise, generate a 2-3 sentence comment.
    - Do NOT include greetings or sign-offs.
    """

def get_summary_system_prompt() -> str:
    return """
    You are a professional analyst. You will be given a list of LinkedIn post contents.
    Your task is to generate a concise "Daily Summary" of what the user's network talked about.
    Summarize the top 3-4 key themes or topics you observed.
    Use bullet points.
    """

# --- 4. Define Graph Nodes ---
async def setup_task(state: AgentState) -> AgentState:
    print("Node: setup_task")
    await manager.broadcast({"type": "status", "message": "Task initialized. Setting up..."})
    try:
        state['user_voice_prompt'] = settings.USER_VOICE_PROMPT
        state['final_logs'] = []
        state['scraped_posts'] = []
        state['summary'] = "No summary generated."
        return state
    except Exception as e:
        print(f"Error in setup_task: {e}")
        state['error'] = str(e)
        return state

async def process_feed(state: AgentState) -> AgentState:
    print("Node: process_feed")
    if state.get('error'): return state
    
    await manager.broadcast({"type": "status", "message": "Initializing browser automation..."})
    
    comment_prompt_template = get_comment_system_prompt(state['user_voice_prompt'])
    
    try:
        automator = LinkedInAutomator(
            cookie_json=state['cookie_json'],
            auto_like=state['auto_like'],
            auto_comment=state['auto_comment']
        )
        
        async with automator:
            await manager.broadcast({"type": "status", "message": "Navigating to LinkedIn feed..."})
            await automator.go_to_feed()
            
            await manager.broadcast({"type": "status", "message": f"Scrolling to find {state['max_posts']} posts..."})
            scraped_posts = await automator.scroll_and_scrape_posts(state['max_posts'])
            
            if not scraped_posts:
                 await manager.broadcast({"type": "status", "message": "No posts found on the feed. Ending run."})
                 return state

            await manager.broadcast({"type": "status", "message": f"Found {len(scraped_posts)} posts. Starting processing..."})

            for i, post in enumerate(scraped_posts):
                post_content = post['content']
                post_author = post['author']
                state['scraped_posts'].append(post)
                
                await manager.broadcast({
                    "type": "status", 
                    "message": f"Processing post {i+1}/{len(scraped_posts)} from {post_author}..."
                })

                # 1. Generate Comment
                full_prompt = f"{comment_prompt_template}\n\n--- POST ---\nAuthor: {post_author}\nContent: {post_content}"
                response = await llm.ainvoke(full_prompt)
                comment_text = response.content.strip()

                if comment_text == "[SKIP]":
                    await manager.broadcast({"type": "log", "message": f"Skipping post by {post_author} (not insightful)."})
                    continue
                
                await manager.broadcast({"type": "log", "message": f"Generated comment: '{comment_text[:50]}...'"})

                # 2. Perform Actions (Like/Comment)
                action_results = await automator.perform_actions(post, comment_text)
                
                # 3. Log to DB and State
                log_entry = CommentLog(
                    post_author=post_author,
                    post_content=post_content,
                    generated_comment=comment_text,
                    posted_to_linkedin=action_results["posted"],
                    liked_post=action_results["liked"]
                )
                await log_entry.insert()
                
                await manager.broadcast({
                    "type": "result", 
                    "log": log_entry.model_dump(include={'post_author', 'generated_comment', 'posted_to_linkedin'})
                })
                
                state['final_logs'].append(log_entry.model_dump())
                
                delay = random.uniform(8, 15)
                await manager.broadcast({"type": "status", "message": f"Pausing for {delay:.1f}s..."})
                await asyncio.sleep(delay)

    except Exception as e:
        print(f"Error in process_feed: {e}")
        state['error'] = str(e)
        await manager.broadcast({"type": "error", "message": str(e)})
    return state

async def generate_summary(state: AgentState) -> AgentState:
    print("Node: generate_summary")
    if state.get('error'): return state

    await manager.broadcast({"type": "status", "message": "Generating final summary..."})
    all_post_content = "\n\n---\n\n".join(
        [p['content'] for p in state['scraped_posts'] if p.get('content')]
    )
    
    if not all_post_content:
        state['summary'] = "No insightful posts were found to summarize."
    else:
        summary_prompt = get_summary_system_prompt()
        full_prompt = f"{summary_prompt}\n\n--- POSTS ---\n{all_post_content}"
        try:
            response = await llm.ainvoke(full_prompt)
            state['summary'] = response.content.strip()
        except Exception as e:
            print(f"Error generating summary: {e}")
            state['error'] = str(e)
            state['summary'] = "Error generating summary."
    
    await manager.broadcast({"type": "summary", "message": state['summary']})
    await manager.broadcast({"type": "status", "message": "Agent run finished."})
    return state

def handle_error(state: AgentState) -> AgentState:
    print(f"Node: handle_error. Error: {state.get('error')}")
    return state

# --- 5. Build Graph ---
def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("setup_task", setup_task)
    workflow.add_node("process_feed", process_feed)
    workflow.add_node("generate_summary", generate_summary)
    workflow.add_node("handle_error", handle_error)

    workflow.set_entry_point("setup_task")
    workflow.add_conditional_edges("setup_task", lambda state: "handle_error" if state.get("error") else "process_feed")
    workflow.add_conditional_edges("process_feed", lambda state: "handle_error" if state.get("error") else "generate_summary")
    workflow.add_edge("generate_summary", END)
    workflow.add_edge("handle_error", END)
    return workflow.compile()

# --- 6. Workflow Getter ---
_workflow = None
def get_workflow():
    global _workflow
    if _workflow is None:
        _workflow = build_graph()
    return _workflow