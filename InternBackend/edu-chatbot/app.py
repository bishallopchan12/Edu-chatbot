from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import logging
import nltk
import pickle
import numpy as np
import mysql.connector.pooling
import sys
import time
import re
import random
import os
import socket
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/chat": {"origins": "http://localhost:*"}, r"/button": {"origins": "http://localhost:*"}})

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('app.log', encoding='utf-8'), logging.StreamHandler(sys.stdout)]
)

# Force unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

# Download NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    logging.info("NLTK data downloaded successfully.")
except Exception as e:
    logging.error(f"Error downloading NLTK data: {e}")
    sys.exit(1)

# Initialize stemmer and stopwords
stemmer = PorterStemmer()
stop_words = set(stopwords.words("english"))

# Predefined button intents
BUTTON_INTENTS = {
    "👋 Start Exploring": "greeting",
    "📚 Available Courses": "course_categories",
    "🏫 Colleges": "college_list",
    "🧪 QuizPro": "quiz_redirect",
    "📩 Contact Us": "contact_us",
    "📚 View More": "view_more_courses",
    "🏠 Back to Start": "greeting",
    "⬅️ Back": "back",
    "📚 Science and Technology": "category_science_tech",
    "🔬 Management and Business": "category_management",
    "💼 Humanities and Social Sciences": "category_humanities",
    "🏫 Education": "category_education",
    "⚖️ Law": "category_law",
    "🏥 Health Sciences": "category_health",
    "🌱 Agriculture and Forestry": "category_agri_forestry",
    "📺 Media and Communication": "category_media",
    "🖌️ Fine Arts and Design": "category_fine_arts",
    "🔧 Vocational and Technical": "category_vocational",
    "👨‍💼 Professional and Specialized": "category_professional",
    "💰 Fees": "course_fees",
    "⏳ Duration": "duration_info",
    "✅ Eligibility": "eligibility_info",
    "🌟 Careers": "career_options",
    "🎓 Scholarships": "scholarship_info",
    "📝 Apply": "application_process",
    "📖 Notes": "notes",
    "📋 Syllabus": "syllabus",
    "🏫 Universities": "universities",
    "✍️ Blogs": "blogs"
}

INITIAL_BUTTONS = [
    "📚 Available Courses", "🏫 Colleges", "🧪 QuizPro", "📩 Contact Us",
    "📖 Notes", "📋 Syllabus", "🏫 Universities", "✍️ Blogs"
]

# Common navigation buttons
BACK_BUTTONS = [
    "⬅️ Back", "🏠 Back to Start"
]

CATEGORY_COURSES = {
    "category_science_tech": ["BSc CSIT", "BSc Physics", "BSc Chemistry", "BSc Mathematics", "BSc Biology", "BSc Environmental Science", "BSc Statistics", "BSc Electronics", "BSc Electronics and Communication", "BSc Biotechnology", "BCA", "BIT", "BE Civil Engineering", "BE Computer Engineering", "BE Electronics and Communication Engineering", "BE Electrical Engineering", "BE Mechanical Engineering", "BE Chemical Engineering", "BE Aerospace Engineering", "BE Agricultural Engineering", "BTech Food Technology", "BE Architecture", "BEIT"],
    "category_management": ["BBA", "BBS", "BHM", "BTTM", "BPA"],
    "category_humanities": ["BA English", "BA Nepali", "BA Sociology", "BA Anthropology", "BA Political Science", "BA History", "BA Economics", "BA Psychology", "BA Geography", "BSW"],
    "category_education": ["BEd English", "BEd Nepali", "BEd Mathematics", "BEd Science", "BEd Social Studies", "BEd ICT"],
    "category_law": ["LLB", "BBA LLB", "BCom LLB", "BSc LLB"],
    "category_health": ["MBBS", "BDS", "BPharm", "BSc Nursing", "BPH", "BPT"],
    "category_agri_forestry": ["BSc Agriculture", "BSc Forestry"],
    "category_media": ["BJMC", "BA Media Studies"],
    "category_fine_arts": ["BFA", "BDes"],
    "category_vocational": ["BHM", "BTTM", "Diploma in Engineering", "TSLC Programs"],
    "category_professional": ["BArch", "Bachelor of Sports Science", "BAMS"]
}

COURSE_BUTTONS = [
    "💰 Fees", "⏳ Duration", "✅ Eligibility", "🌟 Careers", "🎓 Scholarships", "📝 Apply",
    "⬅️ Back", "🏠 Back to Start", "📩 Contact Us"
]

# Database configuration
DB_POOL_CONFIG = {
    'pool_name': 'edu_pool',
    'pool_size': 5,
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Replace with your actual MySQL password
    'database': 'education',
    'connect_timeout': 5
}

# Initialize database pool
db_pool = None
try:
    db_pool = mysql.connector.pooling.MySQLConnectionPool(**DB_POOL_CONFIG)
    logging.info("Database pool initialized successfully.")
except mysql.connector.Error as err:
    logging.warning(f"Failed to initialize database pool: {err}. Using fallback data.")
    db_pool = None

def get_db_connection():
    if db_pool:
        try:
            connection = db_pool.get_connection()
            logging.debug("Database connection retrieved from pool.")
            return connection
        except mysql.connector.Error as err:
            logging.error(f"Database connection error: {err}")
            return None
    logging.warning("No database pool available. Using fallback.")
    return None

# Load intents
def load_intents():
    try:
        with open('intents.json', 'r', encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Error loading intents: {e}")
        return {'intents': []}

intents = load_intents()

# NLTK preprocessing
def tokenize(sentence):
    return nltk.word_tokenize(sentence.lower()) if isinstance(sentence, str) else []

def stem(words):
    return [stemmer.stem(word) for word in words if word not in stop_words and isinstance(word, str)]

# Define a named function for the tokenizer to avoid pickling issues
def nltk_tokenizer(text):
    return stem(tokenize(text))

# Load or train model using NLTK and sklearn
def load_or_train_model():
    vectorizer_path = 'vectorizer.pkl'
    model_path = 'model.pkl'

    if os.path.exists(vectorizer_path) and os.path.exists(model_path):
        try:
            with open(vectorizer_path, 'rb') as f:
                vectorizer = pickle.load(f)
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            logging.info("Loaded existing TF-IDF vectorizer and model.")
            patterns = [pattern for intent in intents['intents'] for pattern in intent['patterns'] if isinstance(pattern, str)]
            if patterns:
                X_test = vectorizer.transform(patterns[:1])
                if X_test.shape[1] != model.n_features_in_:
                    logging.warning("Feature mismatch detected. Retraining model...")
                    raise ValueError("Feature mismatch")
            return vectorizer, model
        except (ValueError, AttributeError, pickle.UnpicklingError) as e:
            logging.error(f"Model loading failed or incompatible: {e}. Retraining model.")

    patterns, tags = [], []
    for intent in intents['intents']:
        for pattern in intent['patterns']:
            if isinstance(pattern, str):
                patterns.append(pattern)
                tags.append(intent['tag'])
    if not patterns:
        logging.warning("No patterns found in intents.json. NLP model not trained.")
        return None, None

    vectorizer = TfidfVectorizer(tokenizer=nltk_tokenizer, max_features=2000)
    X = vectorizer.fit_transform(patterns)
    y = tags
    model = MLPClassifier(hidden_layer_sizes=(150, 100), max_iter=3000, random_state=42)
    model.fit(X, y)
    with open(vectorizer_path, 'wb') as f:
        pickle.dump(vectorizer, f)
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logging.info("Trained and saved new TF-IDF vectorizer and MLP model.")
    return vectorizer, model

vectorizer, model = load_or_train_model()

def predict_intent(user_input):
    if user_input in BUTTON_INTENTS:
        return BUTTON_INTENTS[user_input]
    if not vectorizer or not model:
        logging.warning("NLP model not available. Returning fallback intent.")
        return "fallback"
    try:
        preprocessed_input = " ".join(stem(tokenize(user_input)))
        X = vectorizer.transform([preprocessed_input])
        predicted_tag = model.predict(X)[0]
        confidence = max(model.predict_proba(X)[0])
        logging.debug(f"Predicted intent: {predicted_tag} with confidence: {confidence}")
        return predicted_tag if confidence > 0.5 else "fallback"
    except Exception as e:
        logging.error(f"Error predicting intent: {e}")
        return "fallback"

def extract_course(user_input):
    connection = get_db_connection()
    if connection:
        cursor = None
        try:
            cursor = connection.cursor(dictionary=True, buffered=True)
            query = "SELECT name FROM courses WHERE LOWER(name) = LOWER(%s)"
            cursor.execute(query, (user_input,))
            result = cursor.fetchone()
            return result['name'] if result else None
        except mysql.connector.Error as err:
            logging.error(f"Database query error in extract_course: {err}")
            return None
        finally:
            if cursor:
                cursor.close()
            connection.close()
            logging.debug("Database connection closed in extract_course")
    logging.warning("No database connection for extract_course. Using fallback.")
    return None

course_cache = {}
def get_all_courses():
    if "all_courses" not in course_cache:
        connection = get_db_connection()
        if connection:
            cursor = None
            try:
                cursor = connection.cursor(dictionary=True, buffered=True)
                cursor.execute("SELECT name FROM courses ORDER BY name")
                courses = [row['name'] for row in cursor.fetchall()]
                course_cache["all_courses"] = courses
                logging.debug(f"Cached {len(courses)} courses from database.")
                return courses
            except mysql.connector.Error as err:
                logging.error(f"Database query error in get_all_courses: {err}")
                return []
            finally:
                if cursor:
                    cursor.close()
                connection.close()
                logging.debug("Database connection closed in get_all_courses")
        logging.warning("No database connection for get_all_courses. Using fallback.")
        course_cache["all_courses"] = sum(CATEGORY_COURSES.values(), [])
    return course_cache.get("all_courses", [])

def get_courses_by_category(category):
    cache_key = f"courses_{category.lower()}"
    if cache_key not in course_cache:
        connection = get_db_connection()
        if connection:
            cursor = None
            try:
                cursor = connection.cursor(dictionary=True, buffered=True)
                query = "SELECT name FROM courses WHERE LOWER(category) = LOWER(%s) ORDER BY name"
                cursor.execute(query, (category,))
                courses = [row['name'] for row in cursor.fetchall()]
                course_cache[cache_key] = courses
                logging.debug(f"Cached {len(courses)} courses for category '{category}'.")
                return courses
            except mysql.connector.Error as err:
                logging.error(f"Database query error in get_courses_by_category: {err}")
                return []
            finally:
                if cursor:
                    cursor.close()
                connection.close()
                logging.debug("Database connection closed in get_courses_by_category")
        logging.warning(f"No database connection for category '{category}'. Using fallback.")
        course_cache[cache_key] = CATEGORY_COURSES.get(f"category_{category.lower()}", [])
    return course_cache.get(cache_key, [])

def get_course_details(course_name, detail_type=None):
    connection = get_db_connection()
    if connection:
        cursor = None
        try:
            cursor = connection.cursor(dictionary=True, buffered=True)
            query = "SELECT * FROM courses WHERE name = %s"
            cursor.execute(query, (course_name,))
            result = cursor.fetchone()
            if result:
                if detail_type:
                    responses = {
                        "course_fees": f"💰 **Fees for {course_name}**: {result['fees']} (offered by {result['colleges']})",
                        "duration_info": f"⏳ **Duration**: {result['duration']} for {course_name}",
                        "eligibility_info": f"✅ **Eligibility**: {result['eligibility']} to enroll in {course_name}",
                        "career_options": f"🌟 **Careers**: {result['career_options']} after completing {course_name}",
                        "scholarship_info": f"🎓 **Scholarships**: {result.get('scholarships', 'Merit-based and need-based options available.')}",
                        "application_process": f"📝 **Apply**: {result['admission']} for {course_name}",
                        "syllabus_info": f"📋 **Syllabus for {course_name}**: {result['syllabus']}"
                    }
                    return responses.get(detail_type, "Details not available.")
                return (f"📚 **{course_name}**\n"
                        f"**Category**: {result['category']}\n"
                        f"**Description**: {result['description']}\n"
                        f"**Duration**: {result['duration']}\n"
                        f"**Fees**: {result['fees']}\n"
                        f"**Colleges**: {result['colleges']}\n"
                        f"**Eligibility**: {result['eligibility']}\n"
                        f"**Careers**: {result['career_options']}\n"
                        f"**Syllabus**: {result['syllabus']}")
            logging.warning(f"No details found for '{course_name}' in the database.")
            return f"No details found for {course_name}."
        except mysql.connector.Error as err:
            logging.error(f"Database query error in get_course_details: {err}")
            return f"Error fetching details for {course_name}."
        finally:
            if cursor:
                cursor.close()
            connection.close()
            logging.debug("Database connection closed in get_course_details")
    logging.warning(f"No database connection for get_course_details '{course_name}'. Using static data.")
    static_course_details = {
        "BSc CSIT": {"syllabus": "http://www.example.com/syllabus/bsc-csit"},
        "BBA": {"syllabus": "http://www.example.com/syllabus/bba"},
        "BBS": {"syllabus": "http://www.example.com/syllabus/bbs"},
        "BCA": {"syllabus": "http://www.example.com/syllabus/bca"},
        "BE Civil Engineering": {"syllabus": "http://www.example.com/syllabus/be-civil-engineering"},
        "MBBS": {"syllabus": "http://www.example.com/syllabus/mbbs"},
        "BA Sociology": {"syllabus": "http://www.example.com/syllabus/ba-sociology"},
        "BEd Mathematics": {"syllabus": "http://www.example.com/syllabus/bed-mathematics"},
        "LLB": {"syllabus": "http://www.example.com/syllabus/llb"},
        "BSc Agriculture": {"syllabus": "http://www.example.com/syllabus/bsc-agriculture"}
    }
    if detail_type == "syllabus_info" and course_name in static_course_details:
        return f"📋 **Syllabus for {course_name}**: {static_course_details[course_name]['syllabus']}"
    return "Course details unavailable without database connection."

def get_colleges():
    connection = get_db_connection()
    if connection:
        cursor = None
        try:
            cursor = connection.cursor(dictionary=True, buffered=True)
            cursor.execute("SELECT name, location, courses_offered FROM colleges ORDER BY name")
            colleges = [row for row in cursor.fetchall()]
            logging.debug(f"Fetched {len(colleges)} colleges from database.")
            return colleges
        except mysql.connector.Error as err:
            logging.error(f"Database query error in get_colleges: {err}")
            return []
        finally:
            if cursor:
                cursor.close()
            connection.close()
            logging.debug("Database connection closed in get_colleges")
    logging.warning("No database connection for get_colleges. Using fallback.")
    return [
        {"name": "Tribhuvan University", "location": "Kathmandu", "courses_offered": "BSc CSIT, BBA, MBBS"},
        {"name": "Kathmandu University", "location": "Dhulikhel", "courses_offered": "BE Civil Engineering, BBA, BSc Nursing"},
        {"name": "Purbanchal University", "location": "Biratnagar", "courses_offered": "BSc Agriculture, BHM, BEd"}
    ]

def get_blogs():
    connection = get_db_connection()
    if connection:
        cursor = None
        try:
            cursor = connection.cursor(dictionary=True, buffered=True)
            cursor.execute("SELECT title, excerpt, author, publish_date FROM blogs ORDER BY publish_date DESC")
            blogs = [row for row in cursor.fetchall()]
            logging.debug(f"Fetched {len(blogs)} blogs from database.")
            return blogs
        except mysql.connector.Error as err:
            logging.error(f"Database query error in get_blogs: {err}")
            return []
        finally:
            if cursor:
                cursor.close()
            connection.close()
            logging.debug("Database connection closed in get_blogs")
    logging.warning("No database connection for get_blogs. Using fallback.")
    return [
        {"title": "How to Choose the Right College", "excerpt": "Choosing the right college is crucial for your career...", "author": "John Doe", "publish_date": "2023-10-01"},
        {"title": "Top 10 Universities in Nepal", "excerpt": "Here are the top 10 universities in Nepal...", "author": "Jane Smith", "publish_date": "2023-09-15"}
    ]

def get_universities():
    connection = get_db_connection()
    if connection:
        cursor = None
        try:
            cursor = connection.cursor(dictionary=True, buffered=True)
            cursor.execute("SELECT name, location, established_year, description, website FROM universities ORDER BY name")
            universities = [row for row in cursor.fetchall()]
            logging.debug(f"Fetched {len(universities)} universities from database.")
            return universities
        except mysql.connector.Error as err:
            logging.error(f"Database query error in get_universities: {err}")
            return []
        finally:
            if cursor:
                cursor.close()
            connection.close()
            logging.debug("Database connection closed in get_universities")
    logging.warning("No database connection for get_universities. Using fallback.")
    return [
        {"name": "Tribhuvan University", "location": "Kathmandu", "established_year": 1959, "description": "The oldest university in Nepal, offering a wide range of programs.", "website": "https://tribhuvan-university.edu.np"},
        {"name": "Kathmandu University", "location": "Dhulikhel", "established_year": 1991, "description": "Known for its excellence in science, engineering, and medical programs.", "website": "https://ku.edu.np"},
        {"name": "Purbanchal University", "location": "Biratnagar", "established_year": 1993, "description": "Focuses on diverse fields including agriculture and technology.", "website": "https://pu.edu.np"}
    ]

def handle_predicted_tag(intent, context):
    course = context.get("course", "")
    user_name = context.get("user_name", "")
    state = context.get("state", "start")
    previous_state = context.get("previous_state", "greeting")
    greeting = f"{user_name + ', ' if user_name else ''}"
    path = f"You’re exploring: {context.get('category', '')} > {course}".strip()
    all_courses = get_all_courses()

    logging.debug(f"Handling intent: '{intent}' with course: '{course}', state: '{state}', previous_state: '{previous_state}'")

    if intent == "reset":
        response = f"Conversation reset, {greeting}! Let’s start fresh."
        buttons = INITIAL_BUTTONS
        context["state"] = "greeting"
        context.pop("course", None)
        context.pop("category", None)
        context.pop("previous_state", None)
        context["history"] = []
        return response, context, buttons

    if intent == "back":
        if state == "course_details":
            response = f"Returning to category selection, {greeting}! Which category would you like to explore? {path}"
            buttons = ["📚 Science and Technology", "🔬 Management and Business", "💼 Humanities and Social Sciences", "🏫 Education", "⚖️ Law", "🏥 Health Sciences", "🌱 Agriculture and Forestry", "📺 Media and Communication", "🖌️ Fine Arts and Design", "🔧 Vocational and Technical", "👨‍💼 Professional and Specialized", "🏠 Back to Start"]
            context["state"] = "faculty_selection"
            context.pop("course", None)
        elif state in ["notes_selection", "syllabus_selection", "entrance_exam_selection", "course_recommendation", "college_recommendation", "study_abroad_selection", "online_course_selection", "syllabus_details"]:
            response = f"Returning to the main menu, {greeting}! What would you like to explore? {path}"
            buttons = INITIAL_BUTTONS
            context["state"] = "greeting"
            context.pop("course", None)
            context.pop("category", None)
        else:
            response = f"Returning to the main menu, {greeting}! What would you like to explore? {path}"
            buttons = INITIAL_BUTTONS
            context["state"] = "greeting"
        context.pop("previous_state", None)
        return response, context, buttons

    if state == "ask_name":
        context["user_name"] = intent.strip()
        response = f"Welcome, {context['user_name']}! 😊 Please share your email address."
        buttons = ["⬅️ Back"]
        context["state"] = "ask_email"
        context["previous_state"] = "ask_name"
    elif state == "ask_email":
        email = intent.strip()
        if re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
            context["user_email"] = email
            response = f"Delighted to connect, {context['user_name']}! Your email ({email}) is saved. Let’s explore!"
            buttons = INITIAL_BUTTONS
            context["state"] = "greeting"
            with open("contacts.txt", "a") as f:
                f.write(f"Name: {context['user_name']}, Email: {email}\n")
        else:
            response = "Hmm, that email doesn’t look right. Try again? 📧"
            buttons = ["⬅️ Back"]
            context["state"] = "ask_email"
    elif intent == "greeting":
        response = f"Hello {greeting}! 🌟 Welcome to Entrance Gateway—your guide to education in Nepal."
        buttons = INITIAL_BUTTONS
        context["state"] = "greeting"
        context.pop("course", None)
        context.pop("category", None)
    elif intent == "contact_us":
        response = f"I’m here to assist, {greeting}! 😊 Please tell me your name."
        buttons = ["⬅️ Back"]
        context["state"] = "ask_name"
        context.pop("course", None)
        context.pop("category", None)
        context["previous_state"] = state
    elif intent == "course_categories":
        response = f"Great choice, {greeting}! Which category would you like to explore? {path}"
        buttons = ["📚 Science and Technology", "🔬 Management and Business", "💼 Humanities and Social Sciences", "🏫 Education", "⚖️ Law", "🏥 Health Sciences", "🌱 Agriculture and Forestry", "📺 Media and Communication", "🖌️ Fine Arts and Design", "🔧 Vocational and Technical", "👨‍💼 Professional and Specialized", "🏠 Back to Start"]
        context["state"] = "faculty_selection"
        context["previous_state"] = state
    elif intent == "college_list":
        colleges = get_colleges()
        if colleges:
            response = f"Here are some colleges in Nepal, {greeting}:\n"
            for college in colleges:
                response += f"- **{college['name']}** (Location: {college['location']}, Courses Offered: {college['courses_offered']})\n"
            buttons = INITIAL_BUTTONS + ["⬅️ Back"]
        else:
            response = f"No colleges found, {greeting}. Try another option! {path}"
            buttons = INITIAL_BUTTONS + ["⬅️ Back"]
        context["state"] = "college_list"
        context["previous_state"] = state
    elif intent in CATEGORY_COURSES:
        category = {
            "category_science_tech": "Science and Technology",
            "category_management": "Management and Business",
            "category_humanities": "Humanities and Social Sciences",
            "category_education": "Education",
            "category_law": "Law",
            "category_health": "Health Sciences",
            "category_agri_forestry": "Agriculture and Forestry",
            "category_media": "Media and Communication",
            "category_fine_arts": "Fine Arts and Design",
            "category_vocational": "Vocational and Technical",
            "category_professional": "Professional and Specialized"
        }[intent]
        courses = get_courses_by_category(category)
        if courses:
            response = f"Perfect, {greeting}! Here are courses under {category}. Pick one! {path}"
            buttons = courses[:4] + ["📚 View More"] + BACK_BUTTONS
            context["category"] = category
            context["state"] = "category_courses"
            context["previous_state"] = state
        else:
            response = f"No courses found for {category}, {greeting}. Try another category! {path}"
            buttons = INITIAL_BUTTONS + ["⬅️ Back"]
            context["state"] = "greeting"
            context["previous_state"] = state
    elif intent == "view_more_courses":
        if "category" in context:
            courses = get_courses_by_category(context["category"])
            if len(courses) > 4:
                response = f"More courses under {context['category']}: {', '.join(courses[4:])} Pick one! {path}"
                buttons = courses[4:] + BACK_BUTTONS
            else:
                response = f"No more courses under {context['category']}, {greeting}. What next? {path}"
                buttons = INITIAL_BUTTONS + ["⬅️ Back"]
            context["state"] = "view_more"
            context["previous_state"] = state
        else:
            courses = get_all_courses()
            response = f"All available courses: {', '.join(courses)}. Which one? {path}"
            buttons = courses[:4] + ["📚 View More"] + BACK_BUTTONS
            context["state"] = "view_more"
            context["previous_state"] = state
    elif intent in ["course_fees", "duration_info", "eligibility_info", "career_options", "scholarship_info", "application_process"]:
        if not course:
            response = f"Which course would you like details for, {greeting}? Pick a category: {path}"
            buttons = ["📚 Science and Technology", "🔬 Management and Business", "💼 Humanities and Social Sciences", "🏫 Education", "⚖️ Law", "🏥 Health Sciences", "🌱 Agriculture and Forestry", "📺 Media and Communication", "🖌️ Fine Arts and Design", "🔧 Vocational and Technical", "👨‍💼 Professional and Specialized"] + BACK_BUTTONS
            context["state"] = "course_selection"
            context["previous_state"] = state
        else:
            details = get_course_details(course, intent)
            response = f"{details}\nWhat else about {course} interests you, {greeting}? {path}"
            buttons = COURSE_BUTTONS
            context["state"] = "course_details"
            context["previous_state"] = state
    elif intent == "quiz_redirect":
        response = f"Ready for a quiz on {course or 'a course'}, {greeting}? [Quiz link placeholder] {path}"
        buttons = BACK_BUTTONS
        context["state"] = "quiz_prompt"
        context["previous_state"] = state
    elif intent == "blogs":
        blogs = get_blogs()
        if blogs:
            response = f"Here are some blogs, {greeting}:\n"
            for blog in blogs:
                response += f"- **{blog['title']}** by {blog['author']} ({blog['publish_date']})\n"
            buttons = INITIAL_BUTTONS + ["⬅️ Back"]
        else:
            response = f"No blogs found, {greeting}. Try another option! {path}"
            buttons = INITIAL_BUTTONS + ["⬅️ Back"]
        context["state"] = "blogs"
        context["previous_state"] = state
    elif intent == "universities":
        universities = get_universities()
        if universities:
            response = f"Here are some universities in Nepal, {greeting}:\n"
            for university in universities:
                response += f"- **{university['name']}** (Location: {university['location']}, Established: {university['established_year']}, Description: {university['description']}, Website: {university['website']})\n"
            buttons = INITIAL_BUTTONS + ["⬅️ Back"]
        else:
            response = f"No universities found, {greeting}. Try another option! {path}"
            buttons = INITIAL_BUTTONS + ["⬅️ Back"]
        context["state"] = "universities"
        context["previous_state"] = state
    elif intent == "notes":
        response = f"📖 Looking for study notes, {greeting}? Which course would you like notes for? {path}"
        buttons = all_courses[:4] + ["📚 View More"] + BACK_BUTTONS
        context["state"] = "notes_selection"
        context["previous_state"] = state
    elif intent == "syllabus":
        response = f"📋 I can show you the syllabus, {greeting}! Which course are you interested in? {path}"
        buttons = all_courses[:4] + ["📚 View More"] + BACK_BUTTONS
        context["state"] = "syllabus_selection"
        context["previous_state"] = state
    elif intent == "sign_in":
        response = f"🔐 Please sign in to your Entrance Gateway account, {greeting}. [Sign in link placeholder] {path}"
        buttons = INITIAL_BUTTONS + ["⬅️ Back"]
        context["state"] = "greeting"
        context["previous_state"] = state
    elif intent == "sign_up":
        response = f"📝 Let’s get you started, {greeting}! Sign up for an Entrance Gateway account. [Sign up link placeholder] {path}"
        buttons = INITIAL_BUTTONS + ["⬅️ Back"]
        context["state"] = "greeting"
        context["previous_state"] = state
    elif intent == "best_course":
        response = f"📚 Let’s find the best course for you, {greeting}! What are your interests? (e.g., Science, Management, Health) {path}"
        buttons = ["📚 Science and Technology", "🔬 Management and Business", "💼 Humanities and Social Sciences", "🏫 Education", "⚖️ Law", "🏥 Health Sciences", "🌱 Agriculture and Forestry", "📺 Media and Communication", "🖌️ Fine Arts and Design", "🔧 Vocational and Technical", "👨‍💼 Professional and Specialized"] + BACK_BUTTONS
        context["state"] = "course_recommendation"
        context["previous_state"] = state
    elif intent == "best_college":
        response = f"🏫 Looking for the best college, {greeting}? What course are you interested in studying? {path}"
        buttons = ["📚 Science and Technology", "🔬 Management and Business", "💼 Humanities and Social Sciences", "🏫 Education", "⚖️ Law", "🏥 Health Sciences", "🌱 Agriculture and Forestry", "📺 Media and Communication", "🖌️ Fine Arts and Design", "🔧 Vocational and Technical", "👨‍💼 Professional and Specialized"] + BACK_BUTTONS
        context["state"] = "college_recommendation"
        context["previous_state"] = state
    elif intent == "exam_preparation":
        response = f"📖 Need help with exam preparation, {greeting}? I can share some tips or direct you to study notes! What are you preparing for? {path}"
        buttons = ["📖 Notes", "🧪 QuizPro", "✍️ Blogs"] + BACK_BUTTONS
        context["state"] = "exam_prep"
        context["previous_state"] = state
    elif intent == "entrance_exam":
        response = f"📝 Preparing for an entrance exam, {greeting}? I can help! Which course or college are you applying for? {path}"
        buttons = all_courses[:4] + ["📚 View More"] + BACK_BUTTONS
        context["state"] = "entrance_exam_selection"
        context["previous_state"] = state
    elif intent == "location":
        response = f"📍 I can help with the location, {greeting}! Which college or university are you looking for? {path}"
        colleges = get_colleges()
        universities = get_universities()
        institutions = [college['name'] for college in colleges] + [university['name'] for university in universities]
        buttons = institutions[:4] + BACK_BUTTONS
        context["state"] = "location_selection"
        context["previous_state"] = state
    elif intent == "study_abroad":
        response = f"🌍 Interested in studying abroad, {greeting}? I can help! What country or course are you considering? {path}"
        buttons = ["📚 Science and Technology", "🔬 Management and Business", "💼 Humanities and Social Sciences", "🏫 Education", "⚖️ Law", "🏥 Health Sciences"] + BACK_BUTTONS
        context["state"] = "study_abroad_selection"
        context["previous_state"] = state
    elif intent == "online_courses":
        response = f"💻 Looking for online courses, {greeting}? Let me help you find some options! What subject are you interested in? {path}"
        buttons = ["📚 Science and Technology", "🔬 Management and Business", "💼 Humanities and Social Sciences", "🏫 Education", "⚖️ Law", "🏥 Health Sciences"] + BACK_BUTTONS
        context["state"] = "online_course_selection"
        context["previous_state"] = state
    elif intent == "thank_you":
        response = f"😊 You're welcome, {greeting}! I'm here to help anytime! {path}"
        buttons = INITIAL_BUTTONS + ["⬅️ Back"]
        context["state"] = "greeting"
        context["previous_state"] = state
    elif intent == "goodbye":
        response = f"👋 Goodbye, {greeting}! Feel free to come back if you have more questions! {path}"
        buttons = ["👋 Start Exploring"]
        context["state"] = "goodbye"
        context["previous_state"] = state
    else:
        response = f"Hmm, I’m not sure, {greeting}! Let’s start fresh—pick an option! {path}"
        buttons = INITIAL_BUTTONS + ["⬅️ Back"]
        context["state"] = "greeting"
        context["previous_state"] = state

    context["history"] = context.get("history", []) + [intent]
    return response, context, buttons

def get_response(user_input, context):
    start_time = time.time()
    try:
        logging.debug(f"Processing input: '{user_input}' with context: {context}")
        updated_context = context.copy()
        all_courses = get_all_courses()

        # Handle "reset" command explicitly
        if user_input.lower() == "reset":
            response, updated_context, buttons = handle_predicted_tag("reset", updated_context)
            return response, updated_context, buttons

        # Predict the intent first
        intent = predict_intent(user_input)

        # Handle state-specific logic for ask_name and ask_email
        state = updated_context.get("state", "start")
        if state in ["ask_name", "ask_email"]:
            if user_input in BUTTON_INTENTS or intent in ["contact_us", "greeting", "reset"]:
                updated_context["state"] = "greeting"
                updated_context.pop("user_name", None)
                updated_context.pop("user_email", None)
                updated_context.pop("course", None)
                updated_context.pop("category", None)
                response, updated_context, buttons = handle_predicted_tag(intent, updated_context)
                logging.debug(f"Reset to greeting due to button click or intent in {state} state: {time.time() - start_time:.3f}s")
                return response, updated_context, buttons
            response, updated_context, buttons = handle_predicted_tag(user_input, updated_context)
            logging.debug(f"Text response time for '{user_input}': {time.time() - start_time:.3f}s")
            return response, updated_context, buttons

        # Handle button intents and course selections
        if user_input in BUTTON_INTENTS or user_input in all_courses:
            intent = BUTTON_INTENTS.get(user_input, user_input)
            if user_input in all_courses:
                updated_context["course"] = user_input
                if state == "notes_selection":
                    updated_context["state"] = "notes_details"
                    greeting = f"{updated_context.get('user_name', '') + ', ' if updated_context.get('user_name') else ''}"
                    path = f"You’re exploring: {updated_context.get('category', '')} > {updated_context.get('course', '')}".strip()
                    response = f"Here are some notes for {user_input}, {greeting}! [Notes link placeholder] {path}"
                    buttons = INITIAL_BUTTONS + ["⬅️ Back"]
                    updated_context["history"] = updated_context.get("history", []) + [intent]
                    updated_context["previous_state"] = state
                    logging.debug(f"Button response time for '{user_input}': {time.time() - start_time:.3f}s")
                    return response, updated_context, buttons
                elif state == "syllabus_selection":
                    updated_context["state"] = "syllabus_details"
                    greeting = f"{updated_context.get('user_name', '') + ', ' if updated_context.get('user_name') else ''}"
                    path = f"You’re exploring: {updated_context.get('category', '')} > {updated_context.get('course', '')}".strip()
                    syllabus = get_course_details(user_input, "syllabus_info")
                    response = f"Here’s the syllabus for {user_input}, {greeting}!\n{syllabus}\nWhat else would you like to explore? {path}"
                    buttons = INITIAL_BUTTONS + ["⬅️ Back"]
                    updated_context["history"] = updated_context.get("history", []) + [intent]
                    updated_context["previous_state"] = state
                    logging.debug(f"Button response time for '{user_input}': {time.time() - start_time:.3f}s")
                    return response, updated_context, buttons
                elif state == "entrance_exam_selection":
                    updated_context["state"] = "entrance_exam_details"
                    greeting = f"{updated_context.get('user_name', '') + ', ' if updated_context.get('user_name') else ''}"
                    path = f"You’re exploring: {updated_context.get('category', '')} > {updated_context.get('course', '')}".strip()
                    response = f"Preparing for the entrance exam for {user_input}, {greeting}? Here are some tips: [Entrance exam tips placeholder] {path}"
                    buttons = ["📖 Notes", "🧪 QuizPro", "✍️ Blogs"] + BACK_BUTTONS
                    updated_context["history"] = updated_context.get("history", []) + [intent]
                    updated_context["previous_state"] = state
                    logging.debug(f"Button response time for '{user_input}': {time.time() - start_time:.3f}s")
                    return response, updated_context, buttons
                updated_context["state"] = "course_details"
                greeting = f"{updated_context.get('user_name', '') + ', ' if updated_context.get('user_name') else ''}"
                path = f"You’re exploring: {updated_context.get('category', '')} > {updated_context.get('course', '')}".strip()
                response = get_course_details(user_input) + f"\nWhat about {user_input} interests you, {greeting}? {path}"
                buttons = COURSE_BUTTONS
                updated_context["previous_state"] = state
                updated_context["history"] = updated_context.get("history", []) + [intent]
                logging.debug(f"Button response time for '{user_input}': {time.time() - start_time:.3f}s")
                return response, updated_context, buttons
            elif state == "course_recommendation" and user_input in CATEGORY_COURSES:
                intent = user_input  # Reuse the category intent (e.g., "category_science_tech")
            elif state == "college_recommendation" and user_input in CATEGORY_COURSES:
                category = {
                    "category_science_tech": "Science and Technology",
                    "category_management": "Management and Business",
                    "category_humanities": "Humanities and Social Sciences",
                    "category_education": "Education",
                    "category_law": "Law",
                    "category_health": "Health Sciences",
                    "category_agri_forestry": "Agriculture and Forestry",
                    "category_media": "Media and Communication",
                    "category_fine_arts": "Fine Arts and Design",
                    "category_vocational": "Vocational and Technical",
                    "category_professional": "Professional and Specialized"
                }[user_input]
                colleges = get_colleges()
                greeting = f"{updated_context.get('user_name', '') + ', ' if updated_context.get('user_name') else ''}"
                path = f"You’re exploring: {updated_context.get('category', '')} > {updated_context.get('course', '')}".strip()
                response = f"🏫 Based on your interest in {category}, here are some colleges, {greeting}:\n"
                for college in colleges:
                    if any(course in college['courses_offered'] for course in CATEGORY_COURSES[user_input]):
                        response += f"- **{college['name']}** (Location: {college['location']})\n"
                buttons = INITIAL_BUTTONS + ["⬅️ Back"]
                updated_context["state"] = "greeting"
                updated_context["history"] = updated_context.get("history", []) + [user_input]
                updated_context["previous_state"] = state
                logging.debug(f"Button response time for '{user_input}': {time.time() - start_time:.3f}s")
                return response, updated_context, buttons
            elif state == "location_selection":
                colleges = get_colleges()
                universities = get_universities()
                institution = next((c for c in colleges if c['name'] == user_input), None)
                if not institution:
                    institution = next((u for u in universities if u['name'] == user_input), None)
                greeting = f"{updated_context.get('user_name', '') + ', ' if updated_context.get('user_name') else ''}"
                path = f"You’re exploring: {updated_context.get('category', '')} > {updated_context.get('course', '')}".strip()
                if institution:
                    response = f"📍 {user_input} is located in {institution['location']}, {greeting}! {path}"
                else:
                    response = f"📍 Sorry, I couldn’t find the location of {user_input}, {greeting}. Try another institution! {path}"
                buttons = INITIAL_BUTTONS + ["⬅️ Back"]
                updated_context["state"] = "greeting"
                updated_context["history"] = updated_context.get("history", []) + [user_input]
                updated_context["previous_state"] = state
                logging.debug(f"Button response time for '{user_input}': {time.time() - start_time:.3f}s")
                return response, updated_context, buttons
            response, updated_context, buttons = handle_predicted_tag(intent, updated_context)
            logging.debug(f"Button response time for '{user_input}': {time.time() - start_time:.3f}s")
            return response, updated_context, buttons

        # Handle predicted intent
        response, updated_context, buttons = handle_predicted_tag(intent, updated_context)
        logging.debug(f"Text response time for '{user_input}': {time.time() - start_time:.3f}s")
        return response, updated_context, buttons

    except mysql.connector.Error as e:
        logging.error(f"Database error in get_response: {e}")
        return (f"Sorry, I couldn’t fetch data due to a database issue. Try again or pick an option!", context, INITIAL_BUTTONS)
    except Exception as e:
        logging.error(f"Error in get_response: {e}")
        return (f"Oops, something went wrong with '{user_input}'! Let’s try again.", context, INITIAL_BUTTONS)

@app.route('/')
def home():
    logging.debug("Rendering home page.")
    try:
        courses = get_all_courses()
        return render_template('index.html', courses=courses, colleges=[])
    except Exception as e:
        logging.error(f"Error rendering home page: {e}")
        return "Error loading home page.", 500

@app.route('/colleges')
def colleges():
    logging.debug("Rendering colleges page.")
    try:
        colleges = get_colleges()
        return render_template('colleges.html', colleges=colleges)
    except Exception as e:
        logging.error(f"Error rendering colleges page: {e}")
        return "Error loading colleges page.", 500

@app.route('/courses')
def courses():
    logging.debug("Rendering courses page.")
    try:
        courses = get_all_courses()
        return render_template('courses.html', courses=courses)
    except Exception as e:
        logging.error(f"Error rendering courses page: {e}")
        return "Error loading courses page.", 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_input = data.get('message', '').strip()
        context = data.get('context', {"state": "start", "history": []})
        if not user_input:
            logging.debug("No input provided in /chat. Returning greeting.")
            return jsonify({'response': "Hello! 🌟 Welcome to Entrance Gateway!", 'buttons': INITIAL_BUTTONS, 'context': {"state": "greeting", "history": []}})
        response, updated_context, buttons = get_response(user_input, context)
        return jsonify({'response': response, 'context': updated_context, 'buttons': buttons})
    except Exception as e:
        logging.error(f"Error in /chat: {e}")
        return jsonify({'response': "Oops, something went wrong!", 'buttons': INITIAL_BUTTONS, 'context': context}), 500

@app.route('/button', methods=['POST'])
def button_click():
    try:
        data = request.json
        button_label = data.get('button', '').strip()
        logging.debug(f"Received button click: {button_label}")
        context = data.get('context', {"state": "start", "history": []})
        if not button_label:
            logging.debug("No button label provided in /button. Returning greeting.")
            return jsonify({'response': "Hello! 🌟 Welcome to Entrance Gateway!", 'buttons': INITIAL_BUTTONS, 'context': {"state": "greeting", "history": []}})
        response, updated_context, buttons = get_response(button_label, context)
        return jsonify({'response': response, 'context': updated_context, 'buttons': buttons})
    except Exception as e:
        logging.error(f"Error in /button: {e}")
        return jsonify({'response': "Oops, something went wrong!", 'buttons': INITIAL_BUTTONS, 'context': context}), 500

@app.cli.command("init-db")
def init_db():
    logging.info("Attempting to initialize database...")
    connection = get_db_connection()
    if connection:
        cursor = None
        try:
            cursor = connection.cursor()
            cursor.execute("DROP TABLE IF EXISTS courses, colleges, universities, blogs")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    category VARCHAR(255) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT NOT NULL,
                    duration VARCHAR(50) NOT NULL,
                    fees VARCHAR(100) NOT NULL,
                    colleges TEXT NOT NULL,
                    admission TEXT NOT NULL,
                    eligibility TEXT NOT NULL,
                    career_options TEXT NOT NULL,
                    syllabus TEXT NOT NULL,
                    UNIQUE KEY unique_name (name)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS colleges (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    location VARCHAR(255) NOT NULL,
                    courses_offered TEXT NOT NULL,
                    UNIQUE KEY unique_name (name)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS universities (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    location VARCHAR(255) NOT NULL,
                    established_year INT NOT NULL,
                    description TEXT NOT NULL,
                    website VARCHAR(255),
                    UNIQUE KEY unique_name (name)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blogs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    author VARCHAR(100) NOT NULL,
                    excerpt TEXT NOT NULL,
                    link VARCHAR(255) NOT NULL,
                    publish_date DATE NOT NULL
                )
            """)
            connection.commit()
            logging.info("Database tables initialized successfully.")
        except mysql.connector.Error as err:
            logging.error(f"Database initialization error: {err}")
            raise
        finally:
            if cursor:
                cursor.close()
            connection.close()
            logging.debug("Database connection closed in init_db")
    else:
        logging.warning("No database connection available for init_db.")

@app.cli.command("populate-db")
def populate_db():
    logging.info("Attempting to populate database...")
    connection = get_db_connection()
    if connection:
        cursor = None
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO courses (category, name, description, duration, fees, colleges, admission, eligibility, career_options, syllabus)
                VALUES 
                    ('Science and Technology', 'BSc CSIT', 'Bachelor of Science in Computer Science and Information Technology', '4 years', 'NRP 500,000', 'Tribhuvan University, St. Xavier’s College', 'Entrance exam required', '10+2 with Science (Math/Physics)', 'Software Developer, IT Manager, Data Analyst', 'http://www.example.com/syllabus/bsc-csit'),
                    ('Science and Technology', 'BSc Physics', 'Bachelor of Science in Physics', '4 years', 'NRP 400,000', 'Tribhuvan University', 'Entrance exam required', '10+2 with Science (Physics)', 'Physicist, Researcher, Teacher', 'http://www.example.com/syllabus/bsc-physics'),
                    ('Management and Business', 'BBA', 'Bachelor of Business Administration', '4 years', 'NRP 600,000', 'Kathmandu University', 'Entrance exam and interview', '10+2 in any stream', 'Manager, Entrepreneur, Consultant', 'http://www.example.com/syllabus/bba'),
                    ('Science and Technology', 'BCA', 'Bachelor of Computer Applications', '3 years', 'NRP 450,000', 'Purbanchal University, St. Xavier’s College', 'Entrance exam required', '10+2 in any stream with Mathematics', 'Software Developer, Web Developer, IT Consultant', 'http://www.example.com/syllabus/bca'),
                    ('Science and Technology', 'BE Civil Engineering', 'Bachelor of Engineering in Civil Engineering', '4 years', 'NRP 800,000', 'Kathmandu University, Pulchowk Campus', 'Entrance exam required', '10+2 with Science (Math/Physics)', 'Civil Engineer, Project Manager', 'http://www.example.com/syllabus/be-civil-engineering'),
                    ('Health Sciences', 'MBBS', 'Bachelor of Medicine, Bachelor of Surgery', '5.5 years', 'NRP 4,000,000', 'Tribhuvan University, Kathmandu Medical College', 'Entrance exam required', '10+2 with Science (Biology)', 'Doctor, Surgeon', 'http://www.example.com/syllabus/mbbs'),
                    ('Management and Business', 'BBS', 'Bachelor of Business Studies', '4 years', 'NRP 300,000', 'Purbanchal University', 'Entrance exam required', '10+2 in any stream', 'Accountant, Business Analyst', 'http://www.example.com/syllabus/bbs'),
                    ('Humanities and Social Sciences', 'BA Sociology', 'Bachelor of Arts in Sociology', '3 years', 'NRP 200,000', 'Tribhuvan University', 'Direct admission', '10+2 in any stream', 'Sociologist, Social Worker', 'http://www.example.com/syllabus/ba-sociology'),
                    ('Education', 'BEd Mathematics', 'Bachelor of Education in Mathematics', '4 years', 'NRP 250,000', 'Tribhuvan University', 'Entrance exam required', '10+2 with Mathematics', 'Teacher, Education Consultant', 'http://www.example.com/syllabus/bed-mathematics'),
                    ('Law', 'LLB', 'Bachelor of Laws', '3 years', 'NRP 500,000', 'Kathmandu School of Law', 'Entrance exam or interview', 'Bachelor’s degree in any field', 'Lawyer, Legal Advisor', 'http://www.example.com/syllabus/llb'),
                    ('Agriculture and Forestry', 'BSc Agriculture', 'Bachelor of Science in Agriculture', '4 years', 'NRP 450,000', 'Purbanchal University', 'Entrance exam required', '10+2 with Science (Biology)', 'Agricultural Officer, Farm Manager', 'http://www.example.com/syllabus/bsc-agriculture')
                ON DUPLICATE KEY UPDATE
                    category=VALUES(category), description=VALUES(description), duration=VALUES(duration),
                    fees=VALUES(fees), colleges=VALUES(colleges), admission=VALUES(admission),
                    eligibility=VALUES(eligibility), career_options=VALUES(career_options), syllabus=VALUES(syllabus)
            """)
            cursor.execute("""
                INSERT INTO colleges (name, location, courses_offered)
                VALUES 
                    ('St. Xavier’s College', 'Kathmandu', 'BSc CSIT, BCA, BSc Physics'),
                    ('Kathmandu University School of Management', 'Lalitpur', 'BBA, BBS'),
                    ('Kathmandu Medical College', 'Kathmandu', 'MBBS, BSc Nursing'),
                    ('Pulchowk Campus', 'Lalitpur', 'BE Civil Engineering, BE Computer Engineering'),
                    ('Nepal Law Campus', 'Kathmandu', 'LLB, BBA LLB'),
                    ('Trichandra Multiple Campus', 'Kathmandu', 'BSc Physics, BA Sociology'),
                    ('Amrit Science Campus', 'Kathmandu', 'BSc CSIT, BSc Physics'),
                    ('Patan Multiple Campus', 'Lalitpur', 'BA Sociology, BBS'),
                    ('Bhaktapur Multiple Campus', 'Bhaktapur', 'BBA, BSc Agriculture'),
                    ('Kathmandu Model College', 'Kathmandu', 'BCA, BBA')
                ON DUPLICATE KEY UPDATE
                    name=VALUES(name), location=VALUES(location), courses_offered=VALUES(courses_offered)
            """)
            cursor.execute("""
                INSERT INTO universities (name, location, established_year, description, website)
                VALUES 
                    ('Tribhuvan University', 'Kathmandu', 1959, 'The oldest university in Nepal, offering a wide range of programs.', 'http://www.tu.edu.np'),
                    ('Kathmandu University', 'Dhulikhel', 1991, 'Known for its excellence in science, engineering, and medical programs.', 'http://www.ku.edu.np'),
                    ('Purbanchal University', 'Biratnagar', 1993, 'Focuses on diverse fields including agriculture and technology.', 'http://www.pu.edu.np'),
                    ('Pokhara University', 'Pokhara', 1997, 'Offers programs in engineering, management, and health sciences.', 'http://www.pu.edu.np'),
                    ('Nepal Sanskrit University', 'Beljhundi', 1986, 'Specializes in Sanskrit studies and traditional education.', 'http://www.nsu.edu.np'),
                    ('Lumbini Buddhist University', 'Lumbini', 2004, 'Focuses on Buddhist studies and related disciplines.', 'http://www.lbu.edu.np'),
                    ('Mid-Western University', 'Surkhet', 2010, 'Provides education in various fields in the mid-western region.', 'http://www.mwu.edu.np'),
                    ('Far-Western University', 'Mahendranagar', 2010, 'Serves the far-western region with diverse academic programs.', 'http://www.fwu.edu.np'),
                    ('Agriculture and Forestry University', 'Chitwan', 2010, 'Specializes in agriculture, forestry, and veterinary sciences.', 'http://www.afu.edu.np'),
                    ('Nepal Open University', 'Lalitpur', 2016, 'Offers distance learning programs across various disciplines.', 'http://www.nou.edu.np')
                ON DUPLICATE KEY UPDATE
                    name=VALUES(name), location=VALUES(location), established_year=VALUES(established_year), description=VALUES(description), website=VALUES(website)
            """)
            cursor.execute("""
                INSERT INTO blogs (title, author, excerpt, link, publish_date)
                VALUES 
                    ('Top 10 Tips for Exam Preparation', 'Bishal Lama', 'Learn effective strategies to ace your exams with these proven tips.', 'http://www.example.com/blog/exam-tips', '2025-01-15'),
                    ('Why Choose a Career in STEM?', 'Anita Shrestha', 'Explore the benefits and opportunities in STEM fields.', 'http://www.example.com/blog/stem-career', '2025-02-01'),
                    ('A Guide to Scholarships in Nepal', 'Ramesh Thapa', 'Find out how to secure scholarships for your education in Nepal.', 'http://www.example.com/blog/scholarships', '2025-02-20'),
                    ('How to Ace Your Interviews', 'Priya Sharma', 'Top strategies to prepare for and succeed in job interviews.', 'http://www.example.com/blog/interview-tips', '2025-03-01'),
                    ('The Future of AI in Education', 'Sanjay Gupta', 'How AI is transforming the education sector.', 'http://www.example.com/blog/ai-education', '2025-03-05'),
                    ('Best Study Abroad Destinations', 'Kiran Nepal', 'Explore the top countries for international education.', 'http://www.example.com/blog/study-abroad', '2025-03-10'),
                    ('Time Management for Students', 'Asha Limbu', 'Effective tips to manage your time as a student.', 'http://www.example.com/blog/time-management', '2025-03-15'),
                    ('Career Options in Law', 'Deepak Thapa', 'Discover the opportunities available with a law degree.', 'http://www.example.com/blog/law-careers', '2025-03-20'),
                    ('How to Choose the Right Course', 'Nisha Rai', 'A guide to selecting the perfect course for your future.', 'http://www.example.com/blog/choose-course', '2025-03-25'),
                    ('Benefits of Online Learning', 'Ravi Shrestha', 'Why online education is the future of learning.', 'http://www.example.com/blog/online-learning', '2025-03-30')
                ON DUPLICATE KEY UPDATE
                    title=VALUES(title), author=VALUES(author), excerpt=VALUES(excerpt), link=VALUES(link), publish_date=VALUES(publish_date)
            """)
            connection.commit()
            cursor.execute("SELECT COUNT(*) as count FROM courses")
            count_courses = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) as count FROM colleges")
            count_colleges = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) as count FROM universities")
            count_universities = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) as count FROM blogs")
            count_blogs = cursor.fetchone()[0]
            logging.info(f"Database populated with {count_courses} courses, {count_colleges} colleges, {count_universities} universities, and {count_blogs} blogs.")
        except mysql.connector.Error as err:
            logging.error(f"Error populating database: {err}")
            raise
        finally:
            if cursor:
                cursor.close()
            connection.close()
            logging.debug("Database connection closed in populate_db")
    else:
        logging.warning("No database connection available for populate_db.")

def find_available_port(host='0.0.0.0', start_port=5000, max_attempts=10):
    port = start_port
    for attempt in range(max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
                logging.debug(f"Port {port} is available.")
                return port
            except OSError as e:
                logging.debug(f"Port {port} in use: {e}. Trying next port...")
                port += 1
    logging.error(f"No available ports found between {start_port} and {start_port + max_attempts - 1}")
    raise RuntimeError(f"No available ports found between {start_port} and {start_port + max_attempts - 1}")

if __name__ == '__main__':
    logging.info("Starting Flask application...")
    try:
        port = find_available_port(host='0.0.0.0', start_port=5000)
        logging.info(f"Starting Flask server on port {port}...")
        app.run(debug=True, host='0.0.0.0', port=port)
        logging.info(f"Flask app is running on http://0.0.0.0:{port}")
    except Exception as e:
        logging.error(f"Failed to start Flask server: {e}")
        sys.exit(1)