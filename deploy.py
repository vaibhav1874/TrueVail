#!/usr/bin/env python3
"""
Production Deployment Script for TrueVail Application
This script prepares and deploys the application for production use.
"""

import os
import sys
import shutil
import subprocess
import json
from pathlib import Path

def create_production_config():
    """Create production-ready configuration"""
    print("Creating production configuration...")
    
    # Create production .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, "w") as f:
            f.write("# TrueVail Production Environment Variables\n")
            f.write("GEMINI_API_KEY=\n")
            f.write("AI_PLATFORM=gemini\n")
            f.write("OLLAMA_HOST=http://localhost:11434\n")
            f.write("OLLAMA_MODEL_TEXT=llama3.1:latest\n")
            f.write("OLLAMA_MODEL_VISION=llava:latest\n")
            f.write("NEWS_API_KEY=\n")
            print("Created .env file with default configuration")
    else:
        print(".env file already exists")

def optimize_backend_for_production():
    """Optimize backend for production deployment"""
    print("Optimizing backend for production...")
    
    # Create a production-ready version of app.py
    backend_dir = Path("backend")
    app_py_path = backend_dir / "app.py"
    
    if app_py_path.exists():
        # Read current app.py
        with open(app_py_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Modify to disable debug mode for production
        if "Debug mode: on" in content:
            # Replace debug mode enable with production settings
            content = content.replace("* Debug mode: on", "* Production mode: on")
            content = content.replace("debug=True", "debug=False")
        
        # Add production-ready error handling
        error_handling = '''
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
'''
        
        if "from flask import Flask" in content and "@app.errorhandler" not in content:
            # Insert error handlers near the end of the file
            lines = content.split('\n')
            # Find where main routes end and insert error handlers
            new_lines = []
            for line in lines:
                new_lines.append(line)
                if 'if __name__ == "__main__":' in line:
                    new_lines.append("")
                    new_lines.append(error_handling)
                    break
            else:
                # If __name__ == "__main__" not found, add at the end
                new_lines.extend(["", error_handling])
            
            content = '\n'.join(new_lines)
        
        # Write back the optimized content
        with open(app_py_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        print("Updated app.py for production use")

def create_deployment_docs():
    """Create deployment documentation"""
    print("Creating deployment documentation...")
    
    docs_content = """
# TrueVail Production Deployment Guide

## Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

## Installation Steps

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd TrueVail
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements_prod.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. Start the application:
   ```bash
   cd backend
   python app.py
   ```

## Environment Variables

Required:
- `GEMINI_API_KEY`: Your Google Gemini API key
- `AI_PLATFORM`: Either "gemini" or "ollama"

Optional:
- `OLLAMA_HOST`: Ollama host URL (default: http://localhost:11434)
- `OLLAMA_MODEL_TEXT`: Text model name (default: llama3.1:latest)
- `OLLAMA_MODEL_VISION`: Vision model name (default: llava:latest)
- `NEWS_API_KEY`: News API key for trending news (optional)

## Services

- Backend API: http://localhost:5001
- Frontend: Serve the frontend directory with a web server

## Production Notes

- Disable debug mode in production
- Use a production WSGI server (Gunicorn, uWSGI) instead of Flask dev server
- Set up proper logging
- Implement proper security measures
- Use HTTPS in production
"""
    
    with open("DEPLOYMENT.md", "w") as f:
        f.write(docs_content)
    
    print("Created DEPLOYMENT.md")

def create_health_check():
    """Create a health check endpoint"""
    print("Creating health check endpoint...")
    
    backend_dir = Path("backend")
    app_py_path = backend_dir / "app.py"
    
    if app_py_path.exists():
        with open(app_py_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Add health check endpoint if not present
        if "def health_check" not in content:
            # Find where other imports are and add health check route
            if "from flask import Flask" in content:
                # Add the health check function before the main execution
                health_route = '''

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
'''
                
                # Insert before the if __name__ == "__main__": block
                lines = content.split('\n')
                new_lines = []
                for i, line in enumerate(lines):
                    new_lines.append(line)
                    if 'app.route("/analyze")' in line and len(lines) > i+1 and 'def analyze' not in lines[i+1]:
                        # Add health check after the main route definition
                        new_lines.extend(health_route.split('\n')[1:])  # Skip first empty line
                        break
                else:
                    # If main route not found, add at the end before main block
                    new_lines.extend(health_route.split('\n')[1:])
                
                content = '\n'.join(new_lines)
                
                # Write back the updated content
                with open(app_py_path, "w", encoding="utf-8") as f:
                    f.write(content)
        
        print("Added health check endpoints")

def prepare_frontend():
    """Prepare frontend for deployment"""
    print("Preparing frontend for deployment...")
    
    # Create a build directory structure
    build_dir = Path("build")
    if not build_dir.exists():
        build_dir.mkdir()
    
    # Copy frontend files to build directory
    frontend_dir = Path("frontend")
    if frontend_dir.exists():
        build_frontend_dir = build_dir / "frontend"
        if build_frontend_dir.exists():
            shutil.rmtree(build_frontend_dir)
        
        shutil.copytree(frontend_dir, build_frontend_dir)
        print(f"Copied frontend to {build_frontend_dir}")
    
    # Create a simple production server script
    server_script = '''const express = require('express');
const path = require('path');
const app = express();

// Serve static files from the frontend directory
app.use(express.static(path.join(__dirname, 'frontend')));

// Catch-all handler to serve the main page for client-side routing
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'frontend', 'index.html'));
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Frontend server running on port ${PORT}`);
});
'''
    
    with open("server.js", "w") as f:
        f.write(server_script)
    
    # Create package.json for frontend server
    package_json = {
        "name": "truevail-frontend",
        "version": "1.0.0",
        "description": "Frontend server for TrueVail application",
        "main": "server.js",
        "scripts": {
            "start": "node server.js",
            "dev": "nodemon server.js"
        },
        "dependencies": {
            "express": "^4.18.2"
        },
        "engines": {
            "node": ">=14.0.0"
        }
    }
    
    with open("package.json", "w") as f:
        json.dump(package_json, f, indent=2)
    
    print("Created frontend server files")

def finalize_deployment_package():
    """Finalize the deployment package"""
    print("Finalizing deployment package...")
    
    # Create a deployment checklist
    checklist = """
# Deployment Checklist

## Before Deploying
- [ ] Update version numbers
- [ ] Verify all tests pass
- [ ] Check security configurations
- [ ] Validate environment variables
- [ ] Test API endpoints
- [ ] Verify error handling

## During Deployment
- [ ] Backup existing deployment
- [ ] Deploy backend first
- [ ] Deploy frontend
- [ ] Test all functionality
- [ ] Monitor logs

## After Deployment
- [ ] Verify health checks pass
- [ ] Test all major features
- [ ] Update DNS if needed
- [ ] Notify stakeholders
- [ ] Monitor performance
"""
    
    with open("DEPLOYMENT_CHECKLIST.md", "w") as f:
        f.write(checklist)
    
    print("Created deployment checklist")

def main():
    """Main deployment preparation function"""
    print("Preparing TrueVail for production deployment...")
    print("=" * 50)
    
    try:
        create_production_config()
        optimize_backend_for_production()
        create_health_check()
        create_deployment_docs()
        prepare_frontend()
        finalize_deployment_package()
        
        print("=" * 50)
        print("Deployment preparation complete!")
        print("\nNext steps:")
        print("1. Review DEPLOYMENT.md for detailed instructions")
        print("2. Update environment variables in .env")
        print("3. Test the application locally")
        print("4. Deploy to your production environment")
        
    except Exception as e:
        print(f"Error during deployment preparation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()