from flask import Flask, jsonify, render_template, request
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import os
import requests
from dotenv import load_dotenv
import re
import time
from datetime import datetime, timedelta

# Load environment variables for API keys
load_dotenv()

app = Flask(__name__)

# Global variables to store loaded data
tfidf_vectorizer = None
tfidf_matrix = None
articles_df = None
interactions_df = None

# API keys for news sources
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY")
NY_TIMES_API_KEY = os.getenv("NY_TIMES_API_KEY")

# Cache for API results to avoid hitting rate limits
article_cache = {}
CACHE_DURATION = 3600  # Cache duration in seconds (1 hour)

def load_data():
    """Load all required data files for the recommendation system"""
    global tfidf_vectorizer, tfidf_matrix, articles_df, interactions_df
    
    try:
        # Load article data
        print("Loading article data...")
        
        # Try to load local dataset first
        if os.path.exists('articles.csv'):
            articles_df = pd.read_csv('articles.csv')
            print(f"Loaded {len(articles_df)} articles from local dataset")
        else:
            # If no local data, initialize with empty dataframe
            articles_df = pd.DataFrame(columns=['article_id', 'title', 'category', 'keywords', 'url', 'snippet', 'published_date'])
            print("No local article dataset found. Will rely on API data.")
        
        # Load user interaction data if exists (for hybrid recommendations)
        if os.path.exists('user_interactions.csv'):
            print("Loading user interaction data...")
            interactions_df = pd.read_csv('user_interactions.csv')
            print(f"Loaded {len(interactions_df)} interactions")
        else:
            interactions_df = pd.DataFrame(columns=['user_id', 'article_id', 'timestamp', 'interaction_type'])
            
        # If TF-IDF files exist, load them
        if os.path.exists('tfidf_vectorizer.joblib') and os.path.exists('tfidf_matrix.joblib'):
            print("Loading existing TF-IDF vectorizer and matrix...")
            tfidf_vectorizer = joblib.load('tfidf_vectorizer.joblib')
            tfidf_matrix = joblib.load('tfidf_matrix.joblib')
            print(f"TF-IDF Matrix shape: {tfidf_matrix.shape}")
        else:
            # Initialize the vectorizer (will be trained on-the-fly for real inputs)
            print("Initializing new TF-IDF vectorizer...")
            tfidf_vectorizer = TfidfVectorizer(stop_words='english')
            # Matrix will be created when needed
            
        return True
    
    except Exception as e:
        print(f"Error loading data: {e}")
        return False

def fetch_articles_from_api(query, categories, max_results=20):
    """Fetch real articles from news APIs based on query and categories"""
    # Create a cache key
    cache_key = f"{query}_{'-'.join(sorted(categories))}"
    
    # Check if results are in cache and not expired
    if cache_key in article_cache:
        cache_time, cached_results = article_cache[cache_key]
        if time.time() - cache_time < CACHE_DURATION:
            print(f"Using cached results for: {query}")
            return cached_results
    
    combined_results = []
    
    # Try NewsAPI first
    if NEWS_API_KEY:
        try:
            # Map our categories to NewsAPI categories
            category_mapping = {
                'Technology': 'technology',
                'Business': 'business',
                'Science': 'science',
                'Sports': 'sports',
                'Lifestyle': 'health'  # Closest match
            }
            
            # Filter to categories supported by NewsAPI
            news_api_categories = [category_mapping[c] for c in categories if c in category_mapping]
            category_param = news_api_categories[0] if news_api_categories else None
            
            # Build the API URL
            url = 'https://newsapi.org/v2/everything'
            params = {
                'q': query,
                'apiKey': NEWS_API_KEY,
                'language': 'en',
                'pageSize': max_results,
                'sortBy': 'relevancy'
            }
            
            if category_param:
                params['category'] = category_param
                
            # Make the API request
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if (data['status'] == 'ok') and ('articles' in data):
                    for i, article in enumerate(data['articles']):
                        # Extract keywords from title and description
                        text = f"{article['title']} {article['description'] or ''}"
                        # Simple keyword extraction (could be improved)
                        keywords = extract_keywords(text)
                        
                        # Map to our format
                        result = {
                            'article_id': i + 1,
                            'title': article['title'],
                            'category': next((c for c in categories if category_mapping.get(c) == category_param), categories[0]),
                            'keywords': ','.join(keywords),
                            'url': article['url'],
                            'snippet': article['description'],
                            'published_date': article['publishedAt']
                        }
                        combined_results.append(result)
            
        except Exception as e:
            print(f"Error fetching from NewsAPI: {e}")
    
    # If no results or no NewsAPI key, try Guardian API as backup
    if not combined_results and GUARDIAN_API_KEY:
        try:
            # Map our categories to Guardian sections
            section_mapping = {
                'Technology': 'technology',
                'Business': 'business',
                'Science': 'science',
                'Sports': 'sport',
                'Lifestyle': 'lifeandstyle'
            }
            
            # Filter to categories supported by Guardian
            guardian_sections = [section_mapping[c] for c in categories if c in section_mapping]
            section_param = guardian_sections[0] if guardian_sections else None
            
            # Build the API URL
            url = 'https://content.guardianapis.com/search'
            params = {
                'q': query,
                'api-key': GUARDIAN_API_KEY,
                'show-fields': 'headline,trailText,body',
                'page-size': max_results
            }
            
            if section_param:
                params['section'] = section_param
                
            # Make the API request
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                for i, article in enumerate(data['response']['results']):
                    fields = article.get('fields', {})
                    text = f"{fields.get('headline', '')} {fields.get('trailText', '')}"
                    keywords = extract_keywords(text)
                    
                    result = {
                        'article_id': i + 1,
                        'title': fields.get('headline', article.get('webTitle', 'No title')),
                        'category': next((c for c in categories if section_mapping.get(c) == section_param), categories[0]),
                        'keywords': ','.join(keywords),
                        'url': article['webUrl'],
                        'snippet': fields.get('trailText', 'No preview available'),
                        'published_date': article['webPublicationDate']
                    }
                    combined_results.append(result)
        
        except Exception as e:
            print(f"Error fetching from Guardian API: {e}")
    
    # If still no results, fall back to local dataset
    if not combined_results and len(articles_df) > 0:
        print("No API results, falling back to local dataset")
        # Filter by categories
        filtered_df = articles_df[articles_df['category'].isin(categories)]
        
        # If we have the vectorizer and matrix already, use them to find similar articles
        if tfidf_vectorizer is not None and tfidf_matrix is not None:
            # Vectorize the query
            query_vector = tfidf_vectorizer.transform([query])
            
            # Find similar articles
            cosine_similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
            similar_indices = cosine_similarities.argsort()[::-1][:max_results]
            
            # Get top articles
            for idx in similar_indices:
                if idx < len(filtered_df):
                    article = filtered_df.iloc[idx]
                    result = {
                        'article_id': int(article['article_id']),
                        'title': article['title'],
                        'category': article['category'],
                        'keywords': article['keywords'],
                        'url': article.get('url', ''),
                        'snippet': article.get('snippet', 'No preview available'),
                        'published_date': article.get('published_date', 'Unknown'),
                        'similarity_score': float(cosine_similarities[idx])
                    }
                    combined_results.append(result)
        
        # If no results yet, just return some articles from the dataset
        if not combined_results:
            sample_size = min(max_results, len(filtered_df))
            sample_df = filtered_df.sample(n=sample_size) if sample_size > 0 else filtered_df
            
            for _, article in sample_df.iterrows():
                result = {
                    'article_id': int(article['article_id']),
                    'title': article['title'],
                    'category': article['category'],
                    'keywords': article['keywords'],
                    'url': article.get('url', ''),
                    'snippet': article.get('snippet', 'No preview available'),
                    'published_date': article.get('published_date', 'Unknown'),
                    'similarity_score': 0.5  # Default score
                }
                combined_results.append(result)
    
    # Save results to cache
    article_cache[cache_key] = (time.time(), combined_results)
    
    return combined_results

def extract_keywords(text, max_keywords=5):
    """Simple keyword extraction from text"""
    if not text:
        return []
    
    # Remove special characters and convert to lowercase
    text = re.sub(r'[^\w\s]', '', text.lower())
    
    # Split into words
    words = text.split()
    
    # Remove common stop words (simplified list)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 
                 'be', 'been', 'being', 'in', 'on', 'at', 'by', 'for', 'with', 'about', 
                 'against', 'between', 'into', 'through', 'during', 'before', 'after',
                 'above', 'below', 'to', 'from', 'up', 'down', 'of', 'off', 'over', 'under',
                 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
                 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some',
                 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
                 'can', 'will', 'just', 'should', 'now'}
    
    filtered_words = [word for word in words if word not in stop_words and len(word) > 3]
    
    # Count word frequencies
    word_freq = {}
    for word in filtered_words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and get top words
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    top_words = [word for word, freq in sorted_words[:max_keywords]]
    
    return top_words

def get_recommendations_by_interests(user_interests, categories, max_results=10):
    """
    Get content recommendations based on user interests and categories.
    
    Args:
        user_interests: String of user interests/topics
        categories: List of content categories to include
        max_results: Maximum number of results to return
        
    Returns:
        List of recommended articles
    """
    # First try to get real articles from APIs
    api_results = fetch_articles_from_api(user_interests, categories, max_results)
    if api_results:
        # Add similarity scores for API results
        # Since these are already filtered by API, we can assign high scores
        for i, article in enumerate(api_results):
            # Decrease score slightly by position to add some variety
            similarity = 0.95 - (i * 0.03)
            article['similarity_score'] = max(0.5, min(0.95, similarity))
        
        return api_results
    
    # If no API results, use content-based filtering with local dataset
    if len(articles_df) == 0:
        return []
    
    # Filter articles by selected categories
    filtered_df = articles_df[articles_df['category'].isin(categories)]
    
    if len(filtered_df) == 0:
        return []
    
    # If we have at least one article in filtered_df, use content-based filtering
    global tfidf_vectorizer, tfidf_matrix
    
    # Prepare TF-IDF if not already done
    if tfidf_matrix is None or tfidf_vectorizer is None:
        # Train vectorizer on keywords
        tfidf_vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = tfidf_vectorizer.fit_transform(filtered_df['keywords'])
    
    # Vectorize user interests
    user_vector = tfidf_vectorizer.transform([user_interests])
    
    # Calculate similarity between user interests and all articles
    cosine_similarities = cosine_similarity(user_vector, tfidf_matrix).flatten()
    
    # Get indices of top similar articles
    similar_indices = cosine_similarities.argsort()[::-1][:max_results]
    
    # Prepare recommendations list
    recommendations = []
    for idx in similar_indices:
        if cosine_similarities[idx] > 0.01:  # Only include somewhat relevant items
            article = filtered_df.iloc[idx]
            
            recommendation = {
                'article_id': int(article['article_id']),
                'title': article['title'],
                'category': article['category'],
                'keywords': article['keywords'],
                'similarity_score': float(cosine_similarities[idx]),
                'url': article.get('url', ''),
                'snippet': article.get('snippet', 'No preview available'),
                'published_date': article.get('published_date', 'Unknown')
            }
            recommendations.append(recommendation)
    
    return recommendations

# Flask routes
@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/recommend-by-interests', methods=['POST'])
def recommend_by_interests():
    """API endpoint to get recommendations based on user interests."""
    if not request.json:
        return jsonify({"error": "Invalid request format. JSON required."}), 400
    
    # Get user interests and categories from request
    user_interests = request.json.get('interests', '')
    categories = request.json.get('categories', [])
    
    if not user_interests:
        return jsonify({"error": "No interests provided."}), 400
    
    if not categories:
        return jsonify({"error": "No categories selected."}), 400
    
    # Get recommendations based on interests
    recommendations = get_recommendations_by_interests(
        user_interests=user_interests,
        categories=categories,
        max_results=10
    )
    
    return jsonify({"recommendations": recommendations})

# Run the app
if __name__ == '__main__':
    # Load data when starting the app
    if load_data():
        print("Data loaded successfully. Starting server...")
        app.run(debug=True)
    else:
        print("Failed to load required data. Please ensure data files are available.")