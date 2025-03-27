document.addEventListener('DOMContentLoaded', function () {
    // Get DOM elements
    const userInterestsInput = document.getElementById('user-interests');
    const categoryCheckboxes = document.querySelectorAll('input[name="category"]');
    const getRecommendationsButton = document.getElementById('get-recommendations');
    const loadingElement = document.getElementById('loading');
    const errorElement = document.getElementById('error-message');
    const recommendationsElement = document.getElementById('recommendations');
    const noRecommendationsElement = document.getElementById('no-recommendations');
    const recommendationsList = document.getElementById('recommendations-list');

    // Add event listener to button
    getRecommendationsButton.addEventListener('click', getRecommendations);

    // Also allow pressing Enter in the input field
    userInterestsInput.addEventListener('keyup', function (event) {
        if (event.key === 'Enter') {
            getRecommendations();
        }
    });

    // Function to get recommendations from API
    function getRecommendations() {
        const userInterests = userInterestsInput.value.trim();

        // Get selected categories
        const selectedCategories = Array.from(categoryCheckboxes)
            .filter(checkbox => checkbox.checked)
            .map(checkbox => checkbox.value);

        // Validate input
        if (!userInterests) {
            showError("Please enter some interests or topics");
            return;
        }

        if (selectedCategories.length === 0) {
            showError("Please select at least one category");
            return;
        }

        // Reset UI state
        hideAllElements();
        showElement(loadingElement);

        // Prepare data for POST request
        const requestData = {
            interests: userInterests,
            categories: selectedCategories
        };

        // Make API request
        fetch('/recommend-by-interests', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        })
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
                <p class="article-keywords">Keywords: ${article.keywords}</p>
                <p class="article-content">${article.snippet || 'No preview available'}</p>
                <p class="article-similarity">Relevance: ${similarityPercentage}%</p>
                ${article.url ? `<a href="${article.url}" target="_blank" class="article-link">Read full article</a>` : ''}
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
