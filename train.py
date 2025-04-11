import nltk
import numpy as np
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer

# Download NLTK data
nltk.download('punkt')

# Initialize stemmer
stemmer = PorterStemmer()

# Tokenize a sentence
def tokenize(sentence):
    return nltk.word_tokenize(sentence)

# Stem a word
def stem(word):
    return stemmer.stem(word.lower())

# Preprocess data and create a corpus
def preprocess_data(intents):
    all_words = []
    tags = []
    xy = []
    corpus = []  # For TF-IDF

    for intent in intents['intents']:
        tag = intent['tag']
        tags.append(tag)
        for pattern in intent['patterns']:
            # Tokenize each pattern
            w = tokenize(pattern)
            all_words.extend(w)
            xy.append((w, tag))
            corpus.append(' '.join(w))  # Add pattern to corpus

    # Stem and remove duplicates
    all_words = [stem(w) for w in all_words if w not in ['?', '!']]
    all_words = sorted(set(all_words))
    tags = sorted(set(tags))

    return all_words, tags, xy, corpus

# Initialize TF-IDF Vectorizer
vectorizer = TfidfVectorizer()

# Compute TF-IDF matrix for the corpus
def compute_tfidf(corpus):
    tfidf_matrix = vectorizer.fit_transform(corpus)
    return tfidf_matrix