"""
Streamlit Career Coach Application
Web interface for CV analysis with multiple input methods.
"""

import streamlit as st
import io
import requests
from bs4 import BeautifulSoup
try:
    from cv_analyzer import CVAnalyzer
except ImportError as e:
    raise
from psychometric_assessment import PsychometricAssessment
try:
    # Try importing pypdf (new package name) first
    import pypdf as PyPDF2
except ImportError:
    # Fallback to PyPDF2 for older installations
    try:
        import PyPDF2
    except ImportError as e:
        st.error("❌ PDF library not found. Please run: pip install pypdf")
        raise
from docx import Document
import google.generativeai as genai
import os
import json
import re
import streamlit_authenticator as stauth
from datetime import datetime
from supabase import create_client, Client



def extract_text_from_pdf(uploaded_file) -> str:
    """Extract text from uploaded PDF file."""
    try:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return ""


def extract_text_from_docx(uploaded_file) -> str:
    """Extract text from uploaded DOCX file."""
    try:
        doc = Document(uploaded_file)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        st.error(f"Error extracting text from DOCX: {str(e)}")
        return ""


def extract_text_from_url(url: str) -> str:
    """Extract text from a job listing URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching URL: {str(e)}")
        return ""
    except Exception as e:
        st.error(f"Error extracting text from URL: {str(e)}")
        return ""


def calculate_potential_match_score(gemini_analysis: dict) -> int:
    """Calculate potential match score if suggestions are implemented."""
    current_score = gemini_analysis.get('match_score', 0)
    
    # Base potential improvement factors
    missing_skills = gemini_analysis.get('missing_hard_skills', [])
    cv_improvements = gemini_analysis.get('cv_improvements', [])
    power_word_swaps = gemini_analysis.get('power_word_swaps', [])
    
    # Calculate potential improvement
    improvement = 0
    
    # Missing skills impact (each missing skill addressed = 2-3 points)
    if missing_skills:
        # If user addresses missing skills, they can gain points
        # Assume addressing 50% of missing skills improves score
        improvement += min(len(missing_skills) * 2, 15)  # Max 15 points from skills
    
    # CV improvements impact (each improvement = 1-2 points)
    if cv_improvements:
        improvement += min(len(cv_improvements) * 1.5, 10)  # Max 10 points from improvements
    
    # Power word swaps impact (smaller impact, but adds professionalism)
    if power_word_swaps:
        improvement += min(len(power_word_swaps) * 0.5, 5)  # Max 5 points from power words
    
    # Calculate potential score (capped at 100)
    potential_score = min(current_score + improvement, 100)
    
    # Ensure potential is always at least slightly higher than current (if there are suggestions)
    if (missing_skills or cv_improvements or power_word_swaps) and potential_score <= current_score:
        potential_score = min(current_score + 5, 100)
    
    return int(round(potential_score))


def extract_job_title(job_description: str) -> str:
    """Extract job title from job description."""
    if not job_description:
        return "Untitled Position"
    
    # Look for common patterns
    patterns = [
        r'(?:Job Title|Position|Role):\s*([^\n]+)',
        r'(?:We are|We\'re) (?:looking for|seeking|hiring) (?:a|an)?\s*([A-Z][a-zA-Z\s&]+?)(?:\s+(?:to|who|with|at))',
        r'^([A-Z][a-zA-Z\s&]+?)\s+(?:at|with|for)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, job_description, re.IGNORECASE | re.MULTILINE)
        if match:
            title = match.group(1).strip()
            if len(title) < 100:  # Reasonable title length
                return title
    
    # Fallback: use first line or first 50 chars
    first_line = job_description.split('\n')[0].strip()
    if first_line and len(first_line) < 100:
        return first_line[:50]
    
    return "Untitled Position"


def extract_company_name(job_url: str, job_description: str) -> str:
    """Extract company name from job URL or job description."""
    company_name = ""
    
    # Try to extract from URL
    if job_url:
        # Common patterns in job URLs
        patterns = [
            r'/(?:company|jobs|careers)/([^/]+)',
            r'@([^/]+)',
            r'company=([^&]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, job_url, re.IGNORECASE)
            if match:
                company_name = match.group(1).replace('-', ' ').title()
                break
    
    # If not found in URL, try to extract from job description
    if not company_name and job_description:
        # Look for common patterns like "About [Company]" or "[Company] is looking for"
        patterns = [
            r'(?:at|with|from)\s+([A-Z][a-zA-Z\s&]+?)(?:\s+(?:is|are|seeks|looking))',
            r'([A-Z][a-zA-Z\s&]+?)\s+(?:is|are)\s+(?:looking|seeking)',
            r'About\s+([A-Z][a-zA-Z\s&]+?)(?:\.|,|\n)',
        ]
        for pattern in patterns:
            match = re.search(pattern, job_description, re.IGNORECASE)
            if match:
                potential_name = match.group(1).strip()
                # Filter out common false positives
                if len(potential_name.split()) <= 5 and potential_name.lower() not in ['the', 'a', 'an']:
                    company_name = potential_name
                    break
    
    return company_name.strip() if company_name else "the company"


def get_company_research(company_name: str, job_url: str = "", job_description: str = "") -> dict:
    """Get company research from Gemini AI."""
    try:
        # Get API key from environment or Streamlit secrets
        api_key = os.getenv('GEMINI_API_KEY') or st.secrets.get('GEMINI_API_KEY', None)
        
        if not api_key:
            return {"error": "Google API key not found. Please set GEMINI_API_KEY environment variable or add it to Streamlit secrets."}
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Create the prompt
        context_info = ""
        if job_url:
            context_info += f"\nJob URL: {job_url}"
        if job_description:
            context_info += f"\nJob Description (first 500 chars): {job_description[:500]}"
        
        prompt = f"""Research the following company and provide comprehensive intelligence for a job interview candidate.

Company Name: {company_name}
{context_info}

Provide your research in the following JSON format:
{{
    "company_name": "{company_name}",
    "financial_performance": {{
        "market_position": "<description of current market position>",
        "financial_health": "<recent financial health, funding rounds, profit trends, or share price if public>",
        "key_metrics": "<any relevant financial metrics or indicators>"
    }},
    "recent_news": [
        {{
            "headline": "<headline 1>",
            "summary": "<brief summary>",
            "significance": "<why this matters>"
        }},
        {{
            "headline": "<headline 2>",
            "summary": "<brief summary>",
            "significance": "<why this matters>"
        }},
        {{
            "headline": "<headline 3>",
            "summary": "<brief summary>",
            "significance": "<why this matters>"
        }}
    ],
    "interview_deep_dive": [
        "<Specific thing 1 to research on company website or LinkedIn>",
        "<Specific thing 2 to research on company website or LinkedIn>",
        "<Specific thing 3 to research on company website or LinkedIn>",
        "<Specific thing 4 to research on company website or LinkedIn>",
        "<Specific thing 5 to research on company website or LinkedIn>"
    ]
}}

IMPORTANT: 
- Be specific and actionable in your research
- Focus on recent information (last 12-18 months)
- For financial performance, estimate based on available public information
- For interview deep-dive items, be specific about what to look for (e.g., "Check their 'About Us' page for their mission statement and note their core values")
- Return ONLY valid JSON. Do not include any text before or after the JSON."""
        
        # Generate response
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Try to extract JSON from the response
        json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
        
        # Parse JSON
        research_data = json.loads(response_text)
        return research_data
        
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse JSON response: {str(e)}", "raw_response": response.text if 'response' in locals() else "No response"}
    except Exception as e:
        return {"error": f"Error generating company research: {str(e)}"}


def get_gemini_analysis(cv_text: str, job_description: str) -> dict:
    """Get CV analysis from Gemini AI acting as an elite UK Headhunter."""
    try:
        # Get API key from environment or Streamlit secrets
        api_key = os.getenv('GEMINI_API_KEY') or st.secrets.get('GEMINI_API_KEY', None)
        
        if not api_key:
            return {"error": "Google API key not found. Please set GEMINI_API_KEY environment variable or add it to Streamlit secrets."}
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Create the prompt
        prompt = f"""Act as an elite UK Headhunter with 15+ years of experience. Analyse the following CV against the job description provided.

CV Text:
{cv_text}

Job Description:
{job_description}

Provide your analysis in the following JSON format:
{{
    "match_score": <number 0-100>,
    "salary_range": "<UK salary range, e.g., £45,000 - £55,000>",
    "missing_hard_skills": [
        "<skill 1>",
        "<skill 2>",
        "<skill 3>"
    ],
    "interview_questions": [
        "<Question 1 targeting skill gaps>",
        "<Question 2 targeting skill gaps>",
        "<Question 3 targeting skill gaps>"
    ],
    "power_word_swaps": [
        {{
            "original": "<generic word>",
            "replacement": "<power word>",
            "context": "<brief explanation>"
        }},
        {{
            "original": "<generic word>",
            "replacement": "<power word>",
            "context": "<brief explanation>"
        }},
        {{
            "original": "<generic word>",
            "replacement": "<power word>",
            "context": "<brief explanation>"
        }},
        {{
            "original": "<generic word>",
            "replacement": "<power word>",
            "context": "<brief explanation>"
        }},
        {{
            "original": "<generic word>",
            "replacement": "<power word>",
            "context": "<brief explanation>"
        }}
    ],
    "cv_improvements": [
        {{
            "current": "<current bullet point>",
            "improved": "<improved bullet point>",
            "reason": "<why this change helps>"
        }},
        {{
            "current": "<current bullet point>",
            "improved": "<improved bullet point>",
            "reason": "<why this change helps>"
        }},
        {{
            "current": "<current bullet point>",
            "improved": "<improved bullet point>",
            "reason": "<why this change helps>"
        }}
    ]
}}

IMPORTANT: Return ONLY valid JSON. Do not include any text before or after the JSON."""
        
        # Generate response
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Try to extract JSON from the response
        # Sometimes Gemini wraps JSON in markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
        
        # Parse JSON
        analysis_data = json.loads(response_text)
        return analysis_data
        
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse JSON response: {str(e)}", "raw_response": response.text if 'response' in locals() else "No response"}
    except Exception as e:
        return {"error": f"Error generating analysis: {str(e)}"}


def get_cover_letter(cv_text: str, job_description: str, assessment_profile: dict = None) -> str:
    """Generate a personalized cover letter using Gemini AI."""
    try:
        # Get API key from environment or Streamlit secrets
        api_key = os.getenv('GEMINI_API_KEY') or st.secrets.get('GEMINI_API_KEY', None)
        
        if not api_key:
            return "Error: Google API key not found. Please set GEMINI_API_KEY environment variable or add it to Streamlit secrets."
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Build personality context if assessment is available
        personality_context = ""
        if assessment_profile:
            top_traits = [trait for trait, _ in assessment_profile.get('top_traits', [])[:3]]
            comm_style = assessment_profile.get('communication_style', '')
            work_style = assessment_profile.get('work_style', '')
            motivation_style = assessment_profile.get('motivation_style', '')
            
            personality_context = f"""
IMPORTANT - Use this personality profile to tailor the language and tone:
- Top Personality Traits: {', '.join(top_traits)}
- Communication Style: {comm_style}
- Work Style: {work_style}
- Motivation Style: {motivation_style}

Write the cover letter using language that reflects these traits. For example:
- If communication style is 'direct and concise', use clear, straightforward language
- If work style is 'collaborative team player', emphasize teamwork and collaboration
- If motivation style is 'results-driven', focus on achievements and outcomes
- Match the tone to their personality traits naturally
"""
        else:
            personality_context = """
Use professional, engaging language suitable for a UK job application. 
Write in a confident but not overly formal tone.
"""
        
        # Create the prompt
        prompt = f"""You are an expert UK career coach and cover letter writer. Draft a compelling cover letter for this job application.

CV Text:
{cv_text[:2000]}

Job Description:
{job_description[:2000]}

{personality_context}

Requirements:
1. Write a professional UK-style cover letter (3-4 paragraphs)
2. Address the letter appropriately (use "Dear Hiring Manager" if no specific name is provided)
3. Start with a strong opening that shows genuine interest in the role
4. Highlight 2-3 key experiences from the CV that align with the job requirements
5. Demonstrate understanding of the company/role by referencing specific aspects from the job description
6. Close with enthusiasm and a clear call to action
7. Keep it concise, professional, and impactful
8. Use UK English spelling and conventions
9. The language should match the personality profile provided (if available)

Format the cover letter as a proper business letter with appropriate spacing and structure."""
        
        # Generate response
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"Error generating cover letter: {str(e)}"


def get_supabase_client() -> Client:
    """Initialize and return Supabase client."""
    try:
        supabase_url = os.getenv('SUPABASE_URL') or st.secrets.get('SUPABASE_URL', None)
        supabase_key = os.getenv('SUPABASE_KEY') or st.secrets.get('SUPABASE_KEY', None)
        
        if not supabase_url or not supabase_key:
            return None
        
        supabase: Client = create_client(supabase_url, supabase_key)
        return supabase
    except Exception as e:
        return None


def save_analysis_to_supabase(supabase: Client, username: str, job_title: str, job_description: str, 
                              gemini_analysis: dict, company_research: dict = None, cover_letter: str = None, 
                              email: str = None):
    """Save analysis results to Supabase career_history table. Returns (success: bool, error_message: str)."""
    try:
        if not supabase:
            return False, "Supabase client not available"
        
        company_name = extract_company_name("", job_description)
        
        # Try to get company name from company_research if available (more accurate)
        if company_research:
            # Handle both dict and JSON string formats
            research_dict = company_research
            if isinstance(company_research, str):
                try:
                    research_dict = json.loads(company_research)
                except:
                    research_dict = None
            
            if research_dict and isinstance(research_dict, dict):
                research_company = research_dict.get('company_name') or research_dict.get('company')
                if research_company:
                    company_name = research_company
        
        data = {
            'job_title': job_title,
            'company_name': company_name,
            'match_score': gemini_analysis.get('match_score', 0) if gemini_analysis else 0,
            'analysis_text': json.dumps(gemini_analysis) if gemini_analysis else '{}',
            'company_research': json.dumps(company_research) if company_research else None,
            'cover_letter': cover_letter[:10000] if cover_letter else None,
            'created_at': datetime.now().isoformat()
        }
        
        if email:
            data['user_email'] = email
        
        result = supabase.table('career_history').insert(data).execute()
        
        if result.data:
            return True, None
        else:
            return False, "No data returned from Supabase insert"
            
    except Exception as e:
        error_msg = str(e)
        
        if hasattr(e, 'message'):
            error_msg = e.message
        elif hasattr(e, 'args') and len(e.args) > 0:
            error_msg = str(e.args[0])
        
        if hasattr(e, 'details') and e.details:
            error_msg = f"{error_msg} - Details: {e.details}"
        elif hasattr(e, 'hint') and e.hint:
            error_msg = f"{error_msg} - Hint: {e.hint}"
        
        return False, error_msg


def load_analysis_from_supabase(supabase: Client, username: str, history_id: int, email: str = None) -> dict:
    """Load a specific analysis from Supabase."""
    try:
        if not supabase:
            return None
        
        # Load by ID and user_email if provided
        if email:
            result = supabase.table('career_history').select('*').eq('id', history_id).eq('user_email', email).execute()
        else:
            result = supabase.table('career_history').select('*').eq('id', history_id).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception as e:
        st.error(f"Error loading analysis: {str(e)}")
        return None


def get_user_history(supabase: Client, username: str) -> list:
    """Get all analysis history for a user by username."""
    try:
        if not supabase:
            return []
        
        result = supabase.table('career_history').select('id, job_title, company_name, match_score, created_at').eq('username', username).order('created_at', desc=True).execute()
        
        return result.data if result.data else []
    except Exception as e:
        return []


def load_users_from_database(supabase: Client) -> dict:
    """Load users from Supabase database. Tries 'user_profiles' table first, then 'user_accounts', then 'users' table."""
    users = {}
    try:
        if not supabase:
            return {}
        
        # Try to fetch users from 'user_profiles' table first (as suggested by Supabase)
        # The table has columns: username, email, name, password_hash, created_at
        try:
            result = supabase.table('user_profiles').select('username, name, password_hash, email').execute()
            if result.data:
                for user in result.data:
                    username = user.get('username', '').lower()
                    users[username] = {
                        'name': user.get('name', username),
                        'password': user.get('password_hash', ''),  # Use password_hash for streamlit-authenticator
                        'email': user.get('email', f'{username}@example.com')
                    }
        except Exception as e1:
            # Fallback to 'user_accounts' table (newer schema)
            try:
                result = supabase.table('user_accounts').select('username, full_name, password_hash, email').execute()
                if result.data:
                    for user in result.data:
                        username = user.get('username', '').lower()
                        users[username] = {
                            'name': user.get('full_name', username),
                            'password': user.get('password_hash', ''),
                            'email': user.get('email', f'{username}@example.com')
                        }
            except Exception as e2:
                # Final fallback to 'users' table (older schema)
                try:
                    result = supabase.table('users').select('username, name, password, email').execute()
                    if result.data:
                        for user in result.data:
                            username = user.get('username', '').lower()
                            users[username] = {
                                'name': user.get('name', username),
                                'password': user.get('password', ''),
                                'email': user.get('email', f'{username}@example.com')
                            }
                except:
                    pass
        
    except Exception as e:
        pass
    
    return users


def save_user_to_database(supabase: Client, username: str, name: str, password_hash: str, email: str) -> bool:
    """Save a new user to Supabase database. Tries 'user_profiles' table first, then 'user_accounts', then 'users' table."""
    try:
        if not supabase:
            return False
        
        username_lower = username.lower()
        
        # Try 'user_profiles' table first (as suggested by Supabase)
        try:
            # Check if user already exists
            existing = supabase.table('user_profiles').select('username').eq('username', username_lower).execute()
            if existing.data:
                return False  # User already exists
            
            # Insert new user
            # The table has columns: username, email, name, password_hash, created_at
            user_data = {
                'username': username_lower,
                'name': name,
                'password_hash': password_hash,
                'email': email,
                'created_at': datetime.now().isoformat()
            }
            
            result = supabase.table('user_profiles').insert(user_data).execute()
            return True
        except Exception as e1:
            # Try 'user_accounts' table (newer schema)
            try:
                # Check if user already exists
                existing = supabase.table('user_accounts').select('username').eq('username', username_lower).execute()
                if existing.data:
                    return False  # User already exists
                
                # Insert new user
                user_data = {
                    'username': username_lower,
                    'full_name': name,
                    'password_hash': password_hash,
                    'email': email,
                    'created_at': datetime.now().isoformat()
                }
                
                result = supabase.table('user_accounts').insert(user_data).execute()
                return True
            except Exception as e2:
                # Try 'users' table (older schema)
                try:
                    # Check if user already exists
                    existing = supabase.table('users').select('username').eq('username', username_lower).execute()
                    if existing.data:
                        return False  # User already exists
                    
                    # Insert new user
                    user_data = {
                        'username': username_lower,
                        'name': name,
                        'password': password_hash,
                        'email': email,
                        'created_at': datetime.now().isoformat()
                    }
                    
                    result = supabase.table('users').insert(user_data).execute()
                    return True
                except Exception as e3:
                    return False
    except Exception as e:
        return False


def get_user_history_by_email(supabase: Client, email: str) -> list:
    """
    Get all analysis history for a user by email.
    Only returns records where user_email matches the provided email (multi-user privacy).
    Ordered by date (newest first).
    """
    try:
        if not supabase or not email:
            return []
        
        # Query career_history table filtering by user_email for privacy
        # Try with display_name first, fallback to without if column doesn't exist
        try:
            result = supabase.table('career_history').select(
                'id, job_title, company_name, match_score, created_at, user_email, display_name'
            ).eq('user_email', email).order('created_at', desc=True).execute()
        except Exception as e:
            # If display_name column doesn't exist, try without it
            try:
                result = supabase.table('career_history').select(
                    'id, job_title, company_name, match_score, created_at, user_email'
                ).eq('user_email', email).order('created_at', desc=True).execute()
            except Exception as e2:
                # Log error but return empty list
                st.error(f"Error fetching history: {str(e2)}")
                return []
        
        return result.data if result.data else []
    except Exception as e:
        st.error(f"Error in get_user_history_by_email: {str(e)}")
        return []


def authenticate_user_from_database(supabase: Client, username: str, password: str) -> tuple:
    """
    Authenticate user by querying user_accounts table in Supabase.
    Returns (is_authenticated: bool, user_data: dict or None)
    """
    try:
        if not supabase:
            return False, None
        
        username_lower = username.lower()
        
        # Query user_profiles table first (as suggested by Supabase), then fallback to user_accounts
        # Try with 'name' column first (common alternative to 'full_name')
        result = None
        try:
            # Try user_profiles with 'name' column (instead of 'full_name')
            # First, let's try without case sensitivity - query all users and filter
            all_users = supabase.table('user_profiles').select('username, name, password_hash, email').execute()
            # Filter for matching username (case-insensitive)
            result_data = None
            if all_users.data:
                for user in all_users.data:
                    db_username = user.get('username', '')
                    db_username_lower = db_username.lower()
                    if db_username_lower == username_lower:
                        result_data = [user]
                        break
            result = type('Result', (), {'data': result_data})()
        except Exception as e1:
            # Try with 'full_name' column
            try:
                result = supabase.table('user_profiles').select('username, full_name, password_hash, email').eq('username', username_lower).execute()
            except Exception as e2:
                # Fallback to user_accounts table
                try:
                    result = supabase.table('user_accounts').select('username, full_name, password_hash, email').eq('username', username_lower).execute()
                except Exception as e3:
                    raise e3
        
        if result is None:
            return False, None
        
        if result.data and len(result.data) > 0:
            user_data = result.data[0]
            stored_hash = user_data.get('password_hash', '')
            db_username = user_data.get('username', '')
            # Get name from either 'name' or 'full_name' column
            user_name = user_data.get('name') or user_data.get('full_name') or db_username
            
            if not stored_hash:
                return False, None
            
            # Verify password using bcrypt (works with both bcrypt and stauth.Hasher hashes)
            import bcrypt
            try:
                # Try bcrypt check first (works for both bcrypt and stauth.Hasher hashes)
                password_check = bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
                if password_check:
                    return True, {
                        'username': user_data.get('username', username_lower),
                        'name': user_name,
                        'email': user_data.get('email', f'{username_lower}@example.com')
                    }
                else:
                    return False, None
            except Exception as bcrypt_error:
                return False, None
        else:
            return False, None
    except Exception as e:
        return False, None


def get_user_email_from_database(supabase: Client, username: str) -> str:
    """Get user email from database. Tries 'user_profiles' table first, then 'user_accounts', then 'users' table."""
    try:
        if not supabase:
            # Fallback to hardcoded admin email
            if username.lower() == 'admin':
                return 'admin@example.com'
            return f"{username}@example.com"
        
        username_lower = username.lower()
        
        # Try 'user_profiles' table first (as suggested by Supabase)
        try:
            result = supabase.table('user_profiles').select('email').eq('username', username_lower).execute()
            if result.data and len(result.data) > 0:
                return result.data[0].get('email', f"{username}@example.com")
        except:
            # Try 'user_accounts' table (newer schema)
            try:
                result = supabase.table('user_accounts').select('email').eq('username', username_lower).execute()
                if result.data and len(result.data) > 0:
                    return result.data[0].get('email', f"{username}@example.com")
            except:
                # Try 'users' table (older schema)
                try:
                    result = supabase.table('users').select('email').eq('username', username_lower).execute()
                    if result.data and len(result.data) > 0:
                        return result.data[0].get('email', f"{username}@example.com")
                except:
                    pass
    except:
        pass
    
    # Fallback to username@example.com if email not found
    return f"{username}@example.com"


def load_users_from_database(supabase: Client) -> dict:
    """Load users from Supabase database. Tries 'user_profiles' table first, then 'user_accounts', then 'users' table."""
    users = {}
    try:
        if not supabase:
            return {}
        
        # Try to fetch users from 'user_profiles' table first (as suggested by Supabase)
        # The table has columns: username, email, name, password_hash, created_at
        try:
            result = supabase.table('user_profiles').select('username, name, password_hash, email').execute()
            if result.data:
                for user in result.data:
                    username = user.get('username', '').lower()
                    users[username] = {
                        'name': user.get('name', username),
                        'password': user.get('password_hash', ''),  # Use password_hash for streamlit-authenticator
                        'email': user.get('email', f'{username}@example.com')
                    }
        except Exception as e1:
            # Fallback to 'user_accounts' table (newer schema)
            try:
                result = supabase.table('user_accounts').select('username, full_name, password_hash, email').execute()
                if result.data:
                    for user in result.data:
                        username = user.get('username', '').lower()
                        users[username] = {
                            'name': user.get('full_name', username),
                            'password': user.get('password_hash', ''),
                            'email': user.get('email', f'{username}@example.com')
                        }
            except Exception as e2:
                # Final fallback to 'users' table (older schema)
                try:
                    result = supabase.table('users').select('username, name, password, email').execute()
                    if result.data:
                        for user in result.data:
                            username = user.get('username', '').lower()
                            users[username] = {
                                'name': user.get('name', username),
                                'password': user.get('password', ''),
                                'email': user.get('email', f'{username}@example.com')
                            }
                except:
                    pass
        
    except Exception as e:
        pass
    
    return users


def save_user_to_database(supabase: Client, username: str, name: str, password_hash: str, email: str) -> bool:
    """Save a new user to Supabase database. Tries 'user_profiles' table first, then 'user_accounts', then 'users' table."""
    try:
        if not supabase:
            return False
        
        username_lower = username.lower()
        
        # Try 'user_profiles' table first (as suggested by Supabase)
        try:
            # Check if user already exists
            existing = supabase.table('user_profiles').select('username').eq('username', username_lower).execute()
            if existing.data:
                return False  # User already exists
            
            # Insert new user
            # The table has columns: username, email, name, password_hash, created_at
            user_data = {
                'username': username_lower,
                'name': name,
                'password_hash': password_hash,
                'email': email,
                'created_at': datetime.now().isoformat()
            }
            
            result = supabase.table('user_profiles').insert(user_data).execute()
            return True
        except Exception as e1:
            # Try 'user_accounts' table (newer schema)
            try:
                # Check if user already exists
                existing = supabase.table('user_accounts').select('username').eq('username', username_lower).execute()
                if existing.data:
                    return False  # User already exists
                
                # Insert new user
                user_data = {
                    'username': username_lower,
                    'full_name': name,
                    'password_hash': password_hash,
                    'email': email,
                    'created_at': datetime.now().isoformat()
                }
                
                result = supabase.table('user_accounts').insert(user_data).execute()
                return True
            except Exception as e2:
                # Try 'users' table (older schema)
                try:
                    # Check if user already exists
                    existing = supabase.table('users').select('username').eq('username', username_lower).execute()
                    if existing.data:
                        return False  # User already exists
                    
                    # Insert new user
                    user_data = {
                        'username': username_lower,
                        'name': name,
                        'password': password_hash,
                        'email': email,
                        'created_at': datetime.now().isoformat()
                    }
                    
                    result = supabase.table('users').insert(user_data).execute()
                    return True
                except Exception as e3:
                    return False
    except Exception as e:
        return False


def setup_authentication():
    """Set up authentication configuration, loading users from database."""
    # Get Supabase client
    supabase = get_supabase_client()
    
    users_dict = load_users_from_database(supabase)
    
    # Configuration dictionary for authentication
    config = {
        'credentials': {
            'usernames': users_dict
        },
        'cookie': {
            'expiry_days': 30,
            'key': 'career_coach_auth_key',
            'name': 'career_coach_cookie'
        },
        'preauthorized': {
            'emails': []
        }
    }
    
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )
    
    return authenticator


def main():
    """Main Streamlit application."""
        
    # IMPORTANT: st.set_page_config must be the first Streamlit command
    try:
        st.set_page_config(
            page_title="Career Coach - CV Analyser",
            page_icon="💼",
            layout="wide"
        )
    except Exception as e:
        pass
    
    # Set up authentication
    authenticator = setup_authentication()
    
    # Check if user is already authenticated via session state (for manual login)
    if 'authenticated' in st.session_state and st.session_state.get('authenticated') == True:
                # User is authenticated via session state, proceed to app
        name = st.session_state.get('name', 'User')
        username = st.session_state.get('username', 'user')
        authentication_status = True
        login_result = (name, authentication_status, username)
    else:
        # Check authentication
        # First try 'unrendered' to check if already authenticated
        try:
            login_result = authenticator.login(location='unrendered', key='LoginCheck')
        except Exception as login_error:
            error_str = str(login_error)
            if "User not authorized" in error_str:
                login_result = None
            else:
                login_result = None
            
    if login_result is None:
        st.title("💼 Career Coach - Login")
        st.markdown("Please log in to access the Career Coach application.")
        
        with st.expander("New User? Register Here"):
            try:
                supabase = get_supabase_client()
                
                st.markdown("### Create Your Account")
                reg_username = st.text_input("Username", key="reg_username", help="Choose a unique username")
                reg_name = st.text_input("Full Name", key="reg_name", help="Enter your full name")
                reg_email = st.text_input("Email", key="reg_email", help="Enter your email address")
                reg_password = st.text_input("Password", type="password", key="reg_password", help="Choose a secure password")
                reg_password_confirm = st.text_input("Confirm Password", type="password", key="reg_password_confirm", help="Re-enter your password")
                
                if st.button("Register", key="register_button", type="primary"):
                    if not reg_username or not reg_name or not reg_email or not reg_password:
                        st.error("Please fill in all fields.")
                    elif reg_password != reg_password_confirm:
                        st.error("Passwords do not match.")
                    elif len(reg_password) < 6:
                        st.error("Password must be at least 6 characters long.")
                    else:
                        password_hash = stauth.Hasher([reg_password]).generate()[0]
                        
                        if supabase:
                            if save_user_to_database(supabase, reg_username, reg_name, password_hash, reg_email):
                                st.success("✅ Registration successful! Please log in with your new credentials.")
                                st.session_state['reload_auth'] = True
                            else:
                                st.error("❌ Registration failed. Username may already exist.")
                        else:
                            st.error("❌ Database not available. Please check your configuration.")
            except Exception as e:
                st.error(f"Registration error: {str(e)}")
        
        login_form_error = False
        try:
            if st.session_state.get('reload_auth', False):
                authenticator = setup_authentication()
                st.session_state['reload_auth'] = False
            
            try:
                authenticator.login(
                    location='main', 
                    key='LoginForm',
                    fields={'Form name': 'Login', 'Username': 'Username', 'Password': 'Password'}
                )
            except (TypeError, ValueError):
                authenticator.login(location='main', key='LoginForm')
        except Exception as e:
            error_str = str(e)
            login_form_error = True
            if "User not authorized" not in error_str:
                st.error(f"Authenticator error: {error_str}")
        
        if login_form_error:
            st.markdown("---")
            st.write("**Please log in:**")
            with st.form("login_form", clear_on_submit=False):
                username_input = st.text_input("Username", key="fallback_username")
                password_input = st.text_input("Password", type="password", key="fallback_password")
                submit_button = st.form_submit_button("Login", type="primary", use_container_width=True)
                
                if submit_button:
                    supabase = get_supabase_client()
                    is_authenticated, user_data = authenticate_user_from_database(supabase, username_input, password_input)
                    
                    if is_authenticated and user_data:
                        st.session_state['authenticated'] = True
                        st.session_state['name'] = user_data['name']
                        st.session_state['username'] = user_data['username']
                        st.session_state['user_email'] = user_data['email']
                        st.rerun()
                        return  # Prevent further execution after rerun
                    else:
                        st.error("Invalid username or password")
        
        st.stop()
    
    # Unpack the result - login_result is a tuple (name, authentication_status, username)
    name, authentication_status, username = login_result
    
    # Get user email from database and store in session state for privacy filtering
    if authentication_status == True:
        supabase = get_supabase_client()
        user_email = get_user_email_from_database(supabase, username)
        st.session_state['user_email'] = user_email
        
    # Check authentication status
    if authentication_status == True:
        # User is successfully authenticated - proceed to show the app
                pass  # Continue execution below
    elif authentication_status == False:
        # Login failed - show error and login form again
        st.error('Username/password is incorrect')
        authenticator.login(location='main', key='LoginFormRetry')
        st.stop()
        return
    else:
        # authentication_status is None or other value - show login form
        authenticator.login(location='main', key='LoginForm')
        st.stop()
        return
    
    # User is authenticated - show the app
        # Add logout button and Application History in sidebar
    with st.sidebar:
        st.write(f'Welcome *{name}*')
        
        # Logout button - handle both streamlit-authenticator and manual login
        logout_clicked = False
        try:
            # Try streamlit-authenticator logout first (works if user logged in via authenticator)
            logout_clicked = authenticator.logout(button_name='Logout', location='sidebar')
        except Exception as logout_error:
            # If logout fails (e.g., user logged in via manual form), use custom logout
            # Create custom logout button for manual login
            if st.button('Logout', key='custom_logout'):
                logout_clicked = True
        
        if logout_clicked:
            # Clear all session state on logout
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
        st.markdown("## 📜 Application History")
        
        # Initialize Supabase client
        supabase = get_supabase_client()
        
        if supabase:
            # Get user's email from session state (set during login) or database
            user_email = st.session_state.get('user_email') or get_user_email_from_database(supabase, username)
            
            # Debug: Show email being used for query
            if not user_email:
                st.warning("⚠️ No user email found. History cannot be loaded.")
            
            # Get user's history by email - ensures multi-user privacy
            # Only returns records where email matches the logged-in user
            # Ordered by date (newest first)
            history = get_user_history_by_email(supabase, user_email)
            
            # Debug: Show count of history items found
            if user_email:
                with st.expander("🔍 Debug: History Query", expanded=False):
                    st.write(f"Querying with email: `{user_email}`")
                    st.write(f"Found {len(history)} history items")
                    if history:
                        st.json([{"id": h.get('id'), "job_title": h.get('job_title'), "company": h.get('company_name'), "user_email": h.get('user_email')} for h in history[:3]])
            
            if history:
                # Store selected history ID in session state
                if 'selected_history_id' not in st.session_state:
                    st.session_state.selected_history_id = None
                
                # Create options for selectbox
                history_options = ["Select a past application..."]
                history_dict = {}
                
                for item in history:
                    job_title = item.get('job_title', 'Untitled')
                    company = item.get('company_name', '')
                    display_name = item.get('display_name', '')  # Custom display name if set
                    match_score = item.get('match_score', 0)
                    history_id = item.get('id')
                    created_at = item.get('created_at', '')
                    
                    # Format date
                    try:
                        if created_at:
                            date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            date_str = date_obj.strftime('%d %b %Y')
                        else:
                            date_str = 'Unknown date'
                    except:
                        date_str = 'Unknown date'
                    
                    # Create display label - use custom name if set, otherwise company name first, then job title
                    if display_name:
                        label = f"{display_name} ({match_score}/100) - {date_str}"
                    elif company:
                        label = f"{company} - {job_title} ({match_score}/100) - {date_str}"
                    else:
                        label = f"{job_title} ({match_score}/100) - {date_str}"
                    
                    history_options.append(label)
                    history_dict[label] = history_id
                
                # Display as selectbox
                selected_label = st.selectbox(
                    "Choose an application:",
                    history_options,
                    key="history_selectbox",
                    index=0 if st.session_state.selected_history_id is None else 0
                )
                
                # If a history item is selected, load it
                if selected_label != "Select a past application..." and selected_label in history_dict:
                    history_id = history_dict[selected_label]
                    
                    # Set selected history ID to trigger loading (only if different)
                    if st.session_state.selected_history_id != history_id:
                        st.session_state.selected_history_id = history_id
                        st.rerun()
                    
                    # Add rename functionality (only show if this is the currently selected item)
                    if st.session_state.selected_history_id == history_id:
                        with st.expander("✏️ Rename this application", expanded=False):
                            # Get current display name or default
                            current_item = next((item for item in history if item.get('id') == history_id), None)
                            current_display = current_item.get('display_name', '') if current_item else ''
                            current_company = current_item.get('company_name', '') if current_item else ''
                            current_job = current_item.get('job_title', '') if current_item else ''
                            
                            # Default suggestion
                            if not current_display and current_company:
                                default_name = current_company
                            elif not current_display:
                                default_name = current_job
                            else:
                                default_name = current_display
                            
                            new_display_name = st.text_input(
                                "Custom name:",
                                value=default_name,
                                key=f"rename_{history_id}",
                                help="Enter a custom name for this application. Leave empty to use company name."
                            )
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("💾 Save Name", key=f"save_name_{history_id}", use_container_width=True):
                                    # Update display_name in database
                                    try:
                                        update_data = {}
                                        if new_display_name and new_display_name.strip():
                                            update_data['display_name'] = new_display_name.strip()
                                        else:
                                            update_data['display_name'] = None  # Clear custom name
                                        
                                        supabase.table('career_history').update(update_data).eq('id', history_id).eq('user_email', user_email).execute()
                                        st.success("✅ Name updated!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Failed to update: {str(e)}")
                            
                            with col2:
                                if st.button("🗑️ Clear Name", key=f"clear_name_{history_id}", use_container_width=True):
                                    # Clear display_name in database
                                    try:
                                        supabase.table('career_history').update({'display_name': None}).eq('id', history_id).eq('user_email', user_email).execute()
                                        st.success("✅ Name cleared!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Failed to clear: {str(e)}")
            else:
                st.info("No previous analyses yet. Run your first analysis to see it here!")
        else:
            st.warning("⚠️ Supabase not configured. Add SUPABASE_URL and SUPABASE_KEY to secrets.")
    
        st.title("💼 Career Coach - CV Analyser")
    st.markdown("Compare your CV against job listings and get personalized improvement suggestions.")
    
    # Initialize session state
    if 'cv_text' not in st.session_state:
        st.session_state.cv_text = ""
    if 'psychometric_assessment' not in st.session_state:
        st.session_state.psychometric_assessment = PsychometricAssessment()
    if 'assessment_completed' not in st.session_state:
        st.session_state.assessment_completed = False
    if 'job_url' not in st.session_state:
        st.session_state.job_url = ""
    if 'job_description' not in st.session_state:
        st.session_state.job_description = ""
    if 'show_loaded_analysis' not in st.session_state:
        st.session_state.show_loaded_analysis = False
    
    # Check if we should show loaded analysis instead of input forms
    if st.session_state.get('show_loaded_analysis', False) and 'loaded_analysis' in st.session_state and st.session_state.loaded_analysis is not None:
        # Display loaded analysis instead of input forms
        gemini_analysis = st.session_state.loaded_analysis
        company_research = st.session_state.loaded_company_research if 'loaded_company_research' in st.session_state else {}
        cover_letter_text = st.session_state.loaded_cover_letter if 'loaded_cover_letter' in st.session_state else None
        
        # Display loaded analysis
        st.markdown("## 🚀 Career Strategy Dashboard (Loaded from History)")
        st.markdown("---")
        
        # Top metrics in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            match_score = gemini_analysis.get('match_score', 0)
            st.metric("📊 Current CV Match", f"{match_score}/100", delta=f"{match_score - 50}" if match_score >= 50 else None)
            st.caption("Your current match score")
        
        with col2:
            potential_score = calculate_potential_match_score(gemini_analysis)
            improvement = potential_score - match_score
            delta_label = f"+{improvement}" if improvement > 0 else None
            st.metric("🚀 Potential Match", f"{potential_score}/100", delta=delta_label, delta_color="normal")
            st.caption("With suggested improvements")
        
        with col3:
            salary_range = gemini_analysis.get('salary_range', 'N/A')
            st.metric("💷 UK Salary Benchmark", salary_range)
            st.caption("Estimated salary range")
        
        st.markdown("---")
        
        # Tabs for different sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Skill Gap Analysis", "🎤 Interview Prep", "✍️ CV Improvements", "🏢 Company Intelligence", "📝 Cover Letter"])
        
        with tab1:
            st.markdown("### Missing Hard Skills")
            missing_skills = gemini_analysis.get('missing_hard_skills', [])
            if missing_skills:
                for i, skill in enumerate(missing_skills, 1):
                    st.markdown(f"**{i}.** {skill}")
            else:
                st.info("No missing skills identified - great alignment!")
        
        with tab2:
            st.markdown("### 🎯 Tough Interview Questions")
            interview_questions = gemini_analysis.get('interview_questions', [])
            if interview_questions:
                for i, question in enumerate(interview_questions, 1):
                    with st.expander(f"Question {i}: {question[:60]}..." if len(question) > 60 else f"Question {i}"):
                        st.markdown(f"**{question}**")
            else:
                st.info("No specific interview questions generated.")
        
        with tab3:
            st.markdown("### ✍️ Power Word Swaps")
            power_words = gemini_analysis.get('power_word_swaps', [])
            if power_words:
                for i, swap in enumerate(power_words, 1):
                    st.markdown(f"**{i}. {swap.get('original', 'N/A')}** → **{swap.get('replacement', 'N/A')}**")
                    st.caption(f"💡 {swap.get('context', 'No context provided')}")
            
            st.markdown("---")
            st.markdown("### 📝 CV Bullet Point Improvements")
            cv_improvements = gemini_analysis.get('cv_improvements', [])
            if cv_improvements:
                for i, improvement in enumerate(cv_improvements, 1):
                    with st.expander(f"Improvement {i}"):
                        st.markdown("**Current:**")
                        st.text(improvement.get('current', 'N/A'))
                        st.markdown("**Improved:**")
                        st.success(improvement.get('improved', 'N/A'))
                        st.markdown(f"**Why:** {improvement.get('reason', 'No reason provided')}")
        
        with tab4:
            st.markdown("### 🏢 Company Intelligence")
            if company_research and "error" not in company_research:
                st.markdown("#### 💰 Financial Performance")
                financial = company_research.get('financial_performance', {})
                if financial:
                    st.markdown(f"**Market Position:** {financial.get('market_position', 'N/A')}")
                    st.markdown(f"**Financial Health:** {financial.get('financial_health', 'N/A')}")
                
                st.markdown("---")
                st.markdown("#### 📰 Recent News & Strategic Shifts")
                recent_news = company_research.get('recent_news', [])
                if recent_news:
                    for i, news_item in enumerate(recent_news, 1):
                        with st.expander(f"**{i}. {news_item.get('headline', 'N/A')}**"):
                            st.markdown(f"**Summary:** {news_item.get('summary', 'N/A')}")
                            st.markdown(f"**Significance:** {news_item.get('significance', 'N/A')}")
                
                st.markdown("---")
                st.markdown("#### 🎯 Interview Deep-Dive")
                deep_dive = company_research.get('interview_deep_dive', [])
                if deep_dive:
                    for i, item in enumerate(deep_dive, 1):
                        st.markdown(f"**{i}.** {item}")
            else:
                st.info("Company research not available.")
        
        with tab5:
            st.markdown("### 📝 Personalized Cover Letter")
            if cover_letter_text:
                st.text_area(
                    "Cover Letter Text",
                    value=cover_letter_text,
                    height=500,
                    label_visibility="collapsed",
                    help="Copy this text to use in your application"
                )
                st.download_button(
                    label="📥 Download Cover Letter",
                    data=cover_letter_text,
                    file_name="cover_letter.txt",
                    mime="text/plain"
                )
            else:
                st.info("Cover letter not available for this analysis.")
        
        # Button to go back to input forms
        st.markdown("---")
        if st.button("← Back to New Analysis", use_container_width=True):
            st.session_state.show_loaded_analysis = False
            st.session_state.loaded_analysis = {}
            st.session_state.loaded_company_research = {}
            st.session_state.loaded_cover_letter = None
            st.rerun()
        
        # Stop here - don't show input forms when displaying loaded analysis
        st.stop()
    
    # Two main columns (only shown if not displaying loaded analysis)
    col1, col2 = st.columns([1, 1])
    
    # Left column: About You
    with col1:
        st.header("About You")
        
        # CV file uploader (PDF and DOCX)
        cv_file = st.file_uploader(
            "Upload your CV",
            type=['pdf', 'docx'],
            help="Upload your CV as a PDF or DOCX file"
        )
        
        if cv_file:
            try:
                file_bytes = cv_file.read()
                cv_text = ""
                
                if cv_file.type == "application/pdf":
                    pdf_file = io.BytesIO(file_bytes)
                    cv_text = extract_text_from_pdf(pdf_file)
                elif cv_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    docx_file = io.BytesIO(file_bytes)
                    cv_text = extract_text_from_docx(docx_file)
                
                if cv_text:
                    st.session_state.cv_text = cv_text
                    st.success("✅ CV uploaded successfully!")
            except Exception as e:
                st.error(f"Error extracting text from file: {str(e)}")
        
        # Psychometric Assessment
        st.markdown("### Career Values Assessment")
        st.markdown("Complete this assessment to help us understand your career values and personality.")
        
        # Check if assessment is already completed
        if st.session_state.assessment_completed:
            st.success("✅ Assessment completed!")
            with st.expander("View Your Personality Profile"):
                profile = st.session_state.psychometric_assessment.personality_profile
                if profile:
                    st.markdown("**Top Personality Traits:**")
                    for trait, score in profile.get('top_traits', [])[:5]:
                        st.markdown(f"- {trait.capitalize()}: {score} points")
                    
                    st.markdown(f"**Communication Style:** {profile.get('communication_style', 'N/A')}")
                    st.markdown(f"**Work Style:** {profile.get('work_style', 'N/A')}")
                    st.markdown(f"**Motivation Style:** {profile.get('motivation_style', 'N/A')}")
            
            if st.button("Retake Assessment"):
                st.session_state.psychometric_assessment = PsychometricAssessment()
                st.session_state.assessment_completed = False
                st.rerun()
        else:
            # Display questions one at a time
            questions = st.session_state.psychometric_assessment.questions
            responses = st.session_state.psychometric_assessment.responses
            
            # Find the current question (first unanswered)
            current_q_id = None
            for q in questions:
                if q['id'] not in responses:
                    current_q_id = q['id']
                    break
            
            if current_q_id:
                current_question = next(q for q in questions if q['id'] == current_q_id)
                
                st.markdown(f"**Question {current_q_id} of {len(questions)}**")
                st.markdown(f"**{current_question['question']}**")
                
                # Create radio buttons for options
                selected_option = st.radio(
                    "Select your answer:",
                    options=['a', 'b', 'c', 'd'],
                    format_func=lambda x: current_question['options'][x],
                    key=f"question_{current_q_id}"
                )
                
                if st.button("Next Question", type="primary"):
                    st.session_state.psychometric_assessment.responses[current_q_id] = selected_option
                    st.rerun()
            else:
                # All questions answered, calculate profile
                st.session_state.psychometric_assessment._calculate_personality_profile()
                st.session_state.assessment_completed = True
                st.rerun()
    
    # Right column: The Job
    with col2:
        st.header("The Job")
        
        # Job URL text input
        job_url = st.text_input(
            "Job URL",
            placeholder="https://example.com/job-listing",
            help="Enter the URL of the job listing (optional)"
        )
        st.session_state.job_url = job_url
        
        # Job Description text area
        job_description = st.text_area(
            "Job Description",
            height=200,
            placeholder="Paste the job description here...",
            help="Enter or paste the full job description"
        )
        st.session_state.job_description = job_description
    
    # Check if a history item was selected and load it
    # Get user email from session state (set during login) or database
    supabase = get_supabase_client()
    user_email = st.session_state.get('user_email') or get_user_email_from_database(supabase, username)
    if supabase and 'selected_history_id' in st.session_state and st.session_state.selected_history_id:
        history_id = st.session_state.selected_history_id
        history_data = load_analysis_from_supabase(supabase, username, history_id, email=user_email)
        
        if not history_data:
            st.error(f"❌ Failed to load analysis with ID {history_id}. Please check if the record exists and belongs to your account.")
        elif history_data:
            # Load the analysis data
            st.session_state.job_description = history_data.get('job_description', '')
            st.session_state.job_url = ''  # Clear URL since we're loading from history
            
            # Parse and set the analysis data
            analysis_json = history_data.get('analysis_text', '{}')
            company_research_json = history_data.get('company_research', '{}')
            cover_letter_text = history_data.get('cover_letter', '')
            
            # Store in session state for display
            try:
                st.session_state.loaded_analysis = json.loads(analysis_json) if analysis_json and analysis_json.strip() else {}
            except json.JSONDecodeError as e:
                st.session_state.loaded_analysis = {}
            try:
                st.session_state.loaded_company_research = json.loads(company_research_json) if company_research_json and company_research_json.strip() else {}
            except json.JSONDecodeError as e:
                st.session_state.loaded_company_research = {}
            st.session_state.loaded_cover_letter = cover_letter_text
            st.session_state.loaded_history_id = history_id
            st.session_state.show_loaded_analysis = True  # Flag to show analysis instead of forms
            
            # Clear the selected history ID to prevent reloading
            st.session_state.selected_history_id = None
            
            st.rerun()  # Rerun to show the loaded analysis
    
    # Compare and Coach button at the bottom
    st.markdown("---")
    
    # Check if we have a loaded analysis to display
    if 'loaded_analysis' in st.session_state and st.session_state.loaded_analysis:
        gemini_analysis = st.session_state.loaded_analysis
        company_research = st.session_state.loaded_company_research if 'loaded_company_research' in st.session_state else {}
        cover_letter_text = st.session_state.loaded_cover_letter if 'loaded_cover_letter' in st.session_state else None
        
        # Display loaded analysis
        st.markdown("## 🚀 Career Strategy Dashboard (Loaded from History)")
        st.markdown("---")
        
        # Top metrics in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            match_score = gemini_analysis.get('match_score', 0)
            st.metric("📊 Current CV Match", f"{match_score}/100", delta=f"{match_score - 50}" if match_score >= 50 else None)
            st.caption("Your current match score")
        
        with col2:
            potential_score = calculate_potential_match_score(gemini_analysis)
            improvement = potential_score - match_score
            delta_label = f"+{improvement}" if improvement > 0 else None
            st.metric("🚀 Potential Match", f"{potential_score}/100", delta=delta_label, delta_color="normal")
            st.caption("With suggested improvements")
        
        with col3:
            salary_range = gemini_analysis.get('salary_range', 'N/A')
            st.metric("💷 UK Salary Benchmark", salary_range)
            st.caption("Estimated salary range")
        
        st.markdown("---")
        
        # Tabs for different sections (reuse the same tab structure)
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Skill Gap Analysis", "🎤 Interview Prep", "✍️ CV Improvements", "🏢 Company Intelligence", "📝 Cover Letter"])
        
        # Display all tabs with loaded data (same structure as below)
        # This will be handled by the same tab code, but we'll need to modify it to check for loaded data
    
    if st.button("Compare and Coach", type="primary", use_container_width=True):
        # Extract all text
        cv_text_extracted = st.session_state.cv_text
        job_url_text = st.session_state.job_url
        job_description_text = st.session_state.job_description
        
        # Get psychometric assessment results
        assessment_profile = None
        if st.session_state.assessment_completed:
            assessment_profile = st.session_state.psychometric_assessment.personality_profile
        
        # If URL is provided, try to extract text from it
        job_text_from_url = ""
        if job_url_text.strip():
            with st.spinner("Fetching job listing from URL..."):
                job_text_from_url = extract_text_from_url(job_url_text)
        
        # Combine job description text (prefer URL text if available, otherwise use text area)
        final_job_text = job_text_from_url if job_text_from_url.strip() else job_description_text
        
        # Check if we have both CV and Job data for Gemini analysis
        has_cv = bool(cv_text_extracted)
        has_job_data = bool(final_job_text.strip())
        
        if has_cv and has_job_data:
            # Call Gemini analysis
            with st.spinner("🤖 Analysing CV with elite UK Headhunter..."):
                gemini_analysis = get_gemini_analysis(cv_text_extracted, final_job_text)
            
            # Check for errors
            if gemini_analysis is None:
                st.error("❌ Failed to get analysis from Gemini. Please check your API key and try again.")
            elif "error" in gemini_analysis:
                st.error(f"❌ {gemini_analysis['error']}")
                if "raw_response" in gemini_analysis:
                    with st.expander("View Raw Response"):
                        st.text(gemini_analysis['raw_response'])
            else:
                # Get company research and cover letter
                company_research = {}
                cover_letter_text = None
                
                # Extract company name and get research
                company_name = extract_company_name(job_url_text, final_job_text)
                with st.spinner(f"🔍 Researching {company_name}..."):
                    company_research = get_company_research(company_name, job_url_text, final_job_text)
                
                # Generate cover letter
                with st.spinner("✍️ Drafting cover letter..."):
                    cover_letter_text = get_cover_letter(cv_text_extracted, final_job_text, assessment_profile)
                
                # Extract job title
                job_title = extract_job_title(final_job_text)
                
                # Save to Supabase
                supabase = get_supabase_client()
                if supabase:
                    user_email = st.session_state.get('user_email') or get_user_email_from_database(supabase, username)
                    save_success, error_message = save_analysis_to_supabase(
                        supabase, 
                        username, 
                        job_title, 
                        final_job_text,
                        gemini_analysis,
                        company_research if company_research and "error" not in company_research else None,
                        cover_letter_text if cover_letter_text and not cover_letter_text.startswith("Error:") else None,
                        email=user_email
                    )
                    if save_success:
                        st.success("💾 Analysis saved to Application History!")
                    else:
                        st.error(f"❌ Failed to save: {error_message}")
                
                # Display Career Strategy Dashboard
                st.markdown("## 🚀 Career Strategy Dashboard")
                st.markdown("---")
                
                # Top metrics in columns
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    match_score = gemini_analysis.get('match_score', 0)
                    st.metric("📊 Current CV Match", f"{match_score}/100", delta=f"{match_score - 50}" if match_score >= 50 else None)
                    st.caption("Your current match score")
                
                with col2:
                    potential_score = calculate_potential_match_score(gemini_analysis)
                    improvement = potential_score - match_score
                    delta_label = f"+{improvement}" if improvement > 0 else None
                    st.metric("🚀 Potential Match", f"{potential_score}/100", delta=delta_label, delta_color="normal")
                    st.caption("With suggested improvements")
                
                with col3:
                    salary_range = gemini_analysis.get('salary_range', 'N/A')
                    st.metric("💷 UK Salary Benchmark", salary_range)
                    st.caption("Estimated salary range")
                
                st.markdown("---")
                
                # Tabs for different sections
                tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Skill Gap Analysis", "🎤 Interview Prep", "✍️ CV Improvements", "🏢 Company Intelligence", "📝 Cover Letter"])
                
                with tab1:
                    st.markdown("### Missing Hard Skills")
                    missing_skills = gemini_analysis.get('missing_hard_skills', [])
                    if missing_skills:
                        for i, skill in enumerate(missing_skills, 1):
                            st.markdown(f"**{i}.** {skill}")
                    else:
                        st.info("No missing skills identified - great alignment!")
                    
                    st.markdown("---")
                    st.markdown("### 💡 Why This Matters")
                    st.info("These are the specific technical skills the recruiter will be looking for. Consider highlighting related experience or upskilling in these areas.")
                
                with tab2:
                    st.markdown("### 🎯 Tough Interview Questions")
                    st.markdown("These questions are designed to probe your skill gaps. Prepare strong, honest answers.")
                    
                    interview_questions = gemini_analysis.get('interview_questions', [])
                    if interview_questions:
                        for i, question in enumerate(interview_questions, 1):
                            with st.expander(f"Question {i}: {question[:60]}..." if len(question) > 60 else f"Question {i}"):
                                st.markdown(f"**{question}**")
                                st.markdown("💡 *Tip: Prepare a STAR (Situation, Task, Action, Result) response for this question.*")
                    else:
                        st.info("No specific interview questions generated.")
                    
                    st.markdown("---")
                    st.markdown("### 🎤 Interview Strategy")
                    st.success("Use these questions to prepare your responses. Focus on demonstrating growth mindset and willingness to learn missing skills.")
                
                with tab3:
                    st.markdown("### ✍️ Power Word Swaps")
                    st.markdown("Replace generic buzzwords with high-impact UK action verbs to make your CV stand out.")
                    
                    power_words = gemini_analysis.get('power_word_swaps', [])
                    if power_words:
                        for i, swap in enumerate(power_words, 1):
                            st.markdown(f"**{i}. {swap.get('original', 'N/A')}** → **{swap.get('replacement', 'N/A')}**")
                            st.caption(f"💡 {swap.get('context', 'No context provided')}")
                            st.markdown("")
                    else:
                        st.info("No power word swaps suggested.")
                    
                    st.markdown("---")
                    st.markdown("### 📝 CV Bullet Point Improvements")
                    st.markdown("Specific, actionable edits to make your CV more aligned with this role.")
                    
                    cv_improvements = gemini_analysis.get('cv_improvements', [])
                    if cv_improvements:
                        for i, improvement in enumerate(cv_improvements, 1):
                            with st.expander(f"Improvement {i}"):
                                st.markdown("**Current:**")
                                st.text(improvement.get('current', 'N/A'))
                                st.markdown("**Improved:**")
                                st.success(improvement.get('improved', 'N/A'))
                                st.markdown(f"**Why:** {improvement.get('reason', 'No reason provided')}")
                    else:
                        st.info("No specific CV improvements suggested.")
                
                with tab4:
                    # Company Intelligence
                    st.markdown("### 🏢 Company Intelligence")
                    st.markdown("Research insights to help you stand out in your interview.")
                    
                    # Use loaded company research if available, otherwise get new
                    if 'loaded_company_research' in st.session_state and st.session_state.loaded_company_research:
                        company_research = st.session_state.loaded_company_research
                    else:
                        # Extract company name
                        company_name = extract_company_name(job_url_text, final_job_text)
                        
                        # Get company research
                        with st.spinner(f"🔍 Researching {company_name}..."):
                            company_research = get_company_research(company_name, job_url_text, final_job_text)
                    
                    if company_research and "error" in company_research:
                        st.error(f"❌ {company_research['error']}")
                        if "raw_response" in company_research:
                            with st.expander("View Raw Response"):
                                st.text(company_research['raw_response'])
                    else:
                        # Financial Performance
                        st.markdown("#### 💰 Financial Performance")
                        financial = company_research.get('financial_performance', {})
                        if financial:
                            st.markdown(f"**Market Position:** {financial.get('market_position', 'N/A')}")
                            st.markdown(f"**Financial Health:** {financial.get('financial_health', 'N/A')}")
                            if financial.get('key_metrics'):
                                st.markdown(f"**Key Metrics:** {financial.get('key_metrics', 'N/A')}")
                        else:
                            st.info("Financial information not available.")
                        
                        st.markdown("---")
                        
                        # Recent News
                        st.markdown("#### 📰 Recent News & Strategic Shifts")
                        recent_news = company_research.get('recent_news', [])
                        if recent_news:
                            for i, news_item in enumerate(recent_news, 1):
                                with st.expander(f"**{i}. {news_item.get('headline', 'N/A')}**"):
                                    st.markdown(f"**Summary:** {news_item.get('summary', 'N/A')}")
                                    st.markdown(f"**Significance:** {news_item.get('significance', 'N/A')}")
                        else:
                            st.info("No recent news found.")
                        
                        st.markdown("---")
                        
                        # Interview Deep-Dive
                        st.markdown("#### 🎯 Interview Deep-Dive")
                        st.markdown("**5 specific things to research before your interview:**")
                        st.info("💡 Researching these topics will demonstrate advanced company knowledge and genuine interest.")
                        
                        deep_dive = company_research.get('interview_deep_dive', [])
                        if deep_dive:
                            for i, item in enumerate(deep_dive, 1):
                                st.markdown(f"**{i}.** {item}")
                        else:
                            st.info("No specific research items suggested.")
                        
                        st.markdown("---")
                        st.success(f"💼 **Pro Tip:** Use this intelligence to ask informed questions during your interview. Show you've done your homework!")
                
                with tab5:
                    # Cover Letter
                    st.markdown("### 📝 Personalized Cover Letter")
                    st.markdown("A tailored cover letter for this role, written in your communication style.")
                    
                    # Use loaded cover letter if available, otherwise generate new
                    if 'loaded_cover_letter' in st.session_state and st.session_state.loaded_cover_letter:
                        cover_letter = st.session_state.loaded_cover_letter
                    elif has_cv and has_job_data:
                        # Generate cover letter
                        with st.spinner("✍️ Drafting your personalized cover letter..."):
                            cover_letter = get_cover_letter(cv_text_extracted, final_job_text, assessment_profile)
                    else:
                        cover_letter = None
                    
                    if cover_letter:
                        if cover_letter.startswith("Error:"):
                            st.error(cover_letter)
                        else:
                            # Display cover letter
                            st.markdown("---")
                            st.markdown("#### Your Cover Letter")
                            
                            # Show in a text area for easy copying
                            st.text_area(
                                "Cover Letter Text",
                                value=cover_letter,
                                height=500,
                                label_visibility="collapsed",
                                help="Copy this text to use in your application"
                            )
                            
                            # Download button
                            st.download_button(
                                label="📥 Download Cover Letter",
                                data=cover_letter,
                                file_name="cover_letter.txt",
                                mime="text/plain"
                            )
                            
                            st.markdown("---")
                            
                            # Show personality note if assessment was used
                            if assessment_profile:
                                st.info("💡 **Note:** This cover letter has been tailored to match your personality profile and communication style from the psychometric assessment.")
                            else:
                                st.info("💡 **Tip:** Complete the psychometric assessment to get a cover letter personalized to your communication style and personality traits.")
                    else:
                        if not has_cv:
                            st.warning("⚠️ Please upload your CV to generate a cover letter.")
                        if not has_job_data:
                            st.warning("⚠️ Please provide the job description to generate a cover letter.")
                
                st.markdown("---")
                if st.button("💾 Save to Profile", type="primary", use_container_width=True, key="save_to_profile"):
                    supabase = get_supabase_client()
                    user_email = st.session_state.get('user_email') or get_user_email_from_database(supabase, username)
                    
                    if not supabase:
                        st.error("❌ Database connection failed. Please check your configuration.")
                    elif not user_email:
                        st.error("❌ User email not found. Please log in again.")
                    else:
                        save_success, error_message = save_analysis_to_supabase(
                            supabase,
                            username,
                            job_title,
                            final_job_text,
                            gemini_analysis,
                            company_research if company_research and "error" not in company_research else None,
                            cover_letter_text if cover_letter_text and not cover_letter_text.startswith("Error:") else None,
                            email=user_email
                        )
                        
                        if save_success:
                            st.toast("✅ Analysis saved to your profile!", icon="✅")
                            st.success("✅ Analysis saved to your profile!")
                        else:
                            st.error(f"❌ Failed to save analysis: {error_message}")
        else:
            if not has_cv:
                st.error("❌ Please upload your CV to get analysis")
            if not has_job_data:
                st.error("❌ Please provide job description or URL to get analysis")
        
        # Display summary
        st.markdown("## 📊 Data Summary")
        st.markdown("---")
        
        # About You section
        st.markdown("### About You")
        if cv_text_extracted:
            st.success(f"✅ **CV Received**: {len(cv_text_extracted)} characters extracted")
            with st.expander("View CV Text (first 500 characters)"):
                st.text(cv_text_extracted[:500] + "..." if len(cv_text_extracted) > 500 else cv_text_extracted)
        else:
            st.warning("⚠️ **CV**: Not provided")
        
        if assessment_profile:
            st.success("✅ **Psychometric Assessment**: Completed")
            with st.expander("View Personality Profile"):
                st.markdown("**Top Personality Traits:**")
                for trait, score in assessment_profile.get('top_traits', [])[:5]:
                    st.markdown(f"- {trait.capitalize()}: {score} points")
                
                st.markdown(f"**Communication Style:** {assessment_profile.get('communication_style', 'N/A')}")
                st.markdown(f"**Work Style:** {assessment_profile.get('work_style', 'N/A')}")
                st.markdown(f"**Motivation Style:** {assessment_profile.get('motivation_style', 'N/A')}")
        else:
            st.warning("⚠️ **Psychometric Assessment**: Not completed")
        
        st.markdown("---")
        
        # The Job section
        st.markdown("### The Job")
        if job_url_text.strip():
            st.info(f"🔗 **Job URL**: {job_url_text}")
            if job_text_from_url:
                st.success(f"✅ **Job Text from URL**: {len(job_text_from_url)} characters extracted")
                with st.expander("View Job Text from URL (first 500 characters)"):
                    st.text(job_text_from_url[:500] + "..." if len(job_text_from_url) > 500 else job_text_from_url)
            else:
                st.warning("⚠️ Could not extract text from URL")
        
        if job_description_text.strip():
            st.success(f"✅ **Job Description Received**: {len(job_description_text)} characters")
            with st.expander("View Job Description"):
                st.text(job_description_text)
        else:
            st.warning("⚠️ **Job Description**: Not provided")
        
        # Final status
        st.markdown("---")
        has_assessment = bool(assessment_profile)
        
        if has_cv and has_job_data and has_assessment:
            st.success("✅ **Status**: CV, Assessment, and Job data all received successfully!")
        elif has_cv and has_job_data:
            st.warning("⚠️ **Status**: CV and Job data received, but Assessment is missing")
        elif has_cv:
            st.warning("⚠️ **Status**: CV received, but Job data and Assessment are missing")
        elif has_job_data:
            st.warning("⚠️ **Status**: Job data received, but CV and Assessment are missing")
        else:
            st.error("❌ **Status**: Required data is missing")


if __name__ == "__main__":
    main()

