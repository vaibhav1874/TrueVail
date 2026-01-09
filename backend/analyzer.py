import os
import re
import requests
import json
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse, quote_plus
import google.generativeai as genai
from dotenv import load_dotenv
from fake_news_detection import detect_fake_news, train_fake_news_detector

# Load environment variables from .env file
load_dotenv()

# AI Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
AI_PLATFORM = os.getenv("AI_PLATFORM", "gemini").lower() # gemini or ollama
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL_TEXT = os.getenv("OLLAMA_MODEL_TEXT", "llama3.1:latest")
OLLAMA_MODEL_VISION = os.getenv("OLLAMA_MODEL_VISION", "llava:latest")

def call_ollama(prompt, model="llama3.1", images=None):
    """Calls local Ollama API"""
    print(f"DEBUG: call_ollama called with model: {model}, images: {bool(images)}")
    try:
        with open("ai_debug_output.txt", "a", encoding="utf-8") as f:
            f.write(f"\n--- {time.ctime()} --- OLLAMA REQ ({model}) ---\nPrompt: {prompt[:200]}...\n")
            if images: f.write(f"Images attached: {len(images)}\n")

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1}
        }
        if images:
            payload["images"] = images
            
        print(f"DEBUG: Calling Ollama ({model}) with payload...")
        # Increase timeout for complex models (especially vision/llava)
        # 5 minutes for vision, 2 minutes for text
        timeout = 300 if "llava" in model else 120
        print(f"DEBUG: Using timeout of {timeout} seconds")
        response = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload, timeout=timeout)
        
        with open("ai_debug_output.txt", "a", encoding="utf-8") as f:
            f.write(f"Ollama Status: {response.status_code}\n")

        if response.status_code == 200:
            res_json = response.json()
            print(f"DEBUG: Ollama response received: {res_json.keys() if isinstance(res_json, dict) else type(res_json)}")
            res_text = res_json.get("response", "")
            with open("ai_debug_output.txt", "a", encoding="utf-8") as f:
                f.write(f"Ollama Resp: {res_text[:500]}\n")
            print(f"DEBUG: Returning response: {res_text[:100]}...")
            return res_text
        else:
            err_msg = f"Error: Ollama returned {response.status_code}"
            with open("ai_debug_output.txt", "a", encoding="utf-8") as f:
                f.write(f"{err_msg}\n")
            print(f"DEBUG: Ollama returned error: {err_msg}")
            return err_msg
    except requests.exceptions.ConnectionError:
        err_msg = "Error: Cannot connect to Ollama. Is the Ollama service running?"
        print(f"DEBUG: Connection error to Ollama: {err_msg}")
        return err_msg
    except Exception as e:
        err_msg = f"Error connecting to Ollama: {str(e)}"
        with open("ai_debug_output.txt", "a", encoding="utf-8") as f:
            f.write(f"{err_msg}\n")
        print(f"DEBUG: General error in call_ollama: {err_msg}")
        return err_msg

# Initialize the Gemini model with the google.generativeai package
model = None
if GEMINI_API_KEY and GEMINI_API_KEY != "" and len(GEMINI_API_KEY) > 20:  # Check for a reasonably long API key
    print(f"DEBUG: Key found (starts with: {GEMINI_API_KEY[:4]}...)")
    try:
        # Configure the API key
        genai.configure(api_key=GEMINI_API_KEY)
        # Initialize the model
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("DEBUG: Model initialized successfully")
    except Exception as e:
        print(f"DEBUG: Error initializing model: {e}")
        model = None
else:
    print("DEBUG: No valid API key provided")
    model = None

def analyze_news(text, analysis_type="news", image_data=None, mime_type=None):
    """
    Analyzes news content, a URL, or media for authenticity and risks.
    """
    print(f"DEBUG: analyze_news called with text type: {type(text)}, analysis_type: {analysis_type}, image_data: {bool(image_data)}")
    
    # Check if input is a URL
    parsed_url = urlparse(text.strip()) if text else None
    is_url = bool(parsed_url and parsed_url.scheme and parsed_url.netloc)
    
    if analysis_type == "deepfake":
        # For deepfake detection, we use the uploaded image data if available
        return analyze_deepfake(text, image_data=image_data, mime_type=mime_type)
    elif analysis_type == "privacy":
        # For privacy analysis, use our dedicated function
        print(f"DEBUG: Calling privacy analysis for: {text[:50]}...")
        return analyze_content(text, analysis_type="privacy")
    elif is_url:
        url = text.strip()
        content = fetch_url_content(url)
        if not content:
            # If scraping fails, don't just fail-fast with heuristics.
            # Use the URL itself as the 'content' for the AI, which will trigger a web search.
            content = f"News URL: {url}"
            is_url = True # Keep this flag
            print(f"DEBUG: Scraping failed for {url}. Passing URL to AI for search-enhanced analysis.")
        
        return perform_ai_analysis(content, is_url=is_url, url=url, analysis_type=analysis_type)
    else:
        return perform_ai_analysis(text, analysis_type=analysis_type)

def fetch_url_content(url):
    """
    Fetches the main text content from a given URL.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    # Try a couple of times to fetch the page and extract main content
    for attempt in range(2):
        try:
            response = requests.get(url, headers=headers, timeout=7)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            # Prefer <article> content if available
            article = soup.find('article')
            if article:
                text = article.get_text(separator='\n')
            else:
                # Fallback: join largest <p> blocks (heuristic)
                p_texts = [p.get_text(separator=' ') for p in soup.find_all('p') if p.get_text(strip=True)]
                # Choose longest contiguous set: take top 8 paragraphs by length
                p_texts_sorted = sorted(p_texts, key=lambda s: len(s), reverse=True)
                text = '\n\n'.join(p_texts_sorted[:8]) if p_texts_sorted else soup.get_text()

            # Normalize whitespace and return a reasonable slice
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split('  '))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            return text[:12000]
        except Exception as e:
            # Distinguish timeouts and retry once
            try:
                from requests.exceptions import ReadTimeout
                if isinstance(e, ReadTimeout):
                    print(f"Timeout fetching URL (attempt {attempt+1}): {url}")
                else:
                    print(f"Error fetching URL (attempt {attempt+1}): {e}")
            except:
                print(f"Error fetching URL (attempt {attempt+1}): {e}")
            time.sleep(1)
    return None


def web_search_duckduckgo(query, max_results=3):
    """
    Perform a simple DuckDuckGo HTML search and return a list of result URLs (best-effort).
    This avoids JavaScript-heavy search pages and attempts to provide quick evidence links.
    """
    # Try twice to get search results (best-effort)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    for attempt in range(2):
        try:
            q = quote_plus(query)
            search_url = f"https://html.duckduckgo.com/html/?q={q}"
            r = requests.get(search_url, headers=headers, timeout=6)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('http') and 'duckduckgo.com' not in href:
                    if href not in links:
                        links.append(href)
                if len(links) >= max_results:
                    break
            return links[:max_results]
        except Exception as e:
            print(f"DEBUG: web_search_duckduckgo attempt {attempt+1} failed: {e}")
            time.sleep(1)

def perform_ai_analysis(content, is_url=False, url=None, analysis_type="news"):
    """
    Use the Gemini REST API via curl (subprocess) to analyze content.
    This avoids hanging issues observed with Python libraries on this environment.
    """
    import subprocess
    import json
    import tempfile
    
    if AI_PLATFORM == "ollama":
        if analysis_type == "news":
            # For news analysis, first try the pre-trained model
            try:
                print(f"DEBUG: Attempting to use pre-trained fake news detector for news analysis...")
                detection_result = detect_fake_news(content)
                print(f"DEBUG: Pre-trained model result: {detection_result}")
                
                # Return the result in the expected format
                result = {
                    "status": detection_result['status'],
                    "confidence": detection_result['confidence'],
                    "reason": detection_result['reason'],
                    "correction": detection_result.get('correction', ''),
                    "privacy_risk": "Not Applicable",
                    "privacy_explanation": "Privacy risk assessment not applicable to this function."
                }
                print(f"DEBUG: Returning pre-trained model result: {result['status']} with confidence {result['confidence']}")
                return result
            except Exception as e:
                print(f"DEBUG: Error using pre-trained fake news detector, falling back to Ollama: {e}")
                # Continue with Ollama as fallback
        
        if analysis_type == "privacy":
            # Reduce privacy context and use neutral data classification prompt
            prompt = (
                "Task: Classify data sensitivity.\n"
                f"Input: {content[:1500]}\n"
                "Instructions: Determine if the input contains sensitive personal data (Names, Emails, IDs).\n"
                "Do not write code.\n"
                "Response Format:\n"
                "Status: [High/Medium/Low]\n"
                "Confidence: [0-100]\n"
                "Explanation: [Brief reason]\n"
            )
        else: # news analysis fallback to Ollama
            # Add search context to prevent hallucinations
            # Extract a very concise search query
            lines = content.split('\n')
            first_line = lines[0].strip() if lines else content
            search_query = first_line[:100]
            
            print(f"DEBUG: Performing concise web search for: {search_query}...")
            links = web_search_duckduckgo(search_query, max_results=1)
            search_context = ""
            if links:
                print(f"DEBUG: Found link for context: {links[0]}")
                ref_content = fetch_url_content(links[0])
                if ref_content:
                    # Limit reference content to 1500 chars
                    search_context = f"\n\nREAL-TIME CONTEXT FROM SEARCH:\n{ref_content[:1500]}\n"
            
            prompt = (
                "You are an expert fact-checker. Verify the CONTENT below using 'REAL-TIME CONTEXT' as truth. "
                "Respond ONLY as: Status: [Likely Real/Likely Fake/Uncertain], Confidence: [0-100], Explanation: [Assessment]. "
                f"{search_context}\n\nCONTENT TO ANALYZE: {content[:1500]}"
            )
        
        ai_text = call_ollama(prompt, model=OLLAMA_MODEL_TEXT)
        if "Error" in ai_text:
            return heuristic_fallback(content, is_url, url, ai_text, analysis_type)
        return parse_ai_response(ai_text, analysis_type=analysis_type)

    if not GEMINI_API_KEY or not model:
        return heuristic_fallback(content, is_url, url, "Gemini API key not found or model not initialized", analysis_type)

    try:
        # Save request for debug
        with open("ai_debug_output.txt", "a", encoding="utf-8") as f:
            f.write(f"\n--- {time.ctime()} --- CURL CALL ---\nType: {analysis_type}\n")

        if analysis_type == "privacy":
            prompt_text = f"Identify PII/privacy risks in this text. Respond ONLY as: Status: [Low/Med/High], Confidence: [0-100], Explanation: [Short summary]. TEXT: {content[:5000]}"
        else: # news analysis
            prompt_text = f"Verify news authenticity. Respond ONLY as: Status: [Likely Real/Fake/Uncertain], Confidence: [0-100], Explanation: [Brief assessment]. CONTENT: {content[:5000]}"

        # Prepare payload
        payload = {
            "contents": [{"parts": [{"text": prompt_text}]}],
            "generationConfig": {
                "temperature": 0.1, 
                "maxOutputTokens": 250
            }
        }
        
        # Write payload to a temporary file to avoid shell escape issues
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp:
            json.dump(payload, temp)
            temp_path = temp.name

        # Direct REST API call via curl.exe
        # Using gemini-1.5-flash for maximum stability and quota
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        curl_cmd = f'curl.exe -s -X POST "{api_url}" -H "Content-Type: application/json" -d @"{temp_path}"'
        
        result = subprocess.run(curl_cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        # Clean up temp file
        try: os.unlink(temp_path)
        except: pass

        if result.returncode != 0:
            raise Exception(f"Curl failed with return code {result.returncode}: {result.stderr}")

        res_json = json.loads(result.stdout)
        
        if 'error' in res_json:
            err = res_json['error']
            if err.get('status') == 'RESOURCE_EXHAUSTED' or err.get('code') == 429:
                return {
                    "status": "Quota Exceeded",
                    "confidence": 0,
                    "reason": "AI Analysis limit reached. Running local heuristics instead.",
                    "privacy_risk": "Low",
                    "privacy_explanation": "Limit reached.",
                    "correction": "Please try again later or check API configuration."
                }
            raise Exception(f"API Error: {err.get('message', 'Unknown error')}")
        
        try:
            ai_text = res_json['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError) as e:
            raise Exception(f"Unexpected API response structure")
        
        return parse_ai_response(ai_text, analysis_type=analysis_type)

    except Exception as e:
        print(f"DEBUG: AI analysis failed: {e}")
        return heuristic_fallback(content, is_url, url, f"AI Error: {str(e)}", analysis_type)

def parse_ai_response(ai_response, analysis_type="news"):
    """
    Parse the AI response to extract structured data. Improved for robustness.
    """
    # Default values
    status = "Uncertain"
    confidence = 0.5
    reason = "Could not parse AI response details."
    privacy_risk = "Low"
    privacy_explanation = "No privacy risks detected."
    correction = ""
    
    try:
        # Extract Status (handle markdown and brackets)
        status_match = re.search(r"Status:.*?(\b(Likely Real|Likely Fake|Uncertain|Low|Medium|High)\b)", ai_response, re.IGNORECASE)
        if status_match:
            status = status_match.group(1).title()
            # Map privacy status to risk
            if analysis_type == "privacy":
                privacy_risk = status
                if status == "High": status = "High Risk"
                elif status == "Medium": status = "Medium Risk"
                else: status = "Low Risk"

        # Extract Confidence (handle markdown and brackets)
        conf_match = re.search(r"Confidence:.*?(\d+)", ai_response)
        if conf_match:
            confidence = int(conf_match.group(1)) / 100.0
        
        # Extract Explanation
        exp_match = re.search(r"Explanation:\s*(.*)", ai_response, re.IGNORECASE)
        if exp_match:
            reason = exp_match.group(1).strip()
            if analysis_type == "privacy":
                privacy_explanation = reason

        # Extract Privacy Highlights
        if "Privacy Highlights:" in ai_response:
            highlights = []
            lines = ai_response.split('\n')
            found = False
            for line in lines:
                if "Privacy Highlights:" in line:
                    found = True
                    part = line.split("Privacy Highlights:")[1].strip()
                    if part and part.lower() != 'none':
                        highlights.append(part)
                    continue
                if found:
                    if line.startswith("•") or line.strip().startswith("-"):
                        highlights.append(line.strip("•- "))
                    elif ":" in line and not line.strip().startswith("•"): # Next section
                        break
            
            if highlights and highlights[0].lower() != 'none':
                privacy_explanation = "Detected: " + "; ".join(highlights)
                if analysis_type != "privacy":
                    # If news analysis found privacy issues
                    privacy_risk = "Medium" if len(highlights) < 3 else "High"

        # Special logic for news analysis verdicts
        if analysis_type == "news":
            if "Fake" in ai_response and ("Verdict: Fake" in ai_response or "Status: Likely Fake" in ai_response):
                status = "Likely Fake"
                if "Explanation:" not in ai_response:
                    reason = "AI detected potential misinformation or fake claims in the content."
                # Minimal correction placeholder - AI response could be parsed for better correction
                correction = "Verification with multiple independent sources is recommended for this content."

        return {
            "status": status,
            "confidence": confidence,
            "reason": reason,
            "privacy_risk": privacy_risk,
            "privacy_explanation": privacy_explanation,
            "correction": correction,
            "used_evidence": True
        }
    except Exception as e:
        print(f"DEBUG: Error parsing AI response: {e}")
        return {
            "status": status,
            "confidence": confidence,
            "reason": f"Analysis completed (partial parse). {reason}",
            "privacy_risk": privacy_risk,
            "privacy_explanation": privacy_explanation,
            "correction": correction,
            "used_evidence": True
        }

def analyze_deepfake(file_path_or_data, image_data=None, mime_type=None):
    """
    Analyzes media content for deep fake indicators.
    """
    print(f"DEBUG: analyze_deepfake called with file_path_or_data type: {type(file_path_or_data)}, image_data: {bool(image_data)}, mime_type: {mime_type}")
    
    # If image_data is provided (as base64 string from frontend), use it directly
    if image_data:
        print(f"DEBUG: Using provided image_data for analysis")
        # Ollama Platform
        if AI_PLATFORM == "ollama":
            print(f"DEBUG: Deepfake analysis using Ollama with image data: {bool(image_data)}")
            prompt_text = (
                "Analyze this media for deepfakes, AI artifacts, or facial manipulation. "
                "Respond ONLY as: Verdict: [Likely Real/Likely Deepfake/Uncertain], Confidence: [0-100], Reasoning: [Short assessment]. "
                f"Context: Analyzing uploaded media file."
            )
            
            # image_data from frontend is already base64 encoded
            ai_analysis = call_ollama(prompt_text, model=OLLAMA_MODEL_VISION, images=[image_data])
            
            if "Error" in ai_analysis:
                print(f"DEBUG: Ollama deepfake analysis failed: {ai_analysis}")
                # Fallback to heuristics if ollama fails or model missing
                return heuristic_fallback(file_path_or_data, False, None, ai_analysis, "deepfake")

            print(f"DEBUG: Ollama deepfake analysis result: {ai_analysis[:200]}...")
            # Parse the response (reusing logic)
            verdict = "Uncertain"
            verdict_match = re.search(r"Verdict:\s*\[?(Likely Real|Likely Deepfake|Uncertain|Likely Authentic)", ai_analysis, re.IGNORECASE)
            if verdict_match:
                v_raw = verdict_match.group(1).title()
                if "Deepfake" in v_raw: verdict = "Likely Deepfake"
                elif "Real" in v_raw or "Authentic" in v_raw: verdict = "Likely Authentic"
            
            conf_val = 0.5
            conf_match = re.search(r"Confidence:\s*\[?(\d+)", ai_analysis)
            if conf_match:
                conf_val = int(conf_match.group(1)) / 100.0
            
            reasoning = "Local analysis completed via Ollama."
            reason_match = re.search(r"Reasoning:\s*(.*)", ai_analysis, re.DOTALL | re.IGNORECASE)
            if reason_match:
                reasoning = reason_match.group(1).strip()

            return {
                "status": verdict,
                "confidence": conf_val,
                "reason": reasoning,
                "privacy_risk": "Low",
                "privacy_explanation": "Processed locally via Ollama.",
                "analysis_details": {
                    "indicators_found": 0,
                    "fake_probability": conf_val if "Deepfake" in verdict else 1 - conf_val,
                    "technical_assessment": f"Ollama ({OLLAMA_MODEL_VISION}) assessment: {reasoning}"
                }
            }
        
        # Gemini Platform
        if GEMINI_API_KEY:
            try:
                import subprocess
                import json
                import tempfile
                
                # Create a prompt for the AI
                prompt_text = (
                    "You are an expert deepfake detector. Analyze this media for synthetic generation, manipulation, or AI artifacts. "
                    "For videos, focus on temporal flickering, unnatural movements, and lighting inconsistencies. "
                    f"Context: Analyzing uploaded media file. "
                    "Respond ONLY in this format: Verdict: [Likely Real/Likely Deepfake/Uncertain], Confidence: [0-100], Reasoning: [Short explanation]."
                )
                
                # Prepare parts
                parts = [{"text": prompt_text}]
                if image_data:
                    parts.append({
                        "inline_data": {
                            "mime_type": mime_type or "image/jpeg",
                            "data": image_data
                        }
                    })
                
                # Prepare payload
                payload = {
                    "contents": [{"parts": parts}],
                    "generationConfig": {"temperature": 0.1, "maxOutputTokens": 200}
                }
                
                # Write payload to a temporary file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp:
                    json.dump(payload, temp)
                    temp_path = temp.name

                # Direct REST API call via curl.exe
                # Explicitly using gemini-1.5-flash for stable vision analysis
                api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
                curl_cmd = f'curl.exe -s -X POST "{api_url}" -H "Content-Type: application/json" -d @"{temp_path}"'
                
                with open("ai_debug_output.txt", "a", encoding="utf-8") as f:
                    f.write(f"\n--- {time.ctime()} --- DEEPFAKE CURL ---\n")
                    if image_data:
                        f.write(f"Image data provided (base64 length: {len(image_data)})\n")

                result = subprocess.run(curl_cmd, shell=True, capture_output=True, text=True, timeout=30)
                
                # Clean up temp file
                try: os.unlink(temp_path)
                except: pass

                if result.returncode == 0:
                    res_json = json.loads(result.stdout)
                    if 'error' in res_json:
                        err = res_json['error']
                        if err.get('status') == 'RESOURCE_EXHAUSTED' or err.get('code') == 429:
                            return {
                                "status": "Quota Exceeded",
                                "confidence": 0,
                                "reason": "Deepfake analysis limit reached. AI could not process the media.",
                                "privacy_risk": "Low",
                                "privacy_explanation": "Media analysis failed due to quota limitations.",
                                "analysis_details": {
                                    "indicators_found": 0,
                                    "fake_probability": 0.5,
                                    "technical_assessment": "Gemini API Quota Exceeded. Please try again later."
                                }
                            }

                    if 'candidates' in res_json:
                        ai_analysis = res_json['candidates'][0]['content']['parts'][0]['text']
                        
                        # Simple regex parsing
                        verdict = "Uncertain"
                        verdict_match = re.search(r"Verdict:\s*(Likely Real|Likely Deepfake|Uncertain|Likely Authentic)", ai_analysis, re.IGNORECASE)
                        if verdict_match:
                            v_raw = verdict_match.group(1).title()
                            if "Deepfake" in v_raw: verdict = "Likely Deepfake"
                            elif "Real" in v_raw or "Authentic" in v_raw: verdict = "Likely Authentic"
                        
                        conf_val = 0.5
                        conf_match = re.search(r"Confidence:\s*(\d+)", ai_analysis)
                        if conf_match:
                            conf_val = int(conf_match.group(1)) / 100.0
                        
                        reasoning = "AI analysis completed."
                        reason_match = re.search(r"Reasoning:\s*(.*)", ai_analysis, re.DOTALL | re.IGNORECASE)
                        if reason_match:
                            reasoning = reason_match.group(1).strip()

                        return {
                            "status": verdict,
                            "confidence": conf_val,
                            "reason": reasoning,
                            "privacy_risk": "Low",
                            "privacy_explanation": "Media content analysis completed.",
                            "analysis_details": {
                                "indicators_found": 0,
                                "fake_probability": conf_val if "Deepfake" in verdict else 1 - conf_val,
                                "technical_assessment": f"AI assessment: {reasoning}"
                            }
                        }
                    else:
                        with open("ai_debug_output.txt", "a", encoding="utf-8") as f:
                            f.write(f"ERROR: No candidates in deepfake response: {result.stdout[:500]}\n")
                else:
                    with open("ai_debug_output.txt", "a", encoding="utf-8") as f:
                        f.write(f"ERROR: Curl failed with code {result.returncode}: {result.stderr}\n")
            except Exception as e:
                print(f"DEBUG: Error using AI for deepfake analysis: {e}")
                pass
        
        # If no AI platform is available, use heuristics
        print(f"DEBUG: No AI platform available, using heuristics for deepfake detection")
        # ... (rest of the heuristic logic remains same)
        # This could be a filename or some identifier
        file_lower = str(file_path_or_data).lower()
        
        # Simulated deep fake detection heuristics
        # In a real implementation, this would use ML models to analyze video/image frames
        deepfake_indicators = [
            'fake', 'deepfake', 'manipulated', 'altered', 'synthetic', 'generated',
            'ai-generated', 'computer-generated', 'not real', 'simulation'
        ]
        
        # Count indicators in filename/description
        indicator_count = sum(1 for indicator in deepfake_indicators if indicator in file_lower)
        
        # Calculate probability based on indicators
        if indicator_count > 0:
            fake_probability = min(0.6 + (indicator_count * 0.15), 0.98)  # Higher base probability if indicators found
        else:
            # Analyze filename patterns that might suggest deepfakes
            suspicious_patterns = ['fake', 'deep', 'ai_', '_ai', 'synthetic', 'generated', 'gen_', 'face', 'swap']
            found_suspicious = sum(1 for pattern in suspicious_patterns if pattern in file_lower)
            
            if found_suspicious > 0:
                fake_probability = min(0.5 + (found_suspicious * 0.12), 0.9)  # Moderate probability for suspicious patterns
            else:
                # Default lower probability if no suspicious indicators
                fake_probability = 0.2  # Lower default assumption
                
                # Analyze file extension - certain extensions more likely to contain deepfakes
                if any(ext in file_lower for ext in ['.mp4', '.mov', '.avi', '.mkv']):  # Video formats
                    fake_probability += 0.15
                elif any(ext in file_lower for ext in ['.jpg', '.jpeg', '.png', '.bmp']):  # Image formats
                    fake_probability += 0.1
                
                # Add some variance but keep it reasonable
                import random
                fake_probability += random.uniform(-0.1, 0.15)
                fake_probability = max(0.05, min(0.95, fake_probability))  # Clamp between 5% and 95%
        
        # Determine status based on probability
        if fake_probability > 0.7:
            status = "Likely Deepfake"
            confidence = round(fake_probability, 3)
            reason = f"High probability of manipulation detected ({indicator_count} indicators found)."
        elif fake_probability > 0.4:
            status = "Uncertain"
            confidence = round(fake_probability, 3)
            reason = f"Moderate probability of manipulation ({indicator_count} indicators found)."
        else:
            # If it's a video/image with NO indicators in filename and we are in FALLBACK mode, 
            # we should be MORE uncertain rather than calling it authentic.
            status = "Uncertain (Local Heuristics)"
            confidence = 0.5
            reason = f"AI analysis unavailable. No explicit deepfake indicators found in media metadata, but visual verification is required."
        
        return {
            "status": status,
            "confidence": confidence,
            "reason": reason,
            "privacy_risk": "Low",
            "privacy_explanation": "Media content analysis completed. No privacy risks detected.",
            "analysis_details": {
                "indicators_found": indicator_count,
                "fake_probability": fake_probability,
                "technical_assessment": "Local heuristic fallback triggered. This is less accurate than AI visual analysis."
            }
        }
    else:
        # If no image data provided, use filename-based heuristic analysis
        print(f"DEBUG: No image data provided, using filename-based heuristic analysis")
        file_lower = str(file_path_or_data).lower()
        
        # Simulated deep fake detection heuristics
        deepfake_indicators = [
            'fake', 'deepfake', 'manipulated', 'altered', 'synthetic', 'generated',
            'ai-generated', 'computer-generated', 'not real', 'simulation'
        ]
        
        # Count indicators in filename/description
        indicator_count = sum(1 for indicator in deepfake_indicators if indicator in file_lower)
        
        # Calculate probability based on indicators
        if indicator_count > 0:
            fake_probability = min(0.6 + (indicator_count * 0.15), 0.98)  # Higher base probability if indicators found
        else:
            # Analyze filename patterns that might suggest deepfakes
            suspicious_patterns = ['fake', 'deep', 'ai_', '_ai', 'synthetic', 'generated', 'gen_', 'face', 'swap']
            found_suspicious = sum(1 for pattern in suspicious_patterns if pattern in file_lower)
            
            if found_suspicious > 0:
                fake_probability = min(0.5 + (found_suspicious * 0.12), 0.9)  # Moderate probability for suspicious patterns
            else:
                # Default lower probability if no suspicious indicators
                fake_probability = 0.2  # Lower default assumption
                
                # Analyze file extension - certain extensions more likely to contain deepfakes
                if any(ext in file_lower for ext in ['.mp4', '.mov', '.avi', '.mkv']):  # Video formats
                    fake_probability += 0.15
                elif any(ext in file_lower for ext in ['.jpg', '.jpeg', '.png', '.bmp']):  # Image formats
                    fake_probability += 0.1
                
                # Add some variance but keep it reasonable
                import random
                fake_probability += random.uniform(-0.1, 0.15)
                fake_probability = max(0.05, min(0.95, fake_probability))  # Clamp between 5% and 95%
        
        # Determine status based on probability
        if fake_probability > 0.7:
            status = "Likely Deepfake"
            confidence = round(fake_probability, 3)
            reason = f"High probability of manipulation detected ({indicator_count} indicators found)."
        elif fake_probability > 0.4:
            status = "Uncertain"
            confidence = round(fake_probability, 3)
            reason = f"Moderate probability of manipulation ({indicator_count} indicators found)."
        else:
            status = "Uncertain (Local Heuristics)"
            confidence = 0.5
            reason = f"No explicit deepfake indicators found in media metadata, but visual verification is required."
        
        return {
            "status": status,
            "confidence": confidence,
            "reason": reason,
            "privacy_risk": "Low",
            "privacy_explanation": "Media content analysis completed. No privacy risks detected.",
            "analysis_details": {
                "indicators_found": indicator_count,
                "fake_probability": fake_probability,
                "technical_assessment": "Filename-based heuristic analysis. Visual inspection is recommended."
            }
        }
    # Ollama Platform
    if AI_PLATFORM == "ollama":
        print(f"DEBUG: Deepfake analysis using Ollama with image data: {bool(image_data)}")
        prompt_text = (
            "Analyze this media for deepfakes, AI artifacts, or facial manipulation. "
            "Respond ONLY as: Verdict: [Likely Real/Likely Deepfake/Uncertain], Confidence: [0-100], Reasoning: [Short assessment]. "
            f"Context: {file_path_or_data}."
        )
        
        images = [image_data] if image_data else None
        ai_analysis = call_ollama(prompt_text, model=OLLAMA_MODEL_VISION, images=images)
        
        if "Error" in ai_analysis:
            print(f"DEBUG: Ollama deepfake analysis failed: {ai_analysis}")
            # Fallback to heuristics if ollama fails or model missing
            return heuristic_fallback(file_path_or_data, False, None, ai_analysis, "deepfake")

        print(f"DEBUG: Ollama deepfake analysis result: {ai_analysis[:200]}...")
        # Parse the response (reusing logic)
        verdict = "Uncertain"
        verdict_match = re.search(r"Verdict:\s*\[?(Likely Real|Likely Deepfake|Uncertain|Likely Authentic)", ai_analysis, re.IGNORECASE)
        if verdict_match:
            v_raw = verdict_match.group(1).title()
            if "Deepfake" in v_raw: verdict = "Likely Deepfake"
            elif "Real" in v_raw or "Authentic" in v_raw: verdict = "Likely Authentic"
        
        conf_val = 0.5
        conf_match = re.search(r"Confidence:\s*\[?(\d+)", ai_analysis)
        if conf_match:
            conf_val = int(conf_match.group(1)) / 100.0
        
        reasoning = "Local analysis completed via Ollama."
        reason_match = re.search(r"Reasoning:\s*(.*)", ai_analysis, re.DOTALL | re.IGNORECASE)
        if reason_match:
            reasoning = reason_match.group(1).strip()

        return {
            "status": verdict,
            "confidence": conf_val,
            "reason": reasoning,
            "privacy_risk": "Low",
            "privacy_explanation": "Processed locally via Ollama.",
            "analysis_details": {
                "indicators_found": 0,
                "fake_probability": conf_val if "Deepfake" in verdict else 1 - conf_val,
                "technical_assessment": f"Ollama ({OLLAMA_MODEL_VISION}) assessment: {reasoning}"
            }
        }

    # Gemini Platform
    if GEMINI_API_KEY:
        try:
            import subprocess
            import json
            import tempfile
            
            # Create a prompt for the AI
            prompt_text = (
                "You are an expert deepfake detector. Analyze this media for synthetic generation, manipulation, or AI artifacts. "
                "For videos, focus on temporal flickering, unnatural movements, and lighting inconsistencies. "
                f"Context: {file_path_or_data}. "
                "Respond ONLY in this format: Verdict: [Likely Real/Likely Deepfake/Uncertain], Confidence: [0-100], Reasoning: [Short explanation]."
            )
            
            # Prepare parts
            parts = [{"text": prompt_text}]
            if image_data:
                parts.append({
                    "inline_data": {
                        "mime_type": mime_type or "image/jpeg",
                        "data": image_data
                    }
                })
            
            # Prepare payload
            payload = {
                "contents": [{"parts": parts}],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 200}
            }
            
            # Write payload to a temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp:
                json.dump(payload, temp)
                temp_path = temp.name

            # Direct REST API call via curl.exe
            # Explicitly using gemini-1.5-flash for stable vision analysis
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            curl_cmd = f'curl.exe -s -X POST "{api_url}" -H "Content-Type: application/json" -d @"{temp_path}"'
            
            with open("ai_debug_output.txt", "a", encoding="utf-8") as f:
                f.write(f"\n--- {time.ctime()} --- DEEPFAKE CURL ---\n")
                if image_data:
                    f.write(f"Image data provided (base64 length: {len(image_data)})\n")

            result = subprocess.run(curl_cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            # Clean up temp file
            try: os.unlink(temp_path)
            except: pass

            if result.returncode == 0:
                res_json = json.loads(result.stdout)
                if 'error' in res_json:
                    err = res_json['error']
                    if err.get('status') == 'RESOURCE_EXHAUSTED' or err.get('code') == 429:
                        return {
                            "status": "Quota Exceeded",
                            "confidence": 0,
                            "reason": "Deepfake analysis limit reached. AI could not process the media.",
                            "privacy_risk": "Low",
                            "privacy_explanation": "Media analysis failed due to quota limitations.",
                            "analysis_details": {
                                "indicators_found": 0,
                                "fake_probability": 0.5,
                                "technical_assessment": "Gemini API Quota Exceeded. Please try again later."
                            }
                        }

                if 'candidates' in res_json:
                    ai_analysis = res_json['candidates'][0]['content']['parts'][0]['text']
                    
                    # Simple regex parsing
                    verdict = "Uncertain"
                    verdict_match = re.search(r"Verdict:\s*(Likely Real|Likely Deepfake|Uncertain|Likely Authentic)", ai_analysis, re.IGNORECASE)
                    if verdict_match:
                        v_raw = verdict_match.group(1).title()
                        if "Deepfake" in v_raw: verdict = "Likely Deepfake"
                        elif "Real" in v_raw or "Authentic" in v_raw: verdict = "Likely Authentic"
                    
                    conf_val = 0.5
                    conf_match = re.search(r"Confidence:\s*(\d+)", ai_analysis)
                    if conf_match:
                        conf_val = int(conf_match.group(1)) / 100.0
                    
                    reasoning = "AI analysis completed."
                    reason_match = re.search(r"Reasoning:\s*(.*)", ai_analysis, re.DOTALL | re.IGNORECASE)
                    if reason_match:
                        reasoning = reason_match.group(1).strip()

                    return {
                        "status": verdict,
                        "confidence": conf_val,
                        "reason": reasoning,
                        "privacy_risk": "Low",
                        "privacy_explanation": "Media content analysis completed.",
                        "analysis_details": {
                            "indicators_found": 0,
                            "fake_probability": conf_val if "Deepfake" in verdict else 1 - conf_val,
                            "technical_assessment": f"AI assessment: {reasoning}"
                        }
                    }
                else:
                    with open("ai_debug_output.txt", "a", encoding="utf-8") as f:
                        f.write(f"ERROR: No candidates in deepfake response: {result.stdout[:500]}\n")
            else:
                with open("ai_debug_output.txt", "a", encoding="utf-8") as f:
                    f.write(f"ERROR: Curl failed with code {result.returncode}: {result.stderr}\n")
        except Exception as e:
            print(f"DEBUG: Error using AI for deepfake analysis: {e}")
            pass
    
    # Fallback to heuristic analysis if AI fails or no API key
    if isinstance(file_path_or_data, str):
        # ... (rest of the heuristic logic remains same)
        # This could be a filename or some identifier
        file_lower = file_path_or_data.lower()
        
        # Simulated deep fake detection heuristics
        # In a real implementation, this would use ML models to analyze video/image frames
        deepfake_indicators = [
            'fake', 'deepfake', 'manipulated', 'altered', 'synthetic', 'generated',
            'ai-generated', 'computer-generated', 'not real', 'simulation'
        ]
        
        # Count indicators in filename/description
        indicator_count = sum(1 for indicator in deepfake_indicators if indicator in file_lower)
        
        # Calculate probability based on indicators
        if indicator_count > 0:
            fake_probability = min(0.6 + (indicator_count * 0.15), 0.98)  # Higher base probability if indicators found
        else:
            # Analyze filename patterns that might suggest deepfakes
            suspicious_patterns = ['fake', 'deep', 'ai_', '_ai', 'synthetic', 'generated', 'gen_', 'face', 'swap']
            found_suspicious = sum(1 for pattern in suspicious_patterns if pattern in file_lower)
            
            if found_suspicious > 0:
                fake_probability = min(0.5 + (found_suspicious * 0.12), 0.9)  # Moderate probability for suspicious patterns
            else:
                # Default lower probability if no suspicious indicators
                fake_probability = 0.2  # Lower default assumption
                
                # Analyze file extension - certain extensions more likely to contain deepfakes
                if any(ext in file_lower for ext in ['.mp4', '.mov', '.avi', '.mkv']):  # Video formats
                    fake_probability += 0.15
                elif any(ext in file_lower for ext in ['.jpg', '.jpeg', '.png', '.bmp']):  # Image formats
                    fake_probability += 0.1
                
                # Add some variance but keep it reasonable
                import random
                fake_probability += random.uniform(-0.1, 0.15)
                fake_probability = max(0.05, min(0.95, fake_probability))  # Clamp between 5% and 95%
        
        # Determine status based on probability
        if fake_probability > 0.7:
            status = "Likely Deepfake"
            confidence = round(fake_probability, 3)
            reason = f"High probability of manipulation detected ({indicator_count} indicators found)."
        elif fake_probability > 0.4:
            status = "Uncertain"
            confidence = round(fake_probability, 3)
            reason = f"Moderate probability of manipulation ({indicator_count} indicators found)."
        else:
            # If it's a video/image with NO indicators in filename and we are in FALLBACK mode, 
            # we should be MORE uncertain rather than calling it authentic.
            status = "Uncertain (Local Heuristics)"
            confidence = 0.5
            reason = f"AI analysis unavailable. No explicit deepfake indicators found in media metadata, but visual verification is required."
        
        return {
            "status": status,
            "confidence": confidence,
            "reason": reason,
            "privacy_risk": "Low",
            "privacy_explanation": "Media content analysis completed. No privacy risks detected.",
            "analysis_details": {
                "indicators_found": indicator_count,
                "fake_probability": fake_probability,
                "technical_assessment": "Local heuristic fallback triggered. This is less accurate than AI visual analysis."
            }
        }
    else:
        # Handle binary data case
        return {
            "status": "Uncertain",
            "confidence": 0.5,
            "reason": "Unable to analyze media data format.",
            "privacy_risk": "Low",
            "privacy_explanation": "Media content analysis completed. No privacy risks detected in the analysis process.",
            "analysis_details": {
                "indicators_found": 0,
                "fake_probability": 0.5,
                "technical_assessment": "Format not recognized for deepfake analysis."
            }
        }

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
        confidence = 0.9
        reason = f"Published by a known trusted news source: {domain}"
    elif any(suspicious in domain_lower for suspicious in suspicious_domains):
        status = "Suspicious Source"
        confidence = 0.8
        reason = f"Domain contains suspicious elements: {domain}"
    else:
        status = "Neutral Source"
        confidence = 0.6
        reason = f"Source {domain} is neither explicitly trusted nor suspicious."
    
    return {
        "status": status,
        "confidence": confidence,
        "reason": reason,
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
        print(f"DEBUG: Privacy analysis started for: {text[:50]}...")
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
        result = {
            "status": privacy_risk,
            "confidence": 0.8,
            "reason": "Based on presence of personal identifiers in the text",
            "privacy_risk": privacy_risk,
            "privacy_explanation": privacy_explanation
        }
        print(f"DEBUG: analyze_content (privacy) -> status={result['status']} confidence={result['confidence']}")
        return result
    elif analysis_type == "news":  # News analysis
        print(f"DEBUG: News analysis started for: {text[:50]}...")
        # Use the pre-trained fake news detection model
        try:
            # First try the pre-trained model
            detection_result = detect_fake_news(text)
            
            status = detection_result['status']
            confidence = detection_result['confidence']
            reason = detection_result['reason']
            
            # Generate correction suggestion based on the result
            if detection_result['is_fake']:
                correction_suggestion = generate_correction_suggestion(text)
            else:
                correction_suggestion = ""
                
            # For news analysis, privacy risk is not applicable
            privacy_risk = "Not Applicable"
            privacy_explanation = "Privacy risk assessment not applicable to this function."
            
            result = {
                "status": status,
                "confidence": confidence,
                "reason": reason,
                "correction": correction_suggestion,
                "privacy_risk": privacy_risk,
                "privacy_explanation": privacy_explanation
            }
            print(f"DEBUG: analyze_content (news) -> status={result['status']} confidence={result['confidence']}")
            return result
        except Exception as e:
            print(f"DEBUG: Error using pre-trained fake news detector: {e}")
            # Fall back to the heuristic analysis
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
            
            # Calculate percentages for more intuitive confidence
            total_indicators = fake_score + real_score
            if total_indicators > 0:
                fake_percentage = fake_score / total_indicators
                real_percentage = real_score / total_indicators
            else:
                # Default to a slight bias toward real if no indicators found
                fake_percentage = 0.3
                real_percentage = 0.3

            if fake_percentage > 0.55:  # More than 55% fake indicators
                status = "Likely Fake"
                confidence = min(0.6 + fake_percentage * 0.4, 0.95)  # Scale confidence between 60-95%
                reason = f"Contains strong indicators of fake news: {fake_score} potential indicators found. The text exhibits sensational language, unverifiable claims, or emotional manipulation tactics typical of unreliable sources."
                correction_suggestion = generate_correction_suggestion(text)
            elif real_percentage > 0.55:  # More than 55% real indicators
                status = "Likely Real"
                confidence = min(0.6 + real_percentage * 0.4, 0.95)  # Scale confidence between 60-95%
                reason = f"Contains indicators of reliable reporting: {real_score} credibility indicators found. The text includes verifiable sources, professional journalism markers, and evidence-based language."
                correction_suggestion = ""
            else:
                # If no clear indication, analyze other factors
                # Check for sensational patterns
                exclamation_count = text.count('!')
                caps_ratio = len(re.findall(r'[A-Z]{3,}', text)) / max(len(text.split()), 1)
                
                # If there are many sensational elements, lean toward fake
                if exclamation_count > 3 or caps_ratio > 0.1:
                    status = "Likely Fake"
                    confidence = min(0.55 + (exclamation_count * 0.05) + (caps_ratio * 0.2), 0.8)
                    reason = f"Highly sensational presentation detected: {exclamation_count} exclamation marks and {caps_ratio*100:.1f}% capitalized phrases suggest unreliable source."
                    correction_suggestion = generate_correction_suggestion(text)
                elif fake_score > real_score:
                    status = "Likely Fake"
                    confidence = max(0.5, min(0.5 + fake_percentage * 0.3, 0.75))
                    reason = f"Shows some indicators of fake news: {fake_score} potential indicators found."
                    correction_suggestion = generate_correction_suggestion(text)
                elif real_score > fake_score:
                    status = "Likely Real"
                    confidence = max(0.5, min(0.5 + real_percentage * 0.3, 0.75))
                    reason = f"Shows some indicators of reliable reporting: {real_score} credibility indicators found."
                    correction_suggestion = ""
                else:
                    # Still uncertain, but let's not default to 50%
                    status = "Uncertain"
                    confidence = 0.4  # Lower confidence for truly uncertain cases
                    reason = "Insufficient indicators to determine authenticity. The text contains neither strong fake news indicators nor strong credibility markers."
                    correction_suggestion = ""
        
        # For news analysis, privacy risk is not applicable
        privacy_risk = "Not Applicable"
        privacy_explanation = "Privacy risk assessment not applicable to this function."
        
        result = {
            "status": status,
            "confidence": confidence,
            "reason": reason,
            "correction": correction_suggestion,
            "privacy_risk": privacy_risk,
            "privacy_explanation": privacy_explanation
        }
        print(f"DEBUG: analyze_content -> status={result['status']} confidence={result['confidence']}")
        return result
    else:  # For any other analysis type
        print(f"DEBUG: Unknown analysis type: {analysis_type}, defaulting to heuristic analysis")
        # Default to heuristic analysis for unknown types
        # ... (same heuristic code as before)
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
        
        # Calculate percentages for more intuitive confidence
        total_indicators = fake_score + real_score
        if total_indicators > 0:
            fake_percentage = fake_score / total_indicators
            real_percentage = real_score / total_indicators
        else:
            # Default to a slight bias toward real if no indicators found
            fake_percentage = 0.3
            real_percentage = 0.3

        if fake_percentage > 0.55:  # More than 55% fake indicators
            status = "Likely Fake"
            confidence = min(0.6 + fake_percentage * 0.4, 0.95)  # Scale confidence between 60-95%
            reason = f"Contains strong indicators of fake news: {fake_score} potential indicators found. The text exhibits sensational language, unverifiable claims, or emotional manipulation tactics typical of unreliable sources."
            correction_suggestion = generate_correction_suggestion(text)
        elif real_percentage > 0.55:  # More than 55% real indicators
            status = "Likely Real"
            confidence = min(0.6 + real_percentage * 0.4, 0.95)  # Scale confidence between 60-95%
            reason = f"Contains indicators of reliable reporting: {real_score} credibility indicators found. The text includes verifiable sources, professional journalism markers, and evidence-based language."
            correction_suggestion = ""
        else:
            # If no clear indication, analyze other factors
            # Check for sensational patterns
            exclamation_count = text.count('!')
            caps_ratio = len(re.findall(r'[A-Z]{3,}', text)) / max(len(text.split()), 1)
            
            # If there are many sensational elements, lean toward fake
            if exclamation_count > 3 or caps_ratio > 0.1:
                status = "Likely Fake"
                confidence = min(0.55 + (exclamation_count * 0.05) + (caps_ratio * 0.2), 0.8)
                reason = f"Highly sensational presentation detected: {exclamation_count} exclamation marks and {caps_ratio*100:.1f}% capitalized phrases suggest unreliable source."
                correction_suggestion = generate_correction_suggestion(text)
            elif fake_score > real_score:
                status = "Likely Fake"
                confidence = max(0.5, min(0.5 + fake_percentage * 0.3, 0.75))
                reason = f"Shows some indicators of fake news: {fake_score} potential indicators found."
                correction_suggestion = generate_correction_suggestion(text)
            elif real_score > fake_score:
                status = "Likely Real"
                confidence = max(0.5, min(0.5 + real_percentage * 0.3, 0.75))
                reason = f"Shows some indicators of reliable reporting: {real_score} credibility indicators found."
                correction_suggestion = ""
            else:
                # Still uncertain, but let's not default to 50%
                status = "Uncertain"
                confidence = 0.4  # Lower confidence for truly uncertain cases
                reason = "Insufficient indicators to determine authenticity. The text contains neither strong fake news indicators nor strong credibility markers."
                correction_suggestion = ""
    
        # Default privacy risk for unknown analysis types
        privacy_risk = "Not Applicable"
        privacy_explanation = "Privacy risk assessment not applicable to this function."
        
        result = {
            "status": status,
            "confidence": confidence,
            "reason": reason,
            "correction": correction_suggestion,
            "privacy_risk": privacy_risk,
            "privacy_explanation": privacy_explanation
        }
        print(f"DEBUG: analyze_content (unknown type) -> status={result['status']} confidence={result['confidence']}")
        return result


def generate_correction_suggestion(text):
    # Generate a suggested correction for fake news with actual facts
    corrections = []
    
    text_lower = text.lower()
    
    # Specific patterns that indicate fake news with corresponding corrections
    if 'you won\'t believe' in text_lower:
        corrections.append("This is a classic clickbait phrase. Verify this claim with credible sources before believing it.")
    elif 'breaking news' in text_lower and 'urgent' in text_lower:
        corrections.append("Check established news outlets like Reuters, AP, or BBC to confirm this breaking news story.")
    elif 'shocking' in text_lower or 'unbelievable' in text_lower:
        corrections.append("Be skeptical of sensational claims. Look for evidence from reliable sources.")
    elif 'miracle cure' in text_lower or 'cures all diseases' in text_lower:
        corrections.append("Medical claims should be verified with peer-reviewed studies and official health authorities like WHO or CDC.")
    elif 'virus hoax' in text_lower or 'all a lie' in text_lower:
        corrections.append("Health information should be verified with reputable medical institutions and peer-reviewed research.")
    elif 'election fraud' in text_lower and ('millions of votes' in text_lower or 'rigged' in text_lower):
        corrections.append("Electoral integrity claims should be verified with official election monitoring organizations and certified results.")
    elif 'celebrity death' in text_lower:
        corrections.append("Verify celebrity news with official announcements or reputable entertainment news sources before sharing.")
    elif 'won lottery' in text_lower or 'you\'ve won' in text_lower:
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
        
        result = {
            "status": status,
            "confidence": confidence,
            "reason": reason,
            "correction": content_analysis.get("correction", ""),
            "privacy_risk": content_analysis["privacy_risk"],
            "privacy_explanation": content_analysis["privacy_explanation"]
        }
        print(f"DEBUG: heuristic_fallback (url) -> status={result['status']} confidence={result['confidence']} reason={error_msg}")
        return result
    else:
        # Regular text analysis
        result = analyze_content(text, analysis_type)
        # Ensure the result has the correct structure
        out = {
            "status": result.get("status", "Uncertain"),
            "confidence": result.get("confidence", 0.5),
            "reason": result.get("reason", "Analysis completed"),
            "correction": result.get("correction", ""),
            "privacy_risk": result.get("privacy_risk", "Low"),
            "privacy_explanation": result.get("privacy_explanation", "No privacy risks detected")
        }
        print(f"DEBUG: heuristic_fallback -> status={out['status']} confidence={out['confidence']} reason={error_msg}")
        return out
