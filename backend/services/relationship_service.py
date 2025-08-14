from typing import List, Dict, Tuple, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import spacy
from datetime import datetime, timedelta
import networkx as nx
from networkx.algorithms import community
import asyncio
from models import Memory, MemoryRelationship, MemoryCluster
import logging

logger = logging.getLogger(__name__)

class RelationshipService:
    def __init__(self):
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.nlp = spacy.load('en_core_web_sm')
        
    async def find_relationships(self, memories: List[Memory], user_id: str) -> List[Dict]:
        """Find relationships between memories based on multiple factors"""
        if not memories:
            return []
            
        relationships = []
        
        # Generate embeddings for all memories
        texts = [m.text for m in memories]
        embeddings = self.encoder.encode(texts)
        
        # Calculate similarity matrix
        similarity_matrix = cosine_similarity(embeddings)
        
        # Store embeddings in memories for future use
        for i, memory in enumerate(memories):
            memory.embeddings = embeddings[i].tolist()
        
        # Find relationships between each pair of memories
        for i in range(len(memories)):
            for j in range(i + 1, len(memories)):
                relationship = await self._analyze_relationship(
                    memories[i], 
                    memories[j], 
                    similarity_matrix[i][j],
                    user_id
                )
                if relationship['strength'] > 0.3:  # Threshold
                    relationships.append(relationship)
        
        # Save relationships to database
        for rel in relationships:
            await self._save_relationship(rel)
        
        return relationships
    
    async def _analyze_relationship(self, mem1: Memory, mem2: Memory, similarity: float, user_id: str) -> Dict:
        """Analyze relationship between two memories"""
        relationship = {
            'source_memory_id': str(mem1.id),
            'target_memory_id': str(mem2.id),
            'user_id': user_id,
            'strength': 0.0,
            'relationship_type': 'related',
            'reasons': []
        }
        
        # 1. Semantic similarity
        if similarity > 0.7:
            relationship['strength'] += similarity * 0.4
            relationship['reasons'].append('semantic_similarity')
            relationship['relationship_type'] = 'semantic'
        
        # 2. Temporal proximity
        time_diff = abs((mem1.created_at - mem2.created_at).days)
        
        if time_diff < 1:  # Same day
            relationship['strength'] += 0.4
            relationship['reasons'].append('same_day')
            if relationship['relationship_type'] == 'related':
                relationship['relationship_type'] = 'temporal'
        elif time_diff < 7:  # Within a week
            relationship['strength'] += 0.2
            relationship['reasons'].append('temporal_proximity')
            if relationship['relationship_type'] == 'related':
                relationship['relationship_type'] = 'temporal'
        
        # 3. Entity overlap
        entities1 = self._extract_entities(mem1.text)
        entities2 = self._extract_entities(mem2.text)
        overlap = len(entities1.intersection(entities2))
        
        if overlap > 0:
            relationship['strength'] += min(overlap * 0.15, 0.3)
            relationship['relationship_type'] = 'entity_based'
            relationship['reasons'].append(f'shared_entities:{overlap}')
        
        # 4. Mood correlation
        if mem1.mood == mem2.mood:
            relationship['strength'] += 0.1
            relationship['reasons'].append('same_mood')
        
        # 5. Tag overlap
        tag_overlap = set(mem1.tags).intersection(set(mem2.tags))
        if tag_overlap:
            relationship['strength'] += len(tag_overlap) * 0.1
            relationship['reasons'].append(f'shared_tags:{len(tag_overlap)}')
        
        # Cap strength at 1.0
        relationship['strength'] = min(relationship['strength'], 1.0)
        
        return relationship
    
    def _extract_entities(self, text: str) -> set:
        """Extract named entities from text"""
        try:
            doc = self.nlp(text)
            entities = {ent.text.lower() for ent in doc.ents}
            # Also extract important nouns
            entities.update({
                token.text.lower() 
                for token in doc 
                if token.pos_ in ['PROPN', 'NOUN'] and len(token.text) > 3
            })
            return entities
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return set()
    
    async def _save_relationship(self, relationship: Dict):
        """Save relationship to database"""
        try:
            rel = MemoryRelationship(**relationship)
            await rel.save()
        except Exception as e:
            logger.error(f"Error saving relationship: {e}")
    
    async def detect_clusters(self, user_id: str) -> List[MemoryCluster]:
        """Detect memory clusters using community detection"""
        # Get all memories and relationships for user
        memories = await Memory.find(Memory.user_id == user_id).to_list()
        relationships = await MemoryRelationship.find(
            MemoryRelationship.user_id == user_id
        ).to_list()
        
        if len(memories) < 3:  # Need at least 3 memories for clustering
            return []
        
        # Build network graph
        G = nx.Graph()
        
        # Add nodes
        for mem in memories:
            G.add_node(str(mem.id), memory=mem)
        
        # Add edges
        for rel in relationships:
            if rel.strength > 0.5:  # Only strong relationships
                G.add_edge(
                    rel.source_memory_id, 
                    rel.target_memory_id, 
                    weight=rel.strength
                )
        
        # Detect communities
        try:
            communities = list(community.louvain_communities(G))
        except:
            # Fallback to simple connected components
            communities = list(nx.connected_components(G))
        
        # Create clusters
        clusters = []
        for i, community_nodes in enumerate(communities):
            if len(community_nodes) < 2:  # Skip single-node clusters
                continue
                
            cluster_memories = [
                G.nodes[node]['memory'] 
                for node in community_nodes 
                if node in G.nodes
            ]
            
            cluster = await self._create_cluster(
                cluster_memories, 
                user_id, 
                cluster_id=i
            )
            if cluster:
                clusters.append(cluster)
        
        return clusters
    
    async def _create_cluster(self, memories: List[Memory], user_id: str, cluster_id: int) -> Optional[MemoryCluster]:
        """Create a cluster from a group of memories"""
        if not memories:
            return None
        
        # Extract keywords from all memories
        all_text = " ".join([m.text for m in memories])
        doc = self.nlp(all_text)
        
        # Get most common entities and keywords
        keywords = []
        entity_counts = {}
        
        for ent in doc.ents:
            entity_counts[ent.text] = entity_counts.get(ent.text, 0) + 1
        
        # Sort by frequency and take top keywords
        sorted_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)
        keywords = [entity for entity, count in sorted_entities[:10]]
        
        # Detect theme based on mood distribution and keywords
        mood_counts = {}
        for mem in memories:
            mood_counts[mem.mood] = mood_counts.get(mem.mood, 0) + 1
        
        dominant_mood = max(mood_counts, key=mood_counts.get)
        theme = self._detect_theme(keywords, dominant_mood)
        
        # Generate cluster summary
        summary = f"A collection of {len(memories)} memories related to {theme.lower()}"
        if keywords:
            summary += f", featuring {', '.join(keywords[:3])}"
        
        cluster = MemoryCluster(
            user_id=user_id,
            cluster_name=f"{theme} Memories #{cluster_id + 1}",
            theme=theme,
            memory_ids=[str(m.id) for m in memories],
            keywords=keywords,
            summary=summary
        )
        
        await cluster.save()
        return cluster
    
    def _detect_theme(self, keywords: List[str], dominant_mood: str) -> str:
        """Detect theme based on keywords and mood"""
        # Simple theme detection based on keywords
        work_keywords = {'work', 'office', 'meeting', 'project', 'colleague', 'boss', 'job'}
        travel_keywords = {'travel', 'trip', 'vacation', 'flight', 'hotel', 'visit', 'tourist'}
        family_keywords = {'family', 'mom', 'dad', 'sister', 'brother', 'parent', 'child'}
        friends_keywords = {'friend', 'buddy', 'pal', 'hangout', 'party', 'fun'}
        health_keywords = {'health', 'exercise', 'gym', 'doctor', 'medical', 'fitness', 'wellness'}
        
        keyword_set = set(k.lower() for k in keywords)
        
        if keyword_set.intersection(work_keywords):
            return "Work"
        elif keyword_set.intersection(travel_keywords):
            return "Travel"
        elif keyword_set.intersection(family_keywords):
            return "Family"
        elif keyword_set.intersection(friends_keywords):
            return "Friends"
        elif keyword_set.intersection(health_keywords):
            return "Health"
        elif dominant_mood == "Happy":
            return "Joy"
        elif dominant_mood == "Sad":
            return "Reflection"
        else:
            return "Life"
    
    async def get_memory_path(self, source_id: str, target_id: str, user_id: str) -> Optional[List[str]]:
        """Find the shortest path between two memories through relationships"""
        relationships = await MemoryRelationship.find(
            MemoryRelationship.user_id == user_id
        ).to_list()
        
        # Build graph
        G = nx.Graph()
        for rel in relationships:
            G.add_edge(
                rel.source_memory_id,
                rel.target_memory_id,
                weight=1.0 / rel.strength  # Inverse weight for shortest path
            )
        
        try:
            path = nx.shortest_path(G, source_id, target_id, weight='weight')
            return path
        except nx.NetworkXNoPath:
            return None
