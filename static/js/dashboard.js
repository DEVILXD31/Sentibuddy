// Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize variables
    let sentimentChart = null;
    let aspectsChart = null;
    let productComparisonChart = null;
    
    // Form submission handlers
    const uploadForm = document.getElementById('upload-form');
    const urlForm = document.getElementById('url-form');
    const uploadStatus = document.getElementById('upload-status');
    const resultsContainer = document.getElementById('results-container');
    
    // CSV Upload form handler
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Show loading status
        uploadStatus.classList.remove('d-none');
        
        // Get the file
        const fileInput = document.getElementById('csv-file');
        const file = fileInput.files[0];
        
        if (!file) {
            alert('Please select a CSV file');
            uploadStatus.classList.add('d-none');
            return;
        }
        
        // Create form data
        const formData = new FormData();
        formData.append('file', file);
        formData.append('model', document.getElementById('csv-model-selection').value);
        
        // Send the file to the server
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Hide loading status
            uploadStatus.classList.add('d-none');
            
            // Show results container
            resultsContainer.classList.remove('d-none');
            
            // Update the dashboard with the data
            updateDashboard(data);
        })
        .catch(error => {
            console.error('Error:', error);
            uploadStatus.classList.add('d-none');
            alert('Error processing the file. Please try again.');
        });
    });
    
    // URL form handler
    urlForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Show loading status
        uploadStatus.classList.remove('d-none');
        
        // Get the URL and max comments
        const productUrl = document.getElementById('product-url').value;
        const maxComments = document.getElementById('max-comments').value;
        
        if (!productUrl) {
            alert('Please enter a valid product URL');
            uploadStatus.classList.add('d-none');
            return;
        }
        
        // Create request data
        const requestData = {
            url: productUrl,
            max_comments: parseInt(maxComments),
            model: document.getElementById('model-selection').value
        };
        
        // Send the URL to the server
        fetch('/analyze-url', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Error processing the URL');
                });
            }
            return response.json();
        })
        .then(data => {
            // Hide loading status
            uploadStatus.classList.add('d-none');
            
            // Show results container
            resultsContainer.classList.remove('d-none');
            
            // Update the dashboard with the data
            updateDashboard(data);
        })
        .catch(error => {
            console.error('Error:', error);
            uploadStatus.classList.add('d-none');
            alert(error.message || 'Error processing the URL. Please try again.');
        });
    });
    
    // Function to update the dashboard with data
    function updateDashboard(data) {
        // Update sentiment distribution chart
        updateSentimentChart(data.sentiment_distribution);
        
        // Update sentiment counts
        document.getElementById('positive-count').textContent = data.sentiment_distribution.positive;
        document.getElementById('neutral-count').textContent = data.sentiment_distribution.neutral;
        document.getElementById('negative-count').textContent = data.sentiment_distribution.negative;
        
        // Update average sentiment score
        updateSentimentScore(data.average_sentiment);
        
        // Update aspects chart
        updateAspectsChart(data.top_aspects);
        
        // Update product comparison chart
        updateProductComparisonChart(data.product_sentiment);
        
        // Update recommendations
        updateRecommendations(data.recommendations);
    }
    
    // Function to update the sentiment distribution chart
    function updateSentimentChart(distribution) {
        const ctx = document.getElementById('sentiment-chart').getContext('2d');
        
        // Destroy existing chart if it exists
        if (sentimentChart) {
            sentimentChart.destroy();
        }
        
        // Create new chart
        sentimentChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Positive', 'Neutral', 'Negative'],
                datasets: [{
                    data: [distribution.positive, distribution.neutral, distribution.negative],
                    backgroundColor: ['#28a745', '#ffc107', '#dc3545'],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    title: {
                        display: true,
                        text: 'Sentiment Distribution'
                    }
                }
            }
        });
    }
    
    // Function to update the sentiment score progress bar
    function updateSentimentScore(score) {
        // Convert score from -1 to 1 range to 0 to 100 for progress bar
        const progressValue = ((score + 1) / 2) * 100;
        const progressBar = document.getElementById('avg-sentiment-progress');
        
        progressBar.style.width = `${progressValue}%`;
        progressBar.setAttribute('aria-valuenow', progressValue);
        
        // Set color based on sentiment
        if (score > 0.3) {
            progressBar.className = 'progress-bar progress-bar-positive';
        } else if (score < -0.3) {
            progressBar.className = 'progress-bar progress-bar-negative';
        } else {
            progressBar.className = 'progress-bar progress-bar-neutral';
        }
    }
    
    // Function to update the aspects chart
    function updateAspectsChart(aspects) {
        const ctx = document.getElementById('aspects-chart').getContext('2d');
        
        // Destroy existing chart if it exists
        if (aspectsChart) {
            aspectsChart.destroy();
        }
        
        // Extract labels and data
        const labels = aspects.map(item => item.aspect);
        const data = aspects.map(item => item.count);
        
        // Create new chart
        aspectsChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Mention Count',
                    data: data,
                    backgroundColor: 'rgba(54, 162, 235, 0.7)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    // Function to update the product comparison chart
    function updateProductComparisonChart(productData) {
        const ctx = document.getElementById('product-comparison-chart').getContext('2d');
        
        // Destroy existing chart if it exists
        if (productComparisonChart) {
            productComparisonChart.destroy();
        }
        
        // Extract product names and sentiment scores
        const products = Object.keys(productData);
        const positiveScores = products.map(product => productData[product].positive);
        const neutralScores = products.map(product => productData[product].neutral);
        const negativeScores = products.map(product => productData[product].negative);
        
        // Create new chart
        productComparisonChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: products,
                datasets: [
                    {
                        label: 'Positive',
                        data: positiveScores,
                        backgroundColor: 'rgba(40, 167, 69, 0.7)',
                        borderColor: 'rgba(40, 167, 69, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Neutral',
                        data: neutralScores,
                        backgroundColor: 'rgba(255, 193, 7, 0.7)',
                        borderColor: 'rgba(255, 193, 7, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Negative',
                        data: negativeScores,
                        backgroundColor: 'rgba(220, 53, 69, 0.7)',
                        borderColor: 'rgba(220, 53, 69, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    x: {
                        stacked: false
                    },
                    y: {
                        stacked: false,
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    // Function to update recommendations
    function updateRecommendations(recommendations) {
        const container = document.getElementById('recommendations-container');
        container.innerHTML = '';
        
        if (recommendations.length === 0) {
            container.innerHTML = '<div class="alert alert-info">No recommendations available.</div>';
            return;
        }
        
        // Create recommendation cards
        recommendations.forEach(rec => {
            const card = document.createElement('div');
            card.className = 'recommendation-card';
            
            const title = document.createElement('h5');
            title.textContent = rec.product;
            
            const issue = document.createElement('div');
            issue.className = 'issue';
            issue.innerHTML = '<strong>Issue:</strong> ' + rec.issue;
            
            const suggestion = document.createElement('div');
            suggestion.className = 'suggestion';
            suggestion.innerHTML = '<strong>Suggestion:</strong> ' + rec.suggestion;
            
            card.appendChild(title);
            card.appendChild(issue);
            card.appendChild(suggestion);
            
            container.appendChild(card);
        });
    }
    
    // Handle navigation clicks to scroll to sections
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId !== '#') {
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    window.scrollTo({
                        top: targetElement.offsetTop - 70,
                        behavior: 'smooth'
                    });
                }
            }
        });
    });
});