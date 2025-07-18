"""
AI-powered resume screening and job matching system
"""
import os
import re
import PyPDF2
import docx
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
from typing import Dict, List, Tuple, Optional
from django.conf import settings
from django.utils import timezone
import logging

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

logger = logging.getLogger(__name__)


class ResumeAnalyzer:
    """Main class for AI-powered resume analysis"""
    
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        
        # Common technical skills and keywords
        self.technical_skills = {
            'programming': ['python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'scala', 'kotlin'],
            'web_dev': ['html', 'css', 'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask', 'spring'],
            'databases': ['mysql', 'postgresql', 'mongodb', 'redis', 'oracle', 'sqlite', 'elasticsearch'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'terraform'],
            'data_science': ['pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'spark', 'hadoop'],
            'mobile': ['android', 'ios', 'react native', 'flutter', 'swift', 'kotlin'],
            'tools': ['git', 'jira', 'confluence', 'slack', 'figma', 'photoshop']
        }
        
        # Experience level indicators
        self.experience_indicators = {
            'senior': ['senior', 'lead', 'principal', 'architect', 'team lead', 'tech lead'],
            'mid': ['mid-level', 'intermediate', 'experienced', 'specialist'],
            'junior': ['junior', 'entry', 'associate', 'trainee', 'intern']
        }
        
        # Education indicators
        self.education_indicators = {
            'advanced': ['phd', 'ph.d', 'doctorate', 'masters', 'mba', 'ms', 'ma'],
            'bachelor': ['bachelor', 'bs', 'ba', 'be', 'btech', 'b.tech'],
            'associate': ['associate', 'diploma', 'certificate'],
            'bootcamp': ['bootcamp', 'coding bootcamp', 'intensive course']
        }

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF resume"""
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return ""

    def extract_text_from_docx(self, docx_path: str) -> str:
        """Extract text from DOCX resume"""
        try:
            doc = docx.Document(docx_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {str(e)}")
            return ""

    def extract_resume_text(self, resume_file_path: str) -> str:
        """Extract text from resume file"""
        if not resume_file_path or not os.path.exists(resume_file_path):
            return ""
        
        file_extension = os.path.splitext(resume_file_path)[1].lower()
        
        if file_extension == '.pdf':
            return self.extract_text_from_pdf(resume_file_path)
        elif file_extension in ['.docx', '.doc']:
            return self.extract_text_from_docx(resume_file_path)
        else:
            logger.warning(f"Unsupported file format: {file_extension}")
            return ""

    def preprocess_text(self, text: str) -> str:
        """Preprocess text for analysis"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and numbers
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        
        # Remove extra whitespaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Tokenize and remove stopwords
        tokens = word_tokenize(text)
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens 
                 if token not in self.stop_words and len(token) > 2]
        
        return ' '.join(tokens)

    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extract technical skills from text"""
        text_lower = text.lower()
        found_skills = {}
        
        for category, skills in self.technical_skills.items():
            found_skills[category] = []
            for skill in skills:
                if skill.lower() in text_lower:
                    found_skills[category].append(skill)
        
        return found_skills

    def analyze_experience_level(self, text: str, years_experience: int) -> Dict[str, any]:
        """Analyze experience level from resume text and stated years"""
        text_lower = text.lower()
        experience_signals = {}
        
        # Check for experience level indicators in text
        for level, indicators in self.experience_indicators.items():
            count = sum(1 for indicator in indicators if indicator in text_lower)
            experience_signals[level] = count
        
        # Determine experience level based on years and text signals
        if years_experience >= 7 or experience_signals.get('senior', 0) > 0:
            level = 'senior'
        elif years_experience >= 3 or experience_signals.get('mid', 0) > 0:
            level = 'mid'
        else:
            level = 'junior'
        
        return {
            'level': level,
            'years': years_experience,
            'signals': experience_signals
        }

    def analyze_education(self, education_text: str, resume_text: str) -> Dict[str, any]:
        """Analyze education level and relevance"""
        combined_text = f"{education_text} {resume_text}".lower()
        
        education_level = 'other'
        for level, indicators in self.education_indicators.items():
            if any(indicator in combined_text for indicator in indicators):
                education_level = level
                break
        
        # Check for relevant fields
        cs_related = any(term in combined_text for term in [
            'computer science', 'software engineering', 'information technology',
            'computer engineering', 'data science', 'artificial intelligence'
        ])
        
        return {
            'level': education_level,
            'cs_related': cs_related,
            'text': education_text
        }

    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using TF-IDF and cosine similarity"""
        try:
            processed_text1 = self.preprocess_text(text1)
            processed_text2 = self.preprocess_text(text2)
            
            if not processed_text1 or not processed_text2:
                return 0.0
            
            texts = [processed_text1, processed_text2]
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating text similarity: {str(e)}")
            return 0.0

    def analyze_job_match(self, career_application, job_posting) -> Dict[str, any]:
        """Comprehensive job matching analysis"""
        try:
            # Extract resume text if not already done
            if not career_application.resume_text and career_application.resume:
                resume_path = career_application.resume.path
                career_application.resume_text = self.extract_resume_text(resume_path)
                career_application.save()
            
            resume_text = career_application.resume_text or ""
            
            # Prepare job requirements text
            job_requirements = f"""
            {job_posting.title}
            {job_posting.description}
            {job_posting.requirements}
            {job_posting.responsibilities}
            Department: {job_posting.department}
            Experience Level: {job_posting.get_experience_level_display()}
            """
            
            # Extract skills from resume and job posting
            resume_skills = self.extract_skills(resume_text)
            job_skills = self.extract_skills(job_requirements)
            
            # Calculate skills match
            skills_match = self.calculate_skills_match(resume_skills, job_skills)
            
            # Analyze experience
            experience_analysis = self.analyze_experience_level(
                resume_text, career_application.experience_years
            )
            experience_match = self.calculate_experience_match(
                experience_analysis, job_posting.experience_level
            )
            
            # Analyze education
            education_analysis = self.analyze_education(
                career_application.education, resume_text
            )
            education_match = self.calculate_education_match(
                education_analysis, job_posting.requirements
            )
            
            # Calculate overall match score
            overall_match = (skills_match * 0.4 + experience_match * 0.35 + education_match * 0.25)
            
            # Generate AI insights
            strengths = self.generate_strengths(resume_skills, experience_analysis, education_analysis)
            concerns = self.generate_concerns(skills_match, experience_match, education_match)
            summary = self.generate_summary(career_application, overall_match)
            recommendation = self.generate_recommendation(overall_match)
            
            return {
                'overall_match': round(overall_match, 2),
                'skills_match': round(skills_match, 2),
                'experience_match': round(experience_match, 2),
                'education_match': round(education_match, 2),
                'strengths': strengths,
                'concerns': concerns,
                'summary': summary,
                'recommendation': recommendation,
                'resume_skills': resume_skills,
                'experience_analysis': experience_analysis,
                'education_analysis': education_analysis
            }
            
        except Exception as e:
            logger.error(f"Error in job match analysis: {str(e)}")
            return {
                'overall_match': 0.0,
                'skills_match': 0.0,
                'experience_match': 0.0,
                'education_match': 0.0,
                'strengths': "Error in analysis",
                'concerns': "Analysis could not be completed",
                'summary': "Error occurred during AI analysis",
                'recommendation': 'not_recommended'
            }

    def calculate_skills_match(self, resume_skills: Dict, job_skills: Dict) -> float:
        """Calculate skills match percentage"""
        total_job_skills = sum(len(skills) for skills in job_skills.values())
        if total_job_skills == 0:
            return 50.0  # Default score if no specific skills mentioned
        
        matched_skills = 0
        for category, job_category_skills in job_skills.items():
            resume_category_skills = resume_skills.get(category, [])
            for skill in job_category_skills:
                if skill in resume_category_skills:
                    matched_skills += 1
        
        return min(100.0, (matched_skills / total_job_skills) * 100)

    def calculate_experience_match(self, experience_analysis: Dict, required_level: str) -> float:
        """Calculate experience match percentage"""
        candidate_level = experience_analysis['level']
        years = experience_analysis['years']
        
        level_hierarchy = {'junior': 1, 'mid': 2, 'senior': 3}
        
        candidate_score = level_hierarchy.get(candidate_level, 1)
        required_score = level_hierarchy.get(required_level, 1)
        
        if candidate_score >= required_score:
            return min(100.0, 80.0 + (years * 2))  # Bonus for extra experience
        else:
            return max(30.0, 60.0 - ((required_score - candidate_score) * 20))

    def calculate_education_match(self, education_analysis: Dict, job_requirements: str) -> float:
        """Calculate education match percentage"""
        base_score = 60.0
        
        # Bonus for relevant CS education
        if education_analysis['cs_related']:
            base_score += 25.0
        
        # Bonus for education level
        level_bonuses = {
            'advanced': 15.0,
            'bachelor': 10.0,
            'associate': 5.0,
            'bootcamp': 8.0
        }
        
        base_score += level_bonuses.get(education_analysis['level'], 0)
        
        return min(100.0, base_score)

    def generate_strengths(self, resume_skills: Dict, experience_analysis: Dict, education_analysis: Dict) -> str:
        """Generate candidate strengths summary"""
        strengths = []
        
        # Technical skills strengths
        for category, skills in resume_skills.items():
            if skills:
                strengths.append(f"Strong {category.replace('_', ' ')} skills: {', '.join(skills[:3])}")
        
        # Experience strengths
        if experience_analysis['years'] >= 5:
            strengths.append(f"Extensive experience ({experience_analysis['years']} years)")
        elif experience_analysis['years'] >= 2:
            strengths.append(f"Good experience level ({experience_analysis['years']} years)")
        
        # Education strengths
        if education_analysis['cs_related']:
            strengths.append("Relevant computer science education")
        
        if education_analysis['level'] == 'advanced':
            strengths.append("Advanced degree holder")
        
        return "; ".join(strengths) if strengths else "General background suitable for the role"

    def generate_concerns(self, skills_match: float, experience_match: float, education_match: float) -> str:
        """Generate potential concerns"""
        concerns = []
        
        if skills_match < 40:
            concerns.append("Limited technical skills match")
        
        if experience_match < 50:
            concerns.append("Experience level may not fully meet requirements")
        
        if education_match < 60:
            concerns.append("Education background may need additional consideration")
        
        return "; ".join(concerns) if concerns else "No major concerns identified"

    def generate_summary(self, career_application, overall_match: float) -> str:
        """Generate AI summary of the candidate"""
        name = f"{career_application.first_name} {career_application.last_name}"
        
        if overall_match >= 80:
            return f"{name} appears to be an excellent candidate with strong alignment to the role requirements."
        elif overall_match >= 60:
            return f"{name} shows good potential for the role with several matching qualifications."
        elif overall_match >= 40:
            return f"{name} has some relevant qualifications but may need additional evaluation."
        else:
            return f"{name} has limited alignment with the role requirements."

    def generate_recommendation(self, overall_match: float) -> str:
        """Generate AI recommendation"""
        if overall_match >= 80:
            return 'highly_recommended'
        elif overall_match >= 65:
            return 'recommended'
        elif overall_match >= 45:
            return 'consider'
        else:
            return 'not_recommended'


# Initialize the analyzer
resume_analyzer = ResumeAnalyzer()


def analyze_career_application(career_application):
    """Main function to analyze a career application"""
    try:
        job_posting = career_application.job_posting
        analysis_results = resume_analyzer.analyze_job_match(career_application, job_posting)
        
        # Update the career application with AI analysis
        career_application.ai_analysis_completed = True
        career_application.ai_match_score = analysis_results['overall_match']
        career_application.ai_skills_match = analysis_results['skills_match']
        career_application.ai_experience_match = analysis_results['experience_match']
        career_application.ai_education_match = analysis_results['education_match']
        career_application.ai_summary = analysis_results['summary']
        career_application.ai_strengths = analysis_results['strengths']
        career_application.ai_concerns = analysis_results['concerns']
        career_application.ai_recommendation = analysis_results['recommendation']
        career_application.ai_processed_at = timezone.now()
        
        career_application.save()
        
        logger.info(f"AI analysis completed for application {career_application.id}")
        return analysis_results
        
    except Exception as e:
        logger.error(f"Error analyzing career application {career_application.id}: {str(e)}")
        return None
