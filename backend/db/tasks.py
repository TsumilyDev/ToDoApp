"""
Database operations for tasks.

This module handles all SQLite operations for the tasks table,
isolated from the main application logic.
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path


def get_db_path():
    """Get database path from environment or use default."""
    return os.environ.get("SQLITE3_PATH", "./data/todo.db")


def get_connection():
    """Get a database connection."""
    db_path = get_db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_tasks_table():
    """Create tasks table if it doesn't exist."""
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                labels_json TEXT NOT NULL DEFAULT '[]',
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()


def get_tasks(user_id=1, query=None):
    """
    Get all tasks for a user, optionally filtered by query.
    
    Args:
        user_id: User ID (default 1)
        query: Optional search string to filter by title or labels
    
    Returns:
        List of task dictionaries sorted by completion status and date
    """
    conn = get_connection()
    try:
        sql = """
            SELECT id, user_id, title, labels_json, completed, created_at, updated_at
            FROM tasks
            WHERE user_id = ?
        """
        params = [user_id]
        
        if query:
            sql += """ AND (
                title LIKE ? OR labels_json LIKE ?
            )"""
            search_term = f"%{query}%"
            params.extend([search_term, search_term])
        
        # Sort: incomplete first, then by created_at DESC within each group
        sql += """
            ORDER BY completed ASC, created_at DESC
        """
        
        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
        
        tasks = []
        for row in rows:
            task = {
                "id": row["id"],
                "title": row["title"],
                "completed": bool(row["completed"]),
                "labels": json.loads(row["labels_json"]) if row["labels_json"] else [],
                "createdAt": row["created_at"],
                "updatedAt": row["updated_at"]
            }
            tasks.append(task)
        
        return tasks
    finally:
        conn.close()


def create_task(user_id=1, title="", labels=None):
    """
    Create a new task.
    
    Args:
        user_id: User ID (default 1)
        title: Task title
        labels: List of label strings (optional)
    
    Returns:
        Created task dictionary
    """
    if not title or not title.strip():
        raise ValueError("Task title cannot be empty")
    
    conn = get_connection()
    try:
        now = datetime.utcnow().isoformat() + "Z"
        labels_json = json.dumps(labels if labels else [])
        
        cursor = conn.execute("""
            INSERT INTO tasks (user_id, title, labels_json, completed, created_at, updated_at)
            VALUES (?, ?, ?, 0, ?, ?)
        """, [user_id, title.strip(), labels_json, now, now])
        
        conn.commit()
        task_id = cursor.lastrowid
        
        # Fetch the created task
        cursor = conn.execute("""
            SELECT id, user_id, title, labels_json, completed, created_at, updated_at
            FROM tasks WHERE id = ?
        """, [task_id])
        
        row = cursor.fetchone()
        return {
            "id": row["id"],
            "title": row["title"],
            "completed": bool(row["completed"]),
            "labels": json.loads(row["labels_json"]),
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"]
        }
    finally:
        conn.close()


def update_task(task_id, user_id=1, title=None, completed=None, labels=None):
    """
    Update an existing task.
    
    Args:
        task_id: Task ID to update
        user_id: User ID (default 1)
        title: New title (optional)
        completed: New completion status (optional)
        labels: New labels list (optional)
    
    Returns:
        Updated task dictionary or None if not found
    """
    conn = get_connection()
    try:
        # Check if task exists and belongs to user
        cursor = conn.execute("""
            SELECT id FROM tasks WHERE id = ? AND user_id = ?
        """, [task_id, user_id])
        
        if not cursor.fetchone():
            return None
        
        # Build update query dynamically
        updates = []
        params = []
        
        if title is not None:
            if not title.strip():
                raise ValueError("Task title cannot be empty")
            updates.append("title = ?")
            params.append(title.strip())
        
        if completed is not None:
            updates.append("completed = ?")
            params.append(1 if completed else 0)
        
        if labels is not None:
            updates.append("labels_json = ?")
            params.append(json.dumps(labels))
        
        if not updates:
            # No updates, just return current task
            cursor = conn.execute("""
                SELECT id, user_id, title, labels_json, completed, created_at, updated_at
                FROM tasks WHERE id = ?
            """, [task_id])
            row = cursor.fetchone()
            return {
                "id": row["id"],
                "title": row["title"],
                "completed": bool(row["completed"]),
                "labels": json.loads(row["labels_json"]),
                "createdAt": row["created_at"],
                "updatedAt": row["updated_at"]
            }
        
        # Update timestamp
        now = datetime.utcnow().isoformat() + "Z"
        updates.append("updated_at = ?")
        params.append(now)
        
        # Add WHERE clause params
        params.extend([task_id, user_id])
        
        sql = f"""
            UPDATE tasks
            SET {', '.join(updates)}
            WHERE id = ? AND user_id = ?
        """
        
        conn.execute(sql, params)
        conn.commit()
        
        # Fetch updated task
        cursor = conn.execute("""
            SELECT id, user_id, title, labels_json, completed, created_at, updated_at
            FROM tasks WHERE id = ?
        """, [task_id])
        
        row = cursor.fetchone()
        return {
            "id": row["id"],
            "title": row["title"],
            "completed": bool(row["completed"]),
            "labels": json.loads(row["labels_json"]),
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"]
        }
    finally:
        conn.close()


def delete_task(task_id, user_id=1):
    """
    Delete a task.
    
    Args:
        task_id: Task ID to delete
        user_id: User ID (default 1)
    
    Returns:
        True if deleted, False if not found
    """
    conn = get_connection()
    try:
        cursor = conn.execute("""
            DELETE FROM tasks
            WHERE id = ? AND user_id = ?
        """, [task_id, user_id])
        
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# Initialize table on module import
init_tasks_table()
