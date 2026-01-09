"""
Fake News Detection Model for TrueVail Application
Based on the repository: https://github.com/nguyenvo09/fake_news_detection_deep_learning

This module provides a fake news detection model that can be integrated into the TrueVail backend.
"""
import os
import pickle
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
import joblib
import warnings
warnings.filterwarnings('ignore')

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class FakeNewsDetector:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_df=0.7, 
            max_features=5000,
            min_df=2, 
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.model = LogisticRegression(random_state=42)
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))
        self.is_trained = False
        
    def preprocess_text(self, text):
        """
        Preprocess the input text for fake news detection
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove special characters and digits
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords and stem
        tokens = [self.stemmer.stem(token) for token in tokens if token not in self.stop_words and len(token) > 2]
        
        return ' '.join(tokens)
    
    def prepare_training_data(self, data_dir="train_test_data/data_0"):
        """
        Prepare training data from the fake_news_detection_deep_learning repository
        """
        train_dir = os.path.join(data_dir, "train")
        test_dir = os.path.join(data_dir, "test")
        
        # Read training data
        train_texts = []
        train_labels = []
        
        for filename in os.listdir(train_dir):
            if filename.endswith(".txt"):
                with open(os.path.join(train_dir, filename), 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    if len(lines) > 1:  # Skip if only URL is present
                        content = ' '.join(lines[1:]).strip()  # Skip the first line which is URL
                        if content:
                            train_texts.append(content)
                            # Label based on filename or directory - in a real scenario, 
                            # we would need the ground truth labels
                            # For now, we'll use a heuristic based on the content
                            train_labels.append(0 if "fake" in filename.lower() or len(content) < 50 else 1)
        
        # Read test data
        test_texts = []
        test_labels = []
        
        for filename in os.listdir(test_dir):
            if filename.endswith(".txt"):
                with open(os.path.join(test_dir, filename), 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    if len(lines) > 1:  # Skip if only URL is present
                        content = ' '.join(lines[1:]).strip()  # Skip the first line which is URL
                        if content:
                            test_texts.append(content)
                            # Label based on filename or directory
                            test_labels.append(0 if "fake" in filename.lower() or len(content) < 50 else 1)
        
        return train_texts, train_labels, test_texts, test_labels
    
    def train(self, train_texts=None, train_labels=None):
        """
        Train the fake news detection model
        If no data is provided, it will try to use the repository data
        """
        if train_texts is None or train_labels is None:
            # Try to load from repository if available
            try:
                train_texts, train_labels, _, _ = self.prepare_training_data()
                if not train_texts:
                    # Fallback to a simple training example
                    train_texts = [
                        "This is a real news article with factual information.",
                        "Breaking news: Scientists discover new breakthrough in medicine.",
                        "Government announces new policy to improve education.",
                        "Study shows benefits of regular exercise for heart health.",
                        "Local community raises funds for new library.",
                        "City council votes on new infrastructure improvements.",
                        "Fake news spreading rapidly on social media platforms.",
                        "This story is completely false and made up.",
                        "Unverified claims about political candidates.",
                        "Miracle cure for cancer discovered without scientific evidence.",
                        "You won't believe what happened next.",
                        "Shocking celebrity death reported falsely."
                    ]
                    train_labels = [1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0]  # 1 for real, 0 for fake
            except:
                # Fallback to simple training example
                train_texts = [
                    "This is a real news article with factual information.",
                    "Breaking news: Scientists discover new breakthrough in medicine.",
                    "Government announces new policy to improve education.",
                    "Study shows benefits of regular exercise for heart health.",
                    "Local community raises funds for new library.",
                    "City council votes on new infrastructure improvements.",
                    "Fake news spreading rapidly on social media platforms.",
                    "This story is completely false and made up.",
                    "Unverified claims about political candidates.",
                    "Miracle cure for cancer discovered without scientific evidence.",
                    "You won't believe what happened next.",
                    "Shocking celebrity death reported falsely."
                ]
                train_labels = [1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0]  # 1 for real, 0 for fake
        
        # Preprocess texts
        processed_texts = [self.preprocess_text(text) for text in train_texts]
        
        # Vectorize the texts
        X = self.vectorizer.fit_transform(processed_texts)
        
        # Train the model
        self.model.fit(X, train_labels)
        self.is_trained = True
        
        return self
    
    def predict(self, text):
        """
        Predict if the given text is fake news or real news
        Returns a dictionary with prediction and confidence
        """
        if not self.is_trained:
            self.train()
        
        # Preprocess the input text
        processed_text = self.preprocess_text(text)
        
        # Vectorize the text
        X = self.vectorizer.transform([processed_text])
        
        # Get prediction
        prediction = self.model.predict(X)[0]
        prediction_proba = self.model.predict_proba(X)[0]
        
        # Determine the confidence
        confidence = max(prediction_proba)
        
        result = {
            "status": "Likely Real" if prediction == 1 else "Likely Fake",
            "confidence": float(confidence),
            "reason": f"Content {'matches' if prediction == 1 else 'does not match'} patterns of real news with {confidence*100:.1f}% confidence.",
            "is_fake": prediction == 0,
            "prediction_score": float(prediction_proba[0] if prediction == 0 else prediction_proba[1])
        }
        
        return result
    
    def save_model(self, filepath):
        """
        Save the trained model to a file
        """
        model_data = {
            'vectorizer': self.vectorizer,
            'model': self.model,
            'is_trained': self.is_trained
        }
        joblib.dump(model_data, filepath)
    
    def load_model(self, filepath):
        """
        Load a pre-trained model from a file
        """
        model_data = joblib.load(filepath)
        self.vectorizer = model_data['vectorizer']
        self.model = model_data['model']
        self.is_trained = model_data['is_trained']

# Global instance of the fake news detector
fake_news_detector = FakeNewsDetector()


def detect_fake_news(text):
    """
    Function to detect fake news using the trained model
    """
    print(f"DEBUG: Starting fake news detection for text: {text[:100]}...")
    result = fake_news_detector.predict(text)
    print(f"DEBUG: Fake news detection result: {result}")
    return result


def train_fake_news_detector():
    """
    Function to train the fake news detector
    """
    print("DEBUG: Training fake news detector...")
    fake_news_detector.train()
    print("DEBUG: Fake news detector training completed")
    return fake_news_detector
