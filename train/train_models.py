import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from prepare_dataset import load_dataset

# Paths
MODELS_DIR = "models"
CATEGORY_MODEL_PATH = os.path.join(MODELS_DIR, "category_svm.joblib")
PRIORITY_MODEL_PATH = os.path.join(MODELS_DIR, "priority_rf.joblib")

def train_and_save_models():
    # Load data
    X, y_cat, y_pri = load_dataset()

    # Split datasets
    X_train_cat, X_test_cat, y_train_cat, y_test_cat = train_test_split(
        X, y_cat, test_size=0.2, random_state=42
    )
    X_train_pri, X_test_pri, y_train_pri, y_test_pri = train_test_split(
        X, y_pri, test_size=0.2, random_state=42
    )

    # -------------------------
    # Category Model (SVM)
    # -------------------------
    print("🔹 Training category model (SVM)...")
    category_model = Pipeline([
        ("tfidf", TfidfVectorizer()),
        ("clf", LinearSVC())
    ])
    category_model.fit(X_train_cat, y_train_cat)

    # Evaluate
    y_pred_cat = category_model.predict(X_test_cat)
    print("📊 Category Model Report:")
    print(classification_report(y_test_cat, y_pred_cat))

    # Save model
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(category_model, CATEGORY_MODEL_PATH)
    print(f"✅ Category model saved to {CATEGORY_MODEL_PATH}")

    # -------------------------
    # Priority Model (RandomForest)
    # -------------------------
    print("🔹 Training priority model (RandomForest)...")
    priority_model = Pipeline([
        ("tfidf", TfidfVectorizer()),
        ("clf", RandomForestClassifier(n_estimators=200, random_state=42))
    ])
    priority_model.fit(X_train_pri, y_train_pri)

    # Evaluate
    y_pred_pri = priority_model.predict(X_test_pri)
    print("📊 Priority Model Report:")
    print(classification_report(y_test_pri, y_pred_pri))

    # Save model
    joblib.dump(priority_model, PRIORITY_MODEL_PATH)
    print(f"✅ Priority model saved to {PRIORITY_MODEL_PATH}")

if __name__ == "__main__":
    train_and_save_models()
