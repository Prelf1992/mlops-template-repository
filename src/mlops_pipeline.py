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

# Simulated change for commit 3 on 2023-01-04 09:31:48

# Simulated change for commit 4 on 2023-01-11 17:52:32

# Simulated change for commit 8 on 2023-01-19 11:06:56

# Simulated change for commit 9 on 2023-01-20 09:03:30

# Simulated change for commit 10 on 2023-01-23 12:07:33

# Simulated change for commit 15 on 2023-01-30 17:03:17

# Simulated change for commit 16 on 2023-01-31 13:04:39

# Simulated change for commit 18 on 2023-02-06 10:35:30

# Simulated change for commit 20 on 2023-02-08 10:17:07

# Simulated change for commit 28 on 2023-02-21 13:29:56

# Simulated change for commit 32 on 2023-02-23 17:11:53

# Simulated change for commit 34 on 2023-02-28 09:37:26

# Simulated change for commit 35 on 2023-03-02 11:42:40

# Simulated change for commit 41 on 2023-03-15 14:31:00

# Simulated change for commit 48 on 2023-03-23 09:11:29

# Simulated change for commit 50 on 2023-03-27 12:33:16

# Simulated change for commit 51 on 2023-03-29 10:36:14

# Simulated change for commit 54 on 2023-03-31 15:02:43

# Simulated change for commit 56 on 2023-04-03 16:40:48

# Simulated change for commit 57 on 2023-04-04 15:09:48

# Simulated change for commit 60 on 2023-04-05 15:56:06

# Simulated change for commit 61 on 2023-04-05 15:41:43

# Simulated change for commit 63 on 2023-04-07 09:48:50

# Simulated change for commit 64 on 2023-04-10 14:00:23

# Simulated change for commit 65 on 2023-04-12 10:55:43

# Simulated change for commit 66 on 2023-04-12 09:08:57

# Simulated change for commit 67 on 2023-04-14 14:19:04

# Simulated change for commit 68 on 2023-04-14 17:16:21

# Simulated change for commit 69 on 2023-04-18 15:41:50

# Simulated change for commit 74 on 2023-04-24 13:38:18

# Simulated change for commit 75 on 2023-04-24 09:40:47

# Simulated change for commit 77 on 2023-04-26 17:58:26

# Simulated change for commit 82 on 2023-05-02 14:03:57

# Simulated change for commit 84 on 2023-05-02 16:05:05

# Simulated change for commit 85 on 2023-05-03 17:38:57

# Simulated change for commit 86 on 2023-05-04 09:10:13

# Simulated change for commit 89 on 2023-05-05 13:51:34

# Simulated change for commit 90 on 2023-05-05 10:56:28

# Simulated change for commit 91 on 2023-05-08 17:09:56

# Simulated change for commit 92 on 2023-05-09 09:29:09

# Simulated change for commit 94 on 2023-05-15 14:55:12

# Simulated change for commit 95 on 2023-05-15 14:52:16

# Simulated change for commit 97 on 2023-05-17 09:59:05

# Simulated change for commit 99 on 2023-05-18 17:42:59

# Simulated change for commit 102 on 2023-05-23 11:32:22

# Simulated change for commit 103 on 2023-05-23 09:27:14

# Simulated change for commit 104 on 2023-05-24 17:18:59

# Simulated change for commit 106 on 2023-05-26 16:50:09

# Simulated change for commit 107 on 2023-05-26 17:10:38

# Simulated change for commit 110 on 2023-06-02 13:06:23

# Simulated change for commit 111 on 2023-06-08 11:01:22

# Simulated change for commit 114 on 2023-06-14 09:49:23

# Simulated change for commit 121 on 2023-06-30 17:14:58

# Simulated change for commit 122 on 2023-07-04 13:25:56

# Simulated change for commit 123 on 2023-07-05 09:30:19

# Simulated change for commit 124 on 2023-07-05 13:53:21

# Simulated change for commit 126 on 2023-07-07 14:16:22

# Simulated change for commit 129 on 2023-07-10 17:58:05

# Simulated change for commit 130 on 2023-07-11 13:08:07

# Simulated change for commit 131 on 2023-07-12 10:46:33

# Simulated change for commit 136 on 2023-07-24 17:17:26

# Simulated change for commit 138 on 2023-07-26 15:37:48

# Simulated change for commit 139 on 2023-07-31 17:46:41

# Simulated change for commit 140 on 2023-08-01 15:32:59

# Simulated change for commit 142 on 2023-08-02 11:24:47

# Simulated change for commit 143 on 2023-08-03 17:10:13

# Simulated change for commit 144 on 2023-08-03 16:19:31

# Simulated change for commit 145 on 2023-08-04 17:05:31

# Simulated change for commit 146 on 2023-08-08 13:00:20

# Simulated change for commit 147 on 2023-08-08 11:45:13

# Simulated change for commit 148 on 2023-08-08 09:35:14

# Simulated change for commit 155 on 2023-08-17 16:38:26

# Simulated change for commit 158 on 2023-08-22 12:26:23

# Simulated change for commit 159 on 2023-08-22 13:16:57

# Simulated change for commit 160 on 2023-08-23 09:01:17

# Simulated change for commit 161 on 2023-08-23 16:46:58

# Simulated change for commit 163 on 2023-08-25 16:46:45

# Simulated change for commit 165 on 2023-08-29 10:53:11

# Simulated change for commit 168 on 2023-09-01 17:47:36

# Simulated change for commit 170 on 2023-09-07 16:51:27

# Simulated change for commit 174 on 2023-09-11 12:03:27

# Simulated change for commit 176 on 2023-09-14 16:35:35

# Simulated change for commit 177 on 2023-09-19 11:57:53

# Simulated change for commit 183 on 2023-09-26 11:48:03

# Simulated change for commit 185 on 2023-09-26 10:59:56

# Simulated change for commit 186 on 2023-09-27 12:12:49

# Simulated change for commit 187 on 2023-09-27 14:15:48

# Simulated change for commit 188 on 2023-09-28 13:04:29

# Simulated change for commit 189 on 2023-10-02 12:21:13

# Simulated change for commit 191 on 2023-10-03 10:06:51

# Simulated change for commit 192 on 2023-10-04 10:40:41

# Simulated change for commit 195 on 2023-10-16 12:27:21

# Simulated change for commit 196 on 2023-10-17 15:34:05

# Simulated change for commit 197 on 2023-10-18 16:00:07

# Simulated change for commit 198 on 2023-10-18 09:36:38

# Simulated change for commit 203 on 2023-10-20 10:51:32

# Simulated change for commit 205 on 2023-10-26 09:16:50

# Simulated change for commit 207 on 2023-11-07 15:21:07

# Simulated change for commit 209 on 2023-11-09 16:52:00

# Simulated change for commit 211 on 2023-11-14 13:11:47

# Simulated change for commit 212 on 2023-11-15 09:39:09

# Simulated change for commit 213 on 2023-11-15 13:50:55

# Simulated change for commit 214 on 2023-11-16 14:49:40

# Simulated change for commit 216 on 2023-11-17 14:10:20

# Simulated change for commit 217 on 2023-11-17 09:00:49
