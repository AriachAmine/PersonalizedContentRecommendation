document.addEventListener('DOMContentLoaded', function () {
    // Get DOM elements
    const userIdInput = document.getElementById('user-id');
    const getRecommendationsButton = document.getElementById('get-recommendations');
    const loadingElement = document.getElementById('loading');
    const errorElement = document.getElementById('error-message');
    const recommendationsElement = document.getElementById('recommendations');
    const noRecommendationsElement = document.getElementById('no-recommendations');
    const resultUserIdElement = document.getElementById('result-user-id');
    const recommendationsList = document.getElementById('recommendations-list');

    // Add event listener to button
    getRecommendationsButton.addEventListener('click', getRecommendations);

    // Also allow pressing Enter in the input field
    userIdInput.addEventListener('keyup', function (event) {
        if (event.key === 'Enter') {
            getRecommendations();
        }
    });

    // Function to get recommendations from API
    function getRecommendations() {
        const userId = userIdInput.value.trim();

        // Validate input
        if (!userId || isNaN(userId) || userId < 1) {
            showError("Please enter a valid user ID");
            return;
        }

        // Reset UI state
        hideAllElements();
        showElement(loadingElement);

        // Make API request
        fetch(`/recommend/${userId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Process and display results
                displayRecommendations(data);
            })
            .catch(error => {
                console.error('Error fetching recommendations:', error);
                showError("Failed to load recommendations. Please try again.");
            });
    }

    // Function to display recommendations
    function displayRecommendations(data) {
        hideAllElements();

        if (data.error) {
            showError(data.error);
            return;
        }

        resultUserIdElement.textContent = data.user_id;

        // Check if this is a new user with just a list of article IDs
        if (data.message && data.message.includes('New user')) {
            // Show message for new users
            recommendationsList.innerHTML = `
                <div class="article-card">
                    <p>${data.message}</p>
                    <p>Recommended popular articles: ${data.recommendations.join(', ')}</p>
                </div>
            `;
            showElement(recommendationsElement);
            return;
        }

        // Handle regular recommendations
        if (!data.recommendations || data.recommendations.length === 0) {
            showElement(noRecommendationsElement);
            return;
        }

        // Clear previous recommendations
        recommendationsList.innerHTML = '';

        // Add each recommendation to the list
        data.recommendations.forEach(article => {
            const similarityPercentage = (article.similarity_score * 100).toFixed(1);

            const articleCard = document.createElement('div');
            articleCard.className = 'article-card';
            articleCard.innerHTML = `
                <div class="article-category">${article.category}</div>
                <h3 class="article-title">${article.title}</h3>
                <p class="article-id">Article ID: ${article.article_id}</p>
                <p class="article-similarity">Similarity: ${similarityPercentage}%</p>
            `;

            recommendationsList.appendChild(articleCard);
        });

        showElement(recommendationsElement);
    }

    // Helper functions for UI state management
    function hideAllElements() {
        loadingElement.classList.add('hidden');
        errorElement.classList.add('hidden');
        recommendationsElement.classList.add('hidden');
        noRecommendationsElement.classList.add('hidden');
    }

    function showElement(element) {
        element.classList.remove('hidden');
    }

    function showError(message) {
        hideAllElements();
        errorElement.querySelector('p').textContent = message;
        showElement(errorElement);
    }
});
