from fastapi import FastAPI, APIRouter, HTTPException, Cookie, Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from openai import AsyncOpenAI
import httpx

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# Supabase connection
supabase_url = os.environ.get('VITE_SUPABASE_URL')
supabase_key = os.environ.get('VITE_SUPABASE_SUPABASE_ANON_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

# OpenAI API Key
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Request/Response Models
class SessionDataRequest(BaseModel):
    session_id: str

class ChatRequest(BaseModel):
    message: str
    topic: str
    chat_id: Optional[str] = None

class QuizRequest(BaseModel):
    topic: str
    num_questions: int = 5

class SummaryRequest(BaseModel):
    content: str

class SaveQuizRequest(BaseModel):
    topic: str
    score: int
    total: int
    questions: List[dict]

class UpdateInterestsRequest(BaseModel):
    interests: List[str]

# Helper Functions
async def get_user_from_token(session_token: Optional[str]) -> Optional[dict]:
    if not session_token:
        return None

    try:
        # Get session
        session_response = supabase.table('sessions').select('*').eq('session_token', session_token).maybeSingle().execute()

        if not session_response.data:
            return None

        session = session_response.data

        # Check if session expired
        expires_at = datetime.fromisoformat(session['expires_at'].replace('Z', '+00:00'))
        if expires_at < datetime.now(timezone.utc):
            supabase.table('sessions').delete().eq('session_token', session_token).execute()
            return None

        # Get user
        user_response = supabase.table('users').select('*').eq('id', session['user_id']).maybeSingle().execute()

        return user_response.data
    except Exception as e:
        logging.error(f"Error getting user from token: {e}")
        return None

# Auth Endpoints
@api_router.post("/auth/session")
async def process_session(request: SessionDataRequest, response: Response):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": request.session_id},
                timeout=10.0
            )

            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail="Invalid session ID")

            data = resp.json()

        # Check if user exists
        existing_user_response = supabase.table('users').select('*').eq('email', data['email']).maybeSingle().execute()

        if not existing_user_response.data:
            # Create new user
            user_data = {
                'email': data['email'],
                'name': data['name'],
                'picture': data.get('picture'),
                'learning_interests': []
            }
            user_response = supabase.table('users').insert(user_data).execute()
            user = user_response.data[0]

            # Create initial progress
            progress_data = {
                'user_id': user['id'],
                'xp_points': 0,
                'topics_learned': [],
                'learning_streak': 0,
                'last_activity': datetime.now(timezone.utc).isoformat()
            }
            supabase.table('progress').insert(progress_data).execute()
        else:
            user = existing_user_response.data

        # Create session
        session_token = data['session_token']
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        session_data = {
            'session_token': session_token,
            'user_id': user['id'],
            'expires_at': expires_at.isoformat()
        }

        supabase.table('sessions').insert(session_data).execute()

        # Set cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="none",
            path="/",
            max_age=7 * 24 * 60 * 60
        )

        return {
            "user": user,
            "session_token": session_token
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Session processing internal error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.get("/auth/me")
async def get_current_user(session_token: Optional[str] = Cookie(None)):
    user = await get_user_from_token(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

@api_router.post("/auth/logout")
async def logout(response: Response, session_token: Optional[str] = Cookie(None)):
    if session_token:
        supabase.table('sessions').delete().eq('session_token', session_token).execute()

    response.delete_cookie(
        key="session_token",
        path="/",
        secure=True,
        samesite="none"
    )

    return {"message": "Logged out successfully"}

@api_router.put("/auth/interests")
async def update_interests(request: UpdateInterestsRequest, session_token: Optional[str] = Cookie(None)):
    user = await get_user_from_token(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    supabase.table('users').update({'learning_interests': request.interests}).eq('id', user['id']).execute()

    return {"message": "Interests updated"}

# AI Chat Endpoints
@api_router.post("/chat")
async def chat_with_ai(request: ChatRequest, session_token: Optional[str] = Cookie(None)):
    user = await get_user_from_token(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Get or create chat history
        chat_id = request.chat_id
        if chat_id:
            chat_response = supabase.table('chat_history').select('*').eq('id', chat_id).maybeSingle().execute()
            chat_history = chat_response.data
        else:
            chat_history = None

        if not chat_history:
            # Create new chat
            chat_data = {
                'user_id': user['id'],
                'topic': request.topic,
                'messages': []
            }
            chat_response = supabase.table('chat_history').insert(chat_data).execute()
            chat_history = chat_response.data[0]
            chat_id = chat_history['id']

        # Add user message
        messages = chat_history.get('messages', [])
        user_message = {
            'role': 'user',
            'content': request.message,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        messages.append(user_message)

        # Create AI chat
        if not openai_client:
            raise HTTPException(status_code=503, detail="AI service not configured")

        system_message = f"You are an expert AI tutor helping users learn about {request.topic}. Provide clear, engaging explanations with examples. Keep responses concise but informative."

        # Build conversation history for OpenAI
        openai_messages = [{"role": "system", "content": system_message}]
        for msg in messages:
            openai_messages.append({"role": msg["role"], "content": msg["content"]})

        # Send message to OpenAI
        completion = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=openai_messages
        )
        response = completion.choices[0].message.content

        # Add AI response
        assistant_message = {
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        messages.append(assistant_message)

        # Save to database
        supabase.table('chat_history').update({'messages': messages}).eq('id', chat_id).execute()

        # Update progress
        progress_response = supabase.table('progress').select('*').eq('user_id', user['id']).maybeSingle().execute()
        if progress_response.data:
            progress = progress_response.data
            new_xp = progress['xp_points'] + 10
            topics = list(set(progress.get('topics_learned', []) + [request.topic]))

            supabase.table('progress').update({
                'xp_points': new_xp,
                'topics_learned': topics,
                'last_activity': datetime.now(timezone.utc).isoformat()
            }).eq('user_id', user['id']).execute()

        return {
            "chat_id": chat_id,
            "response": response,
            "timestamp": assistant_message['timestamp']
        }

    except Exception as e:
        logging.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/chat/history")
async def get_chat_history(session_token: Optional[str] = Cookie(None)):
    user = await get_user_from_token(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    response = supabase.table('chat_history').select('*').eq('user_id', user['id']).order('created_at', desc=True).execute()

    return response.data

@api_router.get("/chat/{chat_id}")
async def get_single_chat(chat_id: str, session_token: Optional[str] = Cookie(None)):
    user = await get_user_from_token(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    response = supabase.table('chat_history').select('*').eq('id', chat_id).eq('user_id', user['id']).maybeSingle().execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Chat not found")

    return response.data

# Quiz Generation Endpoint
@api_router.post("/quiz/generate")
async def generate_quiz(request: QuizRequest, session_token: Optional[str] = Cookie(None)):
    user = await get_user_from_token(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        if not openai_client:
            raise HTTPException(status_code=503, detail="AI service not configured")

        system_message = f"""You are an expert quiz generator. Generate {request.num_questions} multiple-choice questions about {request.topic}.

Return ONLY a valid JSON array of objects with this exact structure:
        [
          {{
            "question": "Question text here?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "Option A",
            "explanation": "Brief explanation why this is correct"
          }}
        ]

Make sure questions are educational, clear, and have distinct options."""

        completion = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Generate {request.num_questions} quiz questions about {request.topic}"}
            ]
        )
        response = completion.choices[0].message.content

        # Parse JSON response
        import json
        response_text = response.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        questions = json.loads(response_text)

        return {
            "topic": request.topic,
            "questions": questions
        }

    except Exception as e:
        logging.error(f"Quiz generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/quiz/save")
async def save_quiz_result(request: SaveQuizRequest, session_token: Optional[str] = Cookie(None)):
    user = await get_user_from_token(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    quiz_data = {
        'user_id': user['id'],
        'topic': request.topic,
        'score': request.score,
        'total': request.total,
        'questions': request.questions
    }

    supabase.table('quiz_results').insert(quiz_data).execute()

    # Update progress
    xp_earned = request.score * 20
    progress_response = supabase.table('progress').select('*').eq('user_id', user['id']).maybeSingle().execute()

    if progress_response.data:
        new_xp = progress_response.data['xp_points'] + xp_earned
        supabase.table('progress').update({
            'xp_points': new_xp,
            'last_activity': datetime.now(timezone.utc).isoformat()
        }).eq('user_id', user['id']).execute()

    return {"message": "Quiz result saved", "xp_earned": xp_earned}

@api_router.get("/quiz/results")
async def get_quiz_results(session_token: Optional[str] = Cookie(None)):
    user = await get_user_from_token(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    response = supabase.table('quiz_results').select('*').eq('user_id', user['id']).order('created_at', desc=True).execute()

    return response.data

# Summarization Endpoint
@api_router.post("/summarize")
async def summarize_content(request: SummaryRequest, session_token: Optional[str] = Cookie(None)):
    user = await get_user_from_token(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        if not openai_client:
            raise HTTPException(status_code=503, detail="AI service not configured")

        system_message = "You are an expert at creating concise, informative summaries. Summarize the given content in under 150 words, highlighting key points and main ideas."

        completion = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Summarize this content:\n\n{request.content}"}
            ]
        )
        response = completion.choices[0].message.content

        # Update progress
        progress_response = supabase.table('progress').select('*').eq('user_id', user['id']).maybeSingle().execute()
        if progress_response.data:
            new_xp = progress_response.data['xp_points'] + 5
            supabase.table('progress').update({
                'xp_points': new_xp,
                'last_activity': datetime.now(timezone.utc).isoformat()
            }).eq('user_id', user['id']).execute()

        return {"summary": response}

    except Exception as e:
        logging.error(f"Summarization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Progress Endpoint
@api_router.get("/progress")
async def get_progress(session_token: Optional[str] = Cookie(None)):
    user = await get_user_from_token(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    response = supabase.table('progress').select('*').eq('user_id', user['id']).maybeSingle().execute()

    if not response.data:
        # Create initial progress
        progress_data = {
            'user_id': user['id'],
            'xp_points': 0,
            'topics_learned': [],
            'learning_streak': 0,
            'last_activity': datetime.now(timezone.utc).isoformat()
        }
        create_response = supabase.table('progress').insert(progress_data).execute()
        return create_response.data[0]

    return response.data

# Topics endpoint
@api_router.get("/topics")
async def get_topics():
    return {
        "topics": [
            {"id": "math", "name": "Mathematics", "icon": "calculator"},
            {"id": "python", "name": "Python Programming", "icon": "code"},
            {"id": "biology", "name": "Biology", "icon": "leaf"},
            {"id": "english", "name": "English", "icon": "book-open"},
            {"id": "history", "name": "History", "icon": "landmark"},
            {"id": "physics", "name": "Physics", "icon": "atom"},
            {"id": "chemistry", "name": "Chemistry", "icon": "flask"},
            {"id": "art", "name": "Art & Design", "icon": "palette"}
        ]
    }

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
