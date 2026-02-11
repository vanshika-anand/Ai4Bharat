# MemoryThread: Technical Design Document

## Project Overview

**MemoryThread** is an AI-powered content assistant that maintains persistent memory of everything a creator has written, enabling consistency checking, intelligent reference suggestions, and platform-specific content adaptation.

**Hackathon Track**: Student Track  
**Target Users**: Student bloggers, content creators, and digital writers  
**Core Innovation**: Integration of semantic memory, consistency checking, and multi-platform adaptation in a unified system

---

## System Architecture

### MemoryThread — System Diagram

**Overall Layout (Left → Right)**

```
┌──────────────────────────┐      ┌──────────────────────────┐      ┌──────────────────────────┐
│   Content Memory Layer   │ ---> │  Intelligence Layer      │ ---> │   Output & Adaptation    │
└──────────────────────────┘      └──────────────────────────┘      └──────────────────────────┘
```

---

### 1. Content Memory Layer

```
╔════════════════════════════════════════╗
║     Persistent Content Memory          ║
╠════════════════════════════════════════╣
║                                        ║
║     ┌──────────────────────┐           ║
║     │   User Past Content  │           ║
║     └──────────────────────┘           ║
║                │                       ║
║                ▼                       ║
║     ┌──────────────────────┐           ║
║     │  Embedding Generator │           ║
║     └──────────────────────┘           ║
║                │                       ║
║                ▼                       ║
║     ┌──────────────────────┐           ║
║     │  Semantic Memory DB  │  ◀───┐    ║
║     │      (Cylinder)      │      │    ║
║     └──────────────────────┘      │    ║
║                                   │    ║
╚═══════════════════════════════════╪════╝
                                    │
                                    │ Feedback Loop
```

**Purpose**: Persistent storage and semantic indexing of all creator content

**Key Components**:
- User Past Content: Blog posts, articles, threads
- Embedding Generator: Converts text to semantic vectors
- Semantic Memory DB: Searchable knowledge base

**Note**: This is conceptual memory architecture, not infrastructure details

---

### 2. Intelligence Layer (Core Innovation)

```
╔═══════════════════════════════════════════════╗
║     Content Intelligence Engine               ║
╠═══════════════════════════════════════════════╣
║                                               ║
║     ┌────────────────────────────┐            ║
║     │     Draft Content          │            ║
║     └────────────────────────────┘            ║
║                  │                            ║
║                  ▼                            ║
║     ┌────────────────────────────┐            ║
║     │ Consistency & Recall Model │            ║
║     └────────────────────────────┘            ║
║            ▲             │                    ║
║            │             ▼                    ║
║   ┌────────────────┐  ┌─────────────────────┐ ║
║   │ Memory Context │  │ Intelligence Signals│ ║
║   │ (Past Content) │  │ • Repetition        │ ║
║   └────────────────┘  │ • Contradiction     │ ║ 
║                       │ • References        │ ║
║                       └─────────────────────┘ ║
║                                               ║
╚═══════════════════════════════════════════════╝
```

**Purpose**: Intelligent analysis of new content against entire content history

**Key Innovation**:
- New content is checked against memory
- Intelligence flows bidirectionally
- Not just generation — reasoning over history
- Real-time consistency validation

**Signals Generated**:
- **Repetition**: Similarity scores with past work
- **Contradiction**: Conflicting positions detected
- **References**: Relevant past content to link

---

### 3. Output & Adaptation Layer

```
╔══════════════════════════════════════════╗
║     Platform-Aware Generation            ║
╠══════════════════════════════════════════╣
║                                          ║
║     ┌────────────────────────────┐       ║
║     │ Platform Adaptation Model  │       ║
║     └────────────────────────────┘       ║
║                  │                       ║
║        ┌─────────┼─────────┐             ║
║        ▼         ▼         ▼             ║
║   ┌──────────┐ ┌──────────┐ ┌──────────┐ ║
║   │ LinkedIn │ │ Twitter  │ │ Instagram│ ║
║   └──────────┘ └──────────┘ └──────────┘ ║
║                                          ║
╚══════════════════════════════════════════╝
```

**Purpose**: Intelligent restructuring for platform-specific requirements

**Key Features**:
- Single source content
- Multi-platform divergence
- Context-aware adaptation
- Maintains creator voice

**Output Channels**:
- LinkedIn: Professional frameworks
- Twitter: Threaded narratives
- Instagram: Visual-first captions

---

### Continuous Learning Loop

```
                    ┌─────────────────────────────────────┐
                    │                                     │
                    │  All generated content is stored    │
                    │  back into memory, enabling         │
                    │  continuous learning and            │
                    │  long-term consistency.             │
                    │                                     │
                    └─────────────────────────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────────┐
                    │                                     │
                    │    Output → Memory DB (Feedback)    │
                    │                                     │
                    └─────────────────────────────────────┘
```

**System Evolution**:
- Every adaptation enriches memory
- Consistency improves over time
- Creator voice becomes more defined
- Long-term value compounds

---

### Implementation Philosophy

**Design Principles**:
- **Simplicity First**: Use proven, stable technologies
- **Rapid Iteration**: Fast feedback loops during development
- **Student-Accessible**: Technologies with strong learning resources
- **Production-Ready**: Can scale from demo to real product

---

### System Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     User Experience Layer                   │
│                                                             │
│  Interactive web interface for content management,          │
│  search, consistency checking, and platform adaptation      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Communication Protocol
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Logic Layer                  │
│                                                             │
│  Business rules, content processing, intelligence           │
│  orchestration, and user workflow management                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
          ┌──────────────────┐  ┌──────────────────┐
          │  Persistence     │  │  AI Services     │
          │  Layer           │  │  Layer           │
          │                  │  │                  │
          │  Structured data │  │  Language models │
          │  and semantic    │  │  and semantic    │
          │  vectors         │  │  understanding   │
          └──────────────────┘  └──────────────────┘
```

**Layer Responsibilities**:

**User Experience Layer**
- Content upload and organization
- Search and discovery interface
- Consistency alerts and warnings
- Platform adaptation previews
- Dashboard and analytics

**Application Logic Layer**
- User authentication and authorization
- Content ingestion pipeline
- Semantic search orchestration
- Similarity calculation engine
- Platform-specific adaptation rules

**Persistence Layer**
- User accounts and preferences
- Content library storage
- Semantic vector indexing
- Query optimization

**AI Services Layer**
- Text-to-vector transformation
- Content generation and restructuring
- Natural language understanding
- Context-aware adaptation

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    subscription_tier VARCHAR(50) DEFAULT 'free'
);
```

### Content Table
```sql
CREATE TABLE content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(500) NOT NULL,
    body TEXT NOT NULL,
    platform VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    word_count INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Embeddings Table
```sql
CREATE TABLE embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL,
    embedding_vector TEXT NOT NULL,  -- JSON array of floats
    model_version VARCHAR(50) DEFAULT 'text-embedding-3-small',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (content_id) REFERENCES content(id)
);
```

---

## Core Components

### 1. Content Upload & Memory Building

**Purpose**: Ingest past content and create semantic embeddings

**Flow**:
```
User uploads content → Backend receives → Generate embedding via OpenAI API
→ Store content + embedding in DB → Return success
```

**API Endpoint**:
```python
POST /api/content/upload
Request Body:
{
    "title": "How to Study Effectively",
    "body": "Full content text...",
    "platform": "medium"  # optional
}

Response:
{
    "success": true,
    "content_id": 123,
    "message": "Content uploaded and indexed"
}
```

**Implementation Details**:
- Use OpenAI's `text-embedding-3-small` model (cheaper, faster)
- Embedding dimension: 1536
- Store embeddings as JSON string for SQLite compatibility
- Async processing for large uploads

---

### 2. Semantic Search Engine

**Purpose**: Find relevant past content based on meaning, not just keywords

**Algorithm**:
```python
def semantic_search(query: str, user_id: int, top_k: int = 5):
    # 1. Generate query embedding
    query_embedding = openai.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    
    # 2. Retrieve all user's content embeddings
    user_embeddings = db.get_embeddings(user_id)
    
    # 3. Calculate cosine similarity
    similarities = []
    for content in user_embeddings:
        similarity = cosine_similarity(
            query_embedding,
            content.embedding
        )
        similarities.append((content.id, similarity))
    
    # 4. Sort and return top K
    top_results = sorted(similarities, key=lambda x: x[1], reverse=True)[:top_k]
    
    return [db.get_content(id) for id, score in top_results]
```

**API Endpoint**:
```python
GET /api/search?q=productivity&limit=5

Response:
{
    "results": [
        {
            "content_id": 45,
            "title": "Time Management for Students",
            "similarity_score": 0.89,
            "snippet": "First 200 chars...",
            "created_at": "2024-01-15"
        },
        ...
    ]
}
```

---

### 3. Repetition Detection

**Purpose**: Alert creators when new content is too similar to existing work

**Threshold Logic**:
- **High similarity** (>80%): Strong warning - likely repetition
- **Medium similarity** (60-80%): Caution - related content
- **Low similarity** (<60%): No alert

**API Endpoint**:
```python
POST /api/check/repetition
Request Body:
{
    "title": "Study Tips for Finals",
    "body": "New draft content..."
}

Response:
{
    "has_similar_content": true,
    "matches": [
        {
            "content_id": 23,
            "title": "How to Study for Exams",
            "similarity_score": 0.82,
            "recommendation": "high_overlap",
            "snippet": "Relevant section..."
        }
    ]
}
```

---

### 4. Position Consistency Checker

**Purpose**: Detect potential contradictions with past statements

**Approach**:
```python
def check_consistency(new_content: str, user_id: int):
    # 1. Extract key claims from new content using GPT
    claims = extract_claims(new_content)
    
    # 2. For each claim, search for related past content
    potential_conflicts = []
    for claim in claims:
        related = semantic_search(claim, user_id, top_k=3)
        
        # 3. Use GPT to analyze for contradictions
        for past_content in related:
            analysis = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "system",
                    "content": "Analyze if these statements contradict each other."
                }, {
                    "role": "user",
                    "content": f"New: {claim}\nPast: {past_content.body}"
                }]
            )
            
            if "contradiction" in analysis.lower():
                potential_conflicts.append({
                    "claim": claim,
                    "conflicts_with": past_content,
                    "explanation": analysis
                })
    
    return potential_conflicts
```

**Note**: This is a V2 feature - deferred from MVP due to complexity

---

### 5. Reference Suggestion Engine

**Purpose**: Suggest relevant past content while writing

**Real-time Flow**:
```
User types in editor → Debounced API call every 2 seconds
→ Search for related content → Display suggestions in sidebar
```

**API Endpoint**:
```python
POST /api/suggest/references
Request Body:
{
    "current_draft": "I'm writing about burnout prevention...",
    "context_window": 500  # chars to analyze
}

Response:
{
    "suggestions": [
        {
            "content_id": 67,
            "title": "Managing Stress in College",
            "relevance_score": 0.76,
            "suggested_action": "Consider referencing this earlier work"
        }
    ]
}
```

---

### 6. Platform-Specific Adaptation

**Purpose**: Restructure content for different platform requirements

**Platform Profiles**:

#### LinkedIn
- **Tone**: Professional, authoritative
- **Structure**: Hook → Framework → Actionable insights → Discussion prompt
- **Length**: 1200-1500 characters
- **Format**: Paragraphs with line breaks, occasional bullet points

#### Twitter/X
- **Tone**: Engaging, conversational
- **Structure**: Hook tweet → Numbered thread → CTA
- **Length**: 280 chars per tweet, 8-12 tweet thread
- **Format**: Short sentences, questions, emojis sparingly

#### Instagram
- **Tone**: Casual, aspirational
- **Structure**: Visual hook → Story → Inspiration
- **Length**: 2000-2200 characters
- **Format**: Emojis, hashtags, first-person narrative

**Implementation**:
```python
def adapt_content(content: str, platform: str):
    prompts = {
        "linkedin": """
            Restructure this content for LinkedIn:
            - Start with a credibility hook
            - Present as a framework or system
            - Use professional tone
            - End with a discussion question
            - Keep to 1200-1500 characters
        """,
        "twitter": """
            Convert this to a Twitter thread:
            - Start with an engaging hook tweet
            - Break into 8-12 numbered tweets
            - Each tweet max 280 characters
            - End with a question or CTA
            - Use conversational tone
        """,
        "instagram": """
            Adapt this for Instagram caption:
            - Casual, friendly tone
            - Use relevant emojis
            - First-person narrative
            - Include 5-8 relevant hashtags
            - 2000-2200 characters
        """
    }
    
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompts[platform]},
            {"role": "user", "content": content}
        ],
        temperature=0.7
    )
    
    return response.choices[0].message.content
```

**API Endpoint**:
```python
POST /api/adapt
Request Body:
{
    "content": "Original content...",
    "platforms": ["linkedin", "twitter", "instagram"]
}

Response:
{
    "adaptations": {
        "linkedin": "Adapted version...",
        "twitter": "Thread version...",
        "instagram": "Caption version..."
    }
}
```

---

## Frontend Design

### Component Structure

```
src/
├── components/
│   ├── Dashboard/
│   │   ├── Dashboard.jsx
│   │   ├── ContentList.jsx
│   │   └── StatsCard.jsx
│   ├── Upload/
│   │   ├── UploadForm.jsx
│   │   └── UploadProgress.jsx
│   ├── Search/
│   │   ├── SearchBar.jsx
│   │   ├── SearchResults.jsx
│   │   └── ContentCard.jsx
│   ├── Check/
│   │   ├── RepetitionChecker.jsx
│   │   ├── SimilarityAlert.jsx
│   │   └── ComparisonView.jsx
│   ├── Adapt/
│   │   ├── PlatformSelector.jsx
│   │   ├── AdaptationPreview.jsx
│   │   └── CopyButton.jsx
│   └── Common/
│       ├── Navbar.jsx
│       ├── LoadingSpinner.jsx
│       └── ErrorBoundary.jsx
├── pages/
│   ├── Home.jsx
│   ├── Upload.jsx
│   ├── Search.jsx
│   ├── Check.jsx
│   └── Adapt.jsx
├── services/
│   ├── api.js
│   └── auth.js
└── utils/
    ├── formatters.js
    └── validators.js
```

### Key UI Screens

#### 1. Dashboard
```
┌─────────────────────────────────────────────────────────┐
│  MemoryThread                    [Search] [@User ▼]     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Your Content Memory                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                 │
│  │   25     │ │   150    │ │   12     │                 │
│  │ Pieces   │ │ Searches │ │ Checks   │                 │
│  └──────────┘ └──────────┘ └──────────┘                 │
│                                                         │
│   Recent Content                                        │
│  ┌────────────────────────────────────────────────┐     │
│  │ How to Study Effectively        Jan 15, 2024   │     │
│  │ Time Management Tips            Jan 10, 2024   │     │
│  │ Productivity Hacks              Jan 5, 2024    │     │
│  └────────────────────────────────────────────────┘     │
│                                                         │
│  [+ Upload Content] [ Search] [ Check Draft]            │
└─────────────────────────────────────────────────────────┘
```

#### 2. Repetition Checker
```
┌─────────────────────────────────────────────────────────┐
│  Check for Repetition                                   │
├─────────────────────────────────────────────────────────┤
│  Paste your new draft:                                  │
│  ┌─────────────────────────────────────────────────┐    │
│  │ [Text area for draft content]                   │    │
│  │                                                 │    │
│  └─────────────────────────────────────────────────┘    │
│  [Check for Similar Content]                            │
│                                                         │
│   High Similarity Detected (82%)                        │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Your Draft          │  Past Content             │    │
│  ├─────────────────────┼───────────────────────────┤    │
│  │ Study tips for...  │  How to Study Effectively  │    │
│  │ [Preview...]       │  [Preview...]              │    │
│  │                    │  Written: Jan 15, 2024     │    │
│  └─────────────────────┴───────────────────────────┘    │
│                                                         │
│   Recommendation: Consider referencing your earlier     │
│     post or taking a different angle                    │
└─────────────────────────────────────────────────────────┘
```

#### 3. Platform Adapter
```
┌─────────────────────────────────────────────────────────┐
│  Adapt for Platforms                                    │
├─────────────────────────────────────────────────────────┤
│  Original Content:                                      │
│  ┌─────────────────────────────────────────────────┐    │
│  │ [Your content here...]                          │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  Select Platforms:                                      │
│  [✓] LinkedIn  [✓] Twitter  [✓] Instagram               │
│  [Generate Adaptations]                                 │
│                                                         │
│  ┌─────────────┬─────────────┬─────────────┐            │
│  │  LinkedIn   │   Twitter   │  Instagram  │            │
│  ├─────────────┼─────────────┼─────────────┤            │
│  │ [Adapted    │ [Thread     │ [Caption    │            │
│  │  version]   │  version]   │  version]   │            │
│  │             │             │             │            │
│  │ [Copy] [📋] │ [Copy] [📋] │ [Copy] [📋] │             │
│  └─────────────┴─────────────┴─────────────┘            │
└─────────────────────────────────────────────────────────┘
```

---

## Security & Privacy

### Authentication
- JWT-based authentication
- Password hashing with bcrypt (cost factor: 12)
- Secure session management
- HTTPS only in production

### Data Privacy
- User content is private by default
- No sharing between users
- No training on user data
- Clear data deletion policy

### API Security
- Rate limiting: 100 requests/minute per user
- Input validation and sanitization
- SQL injection prevention (parameterized queries)
- CORS configuration for frontend domain only

---

## Performance Optimization

### Caching Strategy
```python
# Cache embeddings to reduce API calls
@cache.memoize(timeout=3600)
def get_embedding(text: str):
    return openai.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

# Cache search results
@cache.memoize(timeout=300)
def search_content(query: str, user_id: int):
    # Search logic
    pass
```

### Database Optimization
- Index on `user_id` for fast user-specific queries
- Index on `created_at` for chronological sorting
- Pagination for large result sets (20 items per page)

### API Cost Management
- Batch embedding generation when possible
- Use `gpt-3.5-turbo` instead of `gpt-4` (10x cheaper)
- Implement request queuing for non-urgent operations
- Monitor usage with alerts at $50, $100 thresholds

**Estimated Costs**:
- Embeddings: $0.0001 per 1K tokens (~$0.01 per 100 pieces)
- GPT-3.5-turbo: $0.002 per 1K tokens (~$0.10 per 50 adaptations)
- **Total for demo**: <$5

---

## Testing Strategy

### Unit Tests
```python
# test_similarity.py
def test_cosine_similarity():
    vec1 = [1, 0, 0]
    vec2 = [1, 0, 0]
    assert cosine_similarity(vec1, vec2) == 1.0

def test_repetition_detection():
    content1 = "How to study effectively"
    content2 = "Effective study techniques"
    score = check_similarity(content1, content2)
    assert 0.7 < score < 0.9
```

### Integration Tests
- Test full upload → embedding → storage flow
- Test search with various queries
- Test adaptation for all platforms

---

## Deployment Plan

### Development Environment
```bash
# Local setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."
flask run

# Frontend
cd frontend
npm install
npm run dev
```

### Production Deployment

**Backend**: Render.com (Free tier)
- Python 3.11
- Auto-deploy from GitHub
- Environment variables for secrets

**Frontend**: Vercel (Free tier)
- Auto-deploy from GitHub
- Custom domain support

**Database**: 
- SQLite for demo
- PostgreSQL on Render for production

**Monitoring**:
- Sentry for error tracking
- Simple analytics dashboard

---

## MVP Feature Checklist

### Must-Have (Hackathon Demo)
- [x] User authentication (simple)
- [x] Content upload with embedding generation
- [x] Semantic search
- [x] Repetition detection
- [x] Platform adaptation (LinkedIn, Twitter, Instagram)
- [x] Basic dashboard
- [x] Responsive design
---

## Success Metrics

### Technical Metrics
- Search response time: <500ms
- Embedding generation: <2s per piece
- Platform adaptation: <5s per platform
- Uptime: >99%

### User Metrics
- Time to first upload: <2 minutes
- Search accuracy: >80% relevant results
- Repetition detection accuracy: >85%
- User satisfaction: >4/5 stars


---

## Competitive Advantages

1. **Integrated Solution**: Only tool combining memory + consistency + adaptation
2. **Semantic Understanding**: Goes beyond keyword matching
3. **Platform Intelligence**: Understands psychological differences between platforms
4. **Student-Focused**: Affordable pricing and relevant use cases
5. **Privacy-First**: No data sharing or training on user content

---

## Technology Stack Summary

| Layer | Technology | Justification |
|-------|-----------|---------------|
| Frontend | React + Vite | Fast development, modern tooling |
| Styling | Tailwind CSS | Rapid UI development, consistent design |
| Backend | Python + Flask | Easy AI integration, quick prototyping |
| Database | SQLite → PostgreSQL | Simple start, easy migration |
| AI | OpenAI API | Best-in-class embeddings and generation |
| Hosting | Vercel + Render | Free tiers, easy deployment |
| Auth | JWT | Stateless, scalable |


---

**Built for the Student Track Hackathon**

*MemoryThread: The AI writing partner that actually remembers.*
