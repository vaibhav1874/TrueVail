import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# We're using heuristic analysis only, no AI API needed
print("DEBUG: Using heuristic analysis only, no AI API")
model = None

def analyze_news(text, analysis_type="news"):
    """
    Analyzes news content or a URL to determine its authenticity.
    """
    # Check if input is a URL
    parsed_url = urlparse(text.strip())
    is_url = bool(parsed_url.scheme and parsed_url.netloc)
    
    if is_url:
        url = text.strip()
        content = fetch_url_content(url)
        if not content:
            return {
                "analysis": "Failed to fetch content from the provided URL.",
                "status": "Error",
                "confidence": "0",
                "reason": "Could not access the website. It might be blocking scrapers or the link is invalid.",
                "privacy_risk": "Low",
                "privacy_explanation": "Standard URL access attempt."
            }
        return perform_ai_analysis(content, is_url=True, url=url, analysis_type=analysis_type)
    else:
        return perform_ai_analysis(text, analysis_type=analysis_type)

def fetch_url_content(url):
    """
    Fetches the main text content from a given URL.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]):
            script.extract()
            
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text[:10000] 
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return None

def perform_ai_analysis(content, is_url=False, url=None, analysis_type="news"):
    """
    Performs heuristic analysis of the content.
    """
    return heuristic_fallback(content, is_url, url, "Using heuristic analysis only.", analysis_type)

def analyze_url(domain):
    # Heuristics for suspicious domains
    suspicious_domains = [
        'bit.ly', 'tinyurl.com', 'ow.ly', 't.co', 'is.gd', 'buff.ly',
        'clickbait', 'fakenews', 'rumor', 'gossip', 'sensational',
        'unverified', 'shady', 'questionable', 'scam', 'hoax'
    ]
    
    trusted_sources = [
        'reuters.com', 'ap.org', 'bbc.com', 'nytimes.com', 'washingtonpost.com',
        'cnn.com', 'foxnews.com', 'nbcnews.com', 'abcnews.go.com', 'cbsnews.com',
        'theguardian.com', 'telegraph.co.uk', 'latimes.com', 'usatoday.com'
    ]
    
    domain_lower = domain.lower()
    
    if any(trusted in domain_lower for trusted in trusted_sources):
        status = "Trusted Source"
        confidence = "0.9"
        reason = f"Published by a known trusted news source: {domain}"
    elif any(suspicious in domain_lower for suspicious in suspicious_domains):
        status = "Suspicious Source"
        confidence = "0.8"
        reason = f"Domain contains suspicious elements: {domain}"
    else:
        status = "Neutral Source"
        confidence = "0.6"
        reason = f"Source {domain} is neither explicitly trusted nor suspicious."
    
    return {
        "analysis": f"URL Analysis: {status} ({confidence}) - {reason}",
        "status": status,
        "confidence": confidence,
        "reason": reason,
        "correction_suggestion": "",
        "privacy_risk": "Low",
        "privacy_explanation": "URL itself poses minimal privacy risk."
    }


def extract_content_from_url(url):
    # In a real implementation, this would fetch and parse the content from the URL
    # For demo purposes, we'll just return a placeholder indicating it's a URL
    try:
        parsed = urlparse(url)
        return f"Content from {parsed.netloc}: {parsed.path.replace('/', ' ').strip()}"
    except:
        return None


def analyze_content(text, analysis_type="news"):
    # Improved heuristic analysis for demo purposes
    text_lower = text.lower().strip()
    
    if analysis_type == "privacy":
        # Privacy risk detection only
        privacy_indicators = ['@', '.com', 'phone', 'address', 'location', 'email', 'name', 'street', 'city', 'zip', 'ssn', 'credit card', 'password', 'social security', 'account number', 'driver license', 'birth date', 'passport', 'national id', 'tax id']
        privacy_risks = [indicator for indicator in privacy_indicators if indicator in text_lower]
        
        if len(privacy_risks) >= 3:
            privacy_risk = "High"
            privacy_explanation = f"Multiple privacy risks detected: {', '.join(privacy_risks[:3])}. The text contains personal information that could lead to identity theft or privacy violations."
        elif len(privacy_risks) >= 1:
            privacy_risk = "Medium"
            privacy_explanation = f"Potential privacy risks: {', '.join(privacy_risks)}. The text contains some personal information that should be handled carefully."
        else:
            privacy_risk = "Low"
            privacy_explanation = "No significant privacy risks detected. The text does not contain personal identifiable information."
        
        # For privacy analysis, focus only on privacy aspects
        return {
            "analysis": f"Privacy Risk: {privacy_risk}\nPrivacy Explanation: {privacy_explanation}\n\nOriginal text analyzed: {text[:100]}...",
            "status": privacy_risk,
            "confidence": "0.8",
            "reason": "Based on presence of personal identifiers in the text",
            "correction_suggestion": "",
            "privacy_risk": privacy_risk,
            "privacy_explanation": privacy_explanation
        }
    else:  # News analysis
        # More comprehensive fake news detection heuristics
        fake_indicators = [
            # Sensationalism
            'you won\'t believe', 'shocking', 'unbelievable', 'incredible', 'mind-blowing', 
            'unthinkable', 'jaw-dropping', 'cannot be unseen', 'nobody talks about',
            
            # Urgency/Emotional manipulation
            'breaking news', 'urgent', 'act now', 'immediate action required', 
            'limited time', 'don\'t miss', 'must see', 'everyone is talking about',
            
            # Superlatives
            'best ever', 'worst ever', 'only way', 'never seen before', 'final warning',
            'last chance', 'only option', 'game changer', 'revolutionary',
            
            # Grammar/Syntax
            '!!!', '???', 'caps', 'all caps', 'shouting',
            
            # Unverifiable claims
            'secret', 'conspiracy', 'cover-up', 'hidden truth', 'they don\'t want you to know'
        ]
        
        # More comprehensive real news indicators
        real_indicators = [
            # Credible sources
            'according to', 'study shows', 'research indicates', 'reported by', 'confirmed by',
            'verified by', 'documented by', 'data shows', 'statistics show',
            
            # Professional journalism
            'investigation', 'interview', 'quote', 'statement', 'official', 'spokesperson',
            'press release', 'report', 'analysis', 'findings',
            
            # Credibility markers
            'peer-reviewed', 'scientific', 'medical journal', 'university', 'expert',
            'doctor', 'professor', 'researcher', 'scientist', 'evidence', 'proof',
            
            # Date/location context
            'yesterday', 'today', 'recently', 'located', 'based in', 'city', 'country'
        ]
        
        # Count indicators
        fake_score = sum(1 for indicator in fake_indicators if indicator in text_lower)
        real_score = sum(1 for indicator in real_indicators if indicator in text_lower)
        
        # Enhanced scoring with context awareness
        # Look for patterns that indicate fake news
        exclamation_pattern = len(re.findall(r'[!]{2,}', text))
        caps_pattern = len(re.findall(r'([A-Z]{4,})', text))
        sensational_pattern = len(re.findall(r'(you won.t believe|shocking|unbelievable)', text_lower))
        
        # Adjust scores based on patterns
        fake_score += exclamation_pattern * 0.5 + caps_pattern * 0.3 + sensational_pattern * 0.7
        
        if fake_score > real_score * 1.2:  # Increased threshold for fake detection
            status = "Likely Fake"
            confidence = str(min(0.5 + fake_score * 0.15, 0.95))
            reason = f"Contains strong indicators of fake news: {fake_score} potential indicators found. The text exhibits sensational language, unverifiable claims, or emotional manipulation tactics typical of unreliable sources."
            correction_suggestion = generate_correction_suggestion(text)
        elif real_score > fake_score * 1.2:  # Increased threshold for real detection
            status = "Likely Real"
            confidence = str(min(0.5 + real_score * 0.12, 0.95))
            reason = f"Contains indicators of reliable reporting: {real_score} credibility indicators found. The text includes verifiable sources, professional journalism markers, and evidence-based language."
            correction_suggestion = ""
        else:
            status = "Uncertain"
            confidence = "0.5"
            reason = "Insufficient indicators to determine authenticity. The text contains neither strong fake news indicators nor strong credibility markers."
            correction_suggestion = ""
        
        # For news analysis, privacy risk is not applicable
        privacy_risk = "Not Applicable"
        privacy_explanation = "Privacy risk assessment not applicable to this function."
        
        analysis_text = f"Status: {status}\nConfidence: {confidence}\nReason: {reason}\n\nOriginal text analyzed: {text[:100]}..."
        
        return {
            "analysis": analysis_text,
            "status": status,
            "confidence": confidence,
            "reason": reason,
            "correction_suggestion": correction_suggestion,
            "privacy_risk": privacy_risk,
            "privacy_explanation": privacy_explanation
        }


def generate_correction_suggestion(text):
    # Generate a suggested correction for fake news with actual facts
    corrections = []
    
    text_lower = text.lower()
    
    # Specific patterns that indicate fake news with corresponding corrections
    if 'you won\'t believe' in text_lower:
        corrections.append("This is a classic clickbait phrase. Verify this claim with credible sources before believing it.")
    
    if 'breaking news' in text_lower and 'urgent' in text_lower:
        corrections.append("Check established news outlets like Reuters, AP, or BBC to confirm this breaking news story.")
    
    if 'shocking' in text_lower or 'unbelievable' in text_lower:
        corrections.append("Be skeptical of sensational claims. Look for evidence from reliable sources.")
    
    if 'miracle cure' in text_lower or 'cures all diseases' in text_lower:
        corrections.append("Medical claims should be verified with peer-reviewed studies and official health authorities like WHO or CDC.")
    
    if 'virus hoax' in text_lower or 'all a lie' in text_lower:
        corrections.append("Health information should be verified with reputable medical institutions and peer-reviewed research.")
    
    if 'election fraud' in text_lower and ('millions of votes' in text_lower or 'rigged' in text_lower):
        corrections.append("Electoral integrity claims should be verified with official election monitoring organizations and certified results.")
    
    if 'celebrity death' in text_lower:
        corrections.append("Verify celebrity news with official announcements or reputable entertainment news sources before sharing.")
    
    if 'won lottery' in text_lower or 'you\'ve won' in text_lower:
        corrections.append("Unexpected prize notifications are typically scams. Legitimate lotteries don't contact winners unexpectedly.")
    
    # If no specific pattern matched, provide general guidance
    if len(corrections) == 0:
        # Generate a sample correction based on common fake news topics
        if 'covid' in text_lower:
            corrections.append("For COVID-19 information, consult official sources like WHO, CDC, or your national health authority.")
        elif 'politics' in text_lower:
            corrections.append("Political claims should be verified with multiple reputable news sources and fact-checking websites.")
        elif 'health' in text_lower:
            corrections.append("Medical claims should be verified with peer-reviewed studies and official health authorities.")
        else:
            corrections.append("We recommend fact-checking this information with trusted news sources like Reuters, AP News, or BBC, or fact-checking sites like Snopes or PolitiFact.")
    
    return " ".join(corrections)


def heuristic_fallback(text, is_url=False, url=None, error_msg="", analysis_type="news"):
    """
    Comprehensive heuristic analysis when AI is unavailable.
    """
    # Parse URL if the input is a link
    if is_url:
        domain = urlparse(url).netloc.lower()
        url_analysis = analyze_url(domain)
        content_analysis = analyze_content(text, analysis_type)
        # Combine URL and content analysis
        status = content_analysis["status"] if content_analysis["status"] != "Uncertain" else url_analysis["status"]
        confidence = max(float(content_analysis["confidence"]), float(url_analysis["confidence"]))
        reason = content_analysis["reason"] + " " + url_analysis["reason"]
        
        return {
            "analysis": f"URL Analysis: {url_analysis['status']} ({url_analysis['confidence']})\nContent Analysis: {content_analysis['status']} ({content_analysis['confidence']})\nCombined Reason: {reason}",
            "status": status,
            "confidence": str(confidence),
            "reason": reason,
            "correction_suggestion": content_analysis.get("correction_suggestion", ""),
            "privacy_risk": content_analysis["privacy_risk"],
            "privacy_explanation": content_analysis["privacy_explanation"]
        }
    else:
        # Regular text analysis
        return analyze_content(text, analysis_type)
