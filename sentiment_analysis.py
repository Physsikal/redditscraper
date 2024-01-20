# TODO:
# 1. CREATE SENTIMENT ANALYSIS TOOL []

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def analyze_sentiment(text):
    # Initialize the VADER sentiment analyzer
    analyzer = SentimentIntensityAnalyzer()

    # Analyze the sentiment of the input text
    sentiment_scores = analyzer.polarity_scores(text)

    # Determine the sentiment category based on the compound score
    compound_score = sentiment_scores['compound']

    if compound_score >= 0.05:
        sentiment = 'Positive'
    elif compound_score <= -0.05:
        sentiment = 'Negative'
    else:
        sentiment = 'Neutral'

    return {
        'sentiment': sentiment,
        'positive_score': sentiment_scores['pos'],
        'negative_score': sentiment_scores['neg'],
        'neutral_score': sentiment_scores['neu'],
        'compound_score': sentiment_scores['compound']
    }