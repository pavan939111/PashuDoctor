import kagglehub
import os

try:
    # Try to resolve a dataset that might be public to see if auth works
    path = kagglehub.dataset_download("devang03mgr/cattle-diseases-datasets")
    print(f"Auth check successful. Path: {path}")
except Exception as e:
    print(f"Auth check failed: {e}")
