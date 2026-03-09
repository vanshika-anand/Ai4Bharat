"""
MemoryThread - Ollama-Powered Backend
Uses Ollama for embeddings and intelligent content adaptation
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import asyncio
import json
import numpy as np
from datetime import datetime
from contextlib import asynccontextmanager
import logging
from sklearn.metrics.pairwise import cosine_similarity
import sqlite3
from pathlib import Path
import uuid
import httpx
import re
from knowledge_graph import KnowledgeGraph

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
EMBEDDING_MODEL = "nomic-embed-text"  # Fast, high-quality embeddings
LLM_MODEL = "llama3.1:8b"  # Llama 3.1 8B - excellent for content generation

# Similarity thresholds (optimized for nomic-embed-text)
THRESHOLD_HIGH_REPETITION = 0.85  # 85%+ = Very similar, definitely repetitive
THRESHOLD_MODERATE_REPETITION = 0.70  # 70-85% = Moderately similar, worth checking
THRESHOLD_LOW_OVERLAP = 0.60  # 60-70% = Some overlap, informational only
# Below 60% = Different content, no warning needed

# Database setup
DB_PATH = Path("memorythread.db")

class ConnectionManager:
    """WebSocket connection manager for real-time updates"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")

manager = ConnectionManager()

# Pydantic v2 Models
class ContentUpload(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=10, max_length=50000)
    platform: str = Field(default="general")
    tags: List[str] = Field(default_factory=list)

class ContentResponse(BaseModel):
    id: int
    title: str
    platform: str
    created_at: datetime
    word_count: int
    tags: List[str]

class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(default=5, ge=1, le=20)

class SearchResult(BaseModel):
    id: int
    title: str
    content_preview: str
    platform: str
    similarity: float
    created_at: datetime

class RepetitionCheck(BaseModel):
    content: str = Field(..., min_length=10, max_length=50000)

class RepetitionResult(BaseModel):
    is_repetition: bool
    similar_content: List[Dict[str, Any]]
    message: str
    max_similarity: float

class PlatformAdaptation(BaseModel):
    content: str = Field(..., min_length=10, max_length=50000)
    source_platform: Optional[str] = None

class AdaptationResult(BaseModel):
    linkedin: Dict[str, str]
    twitter: Dict[str, str]
    instagram: Dict[str, str]
    tiktok: Dict[str, str]
    original_length: int

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    total_content: int
    ollama_status: str

# Ollama client
ollama_client = httpx.AsyncClient(timeout=60.0)

# Knowledge Graph
knowledge_graph = KnowledgeGraph()

async def check_ollama_health() -> bool:
    """Check if Ollama is running and models are available"""
    try:
        response = await ollama_client.get(f"{OLLAMA_BASE_URL}/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            
            has_embedding = any(EMBEDDING_MODEL in name for name in model_names)
            has_llm = any(LLM_MODEL in name for name in model_names)
            
            if not has_embedding:
                logger.warning(f"Embedding model '{EMBEDDING_MODEL}' not found. Run: ollama pull {EMBEDDING_MODEL}")
            if not has_llm:
                logger.warning(f"LLM model '{LLM_MODEL}' not found. Run: ollama pull {LLM_MODEL}")
            
            return has_embedding and has_llm
        return False
    except Exception as e:
        logger.error(f"Ollama health check failed: {e}")
        return False

async def generate_embedding_ollama(text: str) -> List[float]:
    """Generate embeddings using Ollama"""
    try:
        response = await ollama_client.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={
                "model": EMBEDDING_MODEL,
                "prompt": text
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            embedding = data.get("embedding", [])
            
            # Normalize
            embedding = np.array(embedding)
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            return embedding.tolist()
        else:
            logger.error(f"Ollama embedding error: {response.status_code}")
            raise HTTPException(status_code=500, detail="Embedding generation failed")
    
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def generate_with_ollama(prompt: str, system: str = "", max_tokens: int = 2000) -> str:
    """Generate text using Ollama LLM with optimized settings for Llama 3.1"""
    try:
        response = await ollama_client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": LLM_MODEL,
                "prompt": prompt,
                "system": system,
                "stream": False,
                "options": {
                    "temperature": 0.7,  # Balanced creativity
                    "top_p": 0.9,
                    "top_k": 40,
                    "num_predict": max_tokens,
                    "repeat_penalty": 1.1,  # Reduce repetition
                    "num_ctx": 4096,  # Larger context for Llama 3.1
                }
            },
            timeout=60.0
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("response", "")
        else:
            logger.error(f"Ollama generation error: {response.status_code}")
            return ""
    
    except Exception as e:
        logger.error(f"Error generating text: {e}")
        return ""

def extract_key_phrases(text: str, top_n: int = 10) -> List[str]:
    """Extract key phrases for better content understanding"""
    words = re.findall(r'\b[a-z]{4,}\b', text.lower())
    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:top_n]]

# Database initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    logger.info("Initializing MemoryThread with Ollama...")
    
    # Check Ollama
    ollama_ok = await check_ollama_health()
    if ollama_ok:
        logger.info(f"Ollama is running with {EMBEDDING_MODEL} and {LLM_MODEL}")
    else:
        logger.warning("Ollama not fully configured. Please ensure models are pulled.")
        logger.info(f"   Run: ollama pull {EMBEDDING_MODEL}")
        logger.info(f"   Run: ollama pull {LLM_MODEL}")
    
    await init_db()
    logger.info("Database initialized")
    logger.info("Server ready on http://localhost:8000")
    
    yield
    
    await ollama_client.aclose()
    await knowledge_graph.close()
    logger.info("Shutting down gracefully...")

app = FastAPI(
    title="MemoryThread API (Ollama)",
    description="AI Content Intelligence Platform powered by Ollama",
    version="3.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            platform TEXT DEFAULT 'general',
            word_count INTEGER DEFAULT 0,
            tags TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id INTEGER,
            embedding TEXT NOT NULL,
            model_version TEXT DEFAULT 'ollama-nomic',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (content_id) REFERENCES content(id) ON DELETE CASCADE
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            event_data TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('CREATE INDEX IF NOT EXISTS idx_content_platform ON content(platform)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_content_created ON content(created_at)')

    # Content versioning table
    c.execute('''
        CREATE TABLE IF NOT EXISTS content_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            change_summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (content_id) REFERENCES content(id) ON DELETE CASCADE
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_versions_content ON content_versions(content_id)')

    conn.commit()
    conn.close()

async def log_analytics(event_type: str, event_data: Optional[Dict] = None):
    """Log analytics events"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        'INSERT INTO analytics (event_type, event_data) VALUES (?, ?)',
        (event_type, json.dumps(event_data) if event_data else None)
    )
    conn.commit()
    conn.close()

@app.get("/", response_model=Dict[str, str])
async def root():
    return {
        "message": "MemoryThread API v3.0 (Ollama-powered)",
        "docs": "/docs",
        "health": "/api/health"
    }

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check with Ollama status"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM content')
    total_content = c.fetchone()[0]
    conn.close()
    
    ollama_ok = await check_ollama_health()
    
    return HealthResponse(
        status="healthy" if ollama_ok else "degraded",
        timestamp=datetime.utcnow(),
        version="3.0.0-ollama",
        total_content=total_content,
        ollama_status="connected" if ollama_ok else "disconnected"
    )

@app.post("/api/content/upload", response_model=Dict[str, Any])
async def upload_content(
    content: ContentUpload,
    background_tasks: BackgroundTasks
):
    """Upload content with Ollama embeddings"""
    try:
        content_uuid = str(uuid.uuid4())
        word_count = len(content.content.split())
        
        # Store content
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            '''INSERT INTO content (uuid, title, content, platform, word_count, tags)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (content_uuid, content.title, content.content, content.platform, 
             word_count, json.dumps(content.tags))
        )
        content_id = c.lastrowid
        
        # Generate embedding with Ollama
        embedding = await generate_embedding_ollama(content.content)
        c.execute(
            'INSERT INTO embeddings (content_id, embedding, model_version) VALUES (?, ?, ?)',
            (content_id, json.dumps(embedding), 'ollama-nomic')
        )
        
        conn.commit()
        conn.close()
        
        # Extract knowledge graph in background
        background_tasks.add_task(
            knowledge_graph.extract_knowledge,
            content_id,
            content.title,
            content.content
        )
        
        background_tasks.add_task(log_analytics, "content_upload", {
            "content_id": content_id,
            "platform": content.platform,
            "word_count": word_count
        })
        
        await manager.broadcast({
            "type": "content_uploaded",
            "data": {"id": content_id, "title": content.title}
        })
        
        logger.info(f"Content uploaded: {content_id} - {content.title}")
        
        return {
            "success": True,
            "content_id": content_id,
            "uuid": content_uuid,
            "message": "Content uploaded successfully",
            "word_count": word_count,
            "embedding_dimensions": len(embedding)
        }
    
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/content/list", response_model=List[ContentResponse])
async def list_content(
    platform: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List content with pagination"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        if platform:
            c.execute(
                '''SELECT id, title, platform, created_at, word_count, tags
                   FROM content WHERE platform = ?
                   ORDER BY created_at DESC LIMIT ? OFFSET ?''',
                (platform, limit, offset)
            )
        else:
            c.execute(
                '''SELECT id, title, platform, created_at, word_count, tags
                   FROM content ORDER BY created_at DESC LIMIT ? OFFSET ?''',
                (limit, offset)
            )
        
        rows = c.fetchall()
        conn.close()
        
        return [
            ContentResponse(
                id=row[0],
                title=row[1],
                platform=row[2],
                created_at=datetime.fromisoformat(row[3]),
                word_count=row[4],
                tags=json.loads(row[5]) if row[5] else []
            )
            for row in rows
        ]
    
    except Exception as e:
        logger.error(f"List error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search", response_model=List[SearchResult])
async def search_content(query: SearchQuery):
    """Semantic search using Ollama embeddings"""
    try:
        # Generate query embedding
        query_embedding = np.array(await generate_embedding_ollama(query.query)).reshape(1, -1)
        
        # Get all content
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            SELECT c.id, c.title, c.content, c.platform, c.created_at, e.embedding
            FROM content c
            JOIN embeddings e ON c.id = e.content_id
        ''')
        rows = c.fetchall()
        conn.close()
        
        if not rows:
            return []
        
        # Calculate similarities
        results = []
        for row in rows:
            content_id, title, content, platform, created_at, embedding_str = row
            embedding = np.array(json.loads(embedding_str)).reshape(1, -1)
            
            similarity = cosine_similarity(query_embedding, embedding)[0][0]
            
            # Boost if query terms in title
            query_terms = set(query.query.lower().split())
            title_terms = set(title.lower().split())
            title_boost = len(query_terms & title_terms) * 0.1
            
            final_similarity = min(similarity + title_boost, 1.0)
            
            results.append(SearchResult(
                id=content_id,
                title=title,
                content_preview=content[:300] + "..." if len(content) > 300 else content,
                platform=platform,
                similarity=float(final_similarity * 100),
                created_at=datetime.fromisoformat(created_at)
            ))
        
        results.sort(key=lambda x: x.similarity, reverse=True)
        results = [r for r in results if r.similarity > 20.0]
        
        logger.info(f"Search: '{query.query}' - {len(results)} results")
        
        return results[:query.limit]
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/check-repetition", response_model=RepetitionResult)
async def check_repetition(check: RepetitionCheck):
    """Check for repetition using Ollama embeddings"""
    try:
        draft_embedding = np.array(await generate_embedding_ollama(check.content)).reshape(1, -1)
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            SELECT c.id, c.title, c.content, c.platform, c.created_at, e.embedding
            FROM content c
            JOIN embeddings e ON c.id = e.content_id
        ''')
        rows = c.fetchall()
        conn.close()
        
        if not rows:
            return RepetitionResult(
                is_repetition=False,
                similar_content=[],
                message="No past content to compare against",
                max_similarity=0.0
            )
        
        similar_items = []
        max_sim = 0.0
        
        for row in rows:
            content_id, title, content, platform, created_at, embedding_str = row
            embedding = np.array(json.loads(embedding_str)).reshape(1, -1)
            similarity = cosine_similarity(draft_embedding, embedding)[0][0]
            
            max_sim = max(max_sim, similarity)
            
            # Use optimized thresholds
            if similarity > THRESHOLD_LOW_OVERLAP:
                similar_items.append({
                    'id': content_id,
                    'title': title,
                    'content': content,
                    'platform': platform,
                    'similarity': float(similarity * 100),
                    'created_at': created_at
                })
        
        similar_items.sort(key=lambda x: x['similarity'], reverse=True)
        
        is_rep = len(similar_items) > 0
        
        # Categorize by similarity level
        if is_rep:
            if max_sim > THRESHOLD_HIGH_REPETITION:
                message = f"High repetition detected! Found {len(similar_items)} very similar piece(s). Consider referencing or taking a different angle."
            elif max_sim > THRESHOLD_MODERATE_REPETITION:
                message = f"Moderate similarity detected. Found {len(similar_items)} similar piece(s). You may want to differentiate your approach."
            else:
                message = f"Some thematic overlap with {len(similar_items)} piece(s). This could be an opportunity to build on past work."
        else:
            message = "No significant repetition detected - this content is unique!"
        
        logger.info(f"Repetition check: {is_rep} - Max: {max_sim*100:.1f}%")
        
        return RepetitionResult(
            is_repetition=is_rep,
            similar_content=similar_items[:5],
            message=message,
            max_similarity=float(max_sim * 100)
        )
    
    except Exception as e:
        logger.error(f"Repetition check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/adapt-platform", response_model=AdaptationResult)
async def adapt_platform(adaptation: PlatformAdaptation):
    """Intelligent platform adaptation using Llama 3.1"""
    try:
        content = adaptation.content
        
        logger.info(f"Starting platform adaptation with Llama 3.1 for {len(content)} chars")
        
        # Generate adaptations using Llama 3.1 in parallel for speed
        linkedin_task = generate_linkedin_ollama(content)
        twitter_task = generate_twitter_ollama(content)
        instagram_task = generate_instagram_ollama(content)
        tiktok_task = generate_tiktok_ollama(content)
        
        # Wait for all to complete
        linkedin_content, twitter_content, instagram_content, tiktok_content = await asyncio.gather(
            linkedin_task, twitter_task, instagram_task, tiktok_task
        )
        
        adaptations = {
            'linkedin': {
                'title': 'LinkedIn Professional Post',
                'content': linkedin_content,
                'tone': 'Professional & Thought Leadership',
                'format': 'Strategic framework with engagement hooks'
            },
            'twitter': {
                'title': 'Twitter Thread',
                'content': twitter_content,
                'tone': 'Conversational & Engaging',
                'format': 'Numbered thread with narrative tension'
            },
            'instagram': {
                'title': 'Instagram Caption',
                'content': instagram_content,
                'tone': 'Authentic & Relatable',
                'format': 'Visual storytelling with community focus'
            },
            'tiktok': {
                'title': 'TikTok Video Script',
                'content': tiktok_content,
                'tone': 'Fast-paced & Authentic',
                'format': 'Timed script with visual direction'
            }
        }
        
        logger.info(f"Platform adaptation completed successfully with Llama 3.1")
        
        return AdaptationResult(
            linkedin=adaptations['linkedin'],
            twitter=adaptations['twitter'],
            instagram=adaptations['instagram'],
            tiktok=adaptations['tiktok'],
            original_length=len(content)
        )
    
    except Exception as e:
        logger.error(f"Adaptation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def generate_linkedin_ollama(content: str) -> str:
    """Generate LinkedIn version using Llama 3.1 with enhanced prompting"""
    prompt = f"""Transform the following content into a compelling LinkedIn post that drives professional engagement.

CONTENT TO TRANSFORM:
{content[:1500]}

REQUIREMENTS:
1. Start with a powerful hook that captures attention in the first line
2. Structure using clear sections with strategic line breaks
3. Include 2-3 key insights or actionable takeaways
4. Use professional but conversational tone
5. Add 4-6 relevant professional hashtags
6. End with an engaging question that encourages discussion
7. Keep it between 200-350 words
8. Use bullet points or numbered lists where appropriate

LINKEDIN POST:"""
    
    system = """You are an expert LinkedIn content strategist with deep understanding of what drives engagement on the platform. You create posts that:
- Establish thought leadership and credibility
- Provide genuine value to professionals
- Encourage meaningful discussions
- Use strategic formatting for readability
- Balance professionalism with authenticity"""
    
    result = await generate_with_ollama(prompt, system, max_tokens=800)
    return result if result else f"💡 {content[:400]}...\n\n#ProfessionalDevelopment #Leadership #Innovation"

async def generate_twitter_ollama(content: str) -> str:
    """Generate Twitter thread using Llama 3.1 with enhanced prompting"""
    prompt = f"""Transform the following content into an engaging Twitter thread that maximizes engagement.

CONTENT TO TRANSFORM:
{content[:1500]}

REQUIREMENTS:
1. Start with a powerful hook tweet that stops scrolling (use pattern interruption)
2. Create 5-7 tweets total, numbered (1/, 2/, etc.)
3. Each tweet must be under 280 characters
4. Use strategic line breaks for readability
5. Include 1-2 relevant questions to drive replies
6. End with a clear call-to-action
7. Make it conversational and engaging
8. Use thread structure to build narrative tension

TWITTER THREAD:"""
    
    system = """You are a viral Twitter content strategist who understands thread psychology. You create threads that:
- Hook readers immediately with pattern interruption
- Build curiosity and narrative tension
- Use conversational, authentic voice
- Drive engagement through strategic questions
- Maximize retweets and replies
- Follow proven thread formulas"""
    
    result = await generate_with_ollama(prompt, system, max_tokens=1000)
    return result if result else f"🧵 THREAD:\n\n{content[:200]}...\n\n1/\n\nMore in thread 👇"
async def generate_instagram_ollama(content: str) -> str:
    """Generate Instagram caption using Llama 3.1 with enhanced prompting"""
    prompt = f"""Transform the following content into a captivating Instagram caption that drives engagement.

CONTENT TO TRANSFORM:
{content[:1500]}

REQUIREMENTS:
1. Start with an attention-grabbing first line (use curiosity or emotion)
2. Write in casual, relatable, first-person voice
3. Use emojis naturally throughout (but do not overdo it)
4. Include strategic line breaks for mobile readability
5. Add 3-4 calls-to-action (save, share, comment, tag)
6. Include 10-15 relevant hashtags at the end
7. Keep it between 150-250 words
8. Make it feel authentic and personal, not corporate

INSTAGRAM CAPTION:"""
    
    system = """You are an Instagram content creator who understands visual storytelling and community building. You create captions that:
- Feel authentic and relatable
- Drive saves, shares, and meaningful comments
- Use emojis to enhance (not replace) message
- Build community through inclusive language
- Balance value with personality
- Optimize for Instagram's algorithm"""
    
    result = await generate_with_ollama(prompt, system, max_tokens=800)
    return result if result else f"✨ {content[:250]}...\n\n💭 Save this!\n\n#ContentCreator #SocialMedia"
async def generate_tiktok_ollama(content: str) -> str:
    """Generate TikTok script using Llama 3.1 with enhanced prompting"""
    prompt = f"""Transform the following content into a viral TikTok video script with precise timing and visual direction.

CONTENT TO TRANSFORM:
{content[:1500]}

REQUIREMENTS:
1. [HOOK - 0-3 seconds]: Create a pattern-interrupting hook that stops scrolling
2. [PROBLEM/SETUP - 3-10 seconds]: Establish the problem or question
3. [VALUE/SOLUTION - 10-45 seconds]: Deliver the main content in digestible chunks
4. [CTA - 45-60 seconds]: Strong call-to-action for engagement
5. Include [VISUAL CUES] for what should be on screen
6. Include [TEXT OVERLAY] suggestions for key points
7. Use fast-paced, energetic language
8. Add 5-8 relevant hashtags
9. Make it feel authentic, not scripted
10. Total length: 45-60 seconds of content

TIKTOK SCRIPT:"""
    
    system = """You are a viral TikTok content strategist who understands the platform's unique psychology. You create scripts that:
- Hook viewers in the first 3 seconds
- Use pattern interruption and curiosity gaps
- Deliver value in fast-paced, digestible format
- Include clear visual and text overlay direction
- Feel authentic and relatable, not corporate
- Optimize for watch time and engagement
- Follow proven viral formulas"""
    
    result = await generate_with_ollama(prompt, system, max_tokens=1200)
    return result if result else f"[HOOK]\n🎯 {content[:100]}...\n\n[CTA]\nComment 'MORE' for the guide!\n\n#TikTokTips"

@app.get("/api/stats", response_model=Dict[str, Any])
async def get_stats():
    """Get statistics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) FROM content')
        total_content = c.fetchone()[0]
        
        c.execute('SELECT platform, COUNT(*) FROM content GROUP BY platform')
        platform_stats = dict(c.fetchall())
        
        c.execute('SELECT SUM(word_count) FROM content')
        total_words = c.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_content': total_content,
            'platform_breakdown': platform_stats,
            'total_words': total_words,
            'avg_words_per_content': total_words / total_content if total_content > 0 else 0
        }
    
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# TIER 1: Analytics Dashboard, Contradiction Detection,
#          Smart References, Content Gap Analysis
# ============================================================

@app.get("/api/analytics/dashboard", response_model=Dict[str, Any])
async def get_analytics_dashboard():
    """Comprehensive analytics dashboard data"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Basic counts
        c.execute('SELECT COUNT(*) FROM content')
        total_content = c.fetchone()[0]
        c.execute('SELECT SUM(word_count) FROM content')
        total_words = c.fetchone()[0] or 0

        # Platform breakdown
        c.execute('SELECT platform, COUNT(*) FROM content GROUP BY platform')
        platform_breakdown = dict(c.fetchall())

        # Content timeline (posts per month)
        c.execute('''
            SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count
            FROM content GROUP BY month ORDER BY month
        ''')
        timeline = [{'month': r[0], 'count': r[1]} for r in c.fetchall()]

        # Word count distribution
        c.execute('''
            SELECT id, title, word_count, platform, created_at
            FROM content ORDER BY created_at
        ''')
        word_counts = [
            {'id': r[0], 'title': r[1], 'word_count': r[2], 'platform': r[3], 'date': r[4]}
            for r in c.fetchall()
        ]

        # Top topics from knowledge graph
        c.execute('''
            SELECT t.name, COUNT(ct.content_id) as usage_count
            FROM topics t
            JOIN content_topics ct ON t.id = ct.topic_id
            GROUP BY t.name ORDER BY usage_count DESC LIMIT 15
        ''')
        top_topics = [{'name': r[0], 'count': r[1]} for r in c.fetchall()]

        # Top entities
        c.execute('''
            SELECT e.name, e.type, COUNT(ce.content_id) as usage_count
            FROM entities e
            JOIN content_entities ce ON e.id = ce.entity_id
            GROUP BY e.name ORDER BY usage_count DESC LIMIT 15
        ''')
        top_entities = [{'name': r[0], 'type': r[1], 'count': r[2]} for r in c.fetchall()]

        # Writing frequency (posts per day of week)
        c.execute('''
            SELECT CAST(strftime('%w', created_at) AS INTEGER) as dow, COUNT(*) as count
            FROM content GROUP BY dow ORDER BY dow
        ''')
        day_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        writing_frequency = [{'day': day_names[r[0]], 'count': r[1]} for r in c.fetchall()]

        # Average word count trend
        avg_wc = total_words / total_content if total_content > 0 else 0

        # Content diversity score (0-100): how spread across platforms and topics
        platform_count = len(platform_breakdown)
        topic_count = len(top_topics)
        diversity_score = min(100, int((platform_count / 5) * 40 + (min(topic_count, 10) / 10) * 60))

        conn.close()

        return {
            'total_content': total_content,
            'total_words': total_words,
            'avg_words_per_content': round(avg_wc, 1),
            'platform_breakdown': platform_breakdown,
            'timeline': timeline,
            'word_counts': word_counts,
            'top_topics': top_topics,
            'top_entities': top_entities,
            'writing_frequency': writing_frequency,
            'diversity_score': diversity_score,
        }

    except Exception as e:
        logger.error(f"Analytics dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/check-contradiction", response_model=Dict[str, Any])
async def check_contradiction(check: RepetitionCheck):
    """Detect contradictions between new draft and past content using Llama 3.1"""
    try:
        # First find semantically similar content
        draft_embedding = np.array(await generate_embedding_ollama(check.content)).reshape(1, -1)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            SELECT c.id, c.title, c.content, e.embedding
            FROM content c JOIN embeddings e ON c.id = e.content_id
        ''')
        rows = c.fetchall()
        conn.close()

        if not rows:
            return {
                'has_contradictions': False,
                'contradictions': [],
                'message': '✅ No past content to check against.'
            }

        # Get top 5 most similar pieces
        scored = []
        for cid, title, content, emb_str in rows:
            emb = np.array(json.loads(emb_str)).reshape(1, -1)
            sim = cosine_similarity(draft_embedding, emb)[0][0]
            if sim > 0.40:
                scored.append((cid, title, content, sim))
        scored.sort(key=lambda x: x[3], reverse=True)
        top_similar = scored[:5]

        if not top_similar:
            return {
                'has_contradictions': False,
                'contradictions': [],
                'message': '✅ No related past content found — no contradictions possible.'
            }

        # Use Llama 3.1 to detect contradictions
        contradictions = []
        for cid, title, past_content, sim in top_similar:
            prompt = f"""Analyze these two pieces of content for contradictions, conflicting positions, or inconsistent claims.

PAST CONTENT (Title: "{title}"):
{past_content[:1500]}

NEW DRAFT:
{check.content[:1500]}

If there are contradictions or conflicting positions, describe each one clearly.
If there are NO contradictions, respond with exactly: NO_CONTRADICTIONS

Return your analysis in this JSON format:
{{
  "has_contradictions": true/false,
  "items": [
    {{
      "past_claim": "what was said before",
      "new_claim": "what the new draft says",
      "severity": "high/medium/low",
      "explanation": "why these conflict"
    }}
  ]
}}

JSON:"""

            system = "You are a fact-checking expert. Identify contradictions between texts. Be precise. Only flag genuine contradictions, not topic overlap. Return valid JSON only."

            result = await generate_with_ollama(prompt, system, max_tokens=800)

            if result and 'NO_CONTRADICTIONS' not in result:
                try:
                    start = result.find('{')
                    end = result.rfind('}') + 1
                    if start >= 0 and end > start:
                        parsed = json.loads(result[start:end])
                        if parsed.get('has_contradictions') and parsed.get('items'):
                            for item in parsed['items']:
                                item['past_content_id'] = cid
                                item['past_content_title'] = title
                                item['similarity'] = round(sim * 100, 1)
                            contradictions.extend(parsed['items'])
                except (json.JSONDecodeError, KeyError):
                    pass

        has_contradictions = len(contradictions) > 0

        if has_contradictions:
            high = sum(1 for c in contradictions if c.get('severity') == 'high')
            med = sum(1 for c in contradictions if c.get('severity') == 'medium')
            if high > 0:
                message = f"🚨 Found {len(contradictions)} contradiction(s) — {high} high severity. Review before publishing."
            else:
                message = f"⚠️ Found {len(contradictions)} potential inconsistency(ies). Consider addressing them."
        else:
            message = "✅ No contradictions detected — your positions are consistent!"

        return {
            'has_contradictions': has_contradictions,
            'contradictions': contradictions[:10],
            'message': message,
            'content_checked': len(top_similar)
        }

    except Exception as e:
        logger.error(f"Contradiction check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/smart-references", response_model=Dict[str, Any])
async def get_smart_references(check: RepetitionCheck):
    """Suggest relevant past content to reference while writing"""
    try:
        draft_embedding = np.array(await generate_embedding_ollama(check.content)).reshape(1, -1)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            SELECT c.id, c.title, c.content, c.platform, c.created_at, e.embedding
            FROM content c JOIN embeddings e ON c.id = e.content_id
        ''')
        rows = c.fetchall()
        conn.close()

        if not rows:
            return {'references': [], 'message': 'No past content to reference.'}

        # Score all content
        scored = []
        for cid, title, content, platform, created_at, emb_str in rows:
            emb = np.array(json.loads(emb_str)).reshape(1, -1)
            sim = cosine_similarity(draft_embedding, emb)[0][0]
            if 0.35 < sim < 0.90:  # Related but not duplicate
                scored.append({
                    'id': cid,
                    'title': title,
                    'content_preview': content[:200],
                    'platform': platform,
                    'created_at': created_at,
                    'relevance': round(sim * 100, 1)
                })

        scored.sort(key=lambda x: x['relevance'], reverse=True)
        references = scored[:8]

        # Use Llama to generate reference suggestions
        if references:
            titles = ', '.join([f'"{r["title"]}"' for r in references[:5]])
            prompt = f"""Given a new draft about the following topic, suggest how to reference these past pieces:

NEW DRAFT EXCERPT:
{check.content[:500]}

RELATED PAST CONTENT:
{titles}

For each relevant past piece, write a one-sentence suggestion on how to reference or link to it in the new draft. Be specific and actionable.

Suggestions:"""

            system = "You are a content strategist. Help writers create interconnected content by suggesting natural references to past work."
            suggestions_text = await generate_with_ollama(prompt, system, max_tokens=500)
        else:
            suggestions_text = ""

        return {
            'references': references,
            'suggestions': suggestions_text,
            'message': f"Found {len(references)} relevant piece(s) you could reference." if references else "No closely related past content found.",
            'total_checked': len(rows)
        }

    except Exception as e:
        logger.error(f"Smart references error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/content-gaps", response_model=Dict[str, Any])
async def analyze_content_gaps():
    """Analyze content gaps — topics you haven't covered enough"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Get all topics and their usage
        c.execute('''
            SELECT t.name, t.description, COUNT(ct.content_id) as usage_count
            FROM topics t
            LEFT JOIN content_topics ct ON t.id = ct.topic_id
            GROUP BY t.id ORDER BY usage_count ASC
        ''')
        all_topics = [{'name': r[0], 'description': r[1] or '', 'count': r[2]} for r in c.fetchall()]

        # Get all entities and their usage
        c.execute('''
            SELECT e.name, e.type, COUNT(ce.content_id) as usage_count
            FROM entities e
            LEFT JOIN content_entities ce ON e.id = ce.entity_id
            GROUP BY e.id ORDER BY usage_count ASC
        ''')
        all_entities = [{'name': r[0], 'type': r[1], 'count': r[2]} for r in c.fetchall()]

        # Get total content count
        c.execute('SELECT COUNT(*) FROM content')
        total = c.fetchone()[0]

        conn.close()

        if total == 0:
            return {
                'gaps': [],
                'underexplored_topics': [],
                'suggestions': [],
                'message': 'Upload content first to analyze gaps.'
            }

        # Topics mentioned only once = underexplored
        underexplored = [t for t in all_topics if t['count'] == 1]
        # Topics mentioned many times = well-covered
        well_covered = [t for t in all_topics if t['count'] >= 3]

        # Use Llama to suggest content gaps
        topic_names = [t['name'] for t in all_topics[:20]]
        prompt = f"""Based on these topics that a content creator has written about:
{', '.join(topic_names)}

Suggest 5 NEW topics they should explore that are related but not yet covered. For each suggestion:
1. Topic name
2. Why it's relevant to their existing content
3. A potential article title

Return as JSON:
{{
  "suggestions": [
    {{"topic": "name", "reason": "why", "article_idea": "title"}}
  ]
}}

JSON:"""

        system = "You are a content strategist. Identify gaps in a creator's content portfolio and suggest new topics."
        result = await generate_with_ollama(prompt, system, max_tokens=600)

        suggestions = []
        if result:
            try:
                start = result.find('{')
                end = result.rfind('}') + 1
                if start >= 0 and end > start:
                    parsed = json.loads(result[start:end])
                    suggestions = parsed.get('suggestions', [])
            except (json.JSONDecodeError, KeyError):
                pass

        return {
            'underexplored_topics': underexplored[:10],
            'well_covered_topics': well_covered[:10],
            'suggestions': suggestions,
            'total_topics': len(all_topics),
            'total_entities': len(all_entities),
            'message': f"Analyzed {len(all_topics)} topics across {total} pieces of content."
        }

    except Exception as e:
        logger.error(f"Content gaps error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# TIER 2: Knowledge Graph Visualization, Content Health Score,
#          Tone/Voice Consistency Analyzer
# ============================================================

@app.get("/api/knowledge/visualization", response_model=Dict[str, Any])
async def get_knowledge_visualization(max_nodes: int = 50):
    """Get knowledge graph data for visualization, filtered to most connected nodes"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Get entities ranked by connection count
        c.execute('''
            SELECT e.id, e.name, e.type, COUNT(ce.content_id) as content_count
            FROM entities e
            LEFT JOIN content_entities ce ON e.id = ce.entity_id
            GROUP BY e.id
            ORDER BY content_count DESC
        ''')
        all_entities = [
            {'id': f'e_{r[0]}', 'name': r[1], 'type': r[2], 'size': r[3], 'group': 'entity'}
            for r in c.fetchall()
        ]

        # Get topics ranked by connection count
        c.execute('''
            SELECT t.id, t.name, COUNT(ct.content_id) as content_count
            FROM topics t
            LEFT JOIN content_topics ct ON t.id = ct.topic_id
            GROUP BY t.id
            ORDER BY content_count DESC
        ''')
        all_topics = [
            {'id': f't_{r[0]}', 'name': r[1], 'type': 'topic', 'size': r[2], 'group': 'topic'}
            for r in c.fetchall()
        ]

        # Get content nodes
        c.execute('SELECT id, title, platform FROM content')
        content_nodes = [
            {'id': f'c_{r[0]}', 'name': r[1], 'type': r[2], 'size': 2, 'group': 'content'}
            for r in c.fetchall()
        ]

        # Budget: allocate node slots — content gets priority, then top entities/topics
        content_budget = min(len(content_nodes), max(5, max_nodes // 4))
        remaining = max_nodes - content_budget
        entity_budget = min(len(all_entities), remaining * 2 // 3)
        topic_budget = min(len(all_topics), remaining - entity_budget)

        selected_content = content_nodes[:content_budget]
        selected_entities = all_entities[:entity_budget]
        selected_topics = all_topics[:topic_budget]

        nodes = selected_entities + selected_topics + selected_content
        node_ids = {n['id'] for n in nodes}

        # Build links only between selected nodes
        links = []

        c.execute('SELECT content_id, entity_id FROM content_entities')
        for r in c.fetchall():
            src, tgt = f'c_{r[0]}', f'e_{r[1]}'
            if src in node_ids and tgt in node_ids:
                links.append({'source': src, 'target': tgt, 'type': 'has_entity'})

        c.execute('SELECT content_id, topic_id FROM content_topics')
        for r in c.fetchall():
            src, tgt = f'c_{r[0]}', f't_{r[1]}'
            if src in node_ids and tgt in node_ids:
                links.append({'source': src, 'target': tgt, 'type': 'has_topic'})

        c.execute('SELECT entity1_id, entity2_id, relationship_type FROM entity_relationships')
        for r in c.fetchall():
            src, tgt = f'e_{r[0]}', f'e_{r[1]}'
            if src in node_ids and tgt in node_ids:
                links.append({'source': src, 'target': tgt, 'type': r[2]})

        # Remove orphan nodes (no connections after filtering)
        connected_ids = set()
        for l in links:
            connected_ids.add(l['source']); connected_ids.add(l['target'])
        nodes = [n for n in nodes if n['id'] in connected_ids]

        conn.close()

        return {
            'nodes': nodes,
            'links': links,
            'clusters': len({n['group'] for n in nodes}),
            'stats': {
                'total_nodes': len(nodes),
                'total_links': len(links),
                'entity_count': len([n for n in nodes if n['group'] == 'entity']),
                'topic_count': len([n for n in nodes if n['group'] == 'topic']),
                'content_count': len([n for n in nodes if n['group'] == 'content']),
                'total_entities_in_db': len(all_entities),
                'total_topics_in_db': len(all_topics),
            }
        }

    except Exception as e:
        logger.error(f"Knowledge visualization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/content-health", response_model=Dict[str, Any])
async def get_content_health():
    """Calculate overall content health score"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute('SELECT COUNT(*) FROM content')
        total = c.fetchone()[0]

        if total == 0:
            return {
                'overall_score': 0,
                'breakdown': {},
                'recommendations': ['Start by uploading your content to build your memory base.'],
                'message': 'No content to analyze yet.'
            }

        # 1. Volume score (0-25): Do you have enough content?
        volume_score = min(25, int((total / 20) * 25))

        # 2. Diversity score (0-25): Content across platforms
        c.execute('SELECT COUNT(DISTINCT platform) FROM content')
        platform_count = c.fetchone()[0]
        diversity_score = min(25, int((platform_count / 4) * 25))

        # 3. Consistency score (0-25): Regular posting
        c.execute('''
            SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count
            FROM content GROUP BY month ORDER BY month
        ''')
        months = c.fetchall()
        if len(months) > 1:
            counts = [m[1] for m in months]
            avg = sum(counts) / len(counts)
            variance = sum((c - avg) ** 2 for c in counts) / len(counts)
            # Lower variance = more consistent
            consistency_score = min(25, max(0, int(25 - (variance / avg) * 5))) if avg > 0 else 0
        else:
            consistency_score = 10

        # 4. Depth score (0-25): Topic coverage depth
        c.execute('SELECT COUNT(DISTINCT id) FROM topics')
        topic_count = c.fetchone()[0]
        c.execute('SELECT COUNT(DISTINCT id) FROM entities')
        entity_count = c.fetchone()[0]
        depth_score = min(25, int(((topic_count + entity_count) / (total * 3)) * 25))

        overall = volume_score + diversity_score + consistency_score + depth_score

        # Generate recommendations
        recommendations = []
        if volume_score < 15:
            recommendations.append('📝 Upload more content to build a stronger memory base.')
        if diversity_score < 15:
            recommendations.append('📱 Try posting on more platforms to increase your reach.')
        if consistency_score < 15:
            recommendations.append('📅 Post more consistently — regular cadence builds audience.')
        if depth_score < 15:
            recommendations.append('🔬 Go deeper on your topics — explore subtopics and related areas.')
        if overall >= 80:
            recommendations.append('🌟 Your content portfolio is in great shape!')

        conn.close()

        return {
            'overall_score': overall,
            'breakdown': {
                'volume': {'score': volume_score, 'max': 25, 'label': 'Content Volume'},
                'diversity': {'score': diversity_score, 'max': 25, 'label': 'Platform Diversity'},
                'consistency': {'score': consistency_score, 'max': 25, 'label': 'Posting Consistency'},
                'depth': {'score': depth_score, 'max': 25, 'label': 'Topic Depth'},
            },
            'recommendations': recommendations,
            'message': f'Content Health Score: {overall}/100'
        }

    except Exception as e:
        logger.error(f"Content health error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-tone", response_model=Dict[str, Any])
async def analyze_tone(check: RepetitionCheck):
    """Analyze writing tone/voice consistency against past content"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, title, content FROM content ORDER BY created_at DESC LIMIT 5')
        past_content = c.fetchall()
        conn.close()

        if not past_content:
            return {
                'tone_consistent': True,
                'analysis': {},
                'message': 'No past content to compare voice against.'
            }

        # Build a sample of past writing
        past_samples = '\n---\n'.join([f"Title: {r[1]}\n{r[2][:300]}" for r in past_content[:3]])

        prompt = f"""Analyze the writing tone and voice of these texts.

PAST CONTENT (established voice):
{past_samples}

NEW DRAFT:
{check.content[:1000]}

Compare the tone, style, and voice. Analyze:
1. Formality level (1-10, 1=very casual, 10=very formal)
2. Emotional tone (positive/neutral/negative)
3. Writing style (descriptive/analytical/conversational/academic)
4. Voice consistency (does the new draft match the established voice?)

Return JSON:
{{
  "past_voice": {{
    "formality": 7,
    "tone": "positive",
    "style": "conversational",
    "characteristics": ["engaging", "uses examples"]
  }},
  "new_voice": {{
    "formality": 5,
    "tone": "neutral",
    "style": "analytical",
    "characteristics": ["data-driven", "formal"]
  }},
  "consistency_score": 75,
  "drift_areas": ["formality dropped", "less use of examples"],
  "suggestions": ["Add more examples to match your usual style"]
}}

JSON:"""

        system = "You are a writing style analyst. Compare writing voices precisely. Return valid JSON only."
        result = await generate_with_ollama(prompt, system, max_tokens=600)

        analysis = {}
        if result:
            try:
                start = result.find('{')
                end = result.rfind('}') + 1
                if start >= 0 and end > start:
                    analysis = json.loads(result[start:end])
            except (json.JSONDecodeError, KeyError):
                pass

        consistency = analysis.get('consistency_score', 50)
        is_consistent = consistency >= 70

        if is_consistent:
            message = f"✅ Voice consistency: {consistency}% — Your writing voice is consistent!"
        else:
            message = f"⚠️ Voice consistency: {consistency}% — Your tone has drifted from your usual style."

        return {
            'tone_consistent': is_consistent,
            'consistency_score': consistency,
            'analysis': analysis,
            'message': message,
            'past_content_analyzed': len(past_content)
        }

    except Exception as e:
        logger.error(f"Tone analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# TIER 3: Bulk Upload, Export
# ============================================================

@app.post("/api/content/bulk-upload", response_model=Dict[str, Any])
async def bulk_upload(
    contents: List[ContentUpload],
    background_tasks: BackgroundTasks
):
    """Upload multiple content pieces at once"""
    try:
        results = []
        content_ids_for_extraction = []

        for item in contents:
            content_uuid = str(uuid.uuid4())
            word_count = len(item.content.split())

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                '''INSERT INTO content (uuid, title, content, platform, word_count, tags)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (content_uuid, item.title, item.content, item.platform,
                 word_count, json.dumps(item.tags))
            )
            content_id = c.lastrowid

            embedding = await generate_embedding_ollama(item.content)
            c.execute(
                'INSERT INTO embeddings (content_id, embedding, model_version) VALUES (?, ?, ?)',
                (content_id, json.dumps(embedding), 'ollama-nomic')
            )
            conn.commit()
            conn.close()

            content_ids_for_extraction.append((content_id, item.title, item.content))

            results.append({
                'content_id': content_id,
                'title': item.title,
                'word_count': word_count
            })

        # Extract knowledge sequentially in background to avoid overwhelming Ollama
        async def extract_all_knowledge(items):
            for cid, title, content in items:
                try:
                    await knowledge_graph.extract_knowledge(cid, title, content)
                except Exception as e:
                    logger.warning(f"KG extraction failed for {cid}: {e}")

        background_tasks.add_task(extract_all_knowledge, content_ids_for_extraction)

        return {
            'success': True,
            'uploaded': len(results),
            'items': results,
            'message': f'Successfully uploaded {len(results)} content pieces.'
        }

    except Exception as e:
        logger.error(f"Bulk upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/check-repetition-graph", response_model=Dict[str, Any])
async def check_repetition_graph(check: RepetitionCheck):
    """Check for repetition using knowledge graph analysis"""
    try:
        result = await knowledge_graph.check_repetition_with_graph(check.content)
        logger.info(f"Knowledge graph repetition check: {result['is_repetition']} - Max: {result.get('max_similarity', 0):.1f}%")
        return result
    
    except Exception as e:
        logger.error(f"Knowledge graph repetition check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/knowledge/graph/{content_id}", response_model=Dict[str, Any])
async def get_knowledge_graph(content_id: int):
    """Get the knowledge graph for a specific content"""
    try:
        graph = knowledge_graph.get_content_graph(content_id)
        return {
            "content_id": content_id,
            "graph": graph
        }
    
    except Exception as e:
        logger.error(f"Get knowledge graph error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/knowledge/related/{content_id}", response_model=List[Dict[str, Any]])
async def get_related_content(content_id: int, limit: int = 10):
    """Find related content using knowledge graph"""
    try:
        related = knowledge_graph.find_related_content(content_id, limit)
        return related
    
    except Exception as e:
        logger.error(f"Get related content error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/knowledge/extract/{content_id}")
async def extract_knowledge_for_content(content_id: int):
    """Manually trigger knowledge extraction for existing content"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT title, content FROM content WHERE id = ?', (content_id,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Content not found")
        
        title, content = row
        knowledge = await knowledge_graph.extract_knowledge(content_id, title, content)
        
        return {
            "success": True,
            "content_id": content_id,
            "knowledge": knowledge
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extract knowledge error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/content/clear-all")
async def clear_all_content():
    """Delete all content (use with caution!)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get count before deletion
        c.execute('SELECT COUNT(*) FROM content')
        count = c.fetchone()[0]
        
        # Delete all embeddings
        c.execute('DELETE FROM embeddings')
        
        # Delete all content
        c.execute('DELETE FROM content')
        
        # Reset auto-increment
        c.execute('DELETE FROM sqlite_sequence WHERE name="content"')
        c.execute('DELETE FROM sqlite_sequence WHERE name="embeddings"')
        
        conn.commit()
        conn.close()
        
        logger.warning(f"All content cleared: {count} items deleted")
        
        return {
            "success": True, 
            "message": f"All content cleared ({count} items deleted)",
            "deleted_count": count
        }
    
    except Exception as e:
        logger.error(f"Clear all error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/content/{content_id}")
async def get_content(content_id: int):
    """Get a single content item with full text"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, title, content, platform, word_count, created_at FROM content WHERE id = ?', (content_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            raise HTTPException(status_code=404, detail="Content not found")
        return {
            'id': row[0], 'title': row[1], 'content': row[2],
            'platform': row[3], 'word_count': row[4], 'created_at': row[5]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get content error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/content/{content_id}")
async def delete_content(content_id: int):
    """Delete a specific content item"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if content exists
        c.execute('SELECT id FROM content WHERE id = ?', (content_id,))
        if not c.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Delete embeddings first (foreign key)
        c.execute('DELETE FROM embeddings WHERE content_id = ?', (content_id,))
        
        # Delete content
        c.execute('DELETE FROM content WHERE id = ?', (content_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Content deleted: {content_id}")
        
        return {"success": True, "message": "Content deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# CONTENT CALENDAR — AI-suggested posting schedule
# ═══════════════════════════════════════════════════════════════
@app.get("/api/content-calendar")
async def get_content_calendar():
    """Generate AI-powered content calendar based on gaps and patterns"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute('SELECT id, title, platform, created_at FROM content ORDER BY created_at DESC')
        all_content = [{'id': r[0], 'title': r[1], 'platform': r[2], 'date': r[3]} for r in c.fetchall()]

        c.execute('''
            SELECT t.name, COUNT(ct.content_id) as cnt
            FROM topics t LEFT JOIN content_topics ct ON t.id = ct.topic_id
            GROUP BY t.id ORDER BY cnt ASC LIMIT 15
        ''')
        underexplored = [{'name': r[0], 'count': r[1]} for r in c.fetchall()]

        c.execute('SELECT platform, COUNT(*) FROM content GROUP BY platform')
        platform_counts = {r[0]: r[1] for r in c.fetchall()}

        conn.close()

        if not all_content:
            return {'calendar': [], 'message': 'Upload content first to generate a calendar.'}

        topics_str = ', '.join([t['name'] for t in underexplored[:10]]) or 'general topics'
        platforms_str = ', '.join([f"{p}: {cnt}" for p, cnt in platform_counts.items()])
        recent_titles = ', '.join([c['title'] for c in all_content[:8]])

        prompt = f"""You are a content strategist. Based on this creator's data:

Recent content: {recent_titles}
Underexplored topics: {topics_str}
Platform distribution: {platforms_str}
Total pieces: {len(all_content)}

Create a 7-day content calendar. For each day suggest:
1. A specific content topic/title
2. The best platform for it
3. Why this topic (gap filling, trending, audience growth)
4. Priority (high/medium/low)

Return JSON:
{{
  "calendar": [
    {{"day": 1, "weekday": "Monday", "title": "...", "platform": "...", "reason": "...", "priority": "high", "topic_tags": ["tag1"]}}
  ],
  "strategy_notes": "brief overall strategy"
}}

JSON:"""

        result = await generate_with_ollama(prompt, "You are an expert content strategist. Return valid JSON only.", max_tokens=1200)

        calendar = []
        strategy = ""
        if result:
            try:
                start = result.find('{')
                end = result.rfind('}') + 1
                if start >= 0 and end > start:
                    parsed = json.loads(result[start:end])
                    calendar = parsed.get('calendar', [])
                    strategy = parsed.get('strategy_notes', '')
            except (json.JSONDecodeError, KeyError):
                pass

        await log_analytics("content_calendar", {"items": len(calendar)})

        return {
            'calendar': calendar,
            'strategy_notes': strategy,
            'underexplored_topics': underexplored[:5],
            'platform_balance': platform_counts,
            'message': f"Generated 7-day calendar based on {len(all_content)} pieces of content."
        }
    except Exception as e:
        logger.error(f"Content calendar error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# AUDIENCE PERSONA BUILDER — Generate reader personas
# ═══════════════════════════════════════════════════════════════
@app.get("/api/audience-personas")
async def get_audience_personas():
    """Generate audience personas from content patterns"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute('SELECT title, content, platform FROM content ORDER BY created_at DESC LIMIT 15')
        recent = [{'title': r[0], 'content': r[1][:300], 'platform': r[2]} for r in c.fetchall()]

        c.execute('''
            SELECT t.name, COUNT(ct.content_id) as cnt
            FROM topics t JOIN content_topics ct ON t.id = ct.topic_id
            GROUP BY t.id ORDER BY cnt DESC LIMIT 10
        ''')
        top_topics = [r[0] for r in c.fetchall()]

        c.execute('''
            SELECT e.name, e.type, COUNT(ce.content_id) as cnt
            FROM entities e JOIN content_entities ce ON e.id = ce.entity_id
            GROUP BY e.id ORDER BY cnt DESC LIMIT 10
        ''')
        top_entities = [{'name': r[0], 'type': r[1]} for r in c.fetchall()]

        c.execute('SELECT platform, COUNT(*) FROM content GROUP BY platform')
        platforms = {r[0]: r[1] for r in c.fetchall()}

        conn.close()

        if not recent:
            return {'personas': [], 'message': 'Upload content first to generate personas.'}

        content_summaries = '; '.join([f"[{c['platform']}] {c['title']}: {c['content'][:100]}" for c in recent[:8]])

        prompt = f"""Analyze this content creator's portfolio and generate 3 distinct audience personas.

Content samples: {content_summaries}
Top topics: {', '.join(top_topics)}
Key entities: {', '.join([e['name'] for e in top_entities])}
Platforms used: {', '.join(platforms.keys())}

For each persona create:
1. A name and emoji avatar
2. Demographics (age range, profession, interests)
3. Pain points this content solves
4. Preferred platform
5. Content preferences
6. Engagement style

Return JSON:
{{
  "personas": [
    {{
      "name": "...",
      "emoji": "👩‍💻",
      "age_range": "25-35",
      "profession": "...",
      "interests": ["..."],
      "pain_points": ["..."],
      "preferred_platform": "...",
      "content_preferences": ["..."],
      "engagement_style": "...",
      "description": "one line summary"
    }}
  ],
  "audience_insights": "brief overall audience analysis"
}}

JSON:"""

        result = await generate_with_ollama(prompt, "You are an audience research expert. Return valid JSON only.", max_tokens=1500)

        personas = []
        insights = ""
        if result:
            try:
                start = result.find('{')
                end = result.rfind('}') + 1
                if start >= 0 and end > start:
                    parsed = json.loads(result[start:end])
                    personas = parsed.get('personas', [])
                    insights = parsed.get('audience_insights', '')
            except (json.JSONDecodeError, KeyError):
                pass

        await log_analytics("audience_personas", {"count": len(personas)})

        return {
            'personas': personas,
            'audience_insights': insights,
            'top_topics': top_topics,
            'platforms': platforms,
            'message': f"Generated {len(personas)} personas from {len(recent)} content pieces."
        }
    except Exception as e:
        logger.error(f"Audience personas error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# SEO ANALYZER — Keyword density, readability, meta suggestions
# ═══════════════════════════════════════════════════════════════
class SEORequest(BaseModel):
    content: str
    title: str = ""
    target_keyword: str = ""

@app.post("/api/seo-analyze")
async def analyze_seo(req: SEORequest):
    """Analyze content for SEO: readability, keywords, meta suggestions"""
    try:
        text = req.content
        words = text.split()
        word_count = len(words)
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        sentence_count = max(len(sentences), 1)
        avg_sentence_len = word_count / sentence_count

        def count_syllables(word):
            word = word.lower().strip(".,!?;:'\"")
            if len(word) <= 3:
                return 1
            count = 0
            vowels = 'aeiou'
            prev_vowel = False
            for ch in word:
                is_vowel = ch in vowels
                if is_vowel and not prev_vowel:
                    count += 1
                prev_vowel = is_vowel
            if word.endswith('e'):
                count -= 1
            return max(count, 1)

        total_syllables = sum(count_syllables(w) for w in words)
        avg_syllables = total_syllables / max(word_count, 1)

        flesch = 206.835 - (1.015 * avg_sentence_len) - (84.6 * avg_syllables)
        flesch = max(0, min(100, round(flesch, 1)))

        grade = 0.39 * avg_sentence_len + 11.8 * avg_syllables - 15.59
        grade = max(1, min(18, round(grade, 1)))

        keyword_density = {}
        clean_words = [re.sub(r'[^a-zA-Z]', '', w.lower()) for w in words]
        clean_words = [w for w in clean_words if len(w) > 3]
        stopwords = {'this', 'that', 'with', 'from', 'have', 'been', 'were', 'they', 'their', 'what',
                      'when', 'where', 'which', 'will', 'would', 'could', 'should', 'about', 'there',
                      'these', 'those', 'then', 'than', 'them', 'into', 'some', 'such', 'only', 'other',
                      'more', 'most', 'also', 'very', 'just', 'your', 'each', 'make', 'like', 'does'}
        for w in clean_words:
            if w not in stopwords:
                keyword_density[w] = keyword_density.get(w, 0) + 1

        top_keywords = sorted(keyword_density.items(), key=lambda x: -x[1])[:15]
        top_kw_list = [{'keyword': k, 'count': v, 'density': round(v / max(len(clean_words), 1) * 100, 2)} for k, v in top_keywords]

        target_info = None
        if req.target_keyword:
            tk = req.target_keyword.lower()
            tk_count = text.lower().count(tk)
            tk_density = round(tk_count / max(word_count, 1) * 100, 2)
            in_title = tk in req.title.lower() if req.title else False
            in_first_100 = tk in ' '.join(words[:100]).lower()
            target_info = {
                'keyword': req.target_keyword, 'count': tk_count, 'density': tk_density,
                'in_title': in_title, 'in_first_100_words': in_first_100,
                'optimal_density': '1-3%',
                'status': 'good' if 1 <= tk_density <= 3 else 'low' if tk_density < 1 else 'high'
            }

        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        para_count = len(paragraphs) or 1
        headings = len(re.findall(r'^#{1,6}\s', text, re.MULTILINE))
        links = len(re.findall(r'https?://\S+', text))

        seo_score = 50
        if 14 <= avg_sentence_len <= 20: seo_score += 10
        elif avg_sentence_len < 25: seo_score += 5
        if flesch >= 60: seo_score += 10
        elif flesch >= 40: seo_score += 5
        if 300 <= word_count <= 2500: seo_score += 10
        elif word_count > 2500: seo_score += 5
        if headings >= 2: seo_score += 5
        if para_count >= 3: seo_score += 5
        if target_info and target_info['status'] == 'good': seo_score += 10
        if target_info and target_info['in_title']: seo_score += 5
        seo_score = min(100, seo_score)

        prompt = f"""Analyze this content for SEO and suggest improvements:

Title: {req.title or '(no title)'}
Word count: {word_count}
Readability: Flesch {flesch}, Grade {grade}
Top keywords: {', '.join([k['keyword'] for k in top_kw_list[:5]])}

Content preview: {text[:500]}

Provide:
1. A suggested meta title (50-60 chars)
2. A meta description (150-160 chars)
3. 3 specific SEO improvement tips

Return JSON:
{{
  "meta_title": "...",
  "meta_description": "...",
  "tips": ["tip1", "tip2", "tip3"]
}}

JSON:"""

        llm_result = await generate_with_ollama(prompt, "You are an SEO expert. Return valid JSON only.", max_tokens=500)
        meta = {}
        if llm_result:
            try:
                start = llm_result.find('{')
                end = llm_result.rfind('}') + 1
                if start >= 0 and end > start:
                    meta = json.loads(llm_result[start:end])
            except (json.JSONDecodeError, KeyError):
                pass

        readability_label = (
            'Very Easy' if flesch >= 80 else 'Easy' if flesch >= 70 else
            'Fairly Easy' if flesch >= 60 else 'Standard' if flesch >= 50 else
            'Fairly Difficult' if flesch >= 30 else 'Difficult'
        )

        await log_analytics("seo_analyze", {"word_count": word_count, "score": seo_score})

        return {
            'seo_score': seo_score,
            'readability': {
                'flesch_score': flesch, 'flesch_label': readability_label,
                'grade_level': grade, 'avg_sentence_length': round(avg_sentence_len, 1),
                'avg_syllables_per_word': round(avg_syllables, 2)
            },
            'structure': {
                'word_count': word_count, 'sentence_count': sentence_count,
                'paragraph_count': para_count, 'heading_count': headings, 'link_count': links
            },
            'keywords': top_kw_list,
            'target_keyword': target_info,
            'meta_suggestions': meta,
            'message': f"SEO Score: {seo_score}/100 · Readability: {readability_label}"
        }
    except Exception as e:
        logger.error(f"SEO analyze error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# CONTENT VERSIONING — Track edits and show diffs
# ═══════════════════════════════════════════════════════════════
class ContentUpdate(BaseModel):
    title: str
    content: str

@app.post("/api/content/{content_id}/update")
async def update_content_version(content_id: int, update: ContentUpdate):
    """Update content and save previous version"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute('SELECT title, content FROM content WHERE id = ?', (content_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Content not found")

        old_title, old_content = row

        c.execute('SELECT COALESCE(MAX(version), 0) FROM content_versions WHERE content_id = ?', (content_id,))
        current_version = c.fetchone()[0]
        new_version = current_version + 1

        if current_version == 0:
            c.execute('''INSERT INTO content_versions (content_id, title, content, version, change_summary)
                         VALUES (?, ?, ?, 1, 'Original version')''',
                      (content_id, old_title, old_content))
            new_version = 2

        change_summary = ""
        if old_content != update.content:
            prompt = f"""Compare these two versions and describe what changed in one sentence.

OLD: {old_content[:500]}
NEW: {update.content[:500]}

One sentence summary:"""
            change_summary = await generate_with_ollama(prompt, "Summarize content changes concisely.", max_tokens=100)
            change_summary = change_summary.strip()[:200] if change_summary else "Content updated"

        c.execute('''INSERT INTO content_versions (content_id, title, content, version, change_summary)
                     VALUES (?, ?, ?, ?, ?)''',
                  (content_id, old_title, old_content, new_version, change_summary))

        word_count = len(update.content.split())
        c.execute('''UPDATE content SET title = ?, content = ?, word_count = ?, updated_at = CURRENT_TIMESTAMP
                     WHERE id = ?''', (update.title, update.content, word_count, content_id))

        conn.commit()
        conn.close()

        try:
            embedding = await generate_embedding_ollama(update.content)
            if embedding:
                conn2 = sqlite3.connect(DB_PATH)
                c2 = conn2.cursor()
                c2.execute('DELETE FROM embeddings WHERE content_id = ?', (content_id,))
                c2.execute('INSERT INTO embeddings (content_id, embedding) VALUES (?, ?)',
                           (content_id, json.dumps(embedding)))
                conn2.commit()
                conn2.close()
        except Exception as emb_err:
            logger.warning(f"Embedding update failed: {emb_err}")

        await log_analytics("content_update", {"content_id": content_id, "version": new_version})

        return {
            'content_id': content_id, 'version': new_version,
            'change_summary': change_summary, 'message': f'Updated to version {new_version}'
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/content/{content_id}/versions")
async def get_content_versions(content_id: int):
    """Get version history for a piece of content"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute('SELECT title FROM content WHERE id = ?', (content_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Content not found")

        c.execute('''SELECT version, title, content, change_summary, created_at
                     FROM content_versions WHERE content_id = ? ORDER BY version DESC''', (content_id,))
        versions = [{
            'version': r[0], 'title': r[1], 'content': r[2],
            'change_summary': r[3], 'created_at': r[4]
        } for r in c.fetchall()]

        conn.close()

        return {
            'content_id': content_id, 'current_title': row[0],
            'versions': versions, 'total_versions': len(versions),
            'message': f'{len(versions)} versions found'
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get versions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/content/{content_id}/diff/{version1}/{version2}")
async def get_version_diff(content_id: int, version1: int, version2: int):
    """Get diff between two versions"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute('SELECT version, title, content FROM content_versions WHERE content_id = ? AND version IN (?, ?)',
                  (content_id, version1, version2))
        rows = {r[0]: {'title': r[1], 'content': r[2]} for r in c.fetchall()}
        conn.close()

        if version1 not in rows or version2 not in rows:
            raise HTTPException(status_code=404, detail="Version not found")

        v1, v2 = rows[version1], rows[version2]
        words1 = v1['content'].split()
        words2 = v2['content'].split()

        added = [w for w in words2 if w not in words1]
        removed = [w for w in words1 if w not in words2]

        return {
            'content_id': content_id,
            'version1': {'version': version1, **v1},
            'version2': {'version': version2, **v2},
            'diff': {
                'words_added': len(added), 'words_removed': len(removed),
                'added_sample': added[:20], 'removed_sample': removed[:20],
                'title_changed': v1['title'] != v2['title']
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Diff error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({
                "type": "pong",
                "message": f"Received: {data}",
                "timestamp": datetime.utcnow().isoformat()
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_ollama:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
