import os
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
import time
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline
import numpy as np
from sklearn.preprocessing import MinMaxScaler

# Load environment variables
load_dotenv()

# Configure the Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set. Please set it in the .env file.")

genai.configure(api_key=GEMINI_API_KEY)

# Set up the Gemini model
gemini_model = genai.GenerativeModel('gemini-pro')

# Set up the BERT model
bert_model_name = "distilbert-base-uncased-finetuned-sst-2-english"
bert_tokenizer = None
bert_model = None
bert_pipeline = None

def load_bert_model():
    """Load the BERT model for sentiment analysis"""
    global bert_tokenizer, bert_model, bert_pipeline
    
    if bert_pipeline is None:
        print("Loading BERT model for sentiment analysis...")
        bert_tokenizer = AutoTokenizer.from_pretrained(bert_model_name)
        bert_model = AutoModelForSequenceClassification.from_pretrained(bert_model_name)
        bert_pipeline = pipeline("sentiment-analysis", model=bert_model, tokenizer=bert_tokenizer)
        print("BERT model loaded successfully")
    
    return bert_pipeline

def analyze_sentiment(df, comment_column='cleaned_comment', batch_size=10, rate_limit_delay=1, model_type='gemini'):
    """
    Analyze sentiment of comments using selected model
    
    Args:
        df (pandas.DataFrame): Dataframe with comments to analyze
        comment_column (str): Name of the column containing comments
        batch_size (int): Number of comments to process in each batch
        rate_limit_delay (float): Delay between API calls to avoid rate limiting
        model_type (str): Type of model to use ('gemini' or 'bert')
        
    Returns:
        pandas.DataFrame: Original dataframe with sentiment analysis results added
    """
    if comment_column not in df.columns:
        raise ValueError(f"Column '{comment_column}' not found in the dataframe")
    
    # Create a copy of the dataframe to avoid modifying the original
    result_df = df.copy()
    
    # Initialize sentiment columns
    result_df['sentiment'] = None
    result_df['sentiment_score'] = None
    result_df['key_aspects'] = None
    result_df['model_used'] = model_type
    
    # Load BERT model if needed
    if model_type == 'bert':
        bert_pipeline = load_bert_model()
    
    # Process in batches to handle rate limits
    for i in range(0, len(result_df), batch_size):
        batch = result_df.iloc[i:i+batch_size]
        
        for idx, row in batch.iterrows():
            comment = row[comment_column]
            
            # Skip empty comments
            if not isinstance(comment, str) or not comment.strip():
                continue
            
            try:
                # Get sentiment analysis from selected model
                if model_type == 'bert':
                    sentiment_data = get_sentiment_from_bert(comment)
                else:
                    sentiment_data = get_sentiment_from_gemini(comment)
                
                # Update the dataframe with the results
                result_df.at[idx, 'sentiment'] = sentiment_data.get('sentiment', 'neutral')
                result_df.at[idx, 'sentiment_score'] = sentiment_data.get('score', 0.0)
                result_df.at[idx, 'key_aspects'] = sentiment_data.get('key_aspects', [])
                
                # Add a delay to avoid rate limiting (only for Gemini)
                if model_type == 'gemini':
                    time.sleep(rate_limit_delay)
                
            except Exception as e:
                print(f"Error analyzing comment at index {idx}: {str(e)}")
                # Set default values in case of error
                result_df.at[idx, 'sentiment'] = 'neutral'
                result_df.at[idx, 'sentiment_score'] = 0.0
                result_df.at[idx, 'key_aspects'] = []
    
    return result_df

def get_sentiment_from_bert(comment):
    """
    Get sentiment analysis from BERT model
    
    Args:
        comment (str): Comment text to analyze
        
    Returns:
        dict: Dictionary containing sentiment analysis results
    """
    # Ensure BERT model is loaded
    bert_pipeline = load_bert_model()
    
    try:
        # Get sentiment prediction from BERT
        result = bert_pipeline(comment)
        
        # Extract sentiment and score
        label = result[0]['label'].lower()
        score = result[0]['score']
        
        # Convert BERT's POSITIVE/NEGATIVE to our format
        sentiment = "positive" if label == "positive" else "negative"
        
        # Convert score to range from -1.0 to 1.0
        # BERT scores are 0 to 1, where higher means more confidence in the label
        normalized_score = score if sentiment == "positive" else -score
        
        # Since BERT doesn't extract key aspects, we'll return an empty list
        return {
            "sentiment": sentiment,
            "score": normalized_score,
            "key_aspects": []
        }
    except Exception as e:
        print(f"Error in BERT sentiment analysis: {str(e)}")
        return {
            "sentiment": "neutral",
            "score": 0.0,
            "key_aspects": []
        }

def get_sentiment_from_gemini(comment):
    """
    Get sentiment analysis from Gemini API
    
    Args:
        comment (str): Comment text to analyze
        
    Returns:
        dict: Dictionary containing sentiment analysis results
    """
    # Directly determine sentiment based on comment content for more reliable results
    prompt = f"""
    Analyze the sentiment of the following customer comment. 
    
    IMPORTANT: You MUST classify the sentiment as either "positive" or "negative". DO NOT use "neutral" classification.
    If you're unsure, lean towards the sentiment that seems more likely based on the tone and content.
    
    Provide a structured response with:
    1. Overall sentiment (ONLY "positive" or "negative")
    2. Sentiment score (from -1.0 to 1.0, where -1.0 is very negative and 1.0 is very positive)
    3. Key aspects mentioned (product features, service quality, price, etc.)
    4. Any specific issues or praise mentioned
    
    Format your response as a JSON object with the following structure:
    {{
        "sentiment": "positive/negative",
        "score": 0.0,
        "key_aspects": ["aspect1", "aspect2"],
        "issues": ["issue1", "issue2"],
        "praise": ["praise1", "praise2"]
    }}
    
    Customer comment: "{comment}"
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
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                sentiment_data = json.loads(json_str)
                
                # Force sentiment to be either positive or negative based on score if neutral is returned
                if sentiment_data.get("sentiment") == "neutral":
                    score = sentiment_data.get("score", 0.0)
                    sentiment_data["sentiment"] = "positive" if score >= 0 else "negative"
                    
                # Ensure score is consistent with sentiment
                if sentiment_data.get("sentiment") == "positive" and sentiment_data.get("score", 0) <= 0:
                    sentiment_data["score"] = 0.5  # Default positive score
                elif sentiment_data.get("sentiment") == "negative" and sentiment_data.get("score", 0) >= 0:
                    sentiment_data["score"] = -0.5  # Default negative score
                    
                return sentiment_data
                
            except json.JSONDecodeError:
                print(f"Failed to parse JSON: {json_str}")
                # Fallback to manual sentiment detection
                return determine_sentiment_fallback(comment)
        else:
            # If no JSON found, use fallback method
            return determine_sentiment_fallback(comment)
        
    except Exception as e:
        print(f"Error getting sentiment from Gemini: {str(e)}")
        # Use fallback method in case of error
        return determine_sentiment_fallback(comment)
        
def determine_sentiment_fallback(comment):
    """
    Fallback method to determine sentiment when API fails
    
    Args:
        comment (str): Comment text to analyze
        
    Returns:
        dict: Dictionary containing sentiment analysis results
    """
    # Simple keyword-based sentiment analysis as fallback
    positive_keywords = ["great", "excellent", "good", "best", "love", "amazing", "perfect", "fantastic", 
                         "awesome", "wonderful", "happy", "satisfied", "impressive", "exceptional"]
    negative_keywords = ["bad", "terrible", "worst", "hate", "poor", "disappointing", "disappointed", 
                         "awful", "horrible", "useless", "waste", "slow", "problem", "issue", "fail", 
                         "breaks", "broken", "crash", "error", "overheats", "freezes"]
    
    comment_lower = comment.lower()
    
    # Count occurrences of positive and negative keywords
    positive_count = sum(1 for word in positive_keywords if word in comment_lower)
    negative_count = sum(1 for word in negative_keywords if word in comment_lower)
    
    # Determine sentiment based on keyword counts
    if positive_count > negative_count:
        sentiment = "positive"
        score = min(1.0, 0.5 + (positive_count - negative_count) * 0.1)
        aspects = [word for word in positive_keywords if word in comment_lower]
        return {
            "sentiment": sentiment,
            "score": score,
            "key_aspects": aspects[:3] if aspects else ["general experience"],
            "issues": [],
            "praise": aspects[:2] if aspects else ["overall satisfaction"]
        }
    else:
        sentiment = "negative"
        score = max(-1.0, -0.5 - (negative_count - positive_count) * 0.1)
        aspects = [word for word in negative_keywords if word in comment_lower]
        return {
            "sentiment": sentiment,
            "score": score,
            "key_aspects": aspects[:3] if aspects else ["general experience"],
            "issues": aspects[:2] if aspects else ["customer dissatisfaction"],
            "praise": []
        }

def batch_analyze_comments(comments_list):
    """
    Analyze a batch of comments at once
    
    Args:
        comments_list (list): List of comment strings to analyze
        
    Returns:
        list: List of sentiment analysis results
    """
    results = []
    
    for comment in comments_list:
        try:
            sentiment_data = get_sentiment_from_gemini(comment)
            results.append(sentiment_data)
            # Add a delay to avoid rate limiting
            time.sleep(1)
        except Exception as e:
            print(f"Error analyzing comment: {str(e)}")
            # Add default values in case of error
            results.append({
                "sentiment": "neutral",
                "score": 0.0,
                "key_aspects": [],
                "issues": [],
                "praise": []
            })
    
    return results