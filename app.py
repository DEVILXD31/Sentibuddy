import os
import pandas as pd
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from src.data.data_loader import load_csv_data, preprocess_data
from src.data.web_scraper import scrape_product_comments
from src.models.sentiment_analyzer import analyze_sentiment
from src.utils.insights_generator import generate_insights, generate_recommendations

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')

@app.route('/')
def index():
    """Render the main dashboard page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle CSV file upload and process it"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.endswith('.csv'):
        # Save the file temporarily
        file_path = os.path.join('uploads', file.filename)
        os.makedirs('uploads', exist_ok=True)
        file.save(file_path)
        
        # Get selected model
        model_type = request.form.get('model', 'gemini')
        
        # Process the file
        try:
            df = load_csv_data(file_path)
            processed_df = preprocess_data(df)
            
            # Analyze sentiment with selected model
            sentiment_results = analyze_sentiment(processed_df, model_type=model_type)
            
            # Generate insights and recommendations
            insights = generate_insights(sentiment_results)
            recommendations = generate_recommendations(sentiment_results)
            
            # Format the response to match the dashboard's expected structure
            response = {
                'success': True,
                'model_used': model_type,
                'sentiment_distribution': {
                    'positive': insights.get('sentiment_counts', {}).get('positive', 0),
                    'neutral': insights.get('sentiment_counts', {}).get('neutral', 0),
                    'negative': insights.get('sentiment_counts', {}).get('negative', 0)
                },
                'average_sentiment': insights.get('average_sentiment', 0),
                'top_aspects': insights.get('top_aspects', []),
                'product_sentiment': insights.get('product_sentiment', {}),
                'recommendations': recommendations
            }
            
            return jsonify(response)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'File must be a CSV'}), 400

@app.route('/api/sentiment-summary')
def get_sentiment_summary():
    """Return sentiment analysis summary for the dashboard"""
    # This would typically retrieve from a database or cached results
    # For now, we'll return a placeholder with the expected format
    return jsonify({
        'sentiment_distribution': {
            'positive': 0,
            'neutral': 0,
            'negative': 0
        },
        'average_sentiment': 0,
        'top_aspects': [],
        'product_sentiment': {},
        'recommendations': []
    })

@app.route('/analyze-url', methods=['POST'])
def analyze_url():
    """Handle product URL submission and scrape comments for analysis"""
    data = request.json
    if not data or 'url' not in data:
        return jsonify({'error': 'No URL provided'}), 400
    
    url = data['url']
    max_comments = data.get('max_comments', 100)  # Default to 100 comments
    model_type = data.get('model', 'gemini')  # Get selected model
    
    try:
        # Scrape comments from the provided URL
        df = scrape_product_comments(url, max_comments)
        
        if df.empty:
            return jsonify({'error': 'No comments found on the provided URL'}), 404
        
        # Preprocess the scraped data
        processed_df = preprocess_data(df)
        
        # Analyze sentiment with selected model
        sentiment_results = analyze_sentiment(processed_df, model_type=model_type)
        
        # Generate insights and recommendations
        insights = generate_insights(sentiment_results)
        recommendations = generate_recommendations(sentiment_results)
        
        # Format the response
        response = {
            'success': True,
            'source': 'web_scraping',
            'url': url,
            'model_used': model_type,
            'comments_count': len(sentiment_results),
            'sentiment_distribution': {
                'positive': insights.get('sentiment_counts', {}).get('positive', 0),
                'neutral': insights.get('sentiment_counts', {}).get('neutral', 0),
                'negative': insights.get('sentiment_counts', {}).get('negative', 0)
            },
            'average_sentiment': insights.get('average_sentiment', 0),
            'top_aspects': insights.get('top_aspects', []),
            'product_sentiment': insights.get('product_sentiment', {}),
            'recommendations': recommendations
        }
        
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure upload directory exists
    os.makedirs('uploads', exist_ok=True)
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)