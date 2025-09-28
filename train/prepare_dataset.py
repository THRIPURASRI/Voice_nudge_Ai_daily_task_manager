import pandas as pd

def load_dataset(path="datasets/tasks_dataset.csv"):
    """
    Load dataset from CSV.
    CSV must have columns: text, category, priority
    """
    df = pd.read_csv(path)
    if not {"text", "category", "priority"}.issubset(df.columns):
        raise ValueError("Dataset must contain text, category, and priority columns")

    X = df["text"].astype(str).values
    y_cat = df["category"].astype(str).values
    y_pri = df["priority"].astype(str).values
    return X, y_cat, y_pri
