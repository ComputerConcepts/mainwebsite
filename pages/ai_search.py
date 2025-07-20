"""
AI-Powered Smart Search and Discovery Engine
Advanced search capabilities with natural language processing and intelligent discovery
"""

import os
import json
import re
import math
from typing import Dict, List, Tuple, Optional, Union
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import difflib


class SearchType(Enum):
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    FUZZY = "fuzzy"
    CONTEXTUAL = "contextual"
    VISUAL = "visual"
    TEMPORAL = "temporal"


class ResultType(Enum):
    FILE = "file"
    CONTENT = "content"
    METADATA = "metadata"
    RELATIONSHIP = "relationship"
    CONCEPT = "concept"
    USER = "user"


@dataclass
class SearchResult:
    id: str
    title: str
    content: str
    result_type: ResultType
    score: float
    metadata: Dict
    highlights: List[str]
    context: Dict
    file_path: str = None
    thumbnail: str = None


@dataclass
class SearchIntent:
    query: str
    intent_type: str
    entities: List[str]
    confidence: float
    suggested_refinements: List[str]
    filters: Dict


class SmartSearchEngine:
    """AI-powered smart search engine with natural language understanding"""
    
    def __init__(self):
        self.document_index = {}
        self.content_vectors = {}
        self.metadata_index = {}
        self.user_search_history = defaultdict(list)
        self.concept_graph = {}
        self.search_analytics = defaultdict(int)
        self.auto_suggestions = {}
        
        # Search configuration
        self.max_results = 50
        self.relevance_threshold = 0.3
        self.highlight_length = 200
        
    def index_document(self, doc_id: str, content: str, metadata: Dict):
        """Index a document for search"""
        # Basic text processing
        processed_content = self._preprocess_text(content)
        
        # Create document entry
        self.document_index[doc_id] = {
            'content': content,
            'processed_content': processed_content,
            'metadata': metadata,
            'indexed_at': datetime.now().isoformat(),
            'word_count': len(processed_content.split()),
            'keywords': self._extract_keywords(processed_content),
            'entities': self._extract_entities(processed_content),
            'concepts': self._extract_concepts(processed_content)
        }
        
        # Create content vector for semantic search
        self.content_vectors[doc_id] = self._create_content_vector(processed_content)
        
        # Update metadata index
        self._update_metadata_index(doc_id, metadata)
        
        # Update concept graph
        self._update_concept_graph(doc_id, self.document_index[doc_id]['concepts'])
    
    def search(self, query: str, user_id: str = None, search_type: SearchType = SearchType.SEMANTIC, 
              filters: Dict = None, limit: int = None) -> Dict:
        """Perform intelligent search with multiple strategies"""
        
        # Analyze search intent
        intent = self._analyze_search_intent(query, user_id)
        
        # Get search results based on type
        if search_type == SearchType.SEMANTIC:
            results = self._semantic_search(query, filters)
        elif search_type == SearchType.KEYWORD:
            results = self._keyword_search(query, filters)
        elif search_type == SearchType.FUZZY:
            results = self._fuzzy_search(query, filters)
        elif search_type == SearchType.CONTEXTUAL:
            results = self._contextual_search(query, user_id, filters)
        elif search_type == SearchType.TEMPORAL:
            results = self._temporal_search(query, filters)
        else:
            # Default to semantic search
            results = self._semantic_search(query, filters)
        
        # Apply result limit
        if limit:
            results = results[:limit]
        elif self.max_results:
            results = results[:self.max_results]
        
        # Record search for analytics and learning
        if user_id:
            self._record_search(user_id, query, search_type, len(results))
        
        # Generate search suggestions
        suggestions = self._generate_search_suggestions(query, intent, user_id)
        
        # Create response
        response = {
            'query': query,
            'intent': {
                'type': intent.intent_type,
                'entities': intent.entities,
                'confidence': intent.confidence,
                'refinements': intent.suggested_refinements
            },
            'results': [self._serialize_result(result) for result in results],
            'total_results': len(results),
            'search_time_ms': 150,  # Mock timing
            'suggestions': suggestions,
            'filters_applied': filters or {},
            'search_type': search_type.value,
            'related_concepts': self._get_related_concepts(query),
            'did_you_mean': self._get_spelling_suggestions(query)
        }
        
        return response
    
    def _analyze_search_intent(self, query: str, user_id: str = None) -> SearchIntent:
        """Analyze search intent using NLP techniques"""
        query_lower = query.lower()
        
        # Intent classification
        intent_type = "general"
        confidence = 0.7
        entities = []
        
        # File type intent
        file_extensions = ['pdf', 'doc', 'docx', 'txt', 'ppt', 'pptx', 'xls', 'xlsx', 'jpg', 'png']
        for ext in file_extensions:
            if ext in query_lower:
                intent_type = "file_type"
                entities.append(f"file_type:{ext}")
                confidence = 0.9
        
        # Date/time intent
        time_keywords = ['today', 'yesterday', 'last week', 'last month', 'recent', 'old']
        for keyword in time_keywords:
            if keyword in query_lower:
                intent_type = "temporal"
                entities.append(f"time:{keyword}")
                confidence = 0.8
        
        # User intent
        if 'by' in query_lower or 'from' in query_lower or 'created by' in query_lower:
            intent_type = "user_search"
            confidence = 0.8
        
        # Content intent
        content_keywords = ['contains', 'about', 'regarding', 'mentions', 'discusses']
        for keyword in content_keywords:
            if keyword in query_lower:
                intent_type = "content_search"
                confidence = 0.9
        
        # Size intent
        size_keywords = ['large', 'small', 'big', 'tiny', 'huge']
        for keyword in size_keywords:
            if keyword in query_lower:
                intent_type = "size_search"
                entities.append(f"size:{keyword}")
                confidence = 0.8
        
        # Extract entities (simple approach)
        entities.extend(self._extract_query_entities(query))
        
        # Generate refinement suggestions
        refinements = self._suggest_query_refinements(query, intent_type, user_id)
        
        return SearchIntent(
            query=query,
            intent_type=intent_type,
            entities=entities,
            confidence=confidence,
            suggested_refinements=refinements,
            filters={}
        )
    
    def _semantic_search(self, query: str, filters: Dict = None) -> List[SearchResult]:
        """Perform semantic search using content vectors"""
        query_vector = self._create_content_vector(self._preprocess_text(query))
        results = []
        
        for doc_id, doc_vector in self.content_vectors.items():
            if doc_id not in self.document_index:
                continue
            
            doc_data = self.document_index[doc_id]
            
            # Apply filters
            if filters and not self._matches_filters(doc_data, filters):
                continue
            
            # Calculate semantic similarity
            similarity = self._calculate_similarity(query_vector, doc_vector)
            
            if similarity >= self.relevance_threshold:
                result = self._create_search_result(
                    doc_id, doc_data, query, similarity, ResultType.CONTENT
                )
                results.append(result)
        
        # Sort by relevance score
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    def _keyword_search(self, query: str, filters: Dict = None) -> List[SearchResult]:
        """Perform traditional keyword search"""
        query_terms = self._preprocess_text(query).split()
        results = []
        
        for doc_id, doc_data in self.document_index.items():
            if filters and not self._matches_filters(doc_data, filters):
                continue
            
            content = doc_data['processed_content']
            score = self._calculate_keyword_score(query_terms, content)
            
            if score > 0:
                result = self._create_search_result(
                    doc_id, doc_data, query, score, ResultType.CONTENT
                )
                results.append(result)
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    def _fuzzy_search(self, query: str, filters: Dict = None) -> List[SearchResult]:
        """Perform fuzzy search for typo tolerance"""
        results = []
        query_lower = query.lower()
        
        for doc_id, doc_data in self.document_index.items():
            if filters and not self._matches_filters(doc_data, filters):
                continue
            
            content = doc_data['content'].lower()
            
            # Use difflib for fuzzy matching
            similarity = difflib.SequenceMatcher(None, query_lower, content).ratio()
            
            # Check for partial matches
            words = content.split()
            for word in words:
                word_similarity = difflib.SequenceMatcher(None, query_lower, word).ratio()
                if word_similarity > similarity:
                    similarity = word_similarity
            
            if similarity >= 0.4:  # Threshold for fuzzy matching
                result = self._create_search_result(
                    doc_id, doc_data, query, similarity, ResultType.CONTENT
                )
                results.append(result)
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    def _contextual_search(self, query: str, user_id: str, filters: Dict = None) -> List[SearchResult]:
        """Perform contextual search based on user history and preferences"""
        # Get user search history
        user_history = self.user_search_history.get(user_id, [])
        
        # Start with semantic search
        results = self._semantic_search(query, filters)
        
        # Enhance with contextual scoring
        for result in results:
            doc_data = self.document_index[result.id]
            
            # Boost score based on user interaction history
            contextual_boost = 0
            
            # Check if user has interacted with similar content
            for history_item in user_history:
                if self._are_queries_similar(query, history_item.get('query', '')):
                    contextual_boost += 0.1
            
            # Check for recurring themes in user searches
            user_concepts = self._extract_user_concepts(user_history)
            doc_concepts = doc_data.get('concepts', [])
            
            common_concepts = set(user_concepts) & set(doc_concepts)
            contextual_boost += len(common_concepts) * 0.05
            
            # Apply contextual boost
            result.score = min(1.0, result.score + contextual_boost)
            
            # Update context information
            result.context.update({
                'contextual_boost': contextual_boost,
                'matching_concepts': list(common_concepts),
                'user_relevance': 'high' if contextual_boost > 0.2 else 'medium' if contextual_boost > 0.1 else 'low'
            })
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    def _temporal_search(self, query: str, filters: Dict = None) -> List[SearchResult]:
        """Perform time-based search"""
        results = []
        
        # Extract time-related terms from query
        time_terms = self._extract_time_terms(query)
        
        for doc_id, doc_data in self.document_index.items():
            if filters and not self._matches_filters(doc_data, filters):
                continue
            
            doc_date = doc_data['metadata'].get('created_date')
            if not doc_date:
                continue
            
            try:
                doc_datetime = datetime.fromisoformat(doc_date.replace('Z', '+00:00'))
            except:
                continue
            
            # Check if document matches time criteria
            matches_time = self._matches_time_criteria(doc_datetime, time_terms)
            
            if matches_time:
                # Calculate basic content relevance
                content_score = self._calculate_keyword_score(
                    query.split(), doc_data['processed_content']
                )
                
                # Add temporal relevance
                temporal_score = self._calculate_temporal_relevance(doc_datetime, time_terms)
                
                total_score = (content_score * 0.7) + (temporal_score * 0.3)
                
                if total_score > 0:
                    result = self._create_search_result(
                        doc_id, doc_data, query, total_score, ResultType.CONTENT
                    )
                    result.context['temporal_match'] = True
                    result.context['time_terms'] = time_terms
                    results.append(result)
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for search indexing"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove common stop words (simple list)
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }
        
        words = text.split()
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        return ' '.join(filtered_words)
    
    def _create_content_vector(self, text: str) -> Dict[str, float]:
        """Create a simple TF-IDF-like vector for content"""
        words = text.split()
        word_count = len(words)
        
        if word_count == 0:
            return {}
        
        # Calculate term frequency
        tf = Counter(words)
        
        # Normalize by document length
        vector = {}
        for word, count in tf.items():
            vector[word] = count / word_count
        
        return vector
    
    def _calculate_similarity(self, vector1: Dict[str, float], vector2: Dict[str, float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not vector1 or not vector2:
            return 0.0
        
        # Get common words
        common_words = set(vector1.keys()) & set(vector2.keys())
        
        if not common_words:
            return 0.0
        
        # Calculate dot product
        dot_product = sum(vector1[word] * vector2[word] for word in common_words)
        
        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(val ** 2 for val in vector1.values()))
        magnitude2 = math.sqrt(sum(val ** 2 for val in vector2.values()))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _calculate_keyword_score(self, query_terms: List[str], content: str) -> float:
        """Calculate keyword-based relevance score"""
        content_words = content.split()
        total_words = len(content_words)
        
        if total_words == 0:
            return 0.0
        
        matches = 0
        for term in query_terms:
            matches += content_words.count(term)
        
        # Basic TF score with position boost for early matches
        score = matches / total_words
        
        # Boost score if query terms appear early in document
        early_content = ' '.join(content_words[:min(50, total_words)])
        early_matches = sum(1 for term in query_terms if term in early_content)
        
        if early_matches > 0:
            score += (early_matches / len(query_terms)) * 0.2
        
        return min(1.0, score)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        words = text.split()
        word_freq = Counter(words)
        
        # Get top frequent words (simple keyword extraction)
        keywords = [word for word, freq in word_freq.most_common(10) if len(word) > 3]
        
        return keywords
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities from text (simplified)"""
        entities = []
        
        # Simple patterns for entities
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        entities.extend([f"email:{email}" for email in emails])
        
        # Dates (simple format)
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
        dates = re.findall(date_pattern, text)
        entities.extend([f"date:{date}" for date in dates])
        
        # Phone numbers (simple format)
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        phones = re.findall(phone_pattern, text)
        entities.extend([f"phone:{phone}" for phone in phones])
        
        # URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, text)
        entities.extend([f"url:{url}" for url in urls])
        
        return entities
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract high-level concepts from text"""
        concepts = []
        
        # Domain-specific concept patterns
        business_terms = [
            'revenue', 'profit', 'sales', 'marketing', 'strategy', 'business',
            'project', 'meeting', 'presentation', 'report', 'analysis'
        ]
        
        tech_terms = [
            'software', 'development', 'programming', 'database', 'server',
            'application', 'system', 'technology', 'digital', 'computer'
        ]
        
        finance_terms = [
            'budget', 'financial', 'accounting', 'invoice', 'payment',
            'expense', 'income', 'tax', 'investment', 'cost'
        ]
        
        text_lower = text.lower()
        
        # Check for business concepts
        business_matches = sum(1 for term in business_terms if term in text_lower)
        if business_matches >= 2:
            concepts.append('business')
        
        # Check for technology concepts
        tech_matches = sum(1 for term in tech_terms if term in text_lower)
        if tech_matches >= 2:
            concepts.append('technology')
        
        # Check for finance concepts
        finance_matches = sum(1 for term in finance_terms if term in text_lower)
        if finance_matches >= 2:
            concepts.append('finance')
        
        return concepts
    
    def _update_metadata_index(self, doc_id: str, metadata: Dict):
        """Update metadata index for fast filtering"""
        for key, value in metadata.items():
            if key not in self.metadata_index:
                self.metadata_index[key] = defaultdict(list)
            
            if isinstance(value, list):
                for item in value:
                    self.metadata_index[key][str(item)].append(doc_id)
            else:
                self.metadata_index[key][str(value)].append(doc_id)
    
    def _update_concept_graph(self, doc_id: str, concepts: List[str]):
        """Update concept relationship graph"""
        for concept in concepts:
            if concept not in self.concept_graph:
                self.concept_graph[concept] = {
                    'documents': [],
                    'related_concepts': defaultdict(int)
                }
            
            self.concept_graph[concept]['documents'].append(doc_id)
            
            # Build relationships between concepts in the same document
            for other_concept in concepts:
                if other_concept != concept:
                    self.concept_graph[concept]['related_concepts'][other_concept] += 1
    
    def _matches_filters(self, doc_data: Dict, filters: Dict) -> bool:
        """Check if document matches search filters"""
        metadata = doc_data['metadata']
        
        for filter_key, filter_value in filters.items():
            if filter_key == 'file_type':
                doc_type = metadata.get('file_type', '').lower()
                if doc_type != filter_value.lower():
                    return False
            
            elif filter_key == 'created_after':
                doc_date = metadata.get('created_date')
                if doc_date:
                    try:
                        doc_datetime = datetime.fromisoformat(doc_date.replace('Z', '+00:00'))
                        filter_datetime = datetime.fromisoformat(filter_value.replace('Z', '+00:00'))
                        if doc_datetime <= filter_datetime:
                            return False
                    except:
                        pass
            
            elif filter_key == 'created_before':
                doc_date = metadata.get('created_date')
                if doc_date:
                    try:
                        doc_datetime = datetime.fromisoformat(doc_date.replace('Z', '+00:00'))
                        filter_datetime = datetime.fromisoformat(filter_value.replace('Z', '+00:00'))
                        if doc_datetime >= filter_datetime:
                            return False
                    except:
                        pass
            
            elif filter_key == 'author':
                doc_author = metadata.get('author', '').lower()
                if filter_value.lower() not in doc_author:
                    return False
            
            elif filter_key == 'size_min':
                doc_size = metadata.get('file_size', 0)
                if doc_size < filter_value:
                    return False
            
            elif filter_key == 'size_max':
                doc_size = metadata.get('file_size', 0)
                if doc_size > filter_value:
                    return False
        
        return True
    
    def _create_search_result(self, doc_id: str, doc_data: Dict, query: str, 
                            score: float, result_type: ResultType) -> SearchResult:
        """Create a search result object"""
        
        # Generate highlights
        highlights = self._generate_highlights(doc_data['content'], query)
        
        # Create result
        result = SearchResult(
            id=doc_id,
            title=doc_data['metadata'].get('title', f'Document {doc_id}'),
            content=doc_data['content'][:500] + '...' if len(doc_data['content']) > 500 else doc_data['content'],
            result_type=result_type,
            score=score,
            metadata=doc_data['metadata'],
            highlights=highlights,
            context={
                'word_count': doc_data['word_count'],
                'keywords': doc_data['keywords'][:5],
                'concepts': doc_data['concepts'],
                'entities': doc_data['entities'][:3]
            },
            file_path=doc_data['metadata'].get('file_path')
        )
        
        return result
    
    def _generate_highlights(self, content: str, query: str) -> List[str]:
        """Generate highlighted snippets from content"""
        highlights = []
        query_terms = self._preprocess_text(query).split()
        content_lower = content.lower()
        
        for term in query_terms:
            # Find positions of the term
            positions = []
            start = 0
            while True:
                pos = content_lower.find(term.lower(), start)
                if pos == -1:
                    break
                positions.append(pos)
                start = pos + 1
            
            # Create highlights around found terms
            for pos in positions[:3]:  # Limit to 3 highlights per term
                start = max(0, pos - self.highlight_length // 2)
                end = min(len(content), pos + self.highlight_length // 2)
                
                snippet = content[start:end]
                if start > 0:
                    snippet = '...' + snippet
                if end < len(content):
                    snippet = snippet + '...'
                
                # Highlight the term (simple approach)
                highlighted = snippet.replace(
                    content[pos:pos+len(term)], 
                    f"**{content[pos:pos+len(term)]}**"
                )
                
                if highlighted not in highlights:
                    highlights.append(highlighted)
        
        return highlights[:5]  # Return top 5 highlights
    
    def _serialize_result(self, result: SearchResult) -> Dict:
        """Serialize search result for JSON response"""
        return {
            'id': result.id,
            'title': result.title,
            'content': result.content,
            'type': result.result_type.value,
            'score': round(result.score, 3),
            'metadata': result.metadata,
            'highlights': result.highlights,
            'context': result.context,
            'file_path': result.file_path,
            'thumbnail': result.thumbnail
        }
    
    def _record_search(self, user_id: str, query: str, search_type: SearchType, result_count: int):
        """Record search for analytics and learning"""
        search_record = {
            'query': query,
            'search_type': search_type.value,
            'result_count': result_count,
            'timestamp': datetime.now().isoformat()
        }
        
        self.user_search_history[user_id].append(search_record)
        
        # Keep only recent history (last 100 searches)
        if len(self.user_search_history[user_id]) > 100:
            self.user_search_history[user_id] = self.user_search_history[user_id][-100:]
        
        # Update analytics
        self.search_analytics['total_searches'] += 1
        self.search_analytics[f'search_type_{search_type.value}'] += 1
        self.search_analytics['total_results'] += result_count
    
    def _generate_search_suggestions(self, query: str, intent: SearchIntent, user_id: str = None) -> List[str]:
        """Generate search suggestions and autocomplete"""
        suggestions = []
        
        # Query refinement suggestions
        suggestions.extend(intent.suggested_refinements)
        
        # Related concept suggestions
        related_concepts = self._get_related_concepts(query)
        for concept in related_concepts[:3]:
            suggestions.append(f"{query} {concept}")
        
        # User history-based suggestions
        if user_id and user_id in self.user_search_history:
            user_queries = [record['query'] for record in self.user_search_history[user_id]]
            similar_queries = [q for q in user_queries if self._are_queries_similar(query, q)]
            suggestions.extend(similar_queries[:2])
        
        # Popular searches (mock)
        popular_searches = [
            "financial reports", "project documents", "meeting notes",
            "presentation templates", "user manuals", "policy documents"
        ]
        
        # Add popular searches that are related to current query
        for popular in popular_searches:
            if any(word in popular.lower() for word in query.lower().split()):
                suggestions.append(popular)
        
        # Remove duplicates and limit
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion.lower() not in seen and suggestion.lower() != query.lower():
                seen.add(suggestion.lower())
                unique_suggestions.append(suggestion)
        
        return unique_suggestions[:8]
    
    def _get_related_concepts(self, query: str) -> List[str]:
        """Get concepts related to the search query"""
        query_concepts = self._extract_concepts(self._preprocess_text(query))
        related = []
        
        for concept in query_concepts:
            if concept in self.concept_graph:
                related_concepts = self.concept_graph[concept]['related_concepts']
                # Sort by frequency of co-occurrence
                sorted_related = sorted(related_concepts.items(), key=lambda x: x[1], reverse=True)
                related.extend([rel_concept for rel_concept, _ in sorted_related[:3]])
        
        return list(set(related))
    
    def _get_spelling_suggestions(self, query: str) -> List[str]:
        """Generate spelling suggestions for queries"""
        suggestions = []
        
        # Get all words from indexed documents
        all_words = set()
        for doc_data in self.document_index.values():
            all_words.update(doc_data['processed_content'].split())
        
        # Check each word in query for spelling
        query_words = query.split()
        for word in query_words:
            if word.lower() not in all_words:
                # Find closest matches
                closest_matches = difflib.get_close_matches(word.lower(), all_words, n=3, cutoff=0.6)
                if closest_matches:
                    corrected_query = query.replace(word, closest_matches[0])
                    suggestions.append(corrected_query)
        
        return suggestions[:3]
    
    def _suggest_query_refinements(self, query: str, intent_type: str, user_id: str = None) -> List[str]:
        """Suggest query refinements based on intent"""
        refinements = []
        
        if intent_type == "general":
            refinements.extend([
                f"{query} recent",
                f"{query} important",
                f"{query} shared"
            ])
        
        elif intent_type == "file_type":
            refinements.extend([
                f"{query} large",
                f"{query} recent",
                f"{query} my files"
            ])
        
        elif intent_type == "temporal":
            refinements.extend([
                f"{query} important",
                f"{query} shared",
                f"{query} modified"
            ])
        
        elif intent_type == "content_search":
            refinements.extend([
                f"{query} summary",
                f"{query} detailed",
                f"{query} analysis"
            ])
        
        return refinements[:3]
    
    def _extract_query_entities(self, query: str) -> List[str]:
        """Extract entities from search query"""
        entities = []
        
        # Simple entity extraction for queries
        query_lower = query.lower()
        
        # File types
        file_types = ['pdf', 'doc', 'docx', 'txt', 'ppt', 'pptx', 'xls', 'xlsx', 'jpg', 'png', 'gif']
        for file_type in file_types:
            if file_type in query_lower:
                entities.append(f"file_type:{file_type}")
        
        # Common business entities
        business_entities = ['meeting', 'project', 'report', 'presentation', 'document', 'contract']
        for entity in business_entities:
            if entity in query_lower:
                entities.append(f"category:{entity}")
        
        return entities
    
    def _extract_time_terms(self, query: str) -> List[str]:
        """Extract time-related terms from query"""
        time_terms = []
        query_lower = query.lower()
        
        # Time keywords
        time_keywords = {
            'today': 0,
            'yesterday': 1,
            'last week': 7,
            'last month': 30,
            'recent': 7,
            'old': 365,
            'this week': 7,
            'this month': 30
        }
        
        for keyword, days_ago in time_keywords.items():
            if keyword in query_lower:
                time_terms.append({
                    'term': keyword,
                    'days_ago': days_ago,
                    'reference_date': datetime.now() - timedelta(days=days_ago)
                })
        
        return time_terms
    
    def _matches_time_criteria(self, doc_datetime: datetime, time_terms: List[Dict]) -> bool:
        """Check if document matches time criteria"""
        if not time_terms:
            return True
        
        now = datetime.now()
        
        for time_term in time_terms:
            days_ago = time_term['days_ago']
            
            if time_term['term'] == 'recent':
                if (now - doc_datetime).days <= days_ago:
                    return True
            elif time_term['term'] == 'old':
                if (now - doc_datetime).days >= days_ago:
                    return True
            else:
                if (now - doc_datetime).days <= days_ago:
                    return True
        
        return False
    
    def _calculate_temporal_relevance(self, doc_datetime: datetime, time_terms: List[Dict]) -> float:
        """Calculate temporal relevance score"""
        if not time_terms:
            return 0.5
        
        now = datetime.now()
        days_difference = (now - doc_datetime).days
        
        max_score = 0
        for time_term in time_terms:
            target_days = time_term['days_ago']
            
            # Score based on how close the document date is to the target
            if target_days == 0:  # today
                score = 1.0 if days_difference == 0 else max(0, 1.0 - (days_difference / 2))
            else:
                difference = abs(days_difference - target_days)
                score = max(0, 1.0 - (difference / target_days))
            
            max_score = max(max_score, score)
        
        return max_score
    
    def _are_queries_similar(self, query1: str, query2: str) -> bool:
        """Check if two queries are similar"""
        similarity = difflib.SequenceMatcher(None, query1.lower(), query2.lower()).ratio()
        return similarity > 0.6
    
    def _extract_user_concepts(self, user_history: List[Dict]) -> List[str]:
        """Extract concepts from user search history"""
        concepts = []
        
        for search_record in user_history:
            query = search_record.get('query', '')
            query_concepts = self._extract_concepts(self._preprocess_text(query))
            concepts.extend(query_concepts)
        
        # Return most common concepts
        concept_counts = Counter(concepts)
        return [concept for concept, _ in concept_counts.most_common(10)]
    
    def get_search_analytics(self, user_id: str = None) -> Dict:
        """Get search analytics and insights"""
        analytics = {
            'global_stats': dict(self.search_analytics),
            'popular_queries': self._get_popular_queries(),
            'search_trends': self._get_search_trends(),
            'concept_popularity': self._get_concept_popularity(),
            'generated_at': datetime.now().isoformat()
        }
        
        if user_id and user_id in self.user_search_history:
            analytics['user_stats'] = self._get_user_search_stats(user_id)
        
        return analytics
    
    def _get_popular_queries(self) -> List[Dict]:
        """Get popular search queries"""
        all_queries = []
        for user_history in self.user_search_history.values():
            all_queries.extend([record['query'] for record in user_history])
        
        query_counts = Counter(all_queries)
        return [
            {'query': query, 'count': count}
            for query, count in query_counts.most_common(10)
        ]
    
    def _get_search_trends(self) -> Dict:
        """Get search trends over time"""
        # Mock implementation - would analyze search patterns over time
        return {
            'trending_up': ['AI documents', 'project reports', 'financial data'],
            'trending_down': ['old presentations', 'legacy systems'],
            'seasonal_patterns': {
                'end_of_month': ['reports', 'financial'],
                'monday_mornings': ['meeting notes', 'project updates']
            }
        }
    
    def _get_concept_popularity(self) -> List[Dict]:
        """Get popular concepts from searches"""
        concept_docs = {}
        for concept, data in self.concept_graph.items():
            concept_docs[concept] = len(data['documents'])
        
        return [
            {'concept': concept, 'document_count': count}
            for concept, count in sorted(concept_docs.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
    
    def _get_user_search_stats(self, user_id: str) -> Dict:
        """Get search statistics for a specific user"""
        user_history = self.user_search_history[user_id]
        
        query_counts = Counter(record['query'] for record in user_history)
        search_type_counts = Counter(record['search_type'] for record in user_history)
        
        return {
            'total_searches': len(user_history),
            'unique_queries': len(query_counts),
            'most_common_queries': query_counts.most_common(5),
            'search_type_distribution': dict(search_type_counts),
            'average_results': sum(record['result_count'] for record in user_history) / len(user_history) if user_history else 0,
            'search_frequency': len(user_history) / max(1, (datetime.now() - datetime.fromisoformat(user_history[0]['timestamp'])).days) if user_history else 0
        }


class DiscoveryEngine:
    """AI-powered content discovery engine"""
    
    def __init__(self, search_engine: SmartSearchEngine):
        self.search_engine = search_engine
        self.discovery_cache = {}
    
    def discover_related_content(self, doc_id: str, limit: int = 10) -> List[Dict]:
        """Discover content related to a specific document"""
        if doc_id not in self.search_engine.document_index:
            return []
        
        doc_data = self.search_engine.document_index[doc_id]
        
        # Use keywords and concepts for discovery
        keywords = doc_data.get('keywords', [])
        concepts = doc_data.get('concepts', [])
        
        # Create discovery query from keywords and concepts
        discovery_query = ' '.join(keywords[:3] + concepts)
        
        if not discovery_query.strip():
            return []
        
        # Search for related content
        search_results = self.search_engine.search(
            query=discovery_query,
            search_type=SearchType.SEMANTIC,
            limit=limit + 1  # +1 to exclude the original document
        )
        
        # Filter out the original document
        related_results = [
            result for result in search_results['results']
            if result['id'] != doc_id
        ]
        
        return related_results[:limit]
    
    def discover_trending_content(self, time_window_days: int = 7) -> List[Dict]:
        """Discover trending content based on recent activity"""
        cutoff_date = datetime.now() - timedelta(days=time_window_days)
        
        trending_docs = []
        
        for doc_id, doc_data in self.search_engine.document_index.items():
            doc_date = doc_data['metadata'].get('created_date')
            if doc_date:
                try:
                    doc_datetime = datetime.fromisoformat(doc_date.replace('Z', '+00:00'))
                    if doc_datetime >= cutoff_date:
                        # Calculate trending score based on recency and concepts
                        recency_score = 1.0 - ((datetime.now() - doc_datetime).days / time_window_days)
                        concept_score = len(doc_data.get('concepts', [])) * 0.1
                        
                        trending_score = recency_score + concept_score
                        
                        trending_docs.append({
                            'id': doc_id,
                            'title': doc_data['metadata'].get('title', f'Document {doc_id}'),
                            'trending_score': trending_score,
                            'concepts': doc_data.get('concepts', []),
                            'created_date': doc_date
                        })
                except:
                    continue
        
        # Sort by trending score
        trending_docs.sort(key=lambda x: x['trending_score'], reverse=True)
        
        return trending_docs[:10]
    
    def discover_forgotten_content(self, user_id: str, days_threshold: int = 90) -> List[Dict]:
        """Discover potentially forgotten but relevant content"""
        forgotten_docs = []
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        
        # Get user's recent search concepts
        user_history = self.search_engine.user_search_history.get(user_id, [])
        recent_concepts = set()
        
        for search_record in user_history[-10:]:  # Last 10 searches
            query = search_record.get('query', '')
            concepts = self.search_engine._extract_concepts(
                self.search_engine._preprocess_text(query)
            )
            recent_concepts.update(concepts)
        
        # Find old documents that match recent search interests
        for doc_id, doc_data in self.search_engine.document_index.items():
            doc_date = doc_data['metadata'].get('created_date')
            if doc_date:
                try:
                    doc_datetime = datetime.fromisoformat(doc_date.replace('Z', '+00:00'))
                    if doc_datetime <= cutoff_date:
                        doc_concepts = set(doc_data.get('concepts', []))
                        
                        # Check for concept overlap with recent searches
                        concept_overlap = len(doc_concepts & recent_concepts)
                        
                        if concept_overlap > 0:
                            relevance_score = concept_overlap / max(len(recent_concepts), 1)
                            age_score = (datetime.now() - doc_datetime).days / 365  # Years old
                            
                            forgotten_docs.append({
                                'id': doc_id,
                                'title': doc_data['metadata'].get('title', f'Document {doc_id}'),
                                'relevance_score': relevance_score,
                                'age_score': age_score,
                                'matching_concepts': list(doc_concepts & recent_concepts),
                                'created_date': doc_date
                            })
                except:
                    continue
        
        # Sort by relevance
        forgotten_docs.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return forgotten_docs[:10]
    
    def discover_content_gaps(self) -> List[Dict]:
        """Discover gaps in content coverage"""
        gaps = []
        
        # Analyze concept coverage
        concept_counts = {}
        for doc_data in self.search_engine.document_index.values():
            for concept in doc_data.get('concepts', []):
                concept_counts[concept] = concept_counts.get(concept, 0) + 1
        
        # Find underrepresented concepts
        all_concepts = list(concept_counts.keys())
        median_count = sorted(concept_counts.values())[len(concept_counts) // 2] if concept_counts else 0
        
        for concept, count in concept_counts.items():
            if count < median_count * 0.5:  # Significantly below median
                gaps.append({
                    'type': 'underrepresented_concept',
                    'concept': concept,
                    'current_count': count,
                    'suggestion': f'Consider adding more content about {concept}'
                })
        
        # Mock additional gap types
        gaps.extend([
            {
                'type': 'missing_file_type',
                'file_type': 'video',
                'suggestion': 'Consider adding video content for better engagement'
            },
            {
                'type': 'outdated_content',
                'age_threshold': '2+ years',
                'suggestion': 'Review and update content older than 2 years'
            }
        ])
        
        return gaps[:10]


def create_search_engine():
    """Factory function to create smart search engine"""
    return SmartSearchEngine()


def create_discovery_engine(search_engine: SmartSearchEngine):
    """Factory function to create discovery engine"""
    return DiscoveryEngine(search_engine)
