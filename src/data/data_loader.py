import pandas as pd
import re
import os

def load_csv_data(file_path):
    """
    Load data from a CSV file
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        pandas.DataFrame: Loaded data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file is empty or has invalid format
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        df = pd.read_csv(file_path)
    except pd.errors.EmptyDataError:
        raise ValueError("The CSV file is empty")
    except pd.errors.ParserError:
        raise ValueError("Error parsing the CSV file. Please check the format.")
    
    # Check if the dataframe has any data
    if df.empty:
        raise ValueError("The CSV file contains no data")
    
    # Check if the dataframe has a comments/feedback column
    comment_columns = [col for col in df.columns if any(keyword in col.lower() for 
                                                     keyword in ['comment', 'feedback', 'review', 'text', 'response'])]
    
    if not comment_columns:
        raise ValueError("The CSV file must contain a column with comments/feedback/reviews")
    
    return df

def preprocess_data(df):
    """
    Preprocess the data for sentiment analysis
    
    Args:
        df (pandas.DataFrame): Input dataframe with raw data
        
    Returns:
        pandas.DataFrame: Preprocessed dataframe
    """
    # Make a copy to avoid modifying the original dataframe
    processed_df = df.copy()
    
    # Identify the comment column
    comment_columns = [col for col in processed_df.columns if any(keyword in col.lower() for 
                                                              keyword in ['comment', 'feedback', 'review', 'text', 'response'])]
    
    # If multiple comment columns exist, use the first one
    comment_column = comment_columns[0] if comment_columns else None
    
    if comment_column:
        # Rename the column to a standard name
        processed_df.rename(columns={comment_column: 'comment'}, inplace=True)
        
        # Clean the comments
        processed_df['cleaned_comment'] = processed_df['comment'].apply(clean_text)
        
        # Remove rows with empty comments after cleaning
        processed_df = processed_df[processed_df['cleaned_comment'].str.strip().astype(bool)]
    
    return processed_df

def clean_text(text):
    """
    Clean text data by removing special characters, extra spaces, etc.
    
    Args:
        text (str): Input text
        
    Returns:
        str: Cleaned text
    """
    if not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    # Remove HTML tags
    text = re.sub(r'<.*?>', '', text)
    
    # Remove special characters and numbers (keep letters, spaces, and basic punctuation)
    text = re.sub(r'[^\w\s.,!?]', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_features(df):
    """
    Extract additional features from the data that might be useful for analysis
    
    Args:
        df (pandas.DataFrame): Input dataframe
        
    Returns:
        pandas.DataFrame: Dataframe with additional features
    """
    # Make a copy to avoid modifying the original dataframe
    feature_df = df.copy()
    
    # Calculate comment length
    if 'cleaned_comment' in feature_df.columns:
        feature_df['comment_length'] = feature_df['cleaned_comment'].apply(len)
    
    # Extract other potential features like dates, product categories, etc.
    # This would depend on the specific columns available in the dataset
    
    return feature_df