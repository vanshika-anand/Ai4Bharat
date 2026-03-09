"""
Knowledge Graph for Content Relationships
Uses Llama 3.1 to extract entities, topics, and relationships
"""

import json
import httpx
from typing import List, Dict, Any, Set, Tuple
import sqlite3
from pathlib import Path
import logging
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL = "llama3.1:8b"
DB_PATH = Path("memorythread.db")

class KnowledgeGraph:
    """Build and query a knowledge graph of content"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=120.0)
        self.init_graph_db()
    
    def init_graph_db(self):
        """Initialize knowledge graph tables"""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Entities table (people, concepts, topics, etc.)
        c.execute('''
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Content-Entity relationships
        c.execute('''
            CREATE TABLE IF NOT EXISTS content_entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id INTEGER NOT NULL,
                entity_id INTEGER NOT NULL,
                relevance REAL DEFAULT 1.0,
                FOREIGN KEY (content_id) REFERENCES content(id) ON DELETE CASCADE,
                FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
                UNIQUE(content_id, entity_id)
            )
        ''')
        
        # Topics/themes table
        c.execute('''
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                parent_topic_id INTEGER,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_topic_id) REFERENCES topics(id)
            )
        ''')
        
        # Content-Topic relationships
        c.execute('''
            CREATE TABLE IF NOT EXISTS content_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id INTEGER NOT NULL,
                topic_id INTEGER NOT NULL,
                strength REAL DEFAULT 1.0,
                FOREIGN KEY (content_id) REFERENCES content(id) ON DELETE CASCADE,
                FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE,
                UNIQUE(content_id, topic_id)
            )
        ''')
        
        # Relationships between entities
        c.execute('''
            CREATE TABLE IF NOT EXISTS entity_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity1_id INTEGER NOT NULL,
                entity2_id INTEGER NOT NULL,
                relationship_type TEXT NOT NULL,
                strength REAL DEFAULT 1.0,
                FOREIGN KEY (entity1_id) REFERENCES entities(id) ON DELETE CASCADE,
                FOREIGN KEY (entity2_id) REFERENCES entities(id) ON DELETE CASCADE
            )
        ''')
        
        # Create indexes
        c.execute('CREATE INDEX IF NOT EXISTS idx_content_entities ON content_entities(content_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_content_topics ON content_topics(content_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_entity_name ON entities(name)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_topic_name ON topics(name)')
        
        conn.commit()
        conn.close()
        logger.info("Knowledge graph database initialized")
    
    async def extract_knowledge(self, content_id: int, title: str, content: str) -> Dict[str, Any]:
        """Extract entities, topics, and relationships from content using Llama 3.1"""
        
        prompt = f"""Analyze the following content and extract structured knowledge.

TITLE: {title}

CONTENT:
{content[:2000]}

Extract the following in JSON format:

1. ENTITIES: Key people, organizations, concepts, tools, or technologies mentioned
2. TOPICS: Main themes and subjects (e.g., "productivity", "time management", "AI")
3. KEY_POINTS: 3-5 main ideas or arguments
4. RELATIONSHIPS: How entities relate to each other

Return ONLY valid JSON in this exact format:
{{
  "entities": [
    {{"name": "entity name", "type": "person|concept|tool|organization", "description": "brief description"}}
  ],
  "topics": [
    {{"name": "topic name", "parent": "parent topic or null", "description": "what this topic covers"}}
  ],
  "key_points": ["point 1", "point 2", "point 3"],
  "relationships": [
    {{"entity1": "name1", "entity2": "name2", "type": "relates_to|uses|implements|discusses"}}
  ]
}}

JSON:"""
        
        system = """You are a knowledge extraction expert. Extract structured information from text and return ONLY valid JSON. 
Be precise and focus on the most important entities and topics. Avoid generic terms."""
        
        try:
            response = await self.client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": LLM_MODEL,
                    "prompt": prompt,
                    "system": system,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Lower for more consistent extraction
                        "num_predict": 1000,
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json().get("response", "")
                
                # Extract JSON from response
                try:
                    # Find JSON in response
                    start = result.find('{')
                    end = result.rfind('}') + 1
                    if start >= 0 and end > start:
                        json_str = result[start:end]
                        knowledge = json.loads(json_str)
                        
                        # Store in database
                        await self.store_knowledge(content_id, knowledge)
                        
                        logger.info(f"Extracted knowledge for content {content_id}: {len(knowledge.get('entities', []))} entities, {len(knowledge.get('topics', []))} topics")
                        return knowledge
                    else:
                        logger.warning(f"No JSON found in response for content {content_id}")
                        return {}
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    logger.error(f"Response: {result[:500]}")
                    return {}
            else:
                logger.error(f"Ollama error: {response.status_code}")
                return {}
        
        except Exception as e:
            logger.error(f"Knowledge extraction error: {type(e).__name__}: {e}")
            return {}
    
    async def store_knowledge(self, content_id: int, knowledge: Dict[str, Any]):
        """Store extracted knowledge in the graph database"""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        try:
            # Store entities
            entity_ids = {}
            for entity in knowledge.get('entities', []):
                name = entity.get('name', '').strip()
                if not name:
                    continue
                
                entity_type = entity.get('type', 'concept')
                description = entity.get('description', '')
                
                # Insert or get entity
                c.execute(
                    'INSERT OR IGNORE INTO entities (name, type, description) VALUES (?, ?, ?)',
                    (name, entity_type, description)
                )
                c.execute('SELECT id FROM entities WHERE name = ?', (name,))
                entity_id = c.fetchone()[0]
                entity_ids[name] = entity_id
                
                # Link to content
                c.execute(
                    'INSERT OR IGNORE INTO content_entities (content_id, entity_id, relevance) VALUES (?, ?, ?)',
                    (content_id, entity_id, 1.0)
                )
            
            # Store topics
            topic_ids = {}
            for topic in knowledge.get('topics', []):
                name = topic.get('name', '').strip()
                if not name:
                    continue
                
                parent = topic.get('parent')
                description = topic.get('description', '')
                
                # Insert or get topic
                c.execute(
                    'INSERT OR IGNORE INTO topics (name, description) VALUES (?, ?)',
                    (name, description)
                )
                c.execute('SELECT id FROM topics WHERE name = ?', (name,))
                topic_id = c.fetchone()[0]
                topic_ids[name] = topic_id
                
                # Link to content
                c.execute(
                    'INSERT OR IGNORE INTO content_topics (content_id, topic_id, strength) VALUES (?, ?, ?)',
                    (content_id, topic_id, 1.0)
                )
            
            # Store relationships
            for rel in knowledge.get('relationships', []):
                entity1_name = rel.get('entity1', '').strip()
                entity2_name = rel.get('entity2', '').strip()
                rel_type = rel.get('type', 'relates_to')
                
                if entity1_name in entity_ids and entity2_name in entity_ids:
                    c.execute(
                        'INSERT OR IGNORE INTO entity_relationships (entity1_id, entity2_id, relationship_type, strength) VALUES (?, ?, ?, ?)',
                        (entity_ids[entity1_name], entity_ids[entity2_name], rel_type, 1.0)
                    )
            
            conn.commit()
            logger.info(f"Stored knowledge for content {content_id}")
        
        except Exception as e:
            logger.error(f"Error storing knowledge: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_content_graph(self, content_id: int) -> Dict[str, Any]:
        """Get the knowledge graph for a specific content"""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get entities
        c.execute('''
            SELECT e.id, e.name, e.type, e.description, ce.relevance
            FROM entities e
            JOIN content_entities ce ON e.id = ce.entity_id
            WHERE ce.content_id = ?
        ''', (content_id,))
        entities = [
            {
                'id': row[0],
                'name': row[1],
                'type': row[2],
                'description': row[3],
                'relevance': row[4]
            }
            for row in c.fetchall()
        ]
        
        # Get topics
        c.execute('''
            SELECT t.id, t.name, t.description, ct.strength
            FROM topics t
            JOIN content_topics ct ON t.id = ct.topic_id
            WHERE ct.content_id = ?
        ''', (content_id,))
        topics = [
            {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'strength': row[3]
            }
            for row in c.fetchall()
        ]
        
        conn.close()
        
        return {
            'entities': entities,
            'topics': topics
        }
    
    def find_related_content(self, content_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Find related content using knowledge graph"""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Find content with shared entities
        c.execute('''
            SELECT 
                c.id,
                c.title,
                COUNT(DISTINCT ce2.entity_id) as shared_entities,
                COUNT(DISTINCT ct2.topic_id) as shared_topics
            FROM content c
            JOIN content_entities ce2 ON c.id = ce2.content_id
            LEFT JOIN content_topics ct2 ON c.id = ct2.content_id
            WHERE ce2.entity_id IN (
                SELECT entity_id FROM content_entities WHERE content_id = ?
            )
            AND c.id != ?
            GROUP BY c.id, c.title
            ORDER BY shared_entities DESC, shared_topics DESC
            LIMIT ?
        ''', (content_id, content_id, limit))
        
        results = [
            {
                'id': row[0],
                'title': row[1],
                'shared_entities': row[2],
                'shared_topics': row[3],
                'relevance_score': (row[2] * 2 + row[3]) / 3.0  # Weighted score
            }
            for row in c.fetchall()
        ]
        
        conn.close()
        return results
    
    async def check_repetition_with_graph(self, draft_content: str) -> Dict[str, Any]:
        """Check for repetition using knowledge graph analysis"""
        
        # Extract knowledge from draft
        draft_knowledge = await self.extract_knowledge(0, "Draft", draft_content)
        
        if not draft_knowledge:
            return {
                'is_repetition': False,
                'similar_content': [],
                'message': 'Could not analyze draft content',
                'graph_analysis': {}
            }
        
        # Get all content with their knowledge graphs
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, title, content FROM content')
        all_content = c.fetchall()
        conn.close()
        
        similar_items = []
        
        for content_id, title, content in all_content:
            graph = self.get_content_graph(content_id)
            
            # Calculate overlap
            draft_entities = set(e['name'].lower() for e in draft_knowledge.get('entities', []))
            draft_topics = set(t['name'].lower() for t in draft_knowledge.get('topics', []))
            
            content_entities = set(e['name'].lower() for e in graph['entities'])
            content_topics = set(t['name'].lower() for t in graph['topics'])
            
            # Calculate Jaccard similarity
            entity_overlap = len(draft_entities & content_entities) / len(draft_entities | content_entities) if (draft_entities | content_entities) else 0
            topic_overlap = len(draft_topics & content_topics) / len(draft_topics | content_topics) if (draft_topics | content_topics) else 0
            
            # Combined score (weighted)
            similarity_score = (entity_overlap * 0.6 + topic_overlap * 0.4) * 100
            
            if similarity_score > 40:  # 40% threshold
                similar_items.append({
                    'id': content_id,
                    'title': title,
                    'content': content,
                    'similarity': similarity_score,
                    'shared_entities': list(draft_entities & content_entities),
                    'shared_topics': list(draft_topics & content_topics),
                    'entity_overlap': entity_overlap * 100,
                    'topic_overlap': topic_overlap * 100
                })
        
        # Sort by similarity
        similar_items.sort(key=lambda x: x['similarity'], reverse=True)
        
        is_rep = len(similar_items) > 0
        max_sim = similar_items[0]['similarity'] if similar_items else 0
        
        if is_rep:
            if max_sim > 70:
                message = f"🚨 High overlap detected! Found {len(similar_items)} piece(s) covering similar topics and entities."
            elif max_sim > 50:
                message = f"⚠️ Moderate overlap. Found {len(similar_items)} piece(s) with related themes."
            else:
                message = f"💡 Some thematic overlap with {len(similar_items)} piece(s). Could be an opportunity to reference past work."
        else:
            message = "✅ No significant overlap - this explores new territory!"
        
        return {
            'is_repetition': is_rep,
            'similar_content': similar_items[:5],
            'message': message,
            'max_similarity': max_sim,
            'graph_analysis': {
                'draft_entities': list(draft_entities),
                'draft_topics': list(draft_topics),
                'total_entities_found': len(draft_entities),
                'total_topics_found': len(draft_topics)
            }
        }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
