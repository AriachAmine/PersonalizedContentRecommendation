from flask import Flask, jsonify
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics.pairwise import cosine_similarity
import os

app = Flask(__name__)

# Global variables to store loaded data
tfidf_vectorizer = None
tfidf_matrix = None
articles_df = None
interactions_df = None

def load_data():
    """Load all required data files for the recommendation system"""
    global tfidf_vectorizer, tfidf_matrix, articles_df, interactions_df
    
    try:
        # Load TF-IDF vectorizer and matrix from joblib files
        print("Loading TF-IDF vectorizer and matrix...")
        tfidf_vectorizer = joblib.load('tfidf_vectorizer.joblib')
        tfidf_matrix = joblib.load('tfidf_matrix.joblib')
        
        # Load article data
        print("Loading article data...")
        articles_df = pd.read_csv('articles.csv')
        
        # Load user interaction data
        print("Loading user interaction data...")
        interactions_df = pd.read_csv('user_interactions.csv')
        
        print("Data loaded successfully!")
        print(f"Articles: {len(articles_df)}")
        print(f"Interactions: {len(interactions_df)}")
        print(f"TF-IDF Matrix shape: {tfidf_matrix.shape}")
        return True
    
    except Exception as e:
        print(f"Error loading data: {e}")
        return False

@app.route('/recommend/<int:user_id>')
def recommend(user_id):
    """
    Generate content-based recommendations for a user based on their past interactions.
    
    Args:
        user_id: ID of the user to generate recommendations for
        
    Returns:
        JSON response with recommended articles
    """
    # Check if data is loaded
    if tfidf_matrix is None or articles_df is None or interactions_df is None:
        return jsonify({
            'error': 'Data not loaded. Please check server logs.'
        }), 500
    
    # Number of recommendations to return
    N = 5
    
    try:
        # Find all articles the user has interacted with
        user_interactions = interactions_df[interactions_df['user_id'] == user_id]
        
        # Handle case where user has no interactions
        if len(user_interactions) == 0:
            # Return popular articles as fallback
            # For simplicity, we'll define "popular" as articles with most interactions
            article_counts = interactions_df['article_id'].value_counts().head(N)
            popular_articles = articles_df[articles_df['article_id'].isin(article_counts.index)]
            
            return jsonify({
                'user_id': user_id,
                'recommendations': popular_articles['article_id'].tolist(),
                'message': 'New user. Recommending popular articles.'
            })
        
        # Get the articles this user has interacted with
        user_articles = user_interactions['article_id'].unique()
        
        # Get the TF-IDF vectors for these articles
        # Convert from article_id to 0-based index in the TF-IDF matrix
        article_indices = [article_id - 1 for article_id in user_articles 
                          if article_id <= tfidf_matrix.shape[0]]
        
        if not article_indices:
            return jsonify({
                'user_id': user_id,
                'recommendations': [],
                'message': 'No valid article interactions found.'
            })
        
        # Calculate user profile vector by averaging the TF-IDF vectors
        user_profile = tfidf_matrix[article_indices].mean(axis=0)
        
        # Convert to numpy array properly, avoiding np.matrix which is deprecated
        if hasattr(user_profile, 'toarray'):
            # For sparse matrices
            user_profile = np.asarray(user_profile.toarray()).reshape(1, -1)
        else:
            # For dense arrays
            user_profile = np.asarray(user_profile).reshape(1, -1)
        
        # Compute cosine similarity between user profile and all articles
        # Ensure tfidf_matrix is properly converted to array if needed
        if hasattr(tfidf_matrix, 'toarray'):
            # No need to convert the whole matrix, cosine_similarity handles sparse matrices
            cosine_similarities = cosine_similarity(user_profile, tfidf_matrix).flatten()
        else:
            cosine_similarities = cosine_similarity(user_profile, np.asarray(tfidf_matrix)).flatten()
        
        # Get sorted indices of articles by similarity (highest to lowest)
        similar_indices = cosine_similarities.argsort()[::-1]
        
        # Filter out articles the user has already interacted with
        filtered_indices = [idx for idx in similar_indices 
                           if idx + 1 not in user_articles]
        
        # Get top N article IDs (convert from 0-based index to article_id)
        top_recommendations = [idx + 1 for idx in filtered_indices[:N]]
        
        # Get article details
        recommended_articles = []
        for article_id in top_recommendations:
            article = articles_df[articles_df['article_id'] == article_id].iloc[0]
            recommended_articles.append({
                'article_id': int(article['article_id']),
                'title': article['title'],
                'category': article['category'],
                'similarity_score': float(cosine_similarities[article_id - 1])
            })
        
        return jsonify({
            'user_id': user_id,
            'recommendations': recommended_articles
        })
        
    except Exception as e:
        import traceback
        print(f"Error in recommendation: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'message': 'Error generating recommendations.'
        }), 500

# Load data when app starts
if load_data():
    print("Recommendation system initialized successfully.")
else:
    print("WARNING: Failed to load data. App will respond with errors.")

if __name__ == '__main__':
    app.run(debug=True)
