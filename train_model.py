import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib
import os

def main():
    """
    Train a content-based filtering model using TF-IDF on article keywords.
    """
    print("Loading article data...")
    # Load the articles data from CSV
    articles_df = pd.read_csv('articles.csv')
    
    print(f"Loaded {len(articles_df)} articles.")
    
    print("Converting keywords to TF-IDF features...")
    # Initialize the TF-IDF vectorizer with English stop words
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    
    # Fit and transform the keywords column to create the TF-IDF matrix
    # Using the keywords column which contains comma-separated keywords
    tfidf_matrix = tfidf_vectorizer.fit_transform(articles_df['keywords'])
    
    print(f"Created TF-IDF matrix with shape: {tfidf_matrix.shape}")
    
    print("Saving the vectorizer and TF-IDF matrix...")
    # Save the fitted vectorizer
    joblib.dump(tfidf_vectorizer, 'tfidf_vectorizer.joblib')
    
    # Save the TF-IDF matrix (this will automatically save as sparse matrix)
    joblib.dump(tfidf_matrix, 'tfidf_matrix.joblib')
    
    print("Model training and saving complete!")
    print(f"Files saved: tfidf_vectorizer.joblib, tfidf_matrix.joblib")

if __name__ == "__main__":
    main()
