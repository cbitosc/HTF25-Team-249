import joblib
from sklearn.linear_model import LinearRegression
import numpy as np
import os

print("Creating dummy ML model...")

# Create a simple fake model
X = np.array([[50], [100], [150]])
y = np.array([100, 200, 300])
dummy_model = LinearRegression()
dummy_model.fit(X, y)

# Save it inside the 'app' folder
save_path = os.path.join(os.path.dirname(__file__), "app", "crowd_predictor.pkl")
joblib.dump(dummy_model, save_path)

print(f"✅ Dummy model saved to: {save_path}")