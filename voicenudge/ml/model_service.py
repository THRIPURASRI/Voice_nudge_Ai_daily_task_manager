import os, joblib

# Load pretrained models
CATEGORY_MODEL_PATH = "models/category_svm.joblib"
PRIORITY_MODEL_PATH = "models/priority_rf.joblib"

try:
    category_model = joblib.load(CATEGORY_MODEL_PATH)
except:
    category_model = None

try:
    priority_model = joblib.load(PRIORITY_MODEL_PATH)
except:
    priority_model = None

def predict_category(text: str):
    return category_model.predict([text])[0] if category_model else "Personal"

def predict_priority(text: str):
    return priority_model.predict([text])[0] if priority_model else "Medium"
