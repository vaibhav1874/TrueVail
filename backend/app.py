from flask import Flask, request, jsonify
from analyzer import analyze_news
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins for development

# ✅ HOME ROUTE
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "TrueVail backend is running on port 5001",
        "message": "Use POST /analyze to analyze content"
    })

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    text = data.get("text")
    analysis_type = data.get("type", "news")  # Default to news analysis
    image_data = data.get("image_data") # base64 string
    mime_type = data.get("mime_type")

    if not text and not image_data:
        return jsonify({"analysis": "No text or image provided"})

    try:
        result = analyze_news(text, analysis_type=analysis_type, image_data=image_data, mime_type=mime_type)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "analysis": f"Server error: {str(e)}",
            "status": "Error",
            "confidence": "0",
            "reason": f"An error occurred during analysis: {str(e)}",
            "privacy_risk": "Unknown",
            "privacy_explanation": "Could not determine privacy risks due to error."
        })

if __name__ == "__main__":
    # Switching to port 5001 to avoid ghost process conflicts
    app.run(debug=True, port=5001)
