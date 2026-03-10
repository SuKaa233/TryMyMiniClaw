#!/usr/bin/env python
"""Test script to start the backend server"""
import sys
import os

# Add backend directory to path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'miniclaw', 'backend')
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

print(f"Python path: {sys.path}")
print(f"Working directory: {os.getcwd()}")
print(f"Backend dir: {backend_dir}")

try:
    import app
    print("Successfully imported app module")
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8002, reload=True)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
