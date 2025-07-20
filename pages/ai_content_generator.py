"""
AI-Powered Content Generation and Advanced Summarization Engine
Generates intelligent content, meeting notes, reports, and advanced summaries
"""

import os
import re
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import json
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np


class ContentGenerationEngine:
    """AI-powered content generation and advanced summarization"""
    
    def __init__(self):
        self.template_library = self._load_templates()
        self.writing_patterns = {}
        self.content_history = []
        
    def _load_templates(self) -> Dict:
        """Load content generation templates"""
        return {
            'meeting_notes': {
                'structure': [
                    'Meeting Overview',
                    'Attendees',
                    'Key Discussion Points',
                    'Decisions Made',
                    'Action Items',
                    'Next Steps'
                ],
                'prompts': {
                    'overview': 'What was the main purpose of this meeting?',
                    'decisions': 'What decisions were made during the meeting?',
                    'actions': 'What action items were assigned?'
                }
            },
            'project_report': {
                'structure': [
                    'Executive Summary',
                    'Project Objectives',
                    'Current Status',
                    'Key Achievements',
                    'Challenges and Risks',
                    'Next Phase Planning',
                    'Resource Requirements',
                    'Conclusion'
                ],
                'prompts': {
                    'status': 'What is the current status of the project?',
                    'achievements': 'What are the key accomplishments?',
                    'challenges': 'What challenges have been encountered?'
                }
            },
            'document_summary': {
                'structure': [
                    'Document Overview',
                    'Key Points',
                    'Important Details',
                    'Conclusions',
                    'Recommendations'
                ],
                'prompts': {
                    'overview': 'What is this document about?',
                    'key_points': 'What are the main points?',
                    'conclusions': 'What conclusions are drawn?'
                }
            },
            'email_draft': {
                'structure': [
                    'Subject Line',
                    'Greeting',
                    'Context/Purpose',
                    'Main Content',
                    'Call to Action',
                    'Closing'
                ],
                'prompts': {
                    'purpose': 'What is the purpose of this email?',
                    'action': 'What action do you want the recipient to take?'
                }
            }
        }
    
    def generate_meeting_notes(self, meeting_data: Dict) -> Dict:
        """Generate structured meeting notes from raw input"""
        notes = {
            'title': meeting_data.get('title', 'Meeting Notes'),
            'date': meeting_data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'duration': meeting_data.get('duration', 'Not specified'),
            'generated_content': {},
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'content_type': 'meeting_notes'
            }
        }
        
        # Extract attendees
        attendees_text = meeting_data.get('attendees', '')
        notes['attendees'] = self._extract_attendees(attendees_text)
        
        # Process meeting content
        content = meeting_data.get('content', '')
        if content:
            notes['generated_content'] = self._process_meeting_content(content)
        
        # Generate action items
        notes['action_items'] = self._extract_action_items(content)
        
        # Generate summary
        notes['summary'] = self._generate_meeting_summary(content, notes)
        
        return notes
    
    def generate_project_report(self, project_data: Dict) -> Dict:
        """Generate comprehensive project report"""
        report = {
            'title': project_data.get('title', 'Project Report'),
            'project_name': project_data.get('project_name', 'Unnamed Project'),
            'report_date': datetime.now().strftime('%Y-%m-%d'),
            'sections': {},
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'content_type': 'project_report'
            }
        }
        
        # Generate executive summary
        report['sections']['executive_summary'] = self._generate_executive_summary(project_data)
        
        # Process project status
        status_data = project_data.get('status_updates', [])
        report['sections']['status_analysis'] = self._analyze_project_status(status_data)
        
        # Generate achievements section
        achievements = project_data.get('achievements', [])
        report['sections']['achievements'] = self._format_achievements(achievements)
        
        # Risk analysis
        risks = project_data.get('risks', [])
        report['sections']['risk_analysis'] = self._analyze_risks(risks)
        
        # Resource analysis
        resources = project_data.get('resources', {})
        report['sections']['resource_analysis'] = self._analyze_resources(resources)
        
        # Generate recommendations
        report['sections']['recommendations'] = self._generate_recommendations(project_data)
        
        return report
    
    def create_document_summary(self, file_analysis: Dict, summary_type: str = 'standard') -> Dict:
        """Create advanced document summary with different types"""
        text = file_analysis.get('extracted_text', '')
        if not text:
            return {'error': 'No text content available for summarization'}
        
        summary = {
            'document_title': file_analysis.get('filename', 'Unknown Document'),
            'summary_type': summary_type,
            'generated_at': datetime.now().isoformat(),
            'word_count': file_analysis.get('word_count', 0),
            'original_complexity': file_analysis.get('complexity_score', 0)
        }
        
        if summary_type == 'executive':
            summary['content'] = self._create_executive_summary(text, file_analysis)
        elif summary_type == 'technical':
            summary['content'] = self._create_technical_summary(text, file_analysis)
        elif summary_type == 'bullet_points':
            summary['content'] = self._create_bullet_summary(text, file_analysis)
        elif summary_type == 'abstract':
            summary['content'] = self._create_abstract_summary(text, file_analysis)
        else:  # standard
            summary['content'] = self._create_standard_summary(text, file_analysis)
        
        # Add metadata
        summary['key_insights'] = self._extract_key_insights(text, file_analysis)
        summary['readability_improvement'] = self._calculate_readability_improvement(file_analysis, summary)
        
        return summary
    
    def generate_email_draft(self, email_data: Dict) -> Dict:
        """Generate professional email draft"""
        draft = {
            'generated_at': datetime.now().isoformat(),
            'content_type': 'email_draft',
            'metadata': {}
        }
        
        # Generate subject line
        purpose = email_data.get('purpose', '')
        context = email_data.get('context', '')
        
        draft['subject'] = self._generate_subject_line(purpose, context, email_data.get('urgency', 'normal'))
        
        # Generate greeting
        recipient = email_data.get('recipient', 'Team')
        formality = email_data.get('formality', 'professional')
        draft['greeting'] = self._generate_greeting(recipient, formality)
        
        # Generate main content
        draft['content'] = self._generate_email_content(email_data)
        
        # Generate call to action
        action_needed = email_data.get('action_needed', '')
        draft['call_to_action'] = self._generate_call_to_action(action_needed, email_data.get('deadline'))
        
        # Generate closing
        draft['closing'] = self._generate_email_closing(formality)
        
        # Combine into full email
        draft['full_email'] = self._combine_email_parts(draft)
        
        return draft
    
    def create_content_from_template(self, template_name: str, data: Dict) -> Dict:
        """Create content using predefined templates"""
        if template_name not in self.template_library:
            return {'error': f'Template {template_name} not found'}
        
        template = self.template_library[template_name]
        
        content = {
            'template_used': template_name,
            'generated_at': datetime.now().isoformat(),
            'sections': {}
        }
        
        # Generate content for each section
        for section in template['structure']:
            section_key = section.lower().replace(' ', '_')
            content['sections'][section_key] = self._generate_section_content(
                section, data, template.get('prompts', {})
            )
        
        return content
    
    def analyze_writing_style(self, text: str) -> Dict:
        """Analyze writing style and provide improvement suggestions"""
        analysis = {
            'style_metrics': {},
            'suggestions': [],
            'readability': {},
            'tone_analysis': {}
        }
        
        # Basic style metrics
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        words = text.split()
        
        if not words or not sentences:
            return analysis
        
        # Calculate metrics
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Vocabulary diversity
        unique_words = len(set(word.lower() for word in words))
        vocab_diversity = unique_words / len(words)
        
        analysis['style_metrics'] = {
            'avg_sentence_length': round(avg_sentence_length, 1),
            'avg_word_length': round(avg_word_length, 1),
            'vocabulary_diversity': round(vocab_diversity, 3),
            'total_sentences': len(sentences),
            'total_words': len(words)
        }
        
        # Generate suggestions
        suggestions = []
        
        if avg_sentence_length > 25:
            suggestions.append({
                'type': 'sentence_length',
                'issue': 'Sentences are too long',
                'suggestion': 'Break long sentences into shorter, clearer ones',
                'priority': 'high'
            })
        elif avg_sentence_length < 10:
            suggestions.append({
                'type': 'sentence_length',
                'issue': 'Sentences are too short',
                'suggestion': 'Consider combining related short sentences',
                'priority': 'medium'
            })
        
        if vocab_diversity < 0.3:
            suggestions.append({
                'type': 'vocabulary',
                'issue': 'Limited vocabulary diversity',
                'suggestion': 'Use more varied vocabulary to improve engagement',
                'priority': 'medium'
            })
        
        if avg_word_length > 6:
            suggestions.append({
                'type': 'word_complexity',
                'issue': 'Words are too complex',
                'suggestion': 'Use simpler words for better readability',
                'priority': 'medium'
            })
        
        analysis['suggestions'] = suggestions
        
        # Readability analysis
        analysis['readability'] = self._calculate_readability_metrics(text)
        
        # Tone analysis
        analysis['tone_analysis'] = self._analyze_writing_tone(text)
        
        return analysis
    
    def _extract_attendees(self, attendees_text: str) -> List[str]:
        """Extract attendees from text"""
        if not attendees_text:
            return []
        
        # Split by common delimiters
        attendees = re.split(r'[,;\\n]', attendees_text)
        attendees = [name.strip() for name in attendees if name.strip()]
        
        # Clean up names
        cleaned_attendees = []
        for attendee in attendees:
            # Remove common prefixes and clean
            clean_name = re.sub(r'^(mr\.|mrs\.|ms\.|dr\.|prof\.)\s*', '', attendee.lower())
            clean_name = clean_name.strip().title()
            if clean_name and len(clean_name) > 1:
                cleaned_attendees.append(clean_name)
        
        return cleaned_attendees
    
    def _process_meeting_content(self, content: str) -> Dict:
        """Process meeting content into structured sections"""
        sections = {
            'discussion_points': [],
            'decisions': [],
            'questions_raised': [],
            'next_steps': []
        }
        
        # Split content into paragraphs
        paragraphs = [p.strip() for p in content.split('\\n\\n') if p.strip()]
        
        for paragraph in paragraphs:
            # Classify paragraph content
            lower_para = paragraph.lower()
            
            if any(word in lower_para for word in ['decided', 'agreed', 'concluded', 'resolution']):
                sections['decisions'].append(paragraph)
            elif any(word in lower_para for word in ['question', 'ask', 'unclear', 'clarify']):
                sections['questions_raised'].append(paragraph)
            elif any(word in lower_para for word in ['next', 'follow', 'action', 'todo', 'will']):
                sections['next_steps'].append(paragraph)
            else:
                sections['discussion_points'].append(paragraph)
        
        return sections
    
    def _extract_action_items(self, content: str) -> List[Dict]:
        """Extract action items from meeting content"""
        action_items = []
        
        # Look for action-oriented sentences
        sentences = re.split(r'[.!?]+', content)
        
        action_keywords = [
            'will', 'should', 'must', 'need to', 'todo', 'action',
            'follow up', 'complete', 'finish', 'deliver', 'submit'
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            lower_sentence = sentence.lower()
            
            # Check if sentence contains action keywords
            if any(keyword in lower_sentence for keyword in action_keywords):
                # Try to extract assignee and deadline
                assignee = self._extract_assignee(sentence)
                deadline = self._extract_deadline(sentence)
                
                action_items.append({
                    'description': sentence,
                    'assignee': assignee,
                    'deadline': deadline,
                    'status': 'pending',
                    'priority': self._determine_priority(sentence)
                })
        
        return action_items
    
    def _generate_meeting_summary(self, content: str, notes: Dict) -> str:
        """Generate concise meeting summary"""
        summary_parts = []
        
        # Add meeting basics
        summary_parts.append(f"Meeting held on {notes.get('date', 'unknown date')}")
        
        attendees = notes.get('attendees', [])
        if attendees:
            if len(attendees) <= 3:
                summary_parts.append(f"with {', '.join(attendees)}")
            else:
                summary_parts.append(f"with {len(attendees)} attendees")
        
        # Add key points
        generated_content = notes.get('generated_content', {})
        decisions = generated_content.get('decisions', [])
        if decisions:
            summary_parts.append(f"Key decisions: {len(decisions)} decisions made")
        
        action_items = notes.get('action_items', [])
        if action_items:
            summary_parts.append(f"Action items: {len(action_items)} tasks assigned")
        
        return '. '.join(summary_parts) + '.'
    
    def _generate_executive_summary(self, project_data: Dict) -> str:
        """Generate executive summary for project report"""
        summary_parts = []
        
        project_name = project_data.get('project_name', 'the project')
        status = project_data.get('current_status', 'ongoing')
        
        summary_parts.append(f"This report provides an overview of {project_name}")
        summary_parts.append(f"Current status: {status}")
        
        # Add key metrics if available
        if 'completion_percentage' in project_data:
            completion = project_data['completion_percentage']
            summary_parts.append(f"Project is {completion}% complete")
        
        if 'budget_status' in project_data:
            budget = project_data['budget_status']
            summary_parts.append(f"Budget status: {budget}")
        
        return '. '.join(summary_parts) + '.'
    
    def _create_executive_summary(self, text: str, file_analysis: Dict) -> Dict:
        """Create executive-style summary"""
        summary = {
            'type': 'executive',
            'target_audience': 'senior management',
            'focus': 'key decisions and outcomes'
        }
        
        # Extract key points for executives
        sentences = re.split(r'[.!?]+', text)
        key_sentences = []
        
        executive_keywords = [
            'revenue', 'profit', 'cost', 'budget', 'strategy', 'risk',
            'opportunity', 'growth', 'market', 'customer', 'competitive',
            'recommend', 'decision', 'impact', 'result', 'outcome'
        ]
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in executive_keywords):
                key_sentences.append(sentence.strip())
        
        summary['content'] = '. '.join(key_sentences[:3]) + '.' if key_sentences else text[:300] + '...'
        
        return summary
    
    def _create_technical_summary(self, text: str, file_analysis: Dict) -> Dict:
        """Create technical summary focusing on methodology and details"""
        summary = {
            'type': 'technical',
            'target_audience': 'technical team',
            'focus': 'methodology and implementation details'
        }
        
        technical_keywords = [
            'method', 'process', 'system', 'algorithm', 'implementation',
            'architecture', 'design', 'specification', 'requirement',
            'technical', 'configuration', 'parameter', 'function'
        ]
        
        sentences = re.split(r'[.!?]+', text)
        technical_sentences = []
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in technical_keywords):
                technical_sentences.append(sentence.strip())
        
        summary['content'] = '. '.join(technical_sentences[:4]) + '.' if technical_sentences else text[:400] + '...'
        
        return summary
    
    def _create_bullet_summary(self, text: str, file_analysis: Dict) -> Dict:
        """Create bullet-point summary"""
        summary = {
            'type': 'bullet_points',
            'target_audience': 'general audience',
            'focus': 'key points in easy-to-read format'
        }
        
        # Extract key sentences and convert to bullet points
        sentences = re.split(r'[.!?]+', text)
        key_topics = file_analysis.get('key_topics', [])
        
        bullets = []
        
        # Use key topics as bullet points
        for topic in key_topics[:5]:
            # Find sentence containing this topic
            for sentence in sentences:
                if topic.lower() in sentence.lower():
                    bullets.append(f"• {sentence.strip()}")
                    break
        
        if not bullets:
            # Fallback: use first few sentences as bullets
            for sentence in sentences[:4]:
                if len(sentence.strip()) > 10:
                    bullets.append(f"• {sentence.strip()}")
        
        summary['content'] = '\\n'.join(bullets)
        
        return summary
    
    def _create_abstract_summary(self, text: str, file_analysis: Dict) -> Dict:
        """Create academic-style abstract"""
        summary = {
            'type': 'abstract',
            'target_audience': 'researchers/academics',
            'focus': 'objective and methodology'
        }
        
        # Structure: Background, Objective, Method, Results, Conclusion
        abstract_parts = []
        
        category = file_analysis.get('category', 'document')
        abstract_parts.append(f"This {category} presents")
        
        # Add key findings
        key_topics = file_analysis.get('key_topics', [])
        if key_topics:
            abstract_parts.append(f"key areas including {', '.join(key_topics[:3])}")
        
        # Add methodology if technical
        if 'method' in text.lower() or 'approach' in text.lower():
            abstract_parts.append("The methodology involves systematic analysis")
        
        summary['content'] = '. '.join(abstract_parts) + '.'
        
        return summary
    
    def _create_standard_summary(self, text: str, file_analysis: Dict) -> Dict:
        """Create standard summary"""
        summary = {
            'type': 'standard',
            'target_audience': 'general audience',
            'focus': 'balanced overview'
        }
        
        # Use existing summary if available, enhance it
        existing_summary = file_analysis.get('summary', '')
        if existing_summary and len(existing_summary) > 50:
            summary['content'] = existing_summary
        else:
            # Create new summary
            sentences = re.split(r'[.!?]+', text)
            summary['content'] = '. '.join(sentences[:3]) + '.' if sentences else 'No summary available.'
        
        return summary
    
    def _extract_key_insights(self, text: str, file_analysis: Dict) -> List[str]:
        """Extract key insights from document"""
        insights = []
        
        # Add complexity insight
        complexity = file_analysis.get('complexity_score', 0)
        if complexity > 70:
            insights.append("Document contains complex technical content")
        elif complexity < 30:
            insights.append("Document is written in simple, accessible language")
        
        # Add sentiment insight
        sentiment = file_analysis.get('sentiment', {})
        if sentiment.get('sentiment') == 'positive':
            insights.append("Overall positive tone throughout the document")
        elif sentiment.get('sentiment') == 'negative':
            insights.append("Document expresses concerns or negative sentiments")
        
        # Add entity insights
        entities = file_analysis.get('entities', {})
        if entities.get('email'):
            insights.append("Contains contact information and email addresses")
        if entities.get('date'):
            insights.append("References specific dates and timeframes")
        if entities.get('currency'):
            insights.append("Includes financial information and monetary amounts")
        
        return insights
    
    def _calculate_readability_improvement(self, original_analysis: Dict, summary: Dict) -> Dict:
        """Calculate how much the summary improves readability"""
        original_readability = original_analysis.get('readability_score', 0)
        original_complexity = original_analysis.get('complexity_score', 0)
        
        # Estimate summary readability (summaries are typically more readable)
        estimated_summary_readability = min(100, original_readability + 20)
        estimated_summary_complexity = max(0, original_complexity - 15)
        
        return {
            'readability_improvement': estimated_summary_readability - original_readability,
            'complexity_reduction': original_complexity - estimated_summary_complexity,
            'word_count_reduction': original_analysis.get('word_count', 0) - len(summary.get('content', '').split())
        }
    
    def _generate_subject_line(self, purpose: str, context: str, urgency: str) -> str:
        """Generate email subject line"""
        if urgency == 'urgent':
            prefix = '[URGENT] '
        elif urgency == 'high':
            prefix = '[Important] '
        else:
            prefix = ''
        
        if purpose:
            return f"{prefix}{purpose.title()}"
        else:
            return f"{prefix}Follow-up Required"
    
    def _generate_greeting(self, recipient: str, formality: str) -> str:
        """Generate appropriate email greeting"""
        if formality == 'formal':
            return f"Dear {recipient},"
        elif formality == 'casual':
            return f"Hi {recipient},"
        else:  # professional
            return f"Hello {recipient},"
    
    def _generate_email_content(self, email_data: Dict) -> str:
        """Generate main email content"""
        content_parts = []
        
        # Context
        context = email_data.get('context', '')
        if context:
            content_parts.append(f"I wanted to follow up regarding {context}.")
        
        # Main message
        message = email_data.get('message', '')
        if message:
            content_parts.append(message)
        else:
            content_parts.append("Please see the details below:")
        
        # Additional details
        details = email_data.get('details', [])
        if details:
            content_parts.append("")  # Empty line
            for detail in details:
                content_parts.append(f"• {detail}")
        
        return "\\n\\n".join(content_parts)
    
    def _generate_call_to_action(self, action_needed: str, deadline: str) -> str:
        """Generate call to action"""
        if not action_needed:
            return "Please let me know if you have any questions."
        
        cta = f"Please {action_needed}"
        
        if deadline:
            cta += f" by {deadline}"
        
        return cta + "."
    
    def _generate_email_closing(self, formality: str) -> str:
        """Generate email closing"""
        if formality == 'formal':
            return "Sincerely,"
        elif formality == 'casual':
            return "Thanks,"
        else:  # professional
            return "Best regards,"
    
    def _combine_email_parts(self, draft: Dict) -> str:
        """Combine email parts into full email"""
        parts = [
            f"Subject: {draft.get('subject', '')}",
            "",
            draft.get('greeting', ''),
            "",
            draft.get('content', ''),
            "",
            draft.get('call_to_action', ''),
            "",
            draft.get('closing', ''),
            "[Your Name]"
        ]
        
        return "\\n".join(parts)
    
    def _generate_section_content(self, section: str, data: Dict, prompts: Dict) -> str:
        """Generate content for a specific section"""
        section_key = section.lower().replace(' ', '_')
        
        # Check if data has specific content for this section
        if section_key in data:
            return str(data[section_key])
        
        # Generate based on section type
        if 'overview' in section.lower():
            return f"This section provides an overview of {data.get('subject', 'the topic')}."
        elif 'objectives' in section.lower():
            return "Key objectives include achieving stated goals and deliverables."
        elif 'status' in section.lower():
            return f"Current status: {data.get('status', 'In progress')}."
        elif 'next' in section.lower():
            return "Next steps will be determined based on current progress."
        else:
            return f"[Content for {section} to be added]"
    
    def _extract_assignee(self, sentence: str) -> Optional[str]:
        """Extract assignee from action item sentence"""
        # Look for patterns like "John will", "assigned to Mary", etc.
        patterns = [
            r'(\w+)\s+will\s+',
            r'assigned\s+to\s+(\w+)',
            r'(\w+)\s+should\s+',
            r'(\w+)\s+needs?\s+to\s+'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                return match.group(1).title()
        
        return None
    
    def _extract_deadline(self, sentence: str) -> Optional[str]:
        """Extract deadline from action item sentence"""
        # Look for date patterns
        date_patterns = [
            r'by\s+(\w+\s+\d{1,2})',
            r'deadline\s+(\w+\s+\d{1,2})',
            r'due\s+(\w+\s+\d{1,2})',
            r'(\d{1,2}/\d{1,2}/\d{2,4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _determine_priority(self, sentence: str) -> str:
        """Determine priority of action item"""
        urgent_keywords = ['urgent', 'asap', 'immediately', 'critical', 'high priority']
        low_keywords = ['when possible', 'low priority', 'eventually', 'if time permits']
        
        sentence_lower = sentence.lower()
        
        if any(keyword in sentence_lower for keyword in urgent_keywords):
            return 'high'
        elif any(keyword in sentence_lower for keyword in low_keywords):
            return 'low'
        else:
            return 'medium'
    
    def _analyze_project_status(self, status_updates: List[Dict]) -> Dict:
        """Analyze project status from updates"""
        if not status_updates:
            return {'message': 'No status updates available'}
        
        # Analyze trends
        analysis = {
            'total_updates': len(status_updates),
            'latest_update': status_updates[-1] if status_updates else None,
            'trend_analysis': {},
            'key_milestones': []
        }
        
        # Look for milestone mentions
        for update in status_updates:
            content = update.get('content', '').lower()
            if any(word in content for word in ['completed', 'finished', 'delivered', 'milestone']):
                analysis['key_milestones'].append(update)
        
        return analysis
    
    def _format_achievements(self, achievements: List) -> Dict:
        """Format achievements section"""
        if not achievements:
            return {'message': 'No achievements recorded'}
        
        return {
            'count': len(achievements),
            'highlights': achievements[:5],  # Top 5 achievements
            'summary': f"{len(achievements)} key achievements accomplished"
        }
    
    def _analyze_risks(self, risks: List) -> Dict:
        """Analyze project risks"""
        if not risks:
            return {'message': 'No risks identified'}
        
        risk_levels = {'high': [], 'medium': [], 'low': []}
        
        for risk in risks:
            level = risk.get('level', 'medium').lower()
            if level in risk_levels:
                risk_levels[level].append(risk)
        
        return {
            'total_risks': len(risks),
            'breakdown': {level: len(risk_list) for level, risk_list in risk_levels.items()},
            'high_priority_risks': risk_levels['high']
        }
    
    def _analyze_resources(self, resources: Dict) -> Dict:
        """Analyze resource utilization"""
        analysis = {
            'resource_types': list(resources.keys()),
            'utilization_summary': {},
            'recommendations': []
        }
        
        for resource_type, data in resources.items():
            if isinstance(data, dict) and 'utilized' in data and 'allocated' in data:
                utilization = (data['utilized'] / data['allocated']) * 100
                analysis['utilization_summary'][resource_type] = f"{utilization:.1f}%"
                
                if utilization > 90:
                    analysis['recommendations'].append(f"Consider increasing {resource_type} allocation")
                elif utilization < 50:
                    analysis['recommendations'].append(f"{resource_type} appears underutilized")
        
        return analysis
    
    def _generate_recommendations(self, project_data: Dict) -> List[str]:
        """Generate project recommendations"""
        recommendations = []
        
        # Based on completion percentage
        completion = project_data.get('completion_percentage', 0)
        if completion < 25:
            recommendations.append("Focus on establishing solid project foundations")
        elif completion < 75:
            recommendations.append("Maintain current momentum and address any blockers")
        else:
            recommendations.append("Prepare for project closure and lessons learned")
        
        # Based on budget status
        budget_status = project_data.get('budget_status', '').lower()
        if 'over' in budget_status:
            recommendations.append("Review budget constraints and optimize spending")
        elif 'under' in budget_status:
            recommendations.append("Consider accelerating deliverables with available budget")
        
        return recommendations
    
    def _calculate_readability_metrics(self, text: str) -> Dict:
        """Calculate detailed readability metrics"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        words = text.split()
        
        if not words or not sentences:
            return {'score': 0, 'level': 'unreadable'}
        
        avg_sentence_length = len(words) / len(sentences)
        
        # Simple syllable count approximation
        syllable_count = 0
        for word in words:
            vowels = len([c for c in word.lower() if c in 'aeiou'])
            syllable_count += max(1, vowels)
        
        avg_syllables_per_word = syllable_count / len(words)
        
        # Flesch Reading Ease approximation
        score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        score = max(0, min(100, score))
        
        # Determine reading level
        if score >= 90:
            level = 'very easy'
        elif score >= 80:
            level = 'easy'
        elif score >= 70:
            level = 'fairly easy'
        elif score >= 60:
            level = 'standard'
        elif score >= 50:
            level = 'fairly difficult'
        elif score >= 30:
            level = 'difficult'
        else:
            level = 'very difficult'
        
        return {
            'score': round(score, 1),
            'level': level,
            'avg_sentence_length': round(avg_sentence_length, 1),
            'avg_syllables_per_word': round(avg_syllables_per_word, 1)
        }
    
    def _analyze_writing_tone(self, text: str) -> Dict:
        """Analyze writing tone"""
        formal_indicators = [
            'therefore', 'furthermore', 'consequently', 'moreover', 'nevertheless',
            'however', 'accordingly', 'thus', 'hence', 'whereas'
        ]
        
        casual_indicators = [
            'really', 'pretty', 'quite', 'sort of', 'kind of', 'anyway',
            'basically', 'actually', 'literally', 'seriously'
        ]
        
        positive_indicators = [
            'excellent', 'great', 'wonderful', 'amazing', 'fantastic',
            'positive', 'beneficial', 'advantage', 'success', 'achievement'
        ]
        
        negative_indicators = [
            'terrible', 'awful', 'horrible', 'disappointing', 'failure',
            'problem', 'issue', 'concern', 'risk', 'challenge'
        ]
        
        text_lower = text.lower()
        words = text_lower.split()
        total_words = len(words)
        
        if total_words == 0:
            return {'tone': 'neutral', 'confidence': 0}
        
        formal_count = sum(1 for word in words if word in formal_indicators)
        casual_count = sum(1 for word in words if word in casual_indicators)
        positive_count = sum(1 for word in words if word in positive_indicators)
        negative_count = sum(1 for word in words if word in negative_indicators)
        
        # Determine primary tone
        tones = []
        
        if formal_count > casual_count:
            tones.append('formal')
        elif casual_count > 0:
            tones.append('casual')
        
        if positive_count > negative_count and positive_count > 0:
            tones.append('positive')
        elif negative_count > positive_count and negative_count > 0:
            tones.append('negative')
        
        if not tones:
            tones.append('neutral')
        
        return {
            'primary_tone': tones[0],
            'secondary_tones': tones[1:],
            'confidence': min(1.0, max(formal_count, casual_count, positive_count, negative_count) / total_words * 10),
            'metrics': {
                'formal_ratio': formal_count / total_words,
                'casual_ratio': casual_count / total_words,
                'positive_ratio': positive_count / total_words,
                'negative_ratio': negative_count / total_words
            }
        }


def create_content_generator():
    """Factory function to create content generation engine"""
    return ContentGenerationEngine()
