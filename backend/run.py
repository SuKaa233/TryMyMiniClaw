#!/usr/bin/env python
"""Entry point to run the backend server"""
import sys
import os

# Ensure the backend directory is in the path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Change to backend directory
os.chdir(backend_dir)

# Now import and run
import uvicorn

if __name__ == "__main__":
    print(f"Starting server from: {backend_dir}")
    print(f"Python path includes: {backend_dir}")
    uvicorn.run("app:app", host="0.0.0.0", port=8002, reload=True)
