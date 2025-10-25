from fastapi import FastAPI, APIRouter, HTTPException, Cookie, Response, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
from emergentintegrations.llm.chat import LlmChat, UserMessage
import httpx

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Emergent LLM Key
LLM_API_KEY = os.environ['EMERGENT_LLM_KEY']

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    picture: Optional[str] = None
    learning_interests: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Session(BaseModel):
    model_config = ConfigDict(extra="ignore")
    session_token: str
    user_id: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatHistory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    topic: str
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: str

class QuizResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    topic: str
    score: int
    total: int
    questions: List[dict]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Progress(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    xp_points: int = 0
    topics_learned: List[str] = Field(default_factory=list)
    learning_streak: int = 0
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
async def get_user_from_token(session_token: Optional[str]) -> Optional[User]:
    if not session_token:
        return None
    
    session = await db.sessions.find_one({"session_token": session_token})
    if not session:
        return None
    
    # Check if session expired
    expires_at = datetime.fromisoformat(session['expires_at']) if isinstance(session['expires_at'], str) else session['expires_at']
    if expires_at < datetime.now(timezone.utc):
        await db.sessions.delete_one({"session_token": session_token})
        return None
    
    user_doc = await db.users.find_one({"id": session['user_id']}, {"_id": 0})
    if not user_doc:
        return None
    
    # Convert datetime strings back to datetime objects
    if isinstance(user_doc.get('created_at'), str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    
    return User(**user_doc)

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
        existing_user = await db.users.find_one({"email": data['email']}, {"_id": 0})
        
        if not existing_user:
            # Create new user
            user = User(
                email=data['email'],
                name=data['name'],
                picture=data.get('picture')
            )
            user_dict = user.model_dump()
            user_dict['created_at'] = user_dict['created_at'].isoformat()
            await db.users.insert_one(user_dict)
            
            # Create initial progress
            progress = Progress(user_id=user.id)
            progress_dict = progress.model_dump()
            progress_dict['last_activity'] = progress_dict['last_activity'].isoformat()
            await db.progress.insert_one(progress_dict)
        else:
            if isinstance(existing_user['created_at'], str):
                existing_user['created_at'] = datetime.fromisoformat(existing_user['created_at'])
            user = User(**existing_user)
        
        # Create session
        session_token = data['session_token']
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        session = Session(
            session_token=session_token,
            user_id=user.id,
            expires_at=expires_at
        )
        
        session_dict = session.model_dump()
        session_dict['expires_at'] = session_dict['expires_at'].isoformat()
        session_dict['created_at'] = session_dict['created_at'].isoformat()
        await db.sessions.insert_one(session_dict)
            
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
            "user": user.model_dump(mode='json'),
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
    return user.model_dump(mode='json')

@api_router.post("/auth/logout")
async def logout(response: Response, session_token: Optional[str] = Cookie(None)):
    if session_token:
        await db.sessions.delete_one({"session_token": session_token})
    
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
    
    await db.users.update_one(
        {"id": user.id},
        {"$set": {"learning_interests": request.interests}}
    )
    
    return {"message": "Interests updated"}

# AI Chat Endpoints
@api_router.post("/chat")
async def chat_with_ai(request: ChatRequest, session_token: Optional[str] = Cookie(None)):
    user = await get_user_from_token(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Get or create chat history
        chat_id = request.chat_id or str(uuid.uuid4())
        chat_doc = await db.chat_history.find_one({"id": chat_id}, {"_id": 0})
        
        if chat_doc:
            # Convert datetime strings
            for msg in chat_doc['messages']:
                if isinstance(msg['timestamp'], str):
                    msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
            if isinstance(chat_doc['created_at'], str):
                chat_doc['created_at'] = datetime.fromisoformat(chat_doc['created_at'])
            chat_history = ChatHistory(**chat_doc)
        else:
            chat_history = ChatHistory(
                id=chat_id,
                user_id=user.id,
                topic=request.topic,
                messages=[]
            )
        
        # Add user message
        user_message = ChatMessage(role="user", content=request.message)
        chat_history.messages.append(user_message)
        
        # Create AI chat
        system_message = f"You are an expert AI tutor helping users learn about {request.topic}. Provide clear, engaging explanations with examples. Keep responses concise but informative."
        
        chat = LlmChat(
            api_key=LLM_API_KEY,
            session_id=chat_id,
            system_message=system_message
        ).with_model("openai", "gpt-4o-mini")
        
        # Send message
        ai_message = UserMessage(text=request.message)
        response = await chat.send_message(ai_message)
        
        # Add AI response
        assistant_message = ChatMessage(role="assistant", content=response)
        chat_history.messages.append(assistant_message)
        
        # Save to database
        chat_dict = chat_history.model_dump()
        for msg in chat_dict['messages']:
            msg['timestamp'] = msg['timestamp'].isoformat()
        chat_dict['created_at'] = chat_dict['created_at'].isoformat()
        
        await db.chat_history.update_one(
            {"id": chat_id},
            {"$set": chat_dict},
            upsert=True
        )
        
        # Update progress
        await db.progress.update_one(
            {"user_id": user.id},
            {
                "$inc": {"xp_points": 10},
                "$addToSet": {"topics_learned": request.topic},
                "$set": {"last_activity": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        return {
            "chat_id": chat_id,
            "response": response,
            "timestamp": assistant_message.timestamp.isoformat()
        }
        
    except Exception as e:
        logging.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/chat/history")
async def get_chat_history(session_token: Optional[str] = Cookie(None)):
    user = await get_user_from_token(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    chats = await db.chat_history.find({"user_id": user.id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    for chat in chats:
        for msg in chat['messages']:
            if isinstance(msg['timestamp'], str):
                msg['timestamp'] = datetime.fromisoformat(msg['timestamp']).isoformat()
        if isinstance(chat['created_at'], str):
            chat['created_at'] = datetime.fromisoformat(chat['created_at']).isoformat()
    
    return chats

@api_router.get("/chat/{chat_id}")
async def get_single_chat(chat_id: str, session_token: Optional[str] = Cookie(None)):
    user = await get_user_from_token(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    chat = await db.chat_history.find_one({"id": chat_id, "user_id": user.id}, {"_id": 0})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    for msg in chat['messages']:
        if isinstance(msg['timestamp'], str):
            msg['timestamp'] = datetime.fromisoformat(msg['timestamp']).isoformat()
    if isinstance(chat['created_at'], str):
        chat['created_at'] = datetime.fromisoformat(chat['created_at']).isoformat()
    
    return chat

# Quiz Generation Endpoint
@api_router.post("/quiz/generate")
async def generate_quiz(request: QuizRequest, session_token: Optional[str] = Cookie(None)):
    user = await get_user_from_token(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
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
        
        chat = LlmChat(
            api_key=LLM_API_KEY,
            session_id=f"quiz_{user.id}_{request.topic}",
            system_message=system_message
        ).with_model("openai", "gpt-4o-mini")
        
        message = UserMessage(text=f"Generate {request.num_questions} quiz questions about {request.topic}")
        response = await chat.send_message(message)
        
        # Parse JSON response
        import json
        # Extract JSON from response (in case it has markdown)
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
    
    quiz_result = QuizResult(
        user_id=user.id,
        topic=request.topic,
        score=request.score,
        total=request.total,
        questions=request.questions
    )
    
    result_dict = quiz_result.model_dump()
    result_dict['created_at'] = result_dict['created_at'].isoformat()
    await db.quiz_results.insert_one(result_dict)
    
    # Update progress
    xp_earned = request.score * 20
    await db.progress.update_one(
        {"user_id": user.id},
        {
            "$inc": {"xp_points": xp_earned},
            "$set": {"last_activity": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    return {"message": "Quiz result saved", "xp_earned": xp_earned}

@api_router.get("/quiz/results")
async def get_quiz_results(session_token: Optional[str] = Cookie(None)):
    user = await get_user_from_token(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    results = await db.quiz_results.find({"user_id": user.id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    for result in results:
        if isinstance(result['created_at'], str):
            result['created_at'] = datetime.fromisoformat(result['created_at']).isoformat()
    
    return results

# Summarization Endpoint
@api_router.post("/summarize")
async def summarize_content(request: SummaryRequest, session_token: Optional[str] = Cookie(None)):
    user = await get_user_from_token(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        system_message = "You are an expert at creating concise, informative summaries. Summarize the given content in under 150 words, highlighting key points and main ideas."
        
        chat = LlmChat(
            api_key=LLM_API_KEY,
            session_id=f"summary_{user.id}",
            system_message=system_message
        ).with_model("openai", "gpt-4o-mini")
        
        message = UserMessage(text=f"Summarize this content:\n\n{request.content}")
        response = await chat.send_message(message)
        
        # Update progress
        await db.progress.update_one(
            {"user_id": user.id},
            {
                "$inc": {"xp_points": 5},
                "$set": {"last_activity": datetime.now(timezone.utc).isoformat()}
            }
        )
        
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
    
    progress_doc = await db.progress.find_one({"user_id": user.id}, {"_id": 0})
    if not progress_doc:
        # Create initial progress
        progress = Progress(user_id=user.id)
        progress_dict = progress.model_dump()
        progress_dict['last_activity'] = progress_dict['last_activity'].isoformat()
        await db.progress.insert_one(progress_dict)
        return progress.model_dump(mode='json')
    
    if isinstance(progress_doc['last_activity'], str):
        progress_doc['last_activity'] = datetime.fromisoformat(progress_doc['last_activity']).isoformat()
    
    return progress_doc

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
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()