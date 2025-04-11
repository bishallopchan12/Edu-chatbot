import nltk
import numpy as np
import json
import pickle
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier

# Download NLTK data if not already downloaded
nltk.download('punkt')
nltk.download('stopwords')

# Initialize stemmer
stemmer = PorterStemmer()
stop_words = set(stopwords.words("english"))

# Tokenize a sentence
def tokenize(sentence):
    return nltk.word_tokenize(sentence)

# Stem a word and remove stopwords
def stem(word):
    word = word.lower()
    return stemmer.stem(word) if word not in stop_words else ""

# Preprocess data and create a corpus
def preprocess_data(intents):
    all_words = []
    tags = []
    xy = []
    corpus = []

    for intent in intents['intents']:
        tag = intent['tag']
        tags.append(tag)
        for pattern in intent['patterns']:
            words = tokenize(pattern)
            words = [stem(w) for w in words if w not in ["?", "!", ".", ",", "'s", "'m"]]
            all_words.extend(words)
            xy.append((pattern, tag))  # Store pattern as a string
            corpus.append(" ".join(words))

    all_words = sorted(set(all_words) - {""})
    tags = sorted(set(tags))

    return all_words, tags, xy, corpus

# Load intents
with open("intents.json", "r", encoding="utf-8") as file:
    intents = json.load(file)

# Preprocess data
all_words, tags, xy, corpus = preprocess_data(intents)

# TF-IDF Vectorizer
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(corpus)

# Encode tags
tag_to_code = {tag: i for i, tag in enumerate(tags)}
code_to_tag = {i: tag for tag, i in tag_to_code.items()}
y = np.array([tag_to_code[tag] for _, tag in xy])

# Train model
model = MLPClassifier(hidden_layer_sizes=(64, 64), max_iter=1500, random_state=42, alpha=0.001)
model.fit(X, y)

# Save trained model
with open("chatbot_model.pkl", "wb") as f:
    pickle.dump(model, f)

with open("vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

with open("tag_mappings.pkl", "wb") as f:
    pickle.dump({"tag_to_code": tag_to_code, "code_to_tag": code_to_tag}, f)

print(f"✅ Training complete! Model accuracy: {model.score(X, y) * 100:.2f}%")
print("📂 Model, vectorizer, and tag mappings saved.")
