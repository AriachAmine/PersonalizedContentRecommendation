# Personalized Content Recommendation Agent

A content-based recommendation system that suggests real articles to users based on their interests and preferences.

## Description

This project demonstrates how to build a personalized content recommendation system using content-based filtering techniques. The system analyzes user interests and finds relevant articles from real news sources using APIs, with a fallback to the local dataset when needed.

The project includes real-time article fetching, text analysis, and a RESTful API endpoint to serve recommendations based on user input.

## Features

- **Real-World Article Recommendations**: Connect to news APIs to fetch current articles
- **User Interest Processing**: Generate recommendations based on user-provided interests
- **Category Filtering**: Filter recommendations by content categories
- **Content-Based Filtering**: Recommends articles based on content similarity using TF-IDF
- **API Integration**: Connect to NewsAPI, Guardian API, and more
- **Web Interface**: User-friendly interface to enter interests and view recommendations
- **Fallback Mechanisms**: Use local dataset when API limits are reached or unavailable
- **Detailed Recommendations**: Returns article metadata, snippets, and links to full content

## Technology Stack

- **Python 3.8+**: Core programming language
- **pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **scikit-learn**: Machine learning algorithms (TF-IDF, cosine similarity)
- **Flask**: Web API framework
- **Requests**: HTTP library for API calls
- **HTML/CSS/JavaScript**: Frontend web interface

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

4. Set up API keys for news sources:
   - Get API keys from:
     - [NewsAPI](https://newsapi.org/)
     - [Guardian API](https://open-platform.theguardian.com/)
     - [New York Times API](https://developer.nytimes.com/)
   - Create a `.env` file in the project root:
     ```
     # .env file
     NEWS_API_KEY=your_newsapi_key_here
     GUARDIAN_API_KEY=your_guardian_api_key_here
     NY_TIMES_API_KEY=your_nytimes_api_key_here
     ```
   - Alternatively, you can rename the provided `.env.example` file:
     ```bash
     # On Windows
     copy .env.example .env
     
     # On Linux/Mac
     cp .env.example .env
     ```
   - Then edit the `.env` file and replace "your_api_key_here" with your actual API keys

## Running the Application

Start the recommendation system:

```bash
python app.py
```

The server will run on http://127.0.0.1:5000/ by default.

## Using the Web Interface

The application includes a user-friendly web interface:

1. Open your browser and navigate to http://127.0.0.1:5000/
2. Enter your interests in the input field (e.g., "climate change", "artificial intelligence")
3. Select categories you're interested in
4. Click "Get Recommendations" or press Enter
5. View the personalized recommendations displayed in an easy-to-read card format

The interface shows:
- Article title and category
- Keywords related to the article
- A snippet or preview of the article content
- Relevance score showing how closely the recommendation matches your interests
- Link to read the full article

## API Usage Example

### Request recommendations based on interests

Using curl:
```bash
curl -X POST http://127.0.0.1:5000/recommend-by-interests \
     -H "Content-Type: application/json" \
     -d '{"interests": "climate change renewable energy", "categories": ["Technology", "Science"]}'
```

Or using Python's requests library:

```python
import requests
import json

data = {
    "interests": "climate change renewable energy",
    "categories": ["Technology", "Science"]
}

response = requests.post(
    'http://127.0.0.1:5000/recommend-by-interests',
    headers={'Content-Type': 'application/json'},
    data=json.dumps(data)
)

recommendations = json.loads(response.text)
print(json.dumps(recommendations, indent=2))
```

### Sample Output

```json
{
  "recommendations": [
    {
      "article_id": 1,
      "title": "New Solar Panel Technology Breaks Efficiency Records",
      "category": "Technology",
      "keywords": "solar,energy,efficiency,renewable,technology",
      "url": "https://example.com/article/solar-panel-technology",
      "snippet": "Researchers have developed a new type of solar panel that converts 35% of sunlight into electricity, shattering previous records.",
      "published_date": "2023-06-15T14:30:00Z",
      "similarity_score": 0.85
    },
    {
      "article_id": 2,
      "title": "Climate Scientists Warn of Accelerating Polar Ice Melt",
      "category": "Science",
      "keywords": "climate,change,polar,ice,scientists",
      "url": "https://example.com/article/polar-ice-melt",
      "snippet": "New research indicates that polar ice caps are melting faster than previous models predicted, raising concerns about sea level rise.",
      "published_date": "2023-06-10T09:15:00Z",
      "similarity_score": 0.78
    }
  ]
}
```

## Offline Mode

If no API keys are provided or API rate limits are reached, the system will automatically fall back to using the local dataset (if available). You can generate a synthetic local dataset using:

```bash
python generate_data.py
python train_model.py
```

This creates a dataset to use when API services are unavailable.