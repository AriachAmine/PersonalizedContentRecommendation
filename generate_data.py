import pandas as pd
import random
from faker import Faker
from datetime import datetime, timedelta
import os
import time
import google.generativeai as genai
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Faker for generating fallback data if API fails
fake = Faker()

# Set random seed for reproducibility
random.seed(42)
fake.seed_instance(42)

# Define categories
categories = ['Technology', 'Business', 'Science', 'Lifestyle', 'Sports']

# Initialize Gemini API
def init_gemini_model():
    """Initialize and return a Gemini API model."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("WARNING: GEMINI_API_KEY not found in .env file.")
        print("Using fallback Faker data instead of Gemini API.")
        return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        return model
    except Exception as e:
        print(f"Error initializing Gemini model: {e}")
        return None

# Global model to reuse for multiple calls
gemini_model = init_gemini_model()

def generate_content_with_gemini(prompt, retry_count=3):
    """
    Generate content using the Gemini API with retry mechanism.
    
    Args:
        prompt: Text prompt for Gemini
        model: Model name (not used, kept for backward compatibility)
        retry_count: Number of retries if API call fails
        
    Returns:
        Generated text or None if all retries fail
    """
    if not gemini_model:
        return None
    
    for attempt in range(retry_count):
        try:
            response = gemini_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=300,
                ),
            )
            
            return response.text
        except Exception as e:
            error_str = str(e)
            # Check specifically for quota exceeded error
            if "429" in error_str and "exceeded your current quota" in error_str:
                print("API QUOTA EXCEEDED: You have reached your Gemini API quota limit.")
                # Immediately fall back to synthetic data without retrying
                return None
            else:
                print(f"Attempt {attempt+1}/{retry_count} failed: {e}")
                if attempt < retry_count - 1:
                    # Exponential backoff
                    sleep_time = 2 ** attempt
                    print(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    print("All retries failed. Using fallback data generation.")
                    return None

def generate_article_data_with_gemini(category):
    """
    Generate an article title and keywords using Gemini.
    
    Args:
        category: The article category
        
    Returns:
        tuple: (title, keywords)
    """
    prompt = f"""Create an article title and 3-5 relevant keywords for a {category} article.
    The title should be catchy and realistic, capturing attention while accurately representing the content.
    The keywords should be relevant to the topic and help with content categorization.
    
    Return your answer in JSON format:
    {{
        "title": "Your generated title here",
        "keywords": ["keyword1", "keyword2", "keyword3"]
    }}
    
    Note: Ensure keywords are lowercase and don't include quotes in your response JSON.
    """
    
    response_text = generate_content_with_gemini(prompt)
    
    if response_text:
        try:
            # Extract the JSON part from the response
            # Sometimes LLMs include explanatory text before/after the JSON
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
                
                title = data.get("title", "")
                keywords = data.get("keywords", [])
                
                # Ensure keywords are strings and join them
                keywords_str = ",".join([str(k).lower() for k in keywords])
                
                return title, keywords_str
        except Exception as e:
            print(f"Error parsing Gemini response: {e}")
            print(f"Raw response: {response_text}")
    
    # Fallback to Faker if Gemini fails or response parsing fails
    return generate_title_fallback(category), generate_keywords_fallback()

def generate_keywords_fallback():
    """Generate a string of 3-5 fake lowercase keywords separated by commas (fallback)."""
    num_keywords = random.randint(3, 5)
    keywords = [fake.word().lower() for _ in range(num_keywords)]
    return ','.join(keywords)

def generate_title_fallback(category):
    """Generate a realistic fake article title (fallback)."""
    title_patterns = [
        fake.catch_phrase,
        lambda: f"The Future of {fake.word().capitalize()} in {category}",
        lambda: f"{random.randint(5, 20)} Ways to {fake.word('verb')} Your {fake.word('noun').capitalize()}",
        lambda: f"Why {fake.word('noun').capitalize()} Matters in Today's {fake.word('adjective').capitalize()} World",
        lambda: f"How {fake.name()} Revolutionized {fake.word('noun').capitalize()}"
    ]
    return random.choice(title_patterns)()

def generate_articles(num_articles=200):
    """
    Generate a DataFrame of articles using Gemini for more realistic data.
    
    Args:
        num_articles: Number of articles to generate
        
    Returns:
        pandas DataFrame with article data
    """
    articles = []
    
    print(f"Generating {num_articles} articles...")
    using_gemini = gemini_model is not None
    
    if using_gemini:
        print("Using Gemini API for content generation")
    else:
        print("Using fallback Faker data (Gemini API not available)")
    
    # Track if we encounter a quota error during generation
    quota_exceeded = False
    
    for article_id in range(1, num_articles + 1):
        # Show progress for every 10 articles
        if article_id % 10 == 0:
            print(f"Generated {article_id}/{num_articles} articles")
        
        category = random.choice(categories)
        
        if using_gemini and not quota_exceeded:
            title, keywords = generate_article_data_with_gemini(category)
            # If both are None or empty, the API might have failed due to quota
            if not title and not keywords:
                quota_exceeded = True
                print("Switching to fallback data generation for remaining articles")
                title = generate_title_fallback(category)
                keywords = generate_keywords_fallback()
        else:
            title = generate_title_fallback(category)
            keywords = generate_keywords_fallback()
        
        article = {
            'article_id': article_id,
            'title': title,
            'category': category,
            'keywords': keywords
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
    print("Starting data generation process...")
    
    # Check if API key is set
    if not os.getenv('GEMINI_API_KEY'):
        print("\nNOTE: To use Gemini API, create a .env file with your API key:")
        print("  1. Create a file named '.env' in the project root directory")
        print("  2. Add the following line to the file: GEMINI_API_KEY=your_api_key_here\n")
    
    print("Generating article data...")
    articles_df = generate_articles(200)
    
    # Save articles to CSV
    articles_df.to_csv('articles.csv', index=False)
    print(f"Generated articles.csv with {len(articles_df)} articles")
    
    print("Generating user interaction data...")
    interactions_df = generate_interactions(articles_df, 50, 1000)
    
    # Sort interactions by timestamp for more realistic data
    interactions_df = interactions_df.sort_values('timestamp')
    
    # Save interactions to CSV
    interactions_df.to_csv('user_interactions.csv', index=False)
    print(f"Generated user_interactions.csv with {len(interactions_df)} interactions")
    print("Data generation complete!")

if __name__ == "__main__":
    main()
