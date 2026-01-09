from flask import Flask, request, jsonify
from analyzer import analyze_news, get_trending_news
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

    return jsonify(result)

@app.route('/trending-news', methods=['GET'])
def trending_news():
    try:
        result = get_trending_news()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to fetch trending news: {str(e)}"
        }), 500

# Health check endpoints
@app.route('/health')
def health_check():
    """Health check endpoint for production monitoring"""
    return jsonify({
        "status": "healthy",
        "service": "TrueVail Backend",
        "version": "1.0.0"
    })

@app.route('/ready')
def readiness_check():
    """Readiness check endpoint"""
    # In a real app, you might check database connections, etc.
    return jsonify({
        "status": "ready",
        "service": "TrueVail Backend"
    })

# Error handlers for production
@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Resource not found",
        "message": "The requested endpoint does not exist"
    }), 404

if __name__ == "__main__":
    # For production, use debug=False and host 0.0.0.0
    app.run(host='0.0.0.0', port=5001, debug=False)
