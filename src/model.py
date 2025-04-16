import os
import time
import joblib
import logging
import pandas as pd
from dotenv import load_dotenv
from typing import Literal, Any, Tuple, Dict, List
import mlflow
from mlflow.models import infer_signature
from mlflow.tracking import MlflowClient
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix

from src.sql import load_matches_from_postgres
from src.enums import Feature

load_dotenv()

models = {}

def create_pairwise_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates a balanced dataset with pairwise comparisons
    """
    records = []
    for _, row in df.iterrows():
        # Record 1 : original order (winner in position 1, loser in position 2)
        record_1 = {
            Feature.SERIES.name: row['series'],
            Feature.SURFACE.name: row['surface'],
            Feature.COURT.name: row['court'],
            Feature.ROUND.name: row['round'],
            Feature.DIFF_RANKING.name: row['w_rank'] - row['l_rank'], # rank difference
            Feature.DIFF_POINTS.name: row['w_points'] - row['l_points'], # points difference
            'target': 1 # Player in first position won
        }

        # Record 2 : invert players
        record_2 = record_1.copy()
        record_2[Feature.DIFF_RANKING.name] = -record_2['diffRanking'] # Invert the ranking difference
        record_2[Feature.DIFF_POINTS.name] = -record_2['diffPoints'] # Invert the points difference
        record_2['target'] = 0 # Player in first position lost

        records.append(record_1)
        records.append(record_2)
    
    return pd.DataFrame(records)

def create_pipeline() -> Pipeline:
    """
    Creates a machine learning pipeline with SimpleImputer, StandardScaler, OneHotEncoder and LogisticRegression.

    Returns:
        Pipeline: A scikit-learn pipeline object.
    """
    # Define the features, numerical and categorical
    cat_features = [f.name for f in Feature.get_features_by_type('category')]
    num_features = [f.name for f in Feature.get_features_by_type('number')]

    # Pipeline for numerical variables
    num_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='mean')),
        ('scaler', StandardScaler())
    ])

    # Pipeline for categorical variables
    cat_transformer = OneHotEncoder(handle_unknown='ignore')

    # Preprocessor
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', num_transformer, num_features),
            ('cat', cat_transformer, cat_features)
        ]
    )

    # Full pipeline
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', LogisticRegression(solver='lbfgs', max_iter=1000))
    ])

    return pipeline

def train_model_from_scratch(
        circuit: Literal['atp', 'wta'],
        from_date: str,
        to_date: str,
        output_path: str = '/data/model.pkl') -> Pipeline:
    """
    Train a model from scratch
    """
    # Load data
    data = load_matches_from_postgres(
        table_name=f"{circuit}_data",
        from_date=from_date,
        to_date=to_date)

    # Train the model
    pipeline = create_and_train_model(data)

    # Save the model
    joblib.dump(pipeline, output_path)

    return pipeline

def create_and_train_model(data: pd.DataFrame) -> Pipeline:
    """
    Create and train a model on the given data
    """
    # Split the data
    X_train, _, y_train, _ = preprocess_data(data)

    # Train the model
    pipeline = create_pipeline()
    pipeline = train_model(pipeline, X_train, y_train)

    return pipeline

def train_model(
        pipeline: Pipeline,
        X_train: pd.DataFrame,
        y_train: pd.DataFrame) -> Pipeline:
    """
    Train the pipeline
    """
    pipeline.fit(X_train, y_train)
    return pipeline

def preprocess_data(df: pd.DataFrame) -> Tuple:
    """
    Split the dataframe into X (features) and y (target).

    Args:
        df (pd.DataFrame): Input dataframe.

    Returns:
        Tuple: Split data (X_train, X_test, y_train, y_test).
    """
    # Format data for the model
    df_model = create_pairwise_data(df)

    features = [f.name for f in Feature.get_all_features()]
    X = df_model[features]
    y = df_model['target']

    # Split the data
    return train_test_split(X, y, test_size=0.2)

def evaluate_model(pipeline: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> Dict:
    """
    Evaluates the model
    """
    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, pipeline.predict_proba(X_test)[:, 1])
    cm = confusion_matrix(y_test, y_pred)

    return {
        "accuracy": accuracy,
        "roc_auc": roc_auc,
        "confusion_matrix": cm
    }

def predict(
    pipeline: Pipeline,
    series: str,
    surface: str,
    court: str,
    round_stage: str,
    rank_player_1: int,
    rank_player_2: int,
    points_player_1: int,
    points_player_2: int
) -> Dict[str, Any]:
    diffRanking = rank_player_1 - rank_player_2
    diffPoints = points_player_1 - points_player_2
    
    # Built a DataFrame with the new match
    new_match = pd.DataFrame([{
        Feature.SERIES.name: series,
        Feature.SURFACE.name: surface,
        Feature.COURT.name: court,
        Feature.ROUND.name: round_stage,
        Feature.DIFF_RANKING.name: diffRanking,
        Feature.DIFF_POINTS.name: diffPoints
    }])

    # Use the pipeline to make a prediction
    prediction = pipeline.predict(new_match)[0]
    proba = pipeline.predict_proba(new_match)[0]

    # Print the result
    logging.info("\n--- 📊 Result ---")
    logging.info(f"🏆 Win probability : {proba[1]:.2f}")
    logging.info(f"❌ Lose probability : {proba[0]:.2f}")
    logging.info(f"🎾 Prediction : {'Victory' if prediction == 1 else 'Loss'}")

    return {"result": prediction.item(), "prob": [p.item() for p in proba]}

def run_experiment(
        circuit: Literal['atp', 'wta'],
        from_date: str,
        to_date: str,
        artifact_path: str = None,
        registered_model_name: str = 'LogisticRegression',
        experiment_name: str = 'Logistic Tennis Prediction',
        ):
    """
    Run the entire ML experiment pipeline.

    Args:
        experiment_name (str): Name of the MLflow experiment.
        data_url (str): URL to load the dataset.
        artifact_path (str): Path to store the model artifact.
        registered_model_name (str): Name to register the model under in MLflow.
    """
    if not artifact_path:
        artifact_path = f'{circuit}_model'
    
    # Set tracking URI to your mlflow application
    mlflow.set_tracking_uri(os.environ["MLFLOW_SERVER_URI"])

    # Start timing
    start_time = time.time()

    # Load and preprocess data
    df = load_matches_from_postgres(
        table_name=f"{circuit}_data",
        from_date=from_date,
        to_date=to_date)
    X_train, X_test, y_train, y_test = preprocess_data(df)

    # Create pipeline
    pipe = create_pipeline()

    # Set experiment's info 
    mlflow.set_experiment(experiment_name)

    # Get our experiment info
    experiment = mlflow.get_experiment_by_name(experiment_name)

    # Call mlflow autolog
    mlflow.sklearn.autolog()

    with mlflow.start_run(experiment_id=experiment.experiment_id):
        # Train model
        train_model(pipe, X_train, y_train)
       
        # Store metrics 
        # predicted_output = pipe.predict(X_test.values)
        accuracy = pipe.score(X_test, y_test)
        
        # Print results 
        logging.info("LogisticRegression model")
        logging.info("Accuracy: {}".format(accuracy))
        signature = infer_signature(X_test, pipe.predict(X_test))

        mlflow.sklearn.log_model(
            sk_model=pipe,
            artifact_path=artifact_path,
            registered_model_name=registered_model_name,
            signature=signature
        )

    # Print timing
    logging.info(f"...Training Done! --- Total training time: {time.time() - start_time} seconds")

def list_registered_models() -> List[Dict]:
    """
    List all the registered models
    """
    # Set tracking URI to your Heroku application
    tracking_uri = os.environ.get("MLFLOW_SERVER_URI")
    if tracking_uri is None:
        raise ValueError("MLFLOW_SERVER_URI environment variable is not set.")
    print(f"MLflow tracking URI: {tracking_uri}")

    client = MlflowClient(tracking_uri=tracking_uri)
    # Should be:
    #   results = client.search_registered_models()
    # but this is not working from inside the container
    # so we need to use the store client to get the registered models
    results = client._get_registry_client().store.search_registered_models()

    output = []
    for res in results:
        for mv in res.latest_versions:
            output.append({"name": mv.name, "run_id": mv.run_id, "version": mv.version})
    
    return output

def load_model(name: str, version: str = 'latest') -> Pipeline:
    """
    Load a model from MLflow
    """
    if name in models.keys():
        return models[name]
    
    mlflow.set_tracking_uri(os.environ["MLFLOW_SERVER_URI"])
    client = MlflowClient()

    model_info = client.get_registered_model(name)

    # Load the model
    pipeline = mlflow.sklearn.load_model(model_uri=model_info.latest_versions[0].source)

    logging.info(f'Model {name} loaded')

    models[name] = pipeline

    return pipeline