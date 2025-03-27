import pandas as pd
import random
from faker import Faker
from datetime import datetime, timedelta

# Initialize Faker for generating fake data
fake = Faker()

# Set random seed for reproducibility
random.seed(42)
fake.seed_instance(42)

# Define categories
categories = ['Technology', 'Business', 'Science', 'Lifestyle', 'Sports']

def generate_keywords():
    """Generate a string of 3-5 fake lowercase keywords separated by commas."""
    num_keywords = random.randint(3, 5)
    keywords = [fake.word().lower() for _ in range(num_keywords)]
    return ','.join(keywords)

def generate_title():
    """Generate a realistic fake article title."""
    title_patterns = [
        fake.catch_phrase,
        lambda: f"The Future of {fake.word('noun').capitalize()} in {random.choice(categories)}",
        lambda: f"{random.randint(5, 20)} Ways to {fake.word('verb')} Your {fake.word('noun').capitalize()}",
        lambda: f"Why {fake.word('noun').capitalize()} Matters in Today's {fake.word('adjective').capitalize()} World",
        lambda: f"How {fake.name()} Revolutionized {fake.word('noun').capitalize()}"
    ]
    return random.choice(title_patterns)()

def generate_articles(num_articles=200):
    """
    Generate a DataFrame of fake articles.
    
    Args:
        num_articles: Number of articles to generate
        
    Returns:
        pandas DataFrame with article data
    """
    articles = []
    
    for article_id in range(1, num_articles + 1):
        article = {
            'article_id': article_id,
            'title': generate_title(),
            'category': random.choice(categories),
            'keywords': generate_keywords()
        }
        articles.append(article)
    
    return pd.DataFrame(articles)

def generate_interactions(articles_df, num_users=50, num_interactions=1000):
    """
    Generate a DataFrame of fake user interactions with articles.
    
    Args:
        articles_df: DataFrame of articles
        num_users: Number of unique users
        num_interactions: Total number of interactions to generate
        
    Returns:
        pandas DataFrame with interaction data
    """
    interactions = []
    
    # Assign a preferred category to each user (cycling through categories)
    user_preferences = {}
    for user_id in range(1, num_users + 1):
        preferred_category = categories[(user_id - 1) % len(categories)]
        user_preferences[user_id] = preferred_category
    
    # Generate timestamps within the last year
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    # Group articles by category for faster lookup
    articles_by_category = {category: [] for category in categories}
    for _, article in articles_df.iterrows():
        articles_by_category[article['category']].append(article['article_id'])
    
    for _ in range(num_interactions):
        user_id = random.randint(1, num_users)
        preferred_category = user_preferences[user_id]
        
        # 70% chance to interact with preferred category, 30% chance for random
        if random.random() < 0.7:
            # Choose article from preferred category
            article_id = random.choice(articles_by_category[preferred_category])
        else:
            # Choose random article
            article_id = random.choice(articles_df['article_id'].tolist())
        
        # Generate random timestamp within the last year
        timestamp = fake.date_time_between(
            start_date=start_date,
            end_date=end_date
        )
        
        # 80% chance for 'view', 20% chance for 'click'
        interaction_type = 'view' if random.random() < 0.8 else 'click'
        
        interaction = {
            'user_id': user_id,
            'article_id': article_id,
            'timestamp': timestamp,
            'interaction_type': interaction_type
        }
        interactions.append(interaction)
    
    return pd.DataFrame(interactions)

def main():
    """Generate and save the article and user interaction datasets."""
    print("Generating fake article data...")
    articles_df = generate_articles(200)
    
    # Save articles to CSV
    articles_df.to_csv('articles.csv', index=False)
    print(f"Generated articles.csv with {len(articles_df)} articles")
    
    print("Generating fake user interaction data...")
    interactions_df = generate_interactions(articles_df, 50, 1000)
    
    # Sort interactions by timestamp for more realistic data
    interactions_df = interactions_df.sort_values('timestamp')
    
    # Save interactions to CSV
    interactions_df.to_csv('user_interactions.csv', index=False)
    print(f"Generated user_interactions.csv with {len(interactions_df)} interactions")
    print("Data generation complete!")

if __name__ == "__main__":
    main()
