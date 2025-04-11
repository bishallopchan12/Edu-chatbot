from flask import Flask, render_template, request, jsonify
import random
import json
import numpy as np
from train import preprocess_data, compute_tfidf, tokenize, stem, vectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Load intents
with open('intents.json', 'r') as f:
    intents = json.load(f)

# Preprocess data
all_words, tags, xy, corpus = preprocess_data(intents)

# Compute TF-IDF matrix for the corpus
tfidf_matrix = compute_tfidf(corpus)

# Simple prediction function using TF-IDF
def predict_intent(user_input):
    # Preprocess user input
    tokenized = tokenize(user_input)
    stemmed = [stem(word) for word in tokenized]
    processed_input = ' '.join(stemmed)

    # Transform user input into TF-IDF vector
    user_input_vec = vectorizer.transform([processed_input])

    # Compute cosine similarity between user input and all patterns
    similarities = cosine_similarity(user_input_vec, tfidf_matrix)

    # Find the most similar pattern
    most_similar_idx = np.argmax(similarities)
    most_similar_tag = xy[most_similar_idx][1]  # Get the tag of the most similar pattern

    return most_similar_tag

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json['message']
    intent = predict_intent(user_input)
    for intent_data in intents['intents']:
        if intent_data['tag'] == intent:
            response = random.choice(intent_data['responses'])
            return jsonify({'response': response})
    return jsonify({'response': "I'm not sure. Please contact support."})

if __name__ == '__main__':
    app.run(debug=True)

    context = {}

def predict_intent(user_input, context):
    # Preprocess user input
    tokenized = tokenize(user_input)
    stemmed = [stem(word) for word in tokenized]
    processed_input = ' '.join(stemmed)

    # Transform user input into TF-IDF vector
    user_input_vec = vectorizer.transform([processed_input])

    # Compute cosine similarity between user input and all patterns
    similarities = cosine_similarity(user_input_vec, tfidf_matrix)

    # Find the most similar pattern
    most_similar_idx = np.argmax(similarities)
    most_similar_tag = xy[most_similar_idx][1]  # Get the tag of the most similar pattern

    # Update context if necessary
    if most_similar_tag == "python_info":
        context["topic"] = "Python"
    elif most_similar_tag == "java_info":
        context["topic"] = "Java"

    return most_similar_tag, context

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json['message']
    intent, context = predict_intent(user_input, context)
    for intent_data in intents['intents']:
        if intent_data['tag'] == intent:
            response = random.choice(intent_data['responses'])
            return jsonify({'response': response, 'context': context})
    return jsonify({'response': "I'm not sure. Please contact support.", 'context': context})
from textblob import TextBlob

def analyze_sentiment(user_input):
    analysis = TextBlob(user_input)
    if analysis.sentiment.polarity > 0:
        return "positive"
    elif analysis.sentiment.polarity < 0:
        return "negative"
    else:
        return "neutral"

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json['message']
    sentiment = analyze_sentiment(user_input)
    intent, context = predict_intent(user_input, context)
    for intent_data in intents['intents']:
        if intent_data['tag'] == intent:
            response = random.choice(intent_data['responses'])
            if sentiment == "negative":
                response = "I'm sorry to hear that. " + response
            return jsonify({'response': response, 'context': context})
    return jsonify({'response': "I'm not sure. Please contact support.", 'context': context})