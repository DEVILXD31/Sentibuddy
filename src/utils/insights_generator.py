import pandas as pd
import numpy as np
from collections import Counter
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')

def generate_insights(sentiment_df):
    """
    Generate insights from sentiment analysis results
    
    Args:
        sentiment_df (pandas.DataFrame): Dataframe with sentiment analysis results
        
    Returns:
        dict: Dictionary containing insights formatted for dashboard visualization
    """
    # Check if required columns exist
    required_columns = ['sentiment', 'sentiment_score', 'key_aspects']
    for col in required_columns:
        if col not in sentiment_df.columns:
            raise ValueError(f"Required column '{col}' not found in the dataframe")
    
    # Calculate overall sentiment distribution
    sentiment_counts = sentiment_df['sentiment'].value_counts().to_dict()
    total_comments = len(sentiment_df)
    
    # Format sentiment counts for dashboard
    sentiment_counts_formatted = {
        'positive': sentiment_counts.get('positive', 0),
        'neutral': sentiment_counts.get('neutral', 0),
        'negative': sentiment_counts.get('negative', 0)
    }
    
    # Calculate average sentiment score
    average_sentiment = sentiment_df['sentiment_score'].mean()
    
    # Extract common aspects mentioned
    all_aspects = []
    for aspects in sentiment_df['key_aspects']:
        if isinstance(aspects, list):
            all_aspects.extend(aspects)
        elif isinstance(aspects, str):
            # Handle case where aspects might be stored as a string
            try:
                import ast
                parsed_aspects = ast.literal_eval(aspects)
                if isinstance(parsed_aspects, list):
                    all_aspects.extend(parsed_aspects)
            except:
                # If parsing fails, just add the string as is
                all_aspects.append(aspects)
    
    # Count aspect frequencies and format for dashboard
    aspect_counter = Counter(all_aspects)
    top_aspects = [{'aspect': aspect, 'count': count} for aspect, count in aspect_counter.most_common(10)]
    
    # Group by product if product column exists
    product_sentiment = {}
    if 'product' in sentiment_df.columns:
        for product in sentiment_df['product'].unique():
            product_df = sentiment_df[sentiment_df['product'] == product]
            product_sentiment_counts = product_df['sentiment'].value_counts().to_dict()
            
            product_sentiment[product] = {
                'positive': product_sentiment_counts.get('positive', 0),
                'neutral': product_sentiment_counts.get('neutral', 0),
                'negative': product_sentiment_counts.get('negative', 0)
            }
    
    # Compile all insights in format expected by dashboard
    insights = {
        'sentiment_counts': sentiment_counts_formatted,
        'average_sentiment': average_sentiment,
        'top_aspects': top_aspects,
        'product_sentiment': product_sentiment,
        'total_comments': total_comments
    }
    
    return insights

def generate_recommendations(sentiment_df):
    """
    Generate product improvement recommendations based on sentiment analysis
    
    Args:
        sentiment_df (pandas.DataFrame): Dataframe with sentiment analysis results
        
    Returns:
        list: List of recommendation objects formatted for dashboard display
    """
    # Filter negative comments for improvement areas
    negative_df = sentiment_df[sentiment_df['sentiment'] == 'negative']
    
    # Extract issues from negative comments
    all_issues = []
    for _, row in negative_df.iterrows():
        if 'issues' in row and isinstance(row['issues'], list) and row['issues']:
            all_issues.extend(row['issues'])
        elif 'key_aspects' in row and isinstance(row['key_aspects'], list) and row['key_aspects']:
            all_issues.extend(row['key_aspects'])
    
    # Count issue frequencies
    issue_counter = Counter(all_issues)
    top_issues = dict(issue_counter.most_common(5))
    
    # Group issues by product if product column exists
    product_recommendations = []
    if 'product' in sentiment_df.columns:
        for product in sentiment_df['product'].unique():
            product_negative_df = negative_df[negative_df['product'] == product]
            
            if len(product_negative_df) == 0:
                continue
                
            product_all_issues = []
            for _, row in product_negative_df.iterrows():
                if 'issues' in row and isinstance(row['issues'], list) and row['issues']:
                    product_all_issues.extend(row['issues'])
                elif 'key_aspects' in row and isinstance(row['key_aspects'], list) and row['key_aspects']:
                    product_all_issues.extend(row['key_aspects'])
            
            product_issue_counter = Counter(product_all_issues)
            top_product_issues = product_issue_counter.most_common(3)
            
            for issue, count in top_product_issues:
                product_recommendations.append({
                    "product": product,
                    "issue": f"{issue} (mentioned {count} times)",
                    "suggestion": f"Consider addressing {issue} issues in {product}"
                })
    
    # Use Gemini to generate specific recommendations if API key is available
    ai_recommendations = []
    if GEMINI_API_KEY and negative_df.shape[0] > 0:
        try:
            # Prepare data for Gemini
            negative_comments = negative_df['cleaned_comment'].tolist()[:10]  # Limit to 10 comments to avoid token limits
            negative_aspects = list(top_issues.keys())
            
            # Generate recommendations using Gemini
            ai_recommendations = get_recommendations_from_gemini(negative_comments, negative_aspects)
            
            # Format AI recommendations to match dashboard expectations
            formatted_ai_recommendations = []
            for rec in ai_recommendations:
                if isinstance(rec, dict) and 'title' in rec and 'issue' in rec and 'suggestion' in rec:
                    formatted_ai_recommendations.append({
                        "product": rec.get('title', 'General'),
                        "issue": rec.get('issue', ''),
                        "suggestion": rec.get('suggestion', '')
                    })
            ai_recommendations = formatted_ai_recommendations
        except Exception as e:
            print(f"Error generating AI recommendations: {str(e)}")
    
    # Combine product-specific and AI recommendations
    all_recommendations = product_recommendations + ai_recommendations
    
    # If no recommendations were generated, provide a default one
    if not all_recommendations:
        all_recommendations = [{
            "product": "General",
            "issue": "Not enough negative feedback to generate specific recommendations",
            "suggestion": "Continue collecting customer feedback to identify improvement areas"
        }]
    
    return all_recommendations

def get_recommendations_from_gemini(negative_comments, negative_aspects):
    """
    Get product improvement recommendations from Gemini API
    
    Args:
        negative_comments (list): List of negative comments
        negative_aspects (list): List of negative aspects mentioned
        
    Returns:
        list: List of recommendations
    """
    if not GEMINI_API_KEY:
        return ["API key not available for generating AI recommendations"]
    
    # Prepare the prompt
    comments_text = "\n".join([f"- {comment}" for comment in negative_comments])
    aspects_text = ", ".join(negative_aspects)
    
    prompt = f"""
    Based on the following negative customer comments and aspects mentioned, provide 3-5 specific product improvement recommendations:
    
    Negative Comments:
    {comments_text}
    
    Negative Aspects Mentioned: {aspects_text}
    
    For each recommendation, please provide:
    1. A clear, actionable title
    2. A brief explanation of the issue
    3. A specific suggestion for improvement
    
    Format your response as a JSON array of recommendation objects, each with 'title', 'issue', and 'suggestion' fields.
    """
    
    try:
        # Generate content using Gemini
        response = model.generate_content(prompt)
        
        # Extract the JSON response
        response_text = response.text
        
        # Parse the JSON response
        import json
        import re
        
        # Extract JSON from the response (in case there's additional text)
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            recommendations = json.loads(json_str)
        else:
            # If no JSON found, create a default response
            recommendations = [
                {
                    "title": "Improve Product Quality",
                    "issue": "Multiple customers mentioned quality issues",
                    "suggestion": "Conduct a quality audit and address common failure points"
                }
            ]
        
        return recommendations
    
    except Exception as e:
        print(f"Error getting recommendations from Gemini: {str(e)}")
        # Return default values in case of error
        return [
            {
                "title": "Improve Product Based on Feedback",
                "issue": "Various issues mentioned in customer feedback",
                "suggestion": "Review all negative feedback and prioritize fixing the most common issues"
            }
        ]