"""
AI-Powered Knowledge Graph and Semantic Search Engine
Creates intelligent connections between documents and enables semantic search
"""

import os
import re
import json
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict, Counter
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import numpy as np
from datetime import datetime


class KnowledgeGraph:
    """AI-powered knowledge graph for document relationships"""
    
    def __init__(self):
        self.graph = nx.Graph()
        self.document_embeddings = {}
        self.concept_clusters = {}
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000, 
            stop_words='english',
            ngram_range=(1, 2)
        )
        
    def build_knowledge_graph(self, file_analyses: List[Dict]) -> Dict:
        """Build knowledge graph from file analyses"""
        if not file_analyses:
            return {'nodes': 0, 'edges': 0, 'clusters': 0}
        
        # Add documents as nodes
        for analysis in file_analyses:
            filename = analysis.get('filename', '')
            self.graph.add_node(filename, **{
                'type': 'document',
                'category': analysis.get('category', 'unknown'),
                'word_count': analysis.get('word_count', 0),
                'complexity': analysis.get('complexity_score', 0),
                'sentiment': analysis.get('sentiment', {}).get('sentiment', 'neutral'),
                'entities': analysis.get('entities', {}),
                'topics': analysis.get('key_topics', [])
            })
        
        # Add concept nodes and relationships
        self._add_concept_relationships(file_analyses)
        self._add_content_similarity_edges(file_analyses)
        self._add_entity_relationships(file_analyses)
        self._cluster_documents(file_analyses)
        
        return {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'clusters': len(self.concept_clusters),
            'graph_density': nx.density(self.graph)
        }
    
    def _add_concept_relationships(self, file_analyses: List[Dict]):
        """Add concept nodes and connect documents with shared topics"""
        topic_to_docs = defaultdict(list)
        
        # Collect all topics and their documents
        for analysis in file_analyses:
            filename = analysis.get('filename', '')
            topics = analysis.get('key_topics', [])
            
            for topic in topics[:10]:  # Top 10 topics
                clean_topic = self._clean_concept_name(topic)
                if clean_topic:
                    topic_to_docs[clean_topic].append(filename)
        
        # Add concept nodes and edges
        for concept, documents in topic_to_docs.items():
            if len(documents) >= 2:  # Only add concepts shared by multiple docs
                concept_node = f"concept_{concept}"
                self.graph.add_node(concept_node, type='concept', name=concept)
                
                # Connect documents through concepts
                for doc in documents:
                    if self.graph.has_node(doc):
                        self.graph.add_edge(doc, concept_node, 
                                          relation='contains_concept', weight=1.0)
                
                # Connect documents that share concepts
                for i, doc1 in enumerate(documents):
                    for doc2 in documents[i+1:]:
                        if self.graph.has_node(doc1) and self.graph.has_node(doc2):
                            if self.graph.has_edge(doc1, doc2):
                                # Increase weight for shared concepts
                                self.graph[doc1][doc2]['weight'] += 0.5
                            else:
                                self.graph.add_edge(doc1, doc2, 
                                                  relation='shared_concept', 
                                                  weight=0.5, concept=concept)
    
    def _add_content_similarity_edges(self, file_analyses: List[Dict]):
        """Add edges based on content similarity"""
        texts = []
        filenames = []
        
        for analysis in file_analyses:
            text = analysis.get('extracted_text', '')
            if text and len(text) > 50:
                texts.append(text)
                filenames.append(analysis.get('filename', ''))
        
        if len(texts) < 2:
            return
        
        try:
            # Calculate TF-IDF similarity matrix
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Add similarity edges
            for i, filename1 in enumerate(filenames):
                for j, filename2 in enumerate(filenames[i+1:], i+1):
                    similarity = similarity_matrix[i][j]
                    
                    if similarity > 0.3:  # Significant similarity threshold
                        if (self.graph.has_node(filename1) and 
                            self.graph.has_node(filename2)):
                            
                            if self.graph.has_edge(filename1, filename2):
                                # Update existing edge weight
                                current_weight = self.graph[filename1][filename2].get('weight', 0)
                                self.graph[filename1][filename2]['weight'] = max(current_weight, similarity)
                                self.graph[filename1][filename2]['content_similarity'] = similarity
                            else:
                                self.graph.add_edge(filename1, filename2,
                                                  relation='content_similar',
                                                  weight=similarity,
                                                  content_similarity=similarity)
        except Exception as e:
            print(f"Error calculating content similarity: {e}")
    
    def _add_entity_relationships(self, file_analyses: List[Dict]):
        """Add relationships based on shared entities"""
        entity_to_docs = defaultdict(list)
        
        # Collect entities
        for analysis in file_analyses:
            filename = analysis.get('filename', '')
            entities = analysis.get('entities', {})
            
            for entity_type, entity_list in entities.items():
                for entity in entity_list:
                    clean_entity = entity.strip().lower()
                    if len(clean_entity) > 2:
                        entity_key = f"{entity_type}_{clean_entity}"
                        entity_to_docs[entity_key].append(filename)
        
        # Add entity relationships
        for entity_key, documents in entity_to_docs.items():
            if len(documents) >= 2:
                entity_type, entity_value = entity_key.split('_', 1)
                
                # Connect documents with shared entities
                for i, doc1 in enumerate(documents):
                    for doc2 in documents[i+1:]:
                        if self.graph.has_node(doc1) and self.graph.has_node(doc2):
                            edge_key = f"shared_{entity_type}"
                            
                            if self.graph.has_edge(doc1, doc2):
                                # Add entity info to existing edge
                                edge_data = self.graph[doc1][doc2]
                                if 'shared_entities' not in edge_data:
                                    edge_data['shared_entities'] = []
                                edge_data['shared_entities'].append(entity_key)
                                edge_data['weight'] += 0.3
                            else:
                                self.graph.add_edge(doc1, doc2,
                                                  relation=edge_key,
                                                  weight=0.3,
                                                  shared_entities=[entity_key])
    
    def _cluster_documents(self, file_analyses: List[Dict]):
        """Cluster documents based on content similarity"""
        texts = []
        filenames = []
        
        for analysis in file_analyses:
            text = analysis.get('extracted_text', '')
            if text and len(text) > 50:
                texts.append(text)
                filenames.append(analysis.get('filename', ''))
        
        if len(texts) < 3:
            return
        
        try:
            # Create TF-IDF vectors
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            
            # Determine optimal number of clusters (max 8, min 2)
            n_clusters = min(8, max(2, len(texts) // 3))
            
            # Perform K-means clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(tfidf_matrix.toarray())
            
            # Group documents by cluster
            for filename, cluster_id in zip(filenames, cluster_labels):
                if cluster_id not in self.concept_clusters:
                    self.concept_clusters[cluster_id] = []
                self.concept_clusters[cluster_id].append(filename)
                
                # Add cluster info to graph nodes
                if self.graph.has_node(filename):
                    self.graph.nodes[filename]['cluster'] = int(cluster_id)
            
        except Exception as e:
            print(f"Error in document clustering: {e}")
    
    def find_related_documents(self, filename: str, max_results: int = 5) -> List[Dict]:
        """Find documents related to the given file"""
        if not self.graph.has_node(filename):
            return []
        
        related = []
        
        # Get direct neighbors (connected documents)
        neighbors = self.graph.neighbors(filename)
        
        for neighbor in neighbors:
            if self.graph.nodes[neighbor].get('type') == 'document':
                edge_data = self.graph[filename][neighbor]
                related.append({
                    'filename': neighbor,
                    'relationship': edge_data.get('relation', 'unknown'),
                    'strength': edge_data.get('weight', 0),
                    'content_similarity': edge_data.get('content_similarity', 0),
                    'shared_entities': edge_data.get('shared_entities', [])
                })
        
        # Sort by relationship strength
        related.sort(key=lambda x: x['strength'], reverse=True)
        return related[:max_results]
    
    def get_document_insights(self, filename: str) -> Dict:
        """Get AI insights about a document's position in the knowledge graph"""
        if not self.graph.has_node(filename):
            return {'error': 'Document not found in knowledge graph'}
        
        node_data = self.graph.nodes[filename]
        
        # Calculate centrality measures
        degree_centrality = nx.degree_centrality(self.graph).get(filename, 0)
        
        try:
            betweenness_centrality = nx.betweenness_centrality(self.graph).get(filename, 0)
        except:
            betweenness_centrality = 0
        
        # Get cluster information
        cluster_id = node_data.get('cluster')
        cluster_mates = []
        if cluster_id is not None and cluster_id in self.concept_clusters:
            cluster_mates = [doc for doc in self.concept_clusters[cluster_id] if doc != filename]
        
        # Calculate document importance
        connections = self.graph.degree(filename)
        
        insights = {
            'centrality_score': degree_centrality,
            'bridge_score': betweenness_centrality,
            'connection_count': connections,
            'cluster_id': cluster_id,
            'cluster_mates': cluster_mates,
            'importance_level': self._calculate_importance_level(degree_centrality, connections),
            'document_role': self._determine_document_role(degree_centrality, betweenness_centrality, connections)
        }
        
        return insights
    
    def semantic_search(self, query: str, file_analyses: List[Dict], max_results: int = 10) -> List[Dict]:
        """Perform semantic search using the knowledge graph"""
        if not file_analyses:
            return []
        
        # Prepare documents for search
        documents = []
        filenames = []
        
        for analysis in file_analyses:
            text = analysis.get('extracted_text', '')
            if text:
                # Combine text with metadata for richer search
                searchable_text = f"{text} {' '.join(analysis.get('key_topics', []))}"
                documents.append(searchable_text)
                filenames.append(analysis)
        
        if not documents:
            return []
        
        try:
            # Add query to documents for similarity calculation
            all_texts = [query] + documents
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_texts)
            
            # Calculate similarity between query and documents
            query_vector = tfidf_matrix[0]
            doc_vectors = tfidf_matrix[1:]
            
            similarities = cosine_similarity(query_vector, doc_vectors).flatten()
            
            # Rank documents by similarity
            results = []
            for i, similarity in enumerate(similarities):
                if similarity > 0.1:  # Minimum relevance threshold
                    analysis = filenames[i]
                    
                    # Enhance score with graph information
                    enhanced_score = self._enhance_search_score(
                        analysis.get('filename', ''), similarity)
                    
                    results.append({
                        'file_analysis': analysis,
                        'relevance_score': similarity,
                        'enhanced_score': enhanced_score,
                        'search_reason': self._generate_search_reason(query, analysis)
                    })
            
            # Sort by enhanced score
            results.sort(key=lambda x: x['enhanced_score'], reverse=True)
            return results[:max_results]
            
        except Exception as e:
            print(f"Error in semantic search: {e}")
            return []
    
    def get_knowledge_clusters(self) -> Dict:
        """Get information about document clusters"""
        cluster_info = {}
        
        for cluster_id, documents in self.concept_clusters.items():
            if len(documents) >= 2:
                # Analyze cluster characteristics
                categories = []
                total_complexity = 0
                total_words = 0
                
                for doc in documents:
                    if self.graph.has_node(doc):
                        node_data = self.graph.nodes[doc]
                        categories.append(node_data.get('category', 'unknown'))
                        total_complexity += node_data.get('complexity', 0)
                        total_words += node_data.get('word_count', 0)
                
                cluster_info[cluster_id] = {
                    'document_count': len(documents),
                    'documents': documents,
                    'dominant_category': Counter(categories).most_common(1)[0][0] if categories else 'unknown',
                    'avg_complexity': total_complexity / len(documents) if documents else 0,
                    'avg_word_count': total_words / len(documents) if documents else 0,
                    'cluster_theme': self._generate_cluster_theme(cluster_id)
                }
        
        return cluster_info
    
    def _clean_concept_name(self, concept: str) -> str:
        """Clean and normalize concept names"""
        # Remove special characters and normalize
        clean = re.sub(r'[^a-zA-Z0-9\s]', '', concept.lower())
        clean = re.sub(r'\s+', '_', clean.strip())
        return clean if len(clean) > 2 else None
    
    def _calculate_importance_level(self, centrality: float, connections: int) -> str:
        """Calculate document importance level"""
        if centrality > 0.1 and connections > 5:
            return 'high'
        elif centrality > 0.05 or connections > 3:
            return 'medium'
        else:
            return 'low'
    
    def _determine_document_role(self, degree_centrality: float, betweenness_centrality: float, connections: int) -> str:
        """Determine the role of a document in the knowledge graph"""
        if betweenness_centrality > 0.1:
            return 'bridge_document'  # Connects different topics
        elif degree_centrality > 0.1:
            return 'hub_document'     # Central to many documents
        elif connections > 3:
            return 'connector_document'  # Well connected
        else:
            return 'standalone_document'  # Few connections
    
    def _enhance_search_score(self, filename: str, base_score: float) -> float:
        """Enhance search score using graph information"""
        if not self.graph.has_node(filename):
            return base_score
        
        # Get graph-based metrics
        centrality = nx.degree_centrality(self.graph).get(filename, 0)
        connections = self.graph.degree(filename)
        
        # Enhance score based on document importance
        enhancement_factor = 1 + (centrality * 0.2) + (min(connections, 10) * 0.01)
        
        return base_score * enhancement_factor
    
    def _generate_search_reason(self, query: str, analysis: Dict) -> str:
        """Generate explanation for why a document was returned"""
        reasons = []
        
        # Check if query terms appear in filename
        filename = analysis.get('filename', '').lower()
        query_lower = query.lower()
        
        if any(term in filename for term in query_lower.split()):
            reasons.append("filename match")
        
        # Check topics
        topics = analysis.get('key_topics', [])
        if any(query_lower in topic.lower() for topic in topics):
            reasons.append("topic relevance")
        
        # Check category
        category = analysis.get('category', '')
        if query_lower in category.lower():
            reasons.append("category match")
        
        # Check content
        text = analysis.get('extracted_text', '').lower()
        if query_lower in text:
            reasons.append("content match")
        
        return ", ".join(reasons) if reasons else "semantic similarity"
    
    def _generate_cluster_theme(self, cluster_id: int) -> str:
        """Generate a theme name for a document cluster"""
        if cluster_id not in self.concept_clusters:
            return "Unknown Theme"
        
        documents = self.concept_clusters[cluster_id]
        
        # Collect categories and topics from cluster documents
        categories = []
        all_topics = []
        
        for doc in documents:
            if self.graph.has_node(doc):
                node_data = self.graph.nodes[doc]
                categories.append(node_data.get('category', 'general'))
                all_topics.extend(node_data.get('topics', []))
        
        # Determine dominant category
        if categories:
            dominant_category = Counter(categories).most_common(1)[0][0]
        else:
            dominant_category = 'general'
        
        # Find common topics
        if all_topics:
            common_topics = Counter(all_topics).most_common(3)
            topic_theme = ", ".join([topic for topic, _ in common_topics])
            return f"{dominant_category.title()} - {topic_theme}"
        else:
            return f"{dominant_category.title()} Documents"


class SemanticSearchEngine:
    """Advanced semantic search with AI-powered understanding"""
    
    def __init__(self):
        self.knowledge_graph = KnowledgeGraph()
        self.query_history = []
        self.search_patterns = {}
    
    def index_documents(self, file_analyses: List[Dict]) -> Dict:
        """Index documents for semantic search"""
        return self.knowledge_graph.build_knowledge_graph(file_analyses)
    
    def search(self, query: str, file_analyses: List[Dict], filters: Dict = None) -> Dict:
        """Perform advanced semantic search"""
        # Store query for pattern analysis
        self.query_history.append({
            'query': query,
            'timestamp': datetime.now().isoformat()
        })
        
        # Basic semantic search
        results = self.knowledge_graph.semantic_search(query, file_analyses)
        
        # Apply filters if provided
        if filters:
            results = self._apply_filters(results, filters)
        
        # Generate search insights
        insights = self._generate_search_insights(query, results)
        
        return {
            'results': results,
            'total_count': len(results),
            'search_insights': insights,
            'suggested_refinements': self._suggest_query_refinements(query, results)
        }
    
    def _apply_filters(self, results: List[Dict], filters: Dict) -> List[Dict]:
        """Apply search filters"""
        filtered_results = []
        
        for result in results:
            analysis = result['file_analysis']
            include = True
            
            # Category filter
            if 'category' in filters:
                if analysis.get('category') != filters['category']:
                    include = False
            
            # Date range filter
            if 'date_range' in filters and include:
                # Implementation depends on how dates are stored
                pass
            
            # File type filter
            if 'file_type' in filters and include:
                filename = analysis.get('filename', '')
                file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
                if file_ext not in filters['file_type']:
                    include = False
            
            # Minimum relevance filter
            if 'min_relevance' in filters and include:
                if result['relevance_score'] < filters['min_relevance']:
                    include = False
            
            if include:
                filtered_results.append(result)
        
        return filtered_results
    
    def _generate_search_insights(self, query: str, results: List[Dict]) -> Dict:
        """Generate insights about the search results"""
        if not results:
            return {'message': 'No results found. Try broader search terms.'}
        
        insights = {}
        
        # Analyze result categories
        categories = [r['file_analysis'].get('category', 'unknown') for r in results]
        category_counts = Counter(categories)
        insights['top_categories'] = category_counts.most_common(3)
        
        # Analyze relevance distribution
        scores = [r['relevance_score'] for r in results]
        insights['avg_relevance'] = sum(scores) / len(scores)
        insights['high_relevance_count'] = sum(1 for score in scores if score > 0.5)
        
        # Content insights
        total_words = sum(r['file_analysis'].get('word_count', 0) for r in results)
        insights['total_content_words'] = total_words
        
        return insights
    
    def _suggest_query_refinements(self, query: str, results: List[Dict]) -> List[str]:
        """Suggest query refinements based on results"""
        suggestions = []
        
        if not results:
            suggestions.append(f"Try broader terms related to '{query}'")
            suggestions.append("Check spelling and try synonyms")
            return suggestions
        
        # Suggest category refinements
        if len(results) > 10:
            categories = [r['file_analysis'].get('category', '') for r in results]
            top_category = Counter(categories).most_common(1)[0][0]
            suggestions.append(f"Add 'category:{top_category}' to narrow results")
        
        # Suggest related topics
        all_topics = []
        for result in results[:5]:  # Top 5 results
            topics = result['file_analysis'].get('key_topics', [])
            all_topics.extend(topics)
        
        if all_topics:
            common_topics = Counter(all_topics).most_common(3)
            for topic, _ in common_topics:
                if query.lower() not in topic.lower():
                    suggestions.append(f"Try searching for '{topic}'")
        
        return suggestions[:3]  # Return top 3 suggestions


def create_knowledge_graph():
    """Factory function to create knowledge graph"""
    return KnowledgeGraph()


def create_semantic_search_engine():
    """Factory function to create semantic search engine"""
    return SemanticSearchEngine()
