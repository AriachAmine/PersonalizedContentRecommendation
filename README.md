# Personalized Content Recommendation Agent

A content-based recommendation system that suggests articles to users based on their previous interactions and content similarity.

## Description

This project demonstrates how to build a personalized content recommendation system using content-based filtering techniques. The system analyzes article keywords using TF-IDF (Term Frequency-Inverse Document Frequency) vectorization to create a profile for each user based on their reading history. It then recommends new articles that are semantically similar to the ones they've previously interacted with.

The project includes data generation (with optional LLM integration), model training, and a RESTful API endpoint to serve recommendations in real-time.

## Features

- **Synthetic Data Generation**: Creates realistic article and user interaction datasets
  - **Gemini API Integration**: Generate more realistic article titles and keywords using Google's Gemini LLM
- **Content-Based Filtering**: Recommends articles based on content similarity using TF-IDF
- **User Profiling**: Builds user profiles based on past article interactions
- **REST API Endpoint**: Serves personalized recommendations via a simple Flask API
- **Web Interface**: User-friendly interface to interact with the recommendation system
- **Fallback Recommendations**: Provides popular article recommendations for new users
- **Detailed Recommendations**: Returns article metadata along with similarity scores

## Technology Stack

- **Python 3.8+**: Core programming language
- **pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **scikit-learn**: Machine learning algorithms (TF-IDF, cosine similarity)
- **joblib**: Model persistence
- **Faker**: Generating synthetic data
- **Flask**: Web API framework
- **HTML/CSS/JavaScript**: Frontend web interface
- **Google Generative AI**: Integration with Gemini LLM for realistic content generation

## Setup & Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/AriachAmine/PersonalizedContentRecommendation.git
   cd PersonalizedContentRecommendation
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. (Optional) Set up Gemini API for enhanced data generation:
   - Get an API key from [Google AI Studio](https://ai.google.dev/)
   - Create a `.env` file in the project root:
     ```
     # .env file
     GEMINI_API_KEY=your_api_key_here
     ```
   - Alternatively, you can rename the provided `.env.example` file:
     ```bash
     # On Windows
     copy .env.example .env
     
     # On Linux/Mac
     cp .env.example .env
     ```
   - Then edit the `.env` file and replace "your_api_key_here" with your actual API key

## Data Generation

Generate synthetic article and user interaction data:

```bash
python generate_data.py
```

This will create:
- `articles.csv`: 200 articles with titles, categories, and keywords
- `user_interactions.csv`: 1000 user interactions (views/clicks) with timestamps

If you've set up the Gemini API key, the script will use the LLM to generate more realistic article titles and keywords. Otherwise, it will fall back to using Faker to generate synthetic data.

## Model Training

Train the TF-IDF vectorizer and create the content feature matrix:

```bash
python train_model.py
```

This will create:
- `tfidf_vectorizer.joblib`: The fitted TF-IDF vectorizer
- `tfidf_matrix.joblib`: The TF-IDF feature matrix for all articles

## Running the Agent

Start the recommendation API server:

```bash
python app.py
```

The server will run on http://127.0.0.1:5000/ by default.

## Using the Web Interface

The application now includes a user-friendly web interface to interact with the recommendation system:

1. Open your browser and navigate to http://127.0.0.1:5000/
2. Enter a user ID in the input field (1-50 for the sample dataset)
3. Click "Get Recommendations" or press Enter
4. View the personalized recommendations displayed in an easy-to-read card format

The interface shows:
- Article title and category
- Article ID for reference
- Similarity score as a percentage showing how closely the recommendation matches the user's interests

For new users with no previous interactions, the system automatically provides popular articles as recommendations.

## API Usage Example

### Request recommendations for a specific user

```bash
curl http://127.0.0.1:5000/recommend/15
```

Or using Python's requests library:

```python
import requests
import json

response = requests.get('http://127.0.0.1:5000/recommend/15')
recommendations = json.loads(response.text)
print(json.dumps(recommendations, indent=2))
```

### Sample Output

```json
{
  "user_id": 15,
  "recommendations": [
    {
      "article_id": 142,
      "title": "Why Solid Matters in Today's Line World",
      "category": "Technology",
      "similarity_score": 0.5872
    },
    {
      "article_id": 87,
      "title": "The Future of Series in Business",
      "category": "Business",
      "similarity_score": 0.5103
    },
    {
      "article_id": 29,
      "title": "How Isabella Sanchez Revolutionized Profit",
      "category": "Science",
      "similarity_score": 0.4921
    },
    {
      "article_id": 195,
      "title": "7 Ways to Wait Your Law",
      "category": "Lifestyle",
      "similarity_score": 0.4751
    },
    {
      "article_id": 112,
      "title": "15 Ways to Run Your Card",
      "category": "Sports",
      "similarity_score": 0.4603
    }
  ]
}
```

For a new user with no previous interactions, the system will recommend popular articles:

```json
{
  "user_id": 999,
  "recommendations": [45, 23, 67, 12, 89],
  "message": "New user. Recommending popular articles."
}
```