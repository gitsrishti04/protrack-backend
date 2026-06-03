"""
AI Chatbot route for Super Admin.

Architecture: LangChain + LangGraph + Gemini API + RAG

LangGraph workflow:
  [fetch_context] → [generate_response] → END

  Node 1 — fetch_context  : Queries PostgreSQL and builds a rich context string (RAG)
  Node 2 — generate_response : Passes context + user question to Gemini via LangChain

Endpoint: POST /chat
"""

import os
from typing import TypedDict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.database import get_db
from app.models.project import Project
from app.models.task import Task
from app.models.project_member import ProjectMember
from app.utils.deps import get_current_user

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

# ── Load env ──────────────────────────────────────────────────────────────
load_dotenv()

router = APIRouter(tags=["chat"])


# ── LangGraph State ───────────────────────────────────────────────────────

class ChatState(TypedDict):
    """State passed between LangGraph nodes"""
    question: str       # user's question
    context:  str       # RAG context fetched from DB
    answer:   str       # final LLM response


# ── RAG: Build context from database ─────────────────────────────────────

def build_project_context(db: Session) -> str:
    """
    Fetches all projects, tasks, and members from DB and formats them
    as a plain-text context block to inject into the LLM prompt (RAG).
    """
    projects = db.query(Project).all()
    tasks    = db.query(Task).all()
    members  = db.query(ProjectMember).all()

    if not projects:
        return "No projects found in the system."

    tasks_by_project: dict[int, list] = {}
    for t in tasks:
        tasks_by_project.setdefault(t.project_id, []).append(t)

    members_by_project: dict[int, list] = {}
    for m in members:
        members_by_project.setdefault(m.project_id, []).append(m)

    lines = ["=== ProTrack Project Database ===\n"]

    for p in projects:
        ptasks   = tasks_by_project.get(p.id, [])
        pmembers = members_by_project.get(p.id, [])

        completed = sum(1 for t in ptasks if t.status == "completed")
        delayed   = sum(1 for t in ptasks if t.status == "delayed")
        in_prog   = sum(1 for t in ptasks if t.status == "in_progress")
        pending   = sum(1 for t in ptasks if t.status == "pending")

        lines.append(f"Project: {p.name}")
        lines.append(f"  ID          : {p.id}")
        lines.append(f"  Status      : {p.status}")
        lines.append(f"  Completion  : {p.completion}%")
        lines.append(f"  Deadline    : {p.deadline}")
        lines.append(f"  Team        : {p.team or 'N/A'}")
        lines.append(f"  Description : {p.description or 'N/A'}")
        lines.append(f"  Tasks       : {len(ptasks)} total | {completed} completed | {in_prog} in-progress | {delayed} delayed | {pending} pending")
        lines.append(f"  Team Members: {len(pmembers)}")

        if pmembers:
            member_list = ", ".join(f"{m.name} ({m.role})" for m in pmembers)
            lines.append(f"  Members     : {member_list}")

        delayed_titles = [t.title for t in ptasks if t.status == "delayed"]
        if delayed_titles:
            lines.append(f"  Delayed Tasks: {', '.join(delayed_titles)}")

        lines.append("")

    total       = len(projects)
    completed_p = sum(1 for p in projects if p.status == "completed")
    delayed_p   = sum(1 for p in projects if p.status == "delayed")
    on_track_p  = sum(1 for p in projects if p.status == "on_track")

    lines.append("=== Portfolio Summary ===")
    lines.append(f"Total Projects  : {total}")
    lines.append(f"Completed       : {completed_p}")
    lines.append(f"On Track        : {on_track_p}")
    lines.append(f"Delayed         : {delayed_p}")
    lines.append(f"Total Tasks     : {len(tasks)}")
    lines.append(f"Total Members   : {len(members)}")

    return "\n".join(lines)


# ── System prompt ─────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are ProTrack AI, an intelligent project management assistant for the Super Admin.

You have access to real-time data from the ProTrack database shown below.

Answer questions about:
- Project progress and status
- Delayed projects and tasks
- Team workload and member assignments
- Resource utilization
- Completion timelines
- Any specific project, task, or team member

Guidelines:
- Be concise and direct
- Use numbers and percentages from the data
- If asked about a specific project, provide specific details
- Format responses clearly with line breaks when listing multiple items
- If the question is not about project management, politely redirect

Database context:
{context}
"""


# ── LangGraph nodes ───────────────────────────────────────────────────────

def generate_response_node(state: ChatState) -> ChatState:
    """
    LangGraph Node 2: Calls Gemini LLM with the RAG context and user question.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {**state, "answer": "Gemini API key not configured."}

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
        temperature=0.3,
    )

    system_with_context = SYSTEM_PROMPT.format(context=state["context"])
    messages = [
        SystemMessage(content=system_with_context),
        HumanMessage(content=state["question"]),
    ]

    try:
        response = llm.invoke(messages)
        return {**state, "answer": response.content}
    except Exception as e:
        return {**state, "answer": f"Error generating response: {str(e)}"}


# ── Build LangGraph workflow ──────────────────────────────────────────────

def build_chat_graph():
    """
    Builds and compiles the LangGraph state machine:
      fetch_context → generate_response → END
    """
    graph = StateGraph(ChatState)

    # Node: generate LLM response (context is injected before running)
    graph.add_node("generate_response", generate_response_node)

    # Edges
    graph.set_entry_point("generate_response")
    graph.add_edge("generate_response", END)

    return graph.compile()


# Compile once at module load
chat_graph = build_chat_graph()


# ── Request / Response schemas ────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


# ── Chat endpoint ─────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    AI Chatbot endpoint for Super Admin.
    Uses LangGraph workflow: RAG context fetch → Gemini LLM response.
    """
    if current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Chatbot is only available to Super Admin")

    # RAG: fetch live context from PostgreSQL
    context = build_project_context(db)

    # Run LangGraph workflow
    try:
        result = chat_graph.invoke({
            "question": request.message,
            "context":  context,
            "answer":   "",
        })
        return ChatResponse(reply=result["answer"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")
