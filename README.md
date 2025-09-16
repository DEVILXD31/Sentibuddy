# Sentiment Analysis Dashboard

A comprehensive sentiment analysis tool that processes customer feedback from CSV files, analyzes sentiment using the Gemini API, and visualizes insights through an interactive dashboard.

## Features

- **CSV Data Processing**: Upload and process customer feedback data from CSV files
- **Sentiment Analysis**: Analyze customer comments using Google's Gemini API
- **Interactive Dashboard**: Visualize sentiment distribution, key aspects, and product comparisons
- **Product Recommendations**: Generate AI-powered product improvement recommendations
- **Responsive Design**: Access the dashboard on any device

## Project Structure

```
├── app.py                  # Main Flask application
├── requirements.txt        # Project dependencies
├── .env.example           # Environment variables template
├── README.md              # Project documentation
├── src/                   # Source code
│   ├── data/              # Data loading and preprocessing
│   ├── models/            # Sentiment analysis models
│   ├── utils/             # Utility functions and insights generation
│   └── dashboard/         # Dashboard components
├── static/                # Static assets
│   ├── css/               # Stylesheets
│   └── js/                # JavaScript files
└── templates/             # HTML templates
```

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file based on `.env.example` and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

## Usage

1. Start the application:
   ```
   python app.py
   ```
2. Open your browser and navigate to `http://localhost:5000`
3. Upload a CSV file containing customer comments
4. View the sentiment analysis results and recommendations

## CSV Format

The CSV file should contain at least one column with customer comments. The application will attempt to identify the comment column automatically, but for best results, include a column named 'comment', 'feedback', or 'review'.

Optional columns:
- `product`: Product name or identifier
- `customer_id`: Customer identifier
- `date`: Date of the comment

## Technologies Used

- **Backend**: Python, Flask
- **Data Processing**: Pandas, NumPy
- **Sentiment Analysis**: Google Gemini API
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Visualization**: Chart.js

## License

MIT