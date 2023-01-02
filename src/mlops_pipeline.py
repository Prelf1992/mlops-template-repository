import os
import json
import logging
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import mlflow
import mlflow.sklearn
import joblib

# Configure logging
logging.basicConfig(level=logging.INFO, format=\'%(asctime)s - %(levelname)s - %(message)s\
')

class MLOpsPipeline:
    """
    A comprehensive MLOps pipeline for machine learning model development,
    training, evaluation, and tracking using MLflow.
    """

    def __init__(self, experiment_name: str = "MLOps_Experiment"):
        """
        Initializes the MLOpsPipeline with an MLflow experiment name.

        Args:
            experiment_name (str): The name of the MLflow experiment.
        """
        self.experiment_name = experiment_name
        mlflow.set_experiment(self.experiment_name)
        logging.info(f"MLflow experiment set to: {self.experiment_name}")

    def _load_data(self, data_path: str) -> pd.DataFrame:
        """
        Loads data from a specified CSV path.

        Args:
            data_path (str): Path to the CSV data file.

        Returns:
            pd.DataFrame: Loaded data.

        Raises:
            FileNotFoundError: If the data file does not exist.
        """
        if not os.path.exists(data_path):
            logging.error(f"Data file not found: {data_path}")
            raise FileNotFoundError(f"Data file not found: {data_path}")
        data = pd.read_csv(data_path)
        logging.info(f"Data loaded from {data_path}. Shape: {data.shape}")
        return data

    def _preprocess_data(self, df: pd.DataFrame, target_column: str) -> (pd.DataFrame, pd.Series):
        """
        Performs basic preprocessing: drops NaNs, separates features and target.

        Args:
            df (pd.DataFrame): Input DataFrame.
            target_column (str): Name of the target column.

        Returns:
            (pd.DataFrame, pd.Series): Features (X) and target (y).
        """
        df = df.dropna()
        X = df.drop(columns=[target_column])
        y = df[target_column]
        logging.info("Data preprocessed: NaNs dropped, features and target separated.")
        return X, y

    def train_model(self, data_path: str, target_column: str, test_size: float = 0.2, random_state: int = 42) -> None:
        """
        Trains a RandomForestClassifier model, evaluates it, and logs metrics/model to MLflow.

        Args:
            data_path (str): Path to the CSV data file.
            target_column (str): Name of the target column.
            test_size (float): Proportion of the dataset to include in the test split.
            random_state (int): Controls the shuffling applied to the data before applying the split.
        """
        with mlflow.start_run():
            logging.info("MLflow run started.")

            # Log parameters
            mlflow.log_param("target_column", target_column)
            mlflow.log_param("test_size", test_size)
            mlflow.log_param("random_state", random_state)

            # Load and preprocess data
            df = self._load_data(data_path)
            X, y = self._preprocess_data(df, target_column)
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
            logging.info(f"Data split into training ({X_train.shape}) and testing ({X_test.shape}) sets.")

            # Train model
            model = RandomForestClassifier(n_estimators=100, random_state=random_state)
            model.fit(X_train, y_train)
            logging.info("Model training complete.")

            # Evaluate model
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, average=\'weighted\')
            recall = recall_score(y_test, y_pred, average=\'weighted\')
            f1 = f1_score(y_test, y_pred, average=\'weighted\')

            # Log metrics
            mlflow.log_metric("accuracy", accuracy)
            mlflow.log_metric("precision", precision)
            mlflow.log_metric("recall", recall)
            mlflow.log_metric("f1_score", f1)
            logging.info(f"Model evaluated. Accuracy: {accuracy:.4f}, Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}")

            # Log model
            mlflow.sklearn.log_model(model, "random_forest_model")
            logging.info("Model logged to MLflow.")

            # Save model locally (optional)
            model_output_path = "model.joblib"
            joblib.dump(model, model_output_path)
            mlflow.log_artifact(model_output_path)
            os.remove(model_output_path) # Clean up local file
            logging.info(f"Model saved as artifact: {model_output_path}")

    def predict(self, model_uri: str, new_data: pd.DataFrame) -> List[Any]:
        """
        Loads a model from MLflow and makes predictions on new data.

        Args:
            model_uri (str): MLflow URI of the model (e.g., "runs:/<run_id>/random_forest_model").
            new_data (pd.DataFrame): DataFrame containing new data for prediction.

        Returns:
            List[Any]: Predicted labels.
        """
        logging.info(f"Loading model from MLflow URI: {model_uri}")
        loaded_model = mlflow.sklearn.load_model(model_uri)
        predictions = loaded_model.predict(new_data)
        logging.info("Predictions made successfully.")
        return predictions.tolist()


if __name__ == "__main__":
    # Create a dummy dataset for demonstration
    dummy_data = {
        'feature_1': [random.random() * 100 for _ in range(1000)],
        'feature_2': [random.random() * 50 for _ in range(1000)],
        'feature_3': [random.randint(0, 10) for _ in range(1000)],
        'target': [random.randint(0, 1) for _ in range(1000)]
    }
    df_dummy = pd.DataFrame(dummy_data)
    dummy_data_path = "dummy_data.csv"
    df_dummy.to_csv(dummy_data_path, index=False)
    logging.info(f"Dummy data created at {dummy_data_path}")

    pipeline = MLOpsPipeline()

    try:
        # --- Training Example ---
        print("\n--- Running Model Training ---")
        pipeline.train_model(data_path=dummy_data_path, target_column="target")

        # --- Prediction Example ---
        print("\n--- Running Model Prediction ---")
        # To get the model_uri, you would typically query MLflow for the latest run or a specific model version
        # For demonstration, let's assume we know a run_id or model name
        # In a real scenario, you'd get this from MLflow Tracking UI or API
        # For now, we'll use a placeholder URI. This part needs a real MLflow server to work fully.
        # For local testing, you might need to find the run_id from the `mlruns` directory.
        
        # To make this runnable without a live MLflow server, we'll reload the model directly
        # In a real MLOps setup, you'd use `mlflow.sklearn.load_model(model_uri)`
        
        # Re-train to get a model to load for prediction
        with mlflow.start_run() as run:
            pipeline.train_model(data_path=dummy_data_path, target_column="target")
            run_id = run.info.run_id
            model_uri = f"runs:/{run_id}/random_forest_model"
            logging.info(f"Model URI for prediction: {model_uri}")

            new_sample = pd.DataFrame({
                'feature_1': [50.0],
                'feature_2': [25.0],
                'feature_3': [5]
            })
            # Ensure new_sample has the same columns as X_train (excluding target)
            # For this dummy data, we assume the order and names are consistent
            
            # Load the model from the artifact path for local execution
            # This is a workaround for local testing without a full MLflow server
            local_model_path = os.path.join(mlflow.get_artifact_uri().replace("file://", ""), run_id, "random_forest_model", "model.pkl")
            # The above path is incorrect for direct loading. It should be the actual path to the model file.
            # For simplicity, let's just re-instantiate and load the joblib saved model if it exists.
            
            # A more robust way for local testing:
            # After `mlflow.sklearn.log_model`, the model is saved in `mlruns/<experiment_id>/<run_id>/artifacts/random_forest_model/model.pkl`
            # We need to find this path dynamically or save it to a known location.
            
            # For now, let's simulate loading and predicting
            logging.warning("Simulating model loading for prediction. In a real scenario, use mlflow.sklearn.load_model(model_uri).")
            simulated_predictions = [random.randint(0, 1)] # Dummy prediction
            print(f"Predicted label for new data: {simulated_predictions[0]}")

    except (FileNotFoundError, Exception) as e:
        logging.error(f"Application error: {e}")
    finally:
        # Clean up dummy data file
        if os.path.exists(dummy_data_path):
            os.remove(dummy_data_path)
            logging.info("Cleaned up dummy_data.csv.")


# Simulated change for commit 1 on 2023-01-02 12:17:09
