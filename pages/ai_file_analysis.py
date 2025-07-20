# AI File Analysis System
import os
import hashlib
import mimetypes
import logging
from collections import Counter
from datetime import datetime, timedelta
from django.conf import settings
from django.core.files.storage import default_storage
from .models import FileDocument, AIFileAnalysis
from .ai_analysis import ResumeAnalyzer
from .ai_recommendations import SmartRecommendationEngine
from .ai_knowledge_graph import KnowledgeGraph
from .ai_content_generator import ContentGenerationEngine
from .ai_predictive_analytics import PredictiveAnalyticsEngine

logger = logging.getLogger(__name__)

class AIFileAnalyzer:
    """
    Enhanced file analyzer integrated with Django models
    """
    
    def __init__(self):
        self.file_analyzer = ResumeAnalyzer()  # Can be used for general file analysis
        self.recommendation_engine = SmartRecommendationEngine()
        self.knowledge_graph = KnowledgeGraph()
        self.content_generator = ContentGenerationEngine()
        self.predictive_analytics = PredictiveAnalyticsEngine()
    
    def analyze_file(self, file_document):
        """
        Comprehensive file analysis integrated with Django models
        """
        try:
            # Get or create analysis record
            analysis, created = AIFileAnalysis.objects.get_or_create(
                file=file_document,
                defaults={'status': 'processing'}
            )
            
            if not created and analysis.status == 'completed':
                # Return existing analysis if already completed
                return analysis
            
            # Start analysis
            analysis.status = 'processing'
            analysis.save()
            
            # Get file path
            file_path = file_document.file.path if hasattr(file_document.file, 'path') else None
            
            if file_path and os.path.exists(file_path):
                # Analyze file content
                file_analysis = self._analyze_file_content(file_path)
                
                # Extract metadata
                metadata = self._extract_metadata(file_document, file_path)
                
                # Generate tags
                tags = self._generate_tags(file_analysis, metadata)
                
                # Calculate similarity scores with other files
                similarity_scores = self._calculate_similarity_scores(file_document, file_analysis)
                
                # Generate recommendations
                recommendations = self._generate_recommendations(file_document, file_analysis)
                
                # Update analysis record
                analysis.analysis_data = {
                    'file_analysis': file_analysis,
                    'metadata': metadata,
                    'tags': tags,
                    'similarity_scores': similarity_scores,
                    'recommendations': recommendations
                }
                analysis.tags = tags
                analysis.status = 'completed'
                analysis.save()
                
                # Update knowledge graph
                self._update_knowledge_graph(file_document, analysis)
                
            else:
                analysis.status = 'failed'
                analysis.error_message = 'File not found or inaccessible'
                analysis.save()
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_document.id}: {str(e)}")
            if 'analysis' in locals():
                analysis.status = 'failed'
                analysis.error_message = str(e)
                analysis.save()
            return None
    
    def _analyze_file_content(self, file_path):
        """Analyze file content based on file type"""
        try:
            _, ext = os.path.splitext(file_path.lower())
            
            # Initialize basic analysis structure
            analysis = {
                'file_type': ext,
                'keywords': [],
                'content_summary': '',
                'file_size': os.path.getsize(file_path),
                'analysis_type': 'general'
            }
            
            if ext in ['.pdf', '.doc', '.docx']:
                # Extract text content
                if ext == '.pdf':
                    text_content = self.file_analyzer.extract_text_from_pdf(file_path)
                elif ext == '.docx':
                    text_content = self.file_analyzer.extract_text_from_docx(file_path)
                else:
                    # For .doc files, just mark as document
                    text_content = ""
                
                if text_content:
                    # Process text content
                    processed_text = self.file_analyzer.preprocess_text(text_content)
                    
                    # Extract keywords (simple approach)
                    words = processed_text.split()
                    word_freq = Counter(words)
                    analysis['keywords'] = [word for word, count in word_freq.most_common(20)]
                    analysis['content_summary'] = text_content[:500] + "..." if len(text_content) > 500 else text_content
                    analysis['word_count'] = len(words)
                    
                    # Check if it's a resume
                    if any(keyword in text_content.lower() for keyword in ['resume', 'cv', 'experience', 'education', 'skills']):
                        analysis['analysis_type'] = 'resume'
                        # Use resume-specific analysis
                        skills = self.file_analyzer.extract_skills(text_content)
                        analysis['skills'] = skills
                
                analysis['has_text_content'] = True
                
            elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                analysis['analysis_type'] = 'image'
                analysis['has_text_content'] = False
                # Could add image analysis here in the future
                
            elif ext in ['.mp4', '.avi', '.mov', '.wmv']:
                analysis['analysis_type'] = 'video'
                analysis['has_text_content'] = False
                
            elif ext in ['.mp3', '.wav', '.flac']:
                analysis['analysis_type'] = 'audio'
                analysis['has_text_content'] = False
                
            else:
                analysis['analysis_type'] = 'unknown'
                analysis['has_text_content'] = False
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing file content: {str(e)}")
            return {
                'file_type': 'unknown',
                'keywords': [],
                'content_summary': '',
                'analysis_type': 'error',
                'error': str(e)
            }
    
    def _extract_metadata(self, file_document, file_path):
        """Extract comprehensive metadata from file"""
        try:
            stat = os.stat(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            
            # Calculate file hash
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            metadata = {
                'filename': file_document.file.name,
                'size': stat.st_size,
                'mime_type': mime_type,
                'created_date': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_date': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'file_hash': file_hash,
                'uploaded_by': file_document.uploaded_by.username if file_document.uploaded_by else None,
                'upload_date': file_document.created_at.isoformat() if hasattr(file_document, 'created_at') else None
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            return {}
    
    def _generate_tags(self, file_analysis, metadata):
        """Generate relevant tags for the file"""
        tags = []
        
        # Tags from file analysis
        if 'keywords' in file_analysis:
            tags.extend(file_analysis['keywords'][:10])  # Top 10 keywords
        
        # Tags from mime type
        if metadata.get('mime_type'):
            mime_type = metadata['mime_type']
            if 'image' in mime_type:
                tags.append('image')
            elif 'document' in mime_type or 'pdf' in mime_type:
                tags.append('document')
            elif 'video' in mime_type:
                tags.append('video')
            elif 'audio' in mime_type:
                tags.append('audio')
        
        # Tags from filename
        filename = metadata.get('filename', '').lower()
        if 'resume' in filename or 'cv' in filename:
            tags.append('resume')
        if 'report' in filename:
            tags.append('report')
        if 'presentation' in filename or 'ppt' in filename:
            tags.append('presentation')
        
        # Remove duplicates and limit
        tags = list(set(tags))[:15]
        
        return tags
    
    def _calculate_similarity_scores(self, current_file, file_analysis):
        """Calculate similarity with other files"""
        try:
            similarity_scores = []
            
            # Get other analyzed files
            other_analyses = AIFileAnalysis.objects.filter(
                status='completed'
            ).exclude(file=current_file)[:50]  # Limit for performance
            
            for other_analysis in other_analyses:
                try:
                    if other_analysis.analysis_data and 'file_analysis' in other_analysis.analysis_data:
                        other_file_analysis = other_analysis.analysis_data['file_analysis']
                        
                        # Calculate content similarity
                        similarity = self._calculate_content_similarity(
                            file_analysis, 
                            other_file_analysis
                        )
                        
                        if similarity > 0.1:  # Only keep significant similarities
                            similarity_scores.append({
                                'file_id': other_analysis.file.id,
                                'filename': other_analysis.file.file.name,
                                'similarity': similarity
                            })
                except Exception as e:
                    logger.error(f"Error calculating similarity with file {other_analysis.file.id}: {str(e)}")
                    continue
            
            # Sort by similarity
            similarity_scores.sort(key=lambda x: x['similarity'], reverse=True)
            
            return similarity_scores[:10]  # Top 10 similar files
            
        except Exception as e:
            logger.error(f"Error calculating similarity scores: {str(e)}")
            return []
    
    def _calculate_content_similarity(self, analysis1, analysis2):
        """Calculate similarity between two file analyses"""
        try:
            # Simple keyword-based similarity
            keywords1 = set(analysis1.get('keywords', []))
            keywords2 = set(analysis2.get('keywords', []))
            
            if not keywords1 or not keywords2:
                return 0.0
            
            intersection = keywords1.intersection(keywords2)
            union = keywords1.union(keywords2)
            
            return len(intersection) / len(union) if union else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating content similarity: {str(e)}")
            return 0.0
    
    def _generate_recommendations(self, file_document, file_analysis):
        """Generate AI-powered recommendations"""
        try:
            recommendations = []
            
            # Get user's file history for context
            user_files = FileDocument.objects.filter(
                uploaded_by=file_document.uploaded_by
            ).exclude(id=file_document.id)[:20]
            
            user_context = {
                'file_count': user_files.count(),
                'recent_files': [f.file.name for f in user_files[:5]],
                'file_types': list(set([f.file.name.split('.')[-1].lower() for f in user_files if '.' in f.file.name]))
            }
            
            # Generate recommendations using AI engine
            ai_recommendations = self.recommendation_engine.generate_recommendations(
                file_analysis, 
                user_context
            )
            
            # Convert to structured format
            for rec in ai_recommendations:
                recommendations.append({
                    'type': rec.get('type', 'general'),
                    'title': rec.get('title', 'Recommendation'),
                    'description': rec.get('description', ''),
                    'priority': rec.get('priority', 'medium'),
                    'action': rec.get('action', '')
                })
            
            return recommendations[:5]  # Limit to top 5
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    def _update_knowledge_graph(self, file_document, analysis):
        """Update the knowledge graph with file information"""
        try:
            # Prepare file information for knowledge graph
            file_info = {
                'id': f"file_{file_document.id}",
                'type': 'file',
                'name': file_document.file.name,
                'tags': analysis.tags,
                'uploaded_by': file_document.uploaded_by.username if file_document.uploaded_by else None
            }
            
            # Add to knowledge graph
            self.knowledge_graph.add_entity(file_info)
            
            # Create relationships with similar files
            if analysis.analysis_data and 'similarity_scores' in analysis.analysis_data:
                for similar_file in analysis.analysis_data['similarity_scores']:
                    if similar_file['similarity'] > 0.3:  # Strong similarity
                        self.knowledge_graph.add_relationship(
                            file_info['id'],
                            f"file_{similar_file['file_id']}",
                            'similar_to',
                            weight=similar_file['similarity']
                        )
            
        except Exception as e:
            logger.error(f"Error updating knowledge graph: {str(e)}")
    
    def get_file_insights(self, file_document):
        """Get comprehensive insights for a file"""
        try:
            analysis = AIFileAnalysis.objects.filter(file=file_document).first()
            
            if not analysis or analysis.status != 'completed':
                return None
            
            insights = {
                'analysis': analysis.analysis_data,
                'tags': analysis.tags,
                'status': analysis.status,
                'analyzed_at': analysis.analyzed_at,
                'suggestions': self._generate_usage_suggestions(analysis),
                'related_files': self._get_related_files(file_document, analysis)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting file insights: {str(e)}")
            return None
    
    def _generate_usage_suggestions(self, analysis):
        """Generate suggestions for file usage"""
        suggestions = []
        
        if analysis.analysis_data:
            # Analyze file type and content to suggest usage
            file_analysis = analysis.analysis_data.get('file_analysis', {})
            metadata = analysis.analysis_data.get('metadata', {})
            
            mime_type = metadata.get('mime_type', '')
            
            if 'pdf' in mime_type.lower() or 'document' in mime_type.lower():
                suggestions.append("Consider adding this document to a knowledge base for future reference")
                suggestions.append("Extract key information for quick summaries")
            
            if 'image' in mime_type.lower():
                suggestions.append("Add descriptive tags for better organization")
                suggestions.append("Consider creating image galleries or presentations")
            
            if 'resume' in analysis.tags:
                suggestions.append("Review candidate qualifications")
                suggestions.append("Add to recruitment pipeline")
            
        return suggestions
    
    def _get_related_files(self, file_document, analysis):
        """Get files related to the current file"""
        related_files = []
        
        if analysis.analysis_data and 'similarity_scores' in analysis.analysis_data:
            similarity_scores = analysis.analysis_data['similarity_scores']
            
            for similar_file in similarity_scores[:5]:  # Top 5 related files
                try:
                    related_doc = FileDocument.objects.get(id=similar_file['file_id'])
                    related_files.append({
                        'id': related_doc.id,
                        'name': related_doc.file.name,
                        'similarity': similar_file['similarity'],
                        'uploaded_by': related_doc.uploaded_by.username if related_doc.uploaded_by else None
                    })
                except FileDocument.DoesNotExist:
                    continue
        
        return related_files
    
    def bulk_analyze_files(self, queryset=None):
        """Analyze multiple files in bulk"""
        if queryset is None:
            # Analyze unanalyzed files
            analyzed_file_ids = AIFileAnalysis.objects.values_list('file_id', flat=True)
            queryset = FileDocument.objects.exclude(id__in=analyzed_file_ids)
        
        results = {
            'total': queryset.count(),
            'processed': 0,
            'failed': 0,
            'errors': []
        }
        
        for file_doc in queryset:
            try:
                analysis = self.analyze_file(file_doc)
                if analysis and analysis.status == 'completed':
                    results['processed'] += 1
                else:
                    results['failed'] += 1
                    if analysis and analysis.error_message:
                        results['errors'].append(f"File {file_doc.id}: {analysis.error_message}")
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"File {file_doc.id}: {str(e)}")
        
        return results

# Convenience function for getting the analyzer instance
def get_ai_file_analyzer():
    """Get AI file analyzer instance"""
    return AIFileAnalyzer()
