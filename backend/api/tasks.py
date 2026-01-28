"""
REST API handlers for tasks.

This module provides HTTP request handlers for the tasks API endpoints.
Handlers follow the existing request_handler pattern used in the codebase.
"""

import json
import re
from http import HTTPStatus
from urllib.parse import parse_qs, urlparse
from backend.db import tasks as tasks_db


def read_json_body(handler):
    """
    Read and parse JSON from request body.
    
    Args:
        handler: HTTP request handler instance
    
    Returns:
        Parsed JSON dictionary or None if invalid
    """
    try:
        content_length = int(handler.headers.get('Content-Length', 0))
        if content_length == 0:
            return {}
        
        body = handler.rfile.read(content_length)
        return json.loads(body.decode('utf-8'))
    except (ValueError, json.JSONDecodeError):
        return None


def send_json_response(handler, status, data):
    """
    Send a JSON response.
    
    Args:
        handler: HTTP request handler instance
        status: HTTP status code
        data: Dictionary to serialize as JSON
    """
    body = json.dumps(data).encode('utf-8')
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json')
    handler.send_header('Content-Length', len(body))
    handler.end_headers()
    handler.wfile.write(body)


def send_error_response(handler, status, message):
    """
    Send an error JSON response.
    
    Args:
        handler: HTTP request handler instance
        status: HTTP status code
        message: Error message string
    """
    send_json_response(handler, status, {"error": message})


# ========================================
# INTERNAL HANDLERS
# ========================================

def _get_tasks_list(handler):
    """GET /api/tasks?query=<string>"""
    try:
        # Parse query parameters
        parsed = urlparse(handler.path)
        query_params = parse_qs(parsed.query)
        search_query = query_params.get('query', [None])[0]
        
        # Fetch tasks from database
        tasks = tasks_db.get_tasks(user_id=1, query=search_query)
        
        send_json_response(handler, HTTPStatus.OK, {"tasks": tasks})
    except Exception as e:
        send_error_response(handler, HTTPStatus.INTERNAL_SERVER_ERROR, str(e))


def _post_task_create(handler):
    """POST /api/tasks"""
    try:
        data = read_json_body(handler)
        if data is None:
            send_error_response(handler, HTTPStatus.BAD_REQUEST, "Invalid JSON")
            return
        
        title = data.get('title', '').strip()
        if not title:
            send_error_response(handler, HTTPStatus.BAD_REQUEST, "Title is required")
            return
        
        labels = data.get('labels', [])
        if not isinstance(labels, list):
            send_error_response(handler, HTTPStatus.BAD_REQUEST, "Labels must be an array")
            return
        
        # Create task in database
        task = tasks_db.create_task(user_id=1, title=title, labels=labels)
        
        send_json_response(handler, HTTPStatus.CREATED, task)
    except ValueError as e:
        send_error_response(handler, HTTPStatus.BAD_REQUEST, str(e))
    except Exception as e:
        send_error_response(handler, HTTPStatus.INTERNAL_SERVER_ERROR, str(e))


def _patch_task_update(handler, task_id):
    """PATCH /api/tasks/<id>"""
    try:
        data = read_json_body(handler)
        if data is None:
            send_error_response(handler, HTTPStatus.BAD_REQUEST, "Invalid JSON")
            return
        
        # Extract update fields
        title = data.get('title')
        completed = data.get('completed')
        labels = data.get('labels')
        
        # Validate types
        if title is not None and not isinstance(title, str):
            send_error_response(handler, HTTPStatus.BAD_REQUEST, "Title must be a string")
            return
        
        if completed is not None and not isinstance(completed, bool):
            send_error_response(handler, HTTPStatus.BAD_REQUEST, "Completed must be a boolean")
            return
        
        if labels is not None and not isinstance(labels, list):
            send_error_response(handler, HTTPStatus.BAD_REQUEST, "Labels must be an array")
            return
        
        # Update task in database
        task = tasks_db.update_task(
            task_id=task_id,
            user_id=1,
            title=title,
            completed=completed,
            labels=labels
        )
        
        if task is None:
            send_error_response(handler, HTTPStatus.NOT_FOUND, "Task not found")
            return
        
        send_json_response(handler, HTTPStatus.OK, task)
    except ValueError as e:
        send_error_response(handler, HTTPStatus.BAD_REQUEST, str(e))
    except Exception as e:
        send_error_response(handler, HTTPStatus.INTERNAL_SERVER_ERROR, str(e))


def _delete_task_by_id(handler, task_id):
    """DELETE /api/tasks/<id>"""
    try:
        # Delete task from database
        deleted = tasks_db.delete_task(task_id=task_id, user_id=1)
        
        if not deleted:
            send_error_response(handler, HTTPStatus.NOT_FOUND, "Task not found")
            return
        
        send_json_response(handler, HTTPStatus.OK, {"ok": True})
    except Exception as e:
        send_error_response(handler, HTTPStatus.INTERNAL_SERVER_ERROR, str(e))


# ========================================
# MAIN API ROUTER
# ========================================

def api_tasks_handler(handler):
    """
    Main router for /api/tasks/* endpoints.
    
    This handler routes to the appropriate internal handler based on
    the HTTP method and path pattern.
    """
    method = handler.command
    path = handler.path.split('?')[0]  # Remove query string for matching
    
    # GET /api/tasks or /api/tasks?query=...
    if method == 'GET' and path == '/api/tasks':
        _get_tasks_list(handler)
        return
    
    # POST /api/tasks
    if method == 'POST' and path == '/api/tasks':
        _post_task_create(handler)
        return
    
    # PATCH /api/tasks/<id>
    if method == 'PATCH':
        match = re.match(r'^/api/tasks/(\d+)$', path)
        if match:
            task_id = int(match.group(1))
            _patch_task_update(handler, task_id)
            return
    
    # DELETE /api/tasks/<id>
    if method == 'DELETE':
        match = re.match(r'^/api/tasks/(\d+)$', path)
        if match:
            task_id = int(match.group(1))
            _delete_task_by_id(handler, task_id)
            return
    
    # No route matched
    send_error_response(handler, HTTPStatus.NOT_FOUND, "Endpoint not found")

