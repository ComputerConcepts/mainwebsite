"""
Free AI File Assistant - No paid APIs required
Uses only open-source and free tools
"""
import os
import json
import re
from typing import Dict, List, Optional
from datetime import datetime
import mimetypes

# Free libraries for text processing
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import docx
except ImportError:
    docx = None

try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.stem import PorterStemmer
except ImportError:
    nltk = None

try:
    from collections import Counter
except ImportError:
    Counter = None


class FreeFileAnalyzer:
    """Free AI file analyzer using only open-source tools"""
    
    def __init__(self):
        self.setup_nltk()
        self.stemmer = PorterStemmer() if nltk else None
    
    def setup_nltk(self):
        """Download required NLTK data"""
        if nltk:
            try:
                # Download required data
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
                nltk.download('averaged_perceptron_tagger', quiet=True)
                
                # Initialize stopwords
                try:
                    self.stop_words = set(stopwords.words('english'))
                except:
                    # Fallback stopwords
                    self.stop_words = {
                        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
                        'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers',
                        'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
                        'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
                        'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
                        'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until',
                        'while', 'of', 'at', 'by', 'for', 'with', 'through', 'during', 'before', 'after',
                        'above', 'below', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
                        'further', 'then', 'once'
                    }
            except Exception as e:
                # If NLTK setup fails, use fallback stopwords
                self.stop_words = {
                    'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are',
                    'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                    'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
                }
        else:
            # Basic stopwords if NLTK not available
            self.stop_words = {
                'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are',
                'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would'
            }
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from various file types"""
        file_ext = os.path.splitext(file_path)[1].lower()
        text = ""
        
        try:
            if file_ext == '.pdf' and PyPDF2:
                text = self._extract_from_pdf(file_path)
            elif file_ext == '.docx' and docx:
                text = self._extract_from_docx(file_path)
            elif file_ext == '.txt':
                text = self._extract_from_txt(file_path)
            elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp'] and pytesseract:
                text = self._extract_from_image(file_path)
            else:
                text = "File type not supported for text extraction"
        except Exception as e:
            text = f"Error extracting text: {str(e)}"
        
        return text
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Check if PDF is encrypted
                if pdf_reader.is_encrypted:
                    try:
                        pdf_reader.decrypt('')  # Try empty password
                    except:
                        return "PDF is encrypted and cannot be read"
                
                # Extract text from pages
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    except Exception as e:
                        text += f"[Error reading page {page_num + 1}] "
                        continue
                
                # If no text was extracted
                if not text.strip():
                    return "No text could be extracted from this PDF (might be image-based)"
                
        except Exception as e:
            text = f"Error reading PDF: {str(e)}"
        
        return self._clean_text(text)
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX"""
        try:
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            text = f"Error reading DOCX: {str(e)}"
        return text
    
    def _extract_from_txt(self, file_path: str) -> str:
        """Extract text from TXT"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                text = file.read()
        except Exception as e:
            text = f"Error reading TXT: {str(e)}"
        return text
    
    def _extract_from_image(self, file_path: str) -> str:
        """Extract text from image using OCR"""
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
        except Exception as e:
            text = f"Error performing OCR: {str(e)}"
        return text
    
    def generate_summary(self, text: str, max_sentences: int = 3) -> str:
        """Generate an intelligent extractive summary using advanced techniques"""
        if not text.strip():
            return "No content to summarize"
        
        # Clean the text first
        text = self._clean_text(text)
        
        if not nltk:
            # Enhanced fallback summary
            return self._generate_fallback_summary(text, max_sentences)
        
        try:
            sentences = sent_tokenize(text)
            if not sentences:
                return "No sentences found to summarize"
            
            if len(sentences) <= max_sentences:
                return text[:500] + "..." if len(text) > 500 else text
            
            # Multi-factor sentence scoring
            sentence_scores = self._score_sentences_advanced(sentences, text)
            
            if not sentence_scores:
                return self._generate_fallback_summary(text, max_sentences)
            
            # Select best sentences with diversity
            selected_sentences = self._select_diverse_sentences(sentence_scores, sentences, max_sentences)
            
            if not selected_sentences:
                return self._generate_fallback_summary(text, max_sentences)
            
            # Order sentences by their original position for coherent flow
            original_positions = {sentence: i for i, sentence in enumerate(sentences)}
            selected_sentences.sort(key=lambda x: original_positions.get(x, 0))
            
            summary = ' '.join(selected_sentences).strip()
            
            # Post-process summary
            summary = self._post_process_summary(summary)
            
            return summary if summary else "Unable to generate meaningful summary"
            
        except Exception as e:
            return self._generate_fallback_summary(text, max_sentences)
    
    def _generate_fallback_summary(self, text: str, max_sentences: int = 3) -> str:
        """Enhanced fallback summary when NLTK is not available"""
        # Split by sentences more intelligently
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        
        if not sentences:
            return text[:200] + "..." if len(text) > 200 else text
        
        if len(sentences) <= max_sentences:
            return '. '.join(sentences) + '.'
        
        # Score sentences by various factors
        sentence_scores = []
        
        for i, sentence in enumerate(sentences):
            score = 0
            
            # Position score (earlier sentences are often more important)
            position_score = max(0, 1 - (i / len(sentences)))
            score += position_score * 0.3
            
            # Length score (medium length sentences are often better)
            length = len(sentence.split())
            if 10 <= length <= 30:
                score += 0.2
            elif 5 <= length <= 40:
                score += 0.1
            
            # Keyword density (sentences with more unique words)
            words = re.findall(r'\b[a-zA-Z]{3,}\b', sentence.lower())
            if words:
                unique_ratio = len(set(words)) / len(words)
                score += unique_ratio * 0.3
            
            # Number presence (sentences with numbers often contain facts)
            if re.search(r'\b\d+\b', sentence):
                score += 0.2
            
            sentence_scores.append((sentence, score))
        
        # Select top sentences
        top_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)[:max_sentences]
        
        # Reorder by original position
        selected = [sent for sent, score in top_sentences]
        original_order = []
        
        for sentence in sentences:
            if sentence in selected:
                original_order.append(sentence)
            if len(original_order) == max_sentences:
                break
        
        return '. '.join(original_order) + '.'
    
    def _score_sentences_advanced(self, sentences: List[str], full_text: str) -> Dict[str, float]:
        """Advanced sentence scoring using multiple factors"""
        word_freq = self._get_word_frequencies(full_text)
        if not word_freq:
            return {}
        
        sentence_scores = {}
        total_sentences = len(sentences)
        
        for i, sentence in enumerate(sentences):
            if len(sentence.strip()) < 15:  # Skip very short sentences
                continue
            
            try:
                words = word_tokenize(sentence.lower())
                score = 0
                
                # 1. Word frequency score
                freq_score = 0
                valid_words = 0
                
                for word in words:
                    if word and word.isalpha() and len(word) > 2:
                        if word not in self.stop_words:
                            freq_score += word_freq.get(word, 0)
                            valid_words += 1
                
                if valid_words > 0:
                    score += (freq_score / valid_words) * 0.4
                
                # 2. Position score (first and last sentences often important)
                position_ratio = i / max(total_sentences - 1, 1)
                if i == 0:  # First sentence
                    score += 0.3
                elif i == total_sentences - 1:  # Last sentence
                    score += 0.2
                elif position_ratio < 0.3:  # Early sentences
                    score += 0.15
                
                # 3. Sentence length score (optimal length gets higher score)
                sentence_length = len(words)
                if 8 <= sentence_length <= 25:  # Optimal length
                    score += 0.2
                elif 5 <= sentence_length <= 35:  # Acceptable length
                    score += 0.1
                elif sentence_length < 5:  # Too short
                    score -= 0.1
                
                # 4. Numerical data bonus (sentences with numbers/stats)
                if re.search(r'\b\d+(?:\.\d+)?%?\b', sentence):
                    score += 0.15
                
                # 5. Question sentences (often important)
                if sentence.strip().endswith('?'):
                    score += 0.1
                
                # 6. Uppercase words (might indicate importance)
                uppercase_count = sum(1 for word in words if word.isupper() and len(word) > 2)
                if uppercase_count > 0:
                    score += min(uppercase_count * 0.05, 0.2)
                
                # 7. Sentence connectivity (sentences with connecting words)
                connectors = {'therefore', 'however', 'moreover', 'furthermore', 'additionally', 
                             'consequently', 'meanwhile', 'nevertheless', 'thus', 'hence'}
                if any(connector in sentence.lower() for connector in connectors):
                    score += 0.1
                
                # 8. Keyword density
                content_words = [w for w in words if w.isalpha() and len(w) > 3 and w not in self.stop_words]
                if content_words:
                    unique_ratio = len(set(content_words)) / len(content_words)
                    score += unique_ratio * 0.15
                
                sentence_scores[sentence] = score
                
            except Exception:
                continue
        
        return sentence_scores
    
    def _select_diverse_sentences(self, sentence_scores: Dict[str, float], sentences: List[str], max_sentences: int) -> List[str]:
        """Select sentences that are both high-scoring and diverse in content"""
        if not sentence_scores:
            return []
        
        # Sort sentences by score
        sorted_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)
        
        selected = []
        selected_topics = set()
        
        for sentence, score in sorted_sentences:
            if len(selected) >= max_sentences:
                break
            
            # Extract key topics from this sentence
            sentence_topics = set()
            try:
                words = word_tokenize(sentence.lower()) if nltk else sentence.lower().split()
                content_words = [w for w in words if w.isalpha() and len(w) > 3]
                sentence_topics = set(content_words[:5])  # Top 5 words as topics
            except:
                sentence_topics = set(sentence.lower().split()[:5])
            
            # Check diversity - avoid sentences with too much topic overlap
            if not selected:
                selected.append(sentence)
                selected_topics.update(sentence_topics)
            else:
                # Calculate topic overlap with already selected sentences
                overlap = len(sentence_topics.intersection(selected_topics))
                overlap_ratio = overlap / max(len(sentence_topics), 1)
                
                # Allow sentence if overlap is not too high or if score is exceptionally high
                if overlap_ratio < 0.7 or score > max(s[1] for s in sorted_sentences[:3]):
                    selected.append(sentence)
                    selected_topics.update(sentence_topics)
        
        return selected
    
    def _post_process_summary(self, summary: str) -> str:
        """Post-process the summary for better readability"""
        if not summary:
            return summary
        
        # Fix spacing and punctuation
        summary = re.sub(r'\s+', ' ', summary)
        summary = summary.strip()
        
        # Ensure proper sentence endings
        if summary and not summary.endswith(('.', '!', '?')):
            summary += '.'
        
        # Fix common issues
        summary = re.sub(r'\.\s*\.', '.', summary)  # Remove double periods
        summary = re.sub(r'\s+([.,!?])', r'\1', summary)  # Fix spacing before punctuation
        
        # Capitalize first letter of sentences
        sentences = re.split(r'([.!?]+)', summary)
        processed_sentences = []
        
        for i, part in enumerate(sentences):
            if i % 2 == 0 and part.strip():  # Sentence content (not punctuation)
                part = part.strip()
                if part:
                    part = part[0].upper() + part[1:] if len(part) > 1 else part.upper()
                processed_sentences.append(part)
            else:
                processed_sentences.append(part)
        
        return ''.join(processed_sentences)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove non-printable characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        return text
    
    def _get_word_frequencies(self, text: str) -> Dict[str, int]:
        """Get word frequency distribution"""
        if not text.strip():
            return {}
        
        try:
            if nltk:
                words = word_tokenize(text.lower())
            else:
                # Simple fallback tokenization
                words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
            
            # Filter words
            filtered_words = []
            for word in words:
                if word and word.isalpha() and len(word) > 2:
                    if not self.stop_words or word not in self.stop_words:
                        filtered_words.append(word)
            
            if Counter:
                return dict(Counter(filtered_words))
            else:
                # Fallback manual counting
                freq = {}
                for word in filtered_words:
                    freq[word] = freq.get(word, 0) + 1
                return freq
        except Exception as e:
            return {}
    
    def extract_key_topics(self, text: str, top_n: int = 10) -> List[str]:
        """Extract key topics/keywords from text using advanced techniques"""
        if not text.strip():
            return []
        
        try:
            # Get word frequencies
            word_freq = self._get_word_frequencies(text)
            if not word_freq:
                return []
            
            # Advanced topic extraction
            topics = self._extract_topics_advanced(text, word_freq, top_n)
            
            if not topics:
                # Fallback to simple extraction
                return self._extract_topics_fallback(text, top_n)
            
            return topics
            
        except Exception as e:
            # Fallback: simple word extraction
            return self._extract_topics_fallback(text, top_n)
    
    def _extract_topics_advanced(self, text: str, word_freq: Dict[str, int], top_n: int) -> List[str]:
        """Advanced topic extraction with context awareness"""
        
        # 1. Get candidate words (filter by length and frequency)
        candidates = {}
        
        for word, freq in word_freq.items():
            if len(word) >= 4 and freq >= 2:  # Minimum length and frequency
                candidates[word] = freq
        
        if not candidates:
            return []
        
        # 2. Score words based on multiple factors
        word_scores = {}
        
        for word, freq in candidates.items():
            score = 0
            
            # Base frequency score
            score += freq * 0.4
            
            # Length bonus (longer words often more specific/important)
            if len(word) >= 6:
                score += 0.3
            elif len(word) >= 5:
                score += 0.2
            
            # Capitalization bonus (might be proper nouns/important terms)
            if any(word.capitalize() in text for word in [word]):
                score += 0.2
            
            # Position bonus (words appearing early in text)
            try:
                first_occurrence = text.lower().find(word)
                if first_occurrence != -1:
                    position_ratio = first_occurrence / len(text)
                    if position_ratio < 0.3:  # First 30% of text
                        score += 0.15
            except:
                pass
            
            # Context relevance (words appearing in multiple sentences)
            if nltk:
                try:
                    sentences = sent_tokenize(text)
                    sentence_count = sum(1 for sentence in sentences if word in sentence.lower())
                    if sentence_count > 1:
                        score += min(sentence_count * 0.1, 0.3)
                except:
                    pass
            
            word_scores[word] = score
        
        # 3. Select diverse topics (avoid too similar words)
        selected_topics = []
        sorted_words = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
        
        for word, score in sorted_words:
            if len(selected_topics) >= top_n:
                break
            
            # Check if word is too similar to already selected topics
            is_diverse = True
            for selected in selected_topics:
                if self._words_too_similar(word, selected):
                    is_diverse = False
                    break
            
            if is_diverse:
                selected_topics.append(word)
        
        return selected_topics
    
    def _words_too_similar(self, word1: str, word2: str) -> bool:
        """Check if two words are too similar (same root, etc.)"""
        # Simple similarity checks
        if word1 == word2:
            return True
        
        # Check if one is contained in the other
        if word1 in word2 or word2 in word1:
            return True
        
        # Check if they share a common root (simple heuristic)
        if len(word1) >= 5 and len(word2) >= 5:
            if word1[:4] == word2[:4]:  # Same first 4 letters
                return True
        
        return False
    
    def _extract_topics_fallback(self, text: str, top_n: int) -> List[str]:
        """Fallback topic extraction method"""
        # Simple word extraction with basic filtering
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        
        if not words:
            return []
        
        # Count word frequencies
        word_counts = {}
        for word in words:
            if word not in self.stop_words:
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Filter by frequency and get unique words
        filtered_words = []
        for word, count in word_counts.items():
            if count >= 2 or len(word) >= 6:  # Keep frequent words or long words
                filtered_words.append((word, count))
        
        # Sort by frequency and length
        filtered_words.sort(key=lambda x: (x[1], len(x[0])), reverse=True)
        
        # Remove duplicates and similar words
        unique_topics = []
        for word, count in filtered_words:
            if len(unique_topics) >= top_n:
                break
            
            # Simple duplication check
            if word not in unique_topics:
                # Check if it's too similar to existing topics
                is_unique = True
                for existing in unique_topics:
                    if word in existing or existing in word:
                        is_unique = False
                        break
                
                if is_unique:
                    unique_topics.append(word)
        
        return unique_topics
    
    def categorize_file(self, text: str, filename: str) -> str:
        """Categorize file based on content using intelligent analysis"""
        text_lower = text.lower()
        filename_lower = filename.lower()
        
        # Enhanced rule-based categorization with weighted scoring
        categories = {
            'financial': {
                'keywords': ['budget', 'invoice', 'payment', 'cost', 'revenue', 'financial', 'money', 'dollar', 
                           'profit', 'expense', 'accounting', 'tax', 'fiscal', 'quarterly', 'annual', 'roi',
                           'investment', 'fund', 'capital', 'balance', 'statement', 'audit', 'payroll'],
                'file_extensions': ['xlsx', 'xls', 'csv'],
                'file_patterns': ['budget', 'invoice', 'financial', 'expense', 'revenue', 'accounting']
            },
            'legal': {
                'keywords': ['contract', 'agreement', 'terms', 'legal', 'law', 'court', 'attorney', 'clause',
                           'litigation', 'compliance', 'regulation', 'policy', 'rights', 'liability', 'warranty',
                           'intellectual', 'property', 'patent', 'trademark', 'copyright', 'license'],
                'file_extensions': ['pdf', 'doc', 'docx'],
                'file_patterns': ['contract', 'agreement', 'legal', 'terms', 'policy', 'license']
            },
            'technical': {
                'keywords': ['code', 'programming', 'software', 'algorithm', 'technical', 'system', 'database',
                           'development', 'api', 'framework', 'library', 'function', 'class', 'method', 'variable',
                           'server', 'network', 'protocol', 'architecture', 'deployment', 'configuration'],
                'file_extensions': ['py', 'js', 'java', 'cpp', 'c', 'html', 'css', 'sql', 'json', 'xml', 'yaml'],
                'file_patterns': ['code', 'tech', 'dev', 'system', 'config', 'setup', 'install']
            },
            'research': {
                'keywords': ['study', 'research', 'analysis', 'methodology', 'conclusion', 'abstract', 'hypothesis',
                           'experiment', 'data', 'results', 'findings', 'literature', 'review', 'survey', 'statistical',
                           'correlation', 'significant', 'variable', 'sample', 'population', 'theory'],
                'file_extensions': ['pdf', 'doc', 'docx'],
                'file_patterns': ['research', 'study', 'analysis', 'report', 'paper', 'thesis', 'dissertation']
            },
            'hr': {
                'keywords': ['employee', 'resume', 'hiring', 'interview', 'salary', 'benefits', 'hr', 'recruitment',
                           'onboarding', 'performance', 'evaluation', 'training', 'development', 'career', 'promotion',
                           'disciplinary', 'termination', 'leave', 'vacation', 'sick', 'overtime'],
                'file_extensions': ['pdf', 'doc', 'docx'],
                'file_patterns': ['hr', 'employee', 'resume', 'cv', 'hiring', 'recruitment', 'payroll']
            },
            'marketing': {
                'keywords': ['marketing', 'campaign', 'brand', 'customer', 'sales', 'promotion', 'advertising',
                           'social', 'media', 'seo', 'content', 'strategy', 'target', 'audience', 'conversion',
                           'analytics', 'engagement', 'reach', 'impression', 'click', 'lead', 'funnel'],
                'file_extensions': ['pdf', 'ppt', 'pptx', 'doc', 'docx'],
                'file_patterns': ['marketing', 'campaign', 'promo', 'ads', 'social', 'brand', 'sales']
            },
            'education': {
                'keywords': ['education', 'learning', 'course', 'lesson', 'curriculum', 'syllabus', 'assignment',
                           'homework', 'exam', 'test', 'quiz', 'grade', 'student', 'teacher', 'instructor',
                           'university', 'college', 'school', 'academic', 'degree', 'certificate'],
                'file_extensions': ['pdf', 'doc', 'docx', 'ppt', 'pptx'],
                'file_patterns': ['course', 'lesson', 'education', 'learning', 'curriculum', 'syllabus']
            },
            'presentation': {
                'keywords': ['presentation', 'slide', 'deck', 'meeting', 'conference', 'workshop', 'seminar',
                           'keynote', 'overview', 'agenda', 'outline', 'summary', 'introduction', 'conclusion'],
                'file_extensions': ['ppt', 'pptx', 'pdf'],
                'file_patterns': ['presentation', 'slide', 'deck', 'meeting', 'conference']
            },
            'design': {
                'keywords': ['design', 'graphic', 'visual', 'creative', 'artwork', 'illustration', 'logo', 'brand',
                           'color', 'font', 'layout', 'template', 'mockup', 'wireframe', 'prototype', 'ui', 'ux'],
                'file_extensions': ['png', 'jpg', 'jpeg', 'gif', 'svg', 'psd', 'ai', 'sketch'],
                'file_patterns': ['design', 'graphic', 'visual', 'artwork', 'logo', 'brand', 'mockup']
            },
            'personal': {
                'keywords': ['personal', 'private', 'family', 'photo', 'diary', 'journal', 'notes', 'thoughts',
                           'memories', 'vacation', 'holiday', 'birthday', 'anniversary', 'wedding', 'graduation'],
                'file_extensions': ['jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov', 'avi'],
                'file_patterns': ['personal', 'private', 'family', 'photo', 'diary', 'journal', 'notes']
            }
        }
        
        # Calculate scores for each category
        category_scores = {}
        
        for category, criteria in categories.items():
            score = 0
            
            # Content keyword matching (weighted by importance)
            keyword_matches = 0
            for keyword in criteria['keywords']:
                if keyword in text_lower:
                    keyword_matches += 1
                    # Give more weight to exact matches
                    if f' {keyword} ' in f' {text_lower} ':
                        score += 2
                    else:
                        score += 1
            
            # Filename keyword matching
            filename_matches = 0
            for keyword in criteria['keywords']:
                if keyword in filename_lower:
                    filename_matches += 1
                    score += 3  # Filename matches are more indicative
            
            # File extension matching
            file_ext = filename_lower.split('.')[-1] if '.' in filename_lower else ''
            if file_ext in criteria.get('file_extensions', []):
                score += 2
            
            # File pattern matching in filename
            for pattern in criteria.get('file_patterns', []):
                if pattern in filename_lower:
                    score += 4  # Pattern matches are highly indicative
            
            # Content density bonus (if many keywords from same category)
            if keyword_matches >= 3:
                score += keyword_matches * 0.5
            
            # Store score if positive
            if score > 0:
                category_scores[category] = score
        
        # Return the highest scoring category
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            best_score = category_scores[best_category]
            
            # Only return category if score is significant enough
            if best_score >= 3:
                return best_category
        
        # Fallback categorization based on file type
        file_ext = filename_lower.split('.')[-1] if '.' in filename_lower else ''
        
        if file_ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg']:
            return 'design'
        elif file_ext in ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm']:
            return 'media'
        elif file_ext in ['mp3', 'wav', 'flac', 'aac', 'ogg']:
            return 'audio'
        elif file_ext in ['pdf', 'doc', 'docx', 'txt', 'rtf']:
            return 'document'
        elif file_ext in ['xlsx', 'xls', 'csv']:
            return 'spreadsheet'
        elif file_ext in ['ppt', 'pptx']:
            return 'presentation'
        elif file_ext in ['py', 'js', 'java', 'cpp', 'c', 'html', 'css', 'sql', 'json', 'xml']:
            return 'technical'
        
        return 'general'
    
    def analyze_file(self, file_path: str, filename: str) -> Dict:
        """Complete intelligent file analysis with enhanced insights"""
        try:
            # Extract text from file
            text = self.extract_text_from_file(file_path)
            
            # Basic metrics
            word_count = len(text.split()) if text else 0
            char_count = len(text)
            line_count = len(text.split('\n')) if text else 0
            
            # Advanced analysis
            summary = self.generate_summary(text, max_sentences=4)  # Slightly longer summary
            key_topics = self.extract_key_topics(text, top_n=15)  # More topics
            category = self.categorize_file(text, filename)
            
            # Content analysis
            content_quality = self._assess_content_quality(text)
            language_complexity = self._assess_language_complexity(text)
            document_structure = self._analyze_document_structure(text)
            
            # Sentiment and tone (basic)
            tone_analysis = self._analyze_tone(text)
            
            # File type specific insights
            file_insights = self._get_file_type_insights(text, filename)
            
            analysis = {
                'filename': filename,
                'file_path': file_path,
                'extracted_text': text[:2000],  # Increased preview
                'text_length': char_count,
                'word_count': word_count,
                'line_count': line_count,
                'summary': summary,
                'key_topics': key_topics,
                'category': category,
                'content_quality': content_quality,
                'language_complexity': language_complexity,
                'document_structure': document_structure,
                'tone_analysis': tone_analysis,
                'file_insights': file_insights,
                'analysis_date': datetime.now().isoformat(),
                'has_text': len(text.strip()) > 10,  # More strict threshold
                'analysis_version': '2.0'  # Track analysis version
            }
            
            return analysis
            
        except Exception as e:
            return {
                'filename': filename,
                'error': str(e),
                'analysis_date': datetime.now().isoformat(),
                'analysis_version': '2.0'
            }
    
    def _assess_content_quality(self, text: str) -> Dict[str, any]:
        """Assess the quality and characteristics of content"""
        if not text.strip():
            return {'score': 0, 'assessment': 'No content'}
        
        quality_metrics = {
            'length_score': 0,
            'vocabulary_diversity': 0,
            'sentence_variety': 0,
            'structure_score': 0,
            'overall_score': 0
        }
        
        try:
            # Length assessment
            word_count = len(text.split())
            if word_count < 50:
                quality_metrics['length_score'] = 1
            elif word_count < 200:
                quality_metrics['length_score'] = 2
            elif word_count < 500:
                quality_metrics['length_score'] = 3
            elif word_count < 1000:
                quality_metrics['length_score'] = 4
            else:
                quality_metrics['length_score'] = 5
            
            # Vocabulary diversity
            words = text.lower().split()
            unique_words = set(words)
            if words:
                diversity_ratio = len(unique_words) / len(words)
                quality_metrics['vocabulary_diversity'] = min(5, int(diversity_ratio * 10))
            
            # Sentence variety (basic)
            sentences = re.split(r'[.!?]+', text)
            if sentences:
                sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
                if sentence_lengths:
                    avg_length = sum(sentence_lengths) / len(sentence_lengths)
                    length_variety = len(set(sentence_lengths[:10]))  # Check first 10 sentences
                    quality_metrics['sentence_variety'] = min(5, max(1, length_variety))
            
            # Structure score (paragraphs, formatting)
            paragraphs = text.split('\n\n')
            if len(paragraphs) > 1:
                quality_metrics['structure_score'] = min(5, len(paragraphs))
            else:
                quality_metrics['structure_score'] = 2
            
            # Overall score
            quality_metrics['overall_score'] = round(sum([
                quality_metrics['length_score'],
                quality_metrics['vocabulary_diversity'],
                quality_metrics['sentence_variety'],
                quality_metrics['structure_score']
            ]) / 4, 1)
            
        except Exception:
            quality_metrics['overall_score'] = 1
        
        return quality_metrics
    
    def _assess_language_complexity(self, text: str) -> Dict[str, any]:
        """Assess language complexity and readability"""
        if not text.strip():
            return {'level': 'none', 'score': 0}
        
        try:
            words = text.split()
            sentences = re.split(r'[.!?]+', text)
            sentences = [s for s in sentences if s.strip()]
            
            if not words or not sentences:
                return {'level': 'basic', 'score': 1}
            
            # Basic readability metrics
            avg_word_length = sum(len(word) for word in words) / len(words)
            avg_sentence_length = len(words) / len(sentences)
            
            # Complex word ratio (words with 3+ syllables approximation)
            complex_words = [w for w in words if len(w) > 6]
            complex_ratio = len(complex_words) / len(words) if words else 0
            
            # Calculate complexity score
            complexity_score = 0
            
            if avg_word_length > 5:
                complexity_score += 1
            if avg_sentence_length > 20:
                complexity_score += 1
            if complex_ratio > 0.15:
                complexity_score += 1
            
            # Determine level
            if complexity_score <= 1:
                level = 'basic'
            elif complexity_score == 2:
                level = 'intermediate'
            else:
                level = 'advanced'
            
            return {
                'level': level,
                'score': complexity_score + 1,
                'avg_word_length': round(avg_word_length, 1),
                'avg_sentence_length': round(avg_sentence_length, 1),
                'complex_word_ratio': round(complex_ratio, 2)
            }
            
        except Exception:
            return {'level': 'basic', 'score': 1}
    
    def _analyze_document_structure(self, text: str) -> Dict[str, any]:
        """Analyze document structure and organization"""
        if not text.strip():
            return {'type': 'unstructured', 'elements': []}
        
        structure_info = {
            'type': 'unstructured',
            'elements': [],
            'has_headings': False,
            'has_lists': False,
            'has_tables': False,
            'paragraph_count': 0
        }
        
        try:
            # Check for headings (lines that are short and followed by content)
            lines = text.split('\n')
            potential_headings = []
            
            for i, line in enumerate(lines):
                line = line.strip()
                if line and len(line) < 60 and not line.endswith('.'):
                    # Check if next line has content
                    if i + 1 < len(lines) and lines[i + 1].strip():
                        potential_headings.append(line)
            
            if potential_headings:
                structure_info['has_headings'] = True
                structure_info['elements'].append('headings')
                structure_info['type'] = 'structured'
            
            # Check for lists (lines starting with bullets, numbers, etc.)
            list_indicators = ['-', '*', '•', '1.', '2.', '3.', 'a)', 'b)', 'c)']
            has_lists = any(any(line.strip().startswith(indicator) for indicator in list_indicators) 
                          for line in lines)
            
            if has_lists:
                structure_info['has_lists'] = True
                structure_info['elements'].append('lists')
                structure_info['type'] = 'structured'
            
            # Check for table-like structures (multiple tabs or pipes)
            has_tables = any('\t' in line or '|' in line for line in lines)
            if has_tables:
                structure_info['has_tables'] = True
                structure_info['elements'].append('tables')
            
            # Count paragraphs
            paragraphs = [p for p in text.split('\n\n') if p.strip()]
            structure_info['paragraph_count'] = len(paragraphs)
            
            # Determine overall type
            if len(structure_info['elements']) >= 2:
                structure_info['type'] = 'well_structured'
            elif len(structure_info['elements']) >= 1:
                structure_info['type'] = 'structured'
            
        except Exception:
            pass
        
        return structure_info
    
    def _analyze_tone(self, text: str) -> Dict[str, any]:
        """Basic tone and sentiment analysis"""
        if not text.strip():
            return {'tone': 'neutral', 'confidence': 0}
        
        # Simple tone analysis using keyword matching
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'outstanding',
                         'success', 'achieve', 'improve', 'benefit', 'advantage', 'opportunity', 'effective']
        
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'fail', 'failure', 'problem', 'issue',
                         'difficult', 'challenge', 'risk', 'concern', 'disadvantage', 'limitation']
        
        formal_words = ['therefore', 'however', 'furthermore', 'consequently', 'nevertheless', 'moreover',
                       'accordingly', 'subsequently', 'whereas', 'notwithstanding']
        
        technical_words = ['system', 'process', 'method', 'analysis', 'implementation', 'configuration',
                          'parameter', 'algorithm', 'specification', 'requirement']
        
        try:
            words = text.lower().split()
            total_words = len(words)
            
            if total_words == 0:
                return {'tone': 'neutral', 'confidence': 0}
            
            positive_count = sum(1 for word in words if word in positive_words)
            negative_count = sum(1 for word in words if word in negative_words)
            formal_count = sum(1 for word in words if word in formal_words)
            technical_count = sum(1 for word in words if word in technical_words)
            
            # Calculate ratios
            positive_ratio = positive_count / total_words
            negative_ratio = negative_count / total_words
            formal_ratio = formal_count / total_words
            technical_ratio = technical_count / total_words
            
            # Determine primary tone
            if technical_ratio > 0.02:
                tone = 'technical'
                confidence = min(0.8, technical_ratio * 10)
            elif formal_ratio > 0.01:
                tone = 'formal'
                confidence = min(0.8, formal_ratio * 20)
            elif positive_ratio > negative_ratio and positive_ratio > 0.01:
                tone = 'positive'
                confidence = min(0.8, positive_ratio * 20)
            elif negative_ratio > positive_ratio and negative_ratio > 0.01:
                tone = 'negative'
                confidence = min(0.8, negative_ratio * 20)
            else:
                tone = 'neutral'
                confidence = 0.5
            
            return {
                'tone': tone,
                'confidence': round(confidence, 2),
                'positive_ratio': round(positive_ratio, 3),
                'negative_ratio': round(negative_ratio, 3),
                'formal_ratio': round(formal_ratio, 3),
                'technical_ratio': round(technical_ratio, 3)
            }
            
        except Exception:
            return {'tone': 'neutral', 'confidence': 0}
    
    def _get_file_type_insights(self, text: str, filename: str) -> Dict[str, any]:
        """Get insights specific to file type"""
        insights = {'type_specific': []}
        
        try:
            file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
            
            if file_ext == 'pdf':
                # PDF specific insights
                if 'abstract' in text.lower():
                    insights['type_specific'].append('Contains abstract - likely academic/research document')
                if 'table of contents' in text.lower():
                    insights['type_specific'].append('Has table of contents - well-structured document')
                if len(text.split()) > 2000:
                    insights['type_specific'].append('Long document - comprehensive content')
            
            elif file_ext in ['doc', 'docx']:
                # Word document insights
                if text.count('\n\n') > 5:
                    insights['type_specific'].append('Multiple sections/paragraphs')
                if any(word in text.lower() for word in ['draft', 'version', 'revision']):
                    insights['type_specific'].append('Appears to be a draft or versioned document')
            
            elif file_ext == 'txt':
                # Text file insights
                if len(text.split('\n')) > 50:
                    insights['type_specific'].append('Many lines - possibly log file or data export')
                if text.count('\t') > 10:
                    insights['type_specific'].append('Contains tabs - possibly structured data')
            
            # Content-based insights
            if re.search(r'\b\d{4}-\d{2}-\d{2}\b', text):
                insights['type_specific'].append('Contains dates - time-sensitive content')
            
            if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text):
                insights['type_specific'].append('Contains email addresses')
            
            if re.search(r'\b\$\d+(?:\.\d{2})?\b', text):
                insights['type_specific'].append('Contains monetary amounts')
            
            if text.count('http') > 0:
                insights['type_specific'].append('Contains web links/URLs')
                
        except Exception:
            pass
        
        return insights
    
    def search_files(self, query: str, file_analyses: List[Dict]) -> List[Dict]:
        """Simple text-based search through analyzed files"""
        query_lower = query.lower()
        results = []
        
        for analysis in file_analyses:
            score = 0
            
            # Check filename
            if query_lower in analysis.get('filename', '').lower():
                score += 3
            
            # Check summary
            if query_lower in analysis.get('summary', '').lower():
                score += 2
            
            # Check topics
            for topic in analysis.get('key_topics', []):
                if query_lower in topic.lower():
                    score += 1
            
            # Check category
            if query_lower in analysis.get('category', '').lower():
                score += 1
            
            # Check extracted text
            if query_lower in analysis.get('extracted_text', '').lower():
                score += 1
            
            if score > 0:
                analysis_copy = analysis.copy()
                analysis_copy['relevance_score'] = score
                results.append(analysis_copy)
        
        # Sort by relevance
        return sorted(results, key=lambda x: x['relevance_score'], reverse=True)


# Simple chatbot for file queries
class FileAssistantBot:
    """Enhanced conversational chatbot for file queries"""
    
    def __init__(self, analyzer: FreeFileAnalyzer):
        self.analyzer = analyzer
        self.file_analyses = []
        self.conversation_history = []
        self.user_context = {}
        self.last_search_results = []
        self.awaiting_clarification = False
        self.clarification_context = None
    
    def load_analyses(self, analyses: List[Dict]):
        """Load file analyses for querying"""
        self.file_analyses = analyses
    
    def process_query(self, query: str) -> str:
        """Process natural language queries about files with conversation flow"""
        query_lower = query.lower().strip()
        
        # Add to conversation history (store as string for JSON serialization)
        self.conversation_history.append({
            "user": query, 
            "timestamp": datetime.now().isoformat()
        })
        
        # Handle follow-up questions
        if self.awaiting_clarification:
            return self._handle_clarification(query)
        
        # Handle conversational responses
        if any(word in query_lower for word in ['thanks', 'thank you', 'great', 'perfect', 'awesome']):
            return self._handle_positive_response()
        
        if any(word in query_lower for word in ['yes', 'yeah', 'yep', 'sure', 'okay']):
            return self._handle_affirmative_response(query)
        
        if any(word in query_lower for word in ['no', 'nope', 'not really', 'nothing']):
            return self._handle_negative_response()
        
        # Handle specific intents with context
        if any(word in query_lower for word in ['more', 'show more', 'continue', 'next']):
            return self._handle_more_request()
        
        if any(word in query_lower for word in ['tell me about', 'what is', 'describe']):
            return self._handle_describe_request(query)
        
        if any(word in query_lower for word in ['help', 'what can you do', 'capabilities']):
            return self._handle_help_request()
        
        # Handle numbered responses (e.g., "1", "first", "number 1")
        if any(word in query_lower for word in ['1', 'first', 'one']) and self.last_search_results:
            return self._provide_file_details(self.last_search_results[0])
        
        if any(word in query_lower for word in ['2', 'second', 'two']) and len(self.last_search_results) > 1:
            return self._provide_file_details(self.last_search_results[1])
        
        if any(word in query_lower for word in ['3', 'third', 'three']) and len(self.last_search_results) > 2:
            return self._provide_file_details(self.last_search_results[2])
        
        # Handle requests for similar files
        if any(phrase in query_lower for phrase in ['find similar', 'similar files', 'related files', 'like this']):
            return self._handle_similar_files_request()
        
        # Handle requests for more topics
        if any(phrase in query_lower for phrase in ['extract more topics', 'more topics', 'deeper analysis']):
            return self._handle_more_topics_request()
        
        # Main intent detection
        if any(word in query_lower for word in ['find', 'search', 'show', 'get', 'looking for']):
            return self._handle_search_query(query)
        elif any(word in query_lower for word in ['summarize', 'summary', 'about']):
            return self._handle_summary_query(query)
        elif any(word in query_lower for word in ['category', 'type', 'kind', 'organize']):
            return self._handle_category_query(query)
        elif any(word in query_lower for word in ['how many', 'count', 'total', 'number']):
            return self._handle_count_query(query)
        elif any(word in query_lower for word in ['recent', 'latest', 'new']):
            return self._handle_recent_query(query)
        elif any(word in query_lower for word in ['large', 'big', 'small', 'size']):
            return self._handle_size_query(query)
        else:
            return self._handle_general_query(query)
    
    def _handle_clarification(self, query: str) -> str:
        """Handle clarification responses"""
        self.awaiting_clarification = False
        
        if self.clarification_context == "search_refinement":
            return self._handle_search_query(query)
        elif self.clarification_context == "file_selection":
            # Try to match user's response to a file
            query_lower = query.lower()
            for i, result in enumerate(self.last_search_results):
                if str(i+1) in query or result['filename'].lower() in query_lower:
                    return self._provide_file_details(result)
            return "I couldn't find that file. Can you be more specific?"
        
        self.clarification_context = None
        return self.process_query(query)
    
    def _handle_positive_response(self) -> str:
        """Handle positive responses"""
        responses = [
            "You're welcome! Is there anything else you'd like to know about your files?",
            "Glad I could help! What else can I do for you?",
            "Happy to assist! Any other questions about your files?",
            "Great! Feel free to ask me anything else about your documents."
        ]
        return self._get_random_response(responses)
    
    def _handle_affirmative_response(self, query: str) -> str:
        """Handle yes/affirmative responses"""
        # If we just provided detailed info about a single file, offer more help
        if len(self.last_search_results) == 1:
            file_info = self.last_search_results[0]
            return f"Great! What else would you like to know about **{file_info['filename']}**? I can:\n\n• Extract more key topics from the content\n• Tell you about similar files in your collection\n• Help you categorize or organize it\n• Search for files with similar content\n\nWhat interests you most?"
        
        # If we have multiple search results, assume they want details about the first one
        elif len(self.last_search_results) > 1:
            return self._provide_file_details(self.last_search_results[0])
        
        # If no recent search results, ask what they want help with
        return "What would you like me to help you with? You can ask me to find files, show categories, or analyze your collection."
    
    def _handle_negative_response(self) -> str:
        """Handle negative responses"""
        return "No problem! Is there something else I can help you find or analyze?"
    
    def _handle_more_request(self) -> str:
        """Handle requests for more information"""
        if self.last_search_results:
            if len(self.last_search_results) > 5:
                response = "Here are more results:\n\n"
                for i, result in enumerate(self.last_search_results[5:10], 6):
                    response += f"{i}. {result['filename']} (Category: {result.get('category', 'unknown')})\n"
                    if result.get('summary'):
                        response += f"   Summary: {result['summary'][:100]}...\n"
                    response += "\n"
                return response
            else:
                return "That's all the results I have. Would you like me to search for something else?"
        return "What would you like to know more about?"
    
    def _handle_describe_request(self, query: str) -> str:
        """Handle describe/tell me about requests"""
        query_lower = query.lower()
        
        # Check if they're asking about "this file" or "it" (referring to recent results)
        if any(word in query_lower for word in ['this file', 'it', 'that file', 'the file']) and self.last_search_results:
            return self._provide_file_details(self.last_search_results[0])
        
        # Extract what they want to know about
        if 'file' in query_lower:
            # Try to find a specific file mentioned
            for analysis in self.file_analyses:
                if analysis['filename'].lower() in query_lower:
                    return self._provide_file_details(analysis)
            
            # If no specific file found but we have recent results, show the first one
            if self.last_search_results:
                return self._provide_file_details(self.last_search_results[0])
            
            return "Which file would you like me to tell you about? You can mention the filename or search for files first."
        
        return "What would you like me to describe? You can ask about specific files, categories, or your document collection."
    
    def _handle_help_request(self) -> str:
        """Handle help requests"""
        return """I'm your AI file assistant! Here's what I can do:

🔍 **Search & Find**
• "Find files about machine learning"
• "Show me PDFs"
• "Looking for invoices"

📊 **Analysis & Stats**
• "What categories do I have?"
• "How many files do I have?"
• "Show me recent files"

📝 **File Details**
• "Tell me about [filename]"
• "Summarize this document"
• "What's in my research folder?"

💬 **Conversation**
• I remember our conversation, so you can ask follow-up questions
• Say "more" to see additional results
• I'll help clarify what you're looking for

What would you like to explore first?"""
    
    def _handle_recent_query(self, query: str) -> str:
        """Handle recent files queries"""
        if not self.file_analyses:
            return "No files have been analyzed yet."
        
        # Sort by analysis date (most recent first)
        recent_files = sorted(self.file_analyses, 
                            key=lambda x: x.get('analysis_date', ''), 
                            reverse=True)[:5]
        
        response = "Here are your most recently analyzed files:\n\n"
        for i, analysis in enumerate(recent_files, 1):
            response += f"{i}. {analysis['filename']} (Category: {analysis.get('category', 'unknown')})\n"
            if analysis.get('summary'):
                response += f"   Summary: {analysis['summary'][:100]}...\n"
            response += "\n"
        
        self.last_search_results = recent_files
        return response + "Would you like to know more about any of these files?"
    
    def _handle_size_query(self, query: str) -> str:
        """Handle file size queries"""
        if not self.file_analyses:
            return "No files have been analyzed yet."
        
        query_lower = query.lower()
        
        if 'large' in query_lower or 'big' in query_lower:
            # Find files with most text content
            large_files = sorted([f for f in self.file_analyses if f.get('text_length', 0) > 1000],
                               key=lambda x: x.get('text_length', 0), reverse=True)[:5]
            
            if large_files:
                response = "Here are your largest files by content:\n\n"
                for i, analysis in enumerate(large_files, 1):
                    response += f"{i}. {analysis['filename']} ({analysis.get('text_length', 0)} characters)\n"
                    response += f"   Category: {analysis.get('category', 'unknown')}\n\n"
                return response
            else:
                return "I couldn't find any particularly large files in your collection."
        
        elif 'small' in query_lower:
            small_files = sorted([f for f in self.file_analyses if f.get('text_length', 0) < 500],
                               key=lambda x: x.get('text_length', 0))[:5]
            
            if small_files:
                response = "Here are your smallest files by content:\n\n"
                for i, analysis in enumerate(small_files, 1):
                    response += f"{i}. {analysis['filename']} ({analysis.get('text_length', 0)} characters)\n"
                return response
            else:
                return "All your files seem to have substantial content."
        
        return "Would you like to see large files or small files?"
    
    def _provide_file_details(self, analysis: Dict) -> str:
        """Provide detailed information about a specific file"""
        response = f"📄 **{analysis['filename']}**\n\n"
        response += f"**Category:** {analysis.get('category', 'unknown').title()}\n"
        response += f"**Content Length:** {analysis.get('text_length', 0)} characters\n"
        
        if analysis.get('key_topics'):
            response += f"**Key Topics:** {', '.join(analysis['key_topics'][:5])}\n"
        
        if analysis.get('summary'):
            response += f"\n**Summary:**\n{analysis['summary']}\n"
        
        if analysis.get('extracted_text'):
            response += f"\n**Preview:**\n{analysis['extracted_text'][:200]}...\n"
        
        # Offer contextual follow-up options
        response += "\n**What would you like to know next?**\n"
        response += "• Ask 'find similar files' to locate related documents\n"
        response += "• Say 'extract more topics' for deeper analysis\n"
        response += "• Ask 'what category is this?' for categorization details\n"
        response += "• Say 'show me more files' to continue exploring\n"
        
        return response
    
    def _handle_similar_files_request(self) -> str:
        """Handle requests to find similar files"""
        if not self.last_search_results:
            return "I need to know which file you're referring to. Try searching for a file first, then ask for similar ones."
        
        # Use the first file from last search results
        reference_file = self.last_search_results[0]
        
        if not reference_file.get('key_topics'):
            return f"I couldn't find enough information about **{reference_file['filename']}** to find similar files."
        
        # Search for files with similar topics
        similar_files = []
        reference_topics = set(reference_file['key_topics'][:5])
        
        for analysis in self.file_analyses:
            if analysis['filename'] == reference_file['filename']:
                continue  # Skip the reference file itself
            
            file_topics = set(analysis.get('key_topics', []))
            overlap = len(reference_topics.intersection(file_topics))
            
            if overlap > 0:
                analysis_copy = analysis.copy()
                analysis_copy['similarity_score'] = overlap
                similar_files.append(analysis_copy)
        
        # Sort by similarity score
        similar_files.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        if not similar_files:
            return f"I couldn't find any files similar to **{reference_file['filename']}** based on content topics."
        
        response = f"📋 **Files similar to {reference_file['filename']}:**\n\n"
        for i, file_info in enumerate(similar_files[:5], 1):
            response += f"{i}. **{file_info['filename']}** (Category: {file_info.get('category', 'unknown')})\n"
            common_topics = list(set(reference_file['key_topics']).intersection(set(file_info.get('key_topics', []))))
            if common_topics:
                response += f"   Common topics: {', '.join(common_topics[:3])}\n"
            response += "\n"
        
        self.last_search_results = similar_files
        return response + "Would you like to know more about any of these similar files?"
    
    def _handle_more_topics_request(self) -> str:
        """Handle requests for deeper topic analysis"""
        if not self.last_search_results:
            return "I need to know which file you're referring to. Try searching for a file first, then ask for deeper analysis."
        
        reference_file = self.last_search_results[0]
        
        # Get more topics from the file
        if 'extracted_text' in reference_file:
            more_topics = self.analyzer.extract_key_topics(reference_file['extracted_text'], top_n=20)
            
            response = f"🔍 **Deeper analysis of {reference_file['filename']}:**\n\n"
            response += f"**Extended Key Topics:**\n"
            
            # Group topics by relevance
            primary_topics = more_topics[:5]
            secondary_topics = more_topics[5:10]
            additional_topics = more_topics[10:15]
            
            if primary_topics:
                response += f"• **Primary:** {', '.join(primary_topics)}\n"
            if secondary_topics:
                response += f"• **Secondary:** {', '.join(secondary_topics)}\n"
            if additional_topics:
                response += f"• **Additional:** {', '.join(additional_topics)}\n"
            
            return response + "\nWhat would you like to explore next about this file?"
        else:
            return f"I couldn't extract additional topics from **{reference_file['filename']}**. The file might not have sufficient readable content."
    
    def _get_random_response(self, responses: List[str]) -> str:
        """Get a random response from a list"""
        import random
        return random.choice(responses)
    
    def _handle_search_query(self, query: str) -> str:
        """Handle search queries with better conversation flow"""
        # Extract search terms (improved approach)
        search_terms = []
        query_words = query.lower().split()
        
        # Skip common words but keep important ones
        skip_words = {'find', 'search', 'show', 'get', 'me', 'all', 'files', 'for', 'about', 'with', 'the', 'a', 'an'}
        
        for word in query_words:
            if word not in skip_words and len(word) > 2:
                search_terms.append(word)
        
        if not search_terms:
            self.awaiting_clarification = True
            self.clarification_context = "search_refinement"
            return "What would you like me to search for? You can mention topics, file types, or specific content."
        
        search_query = ' '.join(search_terms)
        results = self.analyzer.search_files(search_query, self.file_analyses)
        
        if not results:
            return f"I couldn't find any files related to '{search_query}'. Try different keywords or ask me what categories are available."
        
        self.last_search_results = results
        
        if len(results) == 1:
            # For single results, provide details and set context for follow-up
            response = f"I found 1 file related to '{search_query}':\n\n" + self._provide_file_details(results[0])
            # Add context hint for better follow-up
            response += "\n\nSay 'yes' if you'd like more insights about this file, or ask me something else!"
            return response
        
        response = f"I found {len(results)} file(s) related to '{search_query}':\n\n"
        for i, result in enumerate(results[:5], 1):
            response += f"{i}. {result['filename']} (Category: {result.get('category', 'unknown')})\n"
            if result.get('summary'):
                response += f"   Summary: {result['summary'][:100]}...\n"
            response += "\n"
        
        if len(results) > 5:
            response += f"...and {len(results) - 5} more files.\n"
        
        response += "Would you like me to tell you more about any of these files? Just mention the number or filename."
        return response
    
    def _handle_summary_query(self, query: str) -> str:
        """Handle summary requests"""
        query_lower = query.lower()
        
        # Check if they mentioned a specific file
        for analysis in self.file_analyses:
            if analysis['filename'].lower() in query_lower:
                if analysis.get('summary'):
                    return f"📄 **{analysis['filename']}**\n\n**Summary:**\n{analysis['summary']}\n\nWould you like to know more about this file?"
                else:
                    return f"I couldn't generate a summary for {analysis['filename']}. It might not contain extractable text."
        
        # Check if they want summaries of recent results
        if self.last_search_results:
            return "Which file from the search results would you like me to summarize? You can mention the number or filename."
        
        return "Which file would you like me to summarize? You can mention the filename or search for files first."
    
    def _handle_category_query(self, query: str) -> str:
        """Handle category queries"""
        categories = {}
        for analysis in self.file_analyses:
            category = analysis.get('category', 'unknown')
            categories[category] = categories.get(category, 0) + 1
        
        if not categories:
            return "No files have been analyzed yet. Upload some files first!"
        
        query_lower = query.lower()
        
        # Check if they're asking about a specific category
        for category in categories.keys():
            if category in query_lower:
                files_in_category = [f for f in self.file_analyses if f.get('category') == category]
                response = f"📁 **{category.title()} Files ({len(files_in_category)} files):**\n\n"
                for i, file_info in enumerate(files_in_category[:5], 1):
                    response += f"{i}. {file_info['filename']}\n"
                    if file_info.get('summary'):
                        response += f"   {file_info['summary'][:80]}...\n"
                    response += "\n"
                
                if len(files_in_category) > 5:
                    response += f"...and {len(files_in_category) - 5} more files in this category.\n"
                
                return response + "Would you like to know more about any of these files?"
        
        response = "📊 **Your File Categories:**\n\n"
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            response += f"• **{category.title()}:** {count} file(s)\n"
        
        response += "\nWould you like to see files in a specific category? Just ask me about it!"
        return response
    
    def _handle_count_query(self, query: str) -> str:
        """Handle counting queries"""
        total_files = len(self.file_analyses)
        files_with_text = len([a for a in self.file_analyses if a.get('has_text')])
        
        if total_files == 0:
            return "You don't have any analyzed files yet. Upload some files to get started!"
        
        response = f"📊 **File Statistics:**\n\n"
        response += f"• **Total files:** {total_files}\n"
        response += f"• **Files with text:** {files_with_text}\n"
        response += f"• **Text-only files:** {total_files - files_with_text}\n"
        
        # Category breakdown
        categories = {}
        for analysis in self.file_analyses:
            category = analysis.get('category', 'unknown')
            categories[category] = categories.get(category, 0) + 1
        
        response += f"• **Categories:** {len(categories)}\n\n"
        
        if total_files == 1:
            response += "You have 1 file. Would you like me to analyze it for you?"
        elif total_files < 5:
            response += "You have a small collection. Would you like me to show you what's in it?"
        else:
            response += "You have a nice collection! What would you like to explore?"
        
        return response
    
    def _handle_general_query(self, query: str) -> str:
        """Handle general queries with context awareness"""
        query_lower = query.lower()
        
        # Check for greetings
        if any(word in query_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            return "Hello! I'm your AI file assistant. I can help you find, analyze, and organize your documents. What would you like to explore today?"
        
        # Check for gratitude
        if any(word in query_lower for word in ['thank you', 'thanks', 'appreciate']):
            return "You're very welcome! I'm here whenever you need help with your files. What else can I do for you?"
        
        # Check for confusion
        if any(word in query_lower for word in ['confused', 'lost', 'don\'t understand']):
            return "No worries! I'm here to help. Try asking me to:\n• Find files about a topic\n• Show you file categories\n• Tell you about specific files\n• Count your files\n\nWhat would you like to start with?"
        
        # Default response with context
        responses = [
            "I can help you with your files! Here are some things you can ask me:",
            "• 'Find files about [topic]' - I'll search through your content",
            "• 'What categories do I have?' - I'll show you how your files are organized", 
            "• 'How many files do I have?' - I'll give you stats about your collection",
            "• 'Show me recent files' - I'll show recently analyzed files",
            "• 'Tell me about [filename]' - I'll give you detailed info about a specific file",
            "",
            "What would you like to explore first?"
        ]
        return "\n".join(responses)


# Initialize the free AI assistant
def create_free_ai_assistant():
    """Create and return a free AI assistant instance"""
    analyzer = FreeFileAnalyzer()
    bot = FileAssistantBot(analyzer)
    return analyzer, bot
