
import mlflow
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

if __name__ == "__main__":
    with mlflow.start_run():
        # Prepare data
        X = np.array([[1], [2], [3], [4], [5]])
        y = np.array([2, 4, 5, 4, 5])

        # Train model
        model = LinearRegression()
        model.fit(X, y)

        # Evaluate model
        predictions = model.predict(X)
        rmse = np.sqrt(mean_squared_error(y, predictions))

        # Log parameters and metrics
        mlflow.log_param("model_type", "LinearRegression")
        mlflow.log_metric("rmse", rmse)

        print(f"MLflow experiment logged with RMSE: {rmse}")
