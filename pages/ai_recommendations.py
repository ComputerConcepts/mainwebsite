"""
AI-Powered Smart Recommendations Engine
Provides intelligent suggestions for file organization, workflow optimization, and content discovery
"""

import os
import re
from typing import Dict, List, Tuple, Set
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class SmartRecommendationEngine:
    """AI-powered recommendation system for files and workflows"""
    
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(max_features=500, stop_words='english')
        self.user_patterns = {}
        self.content_clusters = {}
        
    def analyze_user_patterns(self, user_id: str, file_activities: List[Dict]) -> Dict:
        """Analyze user behavior patterns to provide personalized recommendations"""
        patterns = {
            'frequent_file_types': [],
            'active_times': [],
            'collaboration_patterns': [],
            'folder_preferences': [],
            'search_patterns': []
        }
        
        # Analyze file type preferences
        file_types = [activity.get('file_type', '').lower() for activity in file_activities]
        type_counts = Counter(file_types)
        patterns['frequent_file_types'] = [
            {'type': ftype, 'frequency': count} 
            for ftype, count in type_counts.most_common(10)
        ]
        
        # Analyze active times
        activity_hours = []
        for activity in file_activities:
            if activity.get('timestamp'):
                try:
                    hour = datetime.fromisoformat(activity['timestamp']).hour
                    activity_hours.append(hour)
                except:
                    continue
        
        if activity_hours:
            hour_counts = Counter(activity_hours)
            patterns['active_times'] = [
                {'hour': hour, 'activity_count': count}
                for hour, count in hour_counts.most_common(5)
            ]
        
        # Analyze folder usage patterns
        folders = [activity.get('folder_path', '') for activity in file_activities if activity.get('folder_path')]
        folder_counts = Counter(folders)
        patterns['folder_preferences'] = [
            {'folder': folder, 'usage_count': count}
            for folder, count in folder_counts.most_common(10)
        ]
        
        self.user_patterns[user_id] = patterns
        return patterns
    
    def recommend_similar_files(self, target_file_analysis: Dict, all_file_analyses: List[Dict], limit: int = 5) -> List[Dict]:
        """Find files similar to the target file using content analysis"""
        if not target_file_analysis.get('extracted_text') or not all_file_analyses:
            return []
        
        # Prepare text corpus
        texts = [target_file_analysis['extracted_text']]
        file_mapping = [None]  # First item is target file
        
        for analysis in all_file_analyses:
            if (analysis.get('filename') != target_file_analysis.get('filename') and 
                analysis.get('extracted_text')):
                texts.append(analysis['extracted_text'])
                file_mapping.append(analysis)
        
        if len(texts) < 2:
            return []
        
        try:
            # Calculate TF-IDF similarity
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            similarity_scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
            
            # Get top similar files
            similar_indices = similarity_scores.argsort()[-limit:][::-1]
            
            recommendations = []
            for idx in similar_indices:
                if similarity_scores[idx] > 0.1:  # Minimum similarity threshold
                    file_info = file_mapping[idx + 1]  # +1 because we skip target file
                    if file_info:
                        recommendations.append({
                            'file': file_info,
                            'similarity_score': float(similarity_scores[idx]),
                            'reason': f'Content similarity: {similarity_scores[idx]:.2%}'
                        })
            
            return recommendations
        except Exception as e:
            return []
    
    def recommend_folder_organization(self, file_analyses: List[Dict]) -> Dict:
        """Suggest optimal folder structure based on file content"""
        suggestions = {
            'suggested_folders': [],
            'misplaced_files': [],
            'organization_score': 0
        }
        
        # Group files by category
        category_groups = defaultdict(list)
        for analysis in file_analyses:
            category = analysis.get('category', 'general')
            category_groups[category].append(analysis)
        
        # Suggest folder structure
        for category, files in category_groups.items():
            if len(files) >= 3:  # Only suggest folders for categories with multiple files
                folder_suggestion = {
                    'folder_name': f"{category.title()} Documents",
                    'category': category,
                    'file_count': len(files),
                    'sample_files': [f['filename'] for f in files[:3]]
                }
                suggestions['suggested_folders'].append(folder_suggestion)
        
        # Identify potentially misplaced files
        for analysis in file_analyses:
            filename = analysis.get('filename', '').lower()
            category = analysis.get('category', 'general')
            
            # Check if file extension doesn't match category
            file_ext = filename.split('.')[-1] if '.' in filename else ''
            if category == 'presentation' and file_ext not in ['ppt', 'pptx', 'pdf']:
                suggestions['misplaced_files'].append({
                    'filename': analysis['filename'],
                    'current_category': category,
                    'suggested_action': 'Review categorization - may not be a presentation'
                })
            elif category == 'spreadsheet' and file_ext not in ['xlsx', 'xls', 'csv']:
                suggestions['misplaced_files'].append({
                    'filename': analysis['filename'],
                    'current_category': category,
                    'suggested_action': 'Review categorization - may not be a spreadsheet'
                })
        
        # Calculate organization score
        total_files = len(file_analyses)
        organized_files = sum(len(files) for files in category_groups.values() if len(files) >= 2)
        suggestions['organization_score'] = (organized_files / total_files * 100) if total_files > 0 else 0
        
        return suggestions
    
    def recommend_duplicate_cleanup(self, file_analyses: List[Dict]) -> List[Dict]:
        """Identify potential duplicate files and suggest cleanup actions"""
        duplicates = []
        processed_files = set()
        
        for i, analysis1 in enumerate(file_analyses):
            if i in processed_files:
                continue
                
            filename1 = analysis1.get('filename', '')
            content1 = analysis1.get('extracted_text', '')
            
            potential_duplicates = []
            
            for j, analysis2 in enumerate(file_analyses[i+1:], i+1):
                if j in processed_files:
                    continue
                    
                filename2 = analysis2.get('filename', '')
                content2 = analysis2.get('extracted_text', '')
                
                # Check for filename similarity
                filename_similarity = self._calculate_filename_similarity(filename1, filename2)
                
                # Check for content similarity
                content_similarity = 0
                if content1 and content2:
                    try:
                        tfidf_matrix = self.tfidf_vectorizer.fit_transform([content1, content2])
                        content_similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                    except:
                        pass
                
                # Determine if files are potential duplicates
                if (filename_similarity > 0.8 or content_similarity > 0.9):
                    potential_duplicates.append({
                        'file': analysis2,
                        'filename_similarity': filename_similarity,
                        'content_similarity': content_similarity,
                        'reason': self._get_duplicate_reason(filename_similarity, content_similarity)
                    })
                    processed_files.add(j)
            
            if potential_duplicates:
                duplicates.append({
                    'primary_file': analysis1,
                    'duplicates': potential_duplicates,
                    'recommended_action': 'Review and consider keeping only the most recent version'
                })
                processed_files.add(i)
        
        return duplicates
    
    def recommend_workflow_optimizations(self, user_activities: List[Dict]) -> Dict:
        """Suggest workflow improvements based on user activity patterns"""
        optimizations = {
            'time_management': [],
            'collaboration_tips': [],
            'automation_suggestions': [],
            'productivity_insights': []
        }
        
        # Analyze activity patterns
        activity_times = []
        file_types = []
        collaboration_files = []
        
        for activity in user_activities:
            if activity.get('timestamp'):
                try:
                    hour = datetime.fromisoformat(activity['timestamp']).hour
                    activity_times.append(hour)
                except:
                    continue
            
            if activity.get('file_type'):
                file_types.append(activity['file_type'])
            
            if activity.get('shared_with'):
                collaboration_files.append(activity)
        
        # Time management suggestions
        if activity_times:
            peak_hours = Counter(activity_times).most_common(3)
            optimizations['time_management'].append({
                'insight': f"Most active during hours: {', '.join([f'{h}:00' for h, _ in peak_hours])}",
                'suggestion': 'Schedule important file work during these peak productivity hours'
            })
        
        # File type insights
        if file_types:
            common_types = Counter(file_types).most_common(3)
            optimizations['productivity_insights'].append({
                'insight': f"Most frequently used file types: {', '.join([t for t, _ in common_types])}",
                'suggestion': 'Consider creating templates for these file types to speed up creation'
            })
        
        # Collaboration suggestions
        if collaboration_files:
            optimizations['collaboration_tips'].append({
                'insight': f"Sharing {len(collaboration_files)} files with team members",
                'suggestion': 'Consider setting up shared folders for frequently collaborated files'
            })
        
        return optimizations
    
    def recommend_content_improvements(self, file_analysis: Dict) -> List[Dict]:
        """Suggest improvements for file content quality"""
        suggestions = []
        
        text = file_analysis.get('extracted_text', '')
        if not text:
            return suggestions
        
        # Check readability
        readability_score = file_analysis.get('readability_score', 0)
        if readability_score < 30:
            suggestions.append({
                'type': 'readability',
                'priority': 'high',
                'suggestion': 'Content may be too complex. Consider simplifying language and shortening sentences.',
                'current_score': readability_score
            })
        elif readability_score > 90:
            suggestions.append({
                'type': 'readability',
                'priority': 'medium',
                'suggestion': 'Content might be too simple. Consider adding more detailed explanations.',
                'current_score': readability_score
            })
        
        # Check content length
        word_count = file_analysis.get('word_count', 0)
        if word_count < 100:
            suggestions.append({
                'type': 'content_length',
                'priority': 'medium',
                'suggestion': 'Document is quite short. Consider adding more detail or examples.',
                'current_word_count': word_count
            })
        
        # Check structure
        if '\n\n' not in text and word_count > 200:
            suggestions.append({
                'type': 'structure',
                'priority': 'medium',
                'suggestion': 'Consider breaking content into paragraphs for better readability.'
            })
        
        # Check for missing elements
        entities = file_analysis.get('entities', {})
        if not entities.get('date') and file_analysis.get('category') in ['financial', 'legal', 'research']:
            suggestions.append({
                'type': 'missing_info',
                'priority': 'low',
                'suggestion': 'Consider adding dates for better document tracking and context.'
            })
        
        return suggestions
    
    def _calculate_filename_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two filenames"""
        # Remove extensions and normalize
        base1 = os.path.splitext(name1.lower())[0]
        base2 = os.path.splitext(name2.lower())[0]
        
        # Calculate character-level similarity
        if not base1 or not base2:
            return 0.0
        
        # Simple Jaccard similarity with character n-grams
        ngrams1 = set(base1[i:i+3] for i in range(len(base1)-2))
        ngrams2 = set(base2[i:i+3] for i in range(len(base2)-2))
        
        if not ngrams1 and not ngrams2:
            return 1.0 if base1 == base2 else 0.0
        
        intersection = len(ngrams1.intersection(ngrams2))
        union = len(ngrams1.union(ngrams2))
        
        return intersection / union if union > 0 else 0.0
    
    def _get_duplicate_reason(self, filename_sim: float, content_sim: float) -> str:
        """Generate reason for duplicate detection"""
        if filename_sim > 0.8 and content_sim > 0.9:
            return "Very similar filename and identical content"
        elif filename_sim > 0.8:
            return "Very similar filename"
        elif content_sim > 0.9:
            return "Identical or nearly identical content"
        else:
            return "Potential duplicate detected"
    
    def generate_smart_tags(self, file_analysis: Dict) -> List[str]:
        """Generate intelligent tags for better file organization"""
        tags = set()
        
        # Add category-based tags
        category = file_analysis.get('category', '')
        if category:
            tags.add(category)
        
        # Add entity-based tags
        entities = file_analysis.get('entities', {})
        for entity_type, entity_list in entities.items():
            if entity_list:
                tags.add(f"contains_{entity_type}")
        
        # Add complexity tags
        complexity_score = file_analysis.get('complexity_score', 0)
        if complexity_score > 70:
            tags.add('complex')
        elif complexity_score < 30:
            tags.add('simple')
        
        # Add length tags
        word_count = file_analysis.get('word_count', 0)
        if word_count > 2000:
            tags.add('long_document')
        elif word_count < 200:
            tags.add('short_document')
        
        # Add sentiment tags
        sentiment = file_analysis.get('sentiment', {})
        if sentiment.get('sentiment') in ['positive', 'negative']:
            tags.add(f"{sentiment['sentiment']}_tone")
        
        # Add topic-based tags from key topics
        key_topics = file_analysis.get('key_topics', [])[:5]  # Top 5 topics
        for topic in key_topics:
            # Clean and add topic as tag
            clean_topic = re.sub(r'[^a-zA-Z0-9]', '_', topic.lower())
            if len(clean_topic) > 2:
                tags.add(clean_topic)
        
        return sorted(list(tags))


def create_recommendation_engine():
    """Factory function to create recommendation engine"""
    return SmartRecommendationEngine()
