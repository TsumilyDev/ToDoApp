"""Test script for API endpoints."""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_create_task():
    """Test POST /api/tasks"""
    print("Testing POST /api/tasks...")
    url = f"{BASE_URL}/api/tasks"
    data = {"title": "Test task 1", "labels": ["urgent", "work"]}
    
    try:
        response = requests.post(url, json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_get_tasks():
    """Test GET /api/tasks"""
    print("\nTesting GET /api/tasks...")
    url = f"{BASE_URL}/api/tasks"
    
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_update_task(task_id):
    """Test PATCH /api/tasks/<id>"""
    print(f"\nTesting PATCH /api/tasks/{task_id}...")
    url = f"{BASE_URL}/api/tasks/{task_id}"
    data = {"completed": True}
    
    try:
        response = requests.patch(url, json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_delete_task(task_id):
    """Test DELETE /api/tasks/<id>"""
    print(f"\nTesting DELETE /api/tasks/{task_id}...")
    url = f"{BASE_URL}/api/tasks/{task_id}"
    
    try:
        response = requests.delete(url)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    print("Make sure the server is running on http://localhost:8000\n")
    
    # Create a task
    task = test_create_task()
    if task and 'id' in task:
        task_id = task['id']
        
        # Get all tasks
        test_get_tasks()
        
        # Update the task
        test_update_task(task_id)
        
        # Delete the task
        test_delete_task(task_id)
        
        # Verify deletion
        test_get_tasks()
