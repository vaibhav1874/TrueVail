import os
import sys
from dotenv import load_dotenv

# Add the backend directory to the path if needed
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from analyzer import perform_ai_analysis

def test_ai():
    print("Testing AI analysis directly...")
    content = "CNN's chief 'fact checker,' Tom Foreman, claimed that Democrats didn't demand Obamacare benefits for illegal immigrants in exchange for ending the government shutdown. The alleged evidence for this, he said, is that 'the law itself says' that the 'only people who could get' these benefits are ' 'lawfully present in the United States'.' In fact, the Democrat bill to reopen the government would have given about $91.4 billion of Obamacare benefits to illegal immigrants and other non-citizens over the next 10 years and multiples of that thereafter."
    
    print("\n--- Starting Analysis ---")
    result = perform_ai_analysis(content, analysis_type="news")
    print("\n--- Result ---")
    import json
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_ai()
