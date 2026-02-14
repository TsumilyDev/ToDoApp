from typing import Literal, Any
from sqlite3 import (
    Row,
    Error as SqlErr,
    IntegrityError as SqlIntegrityErr,
    connect,
    Cursor,
)
import logging
from http import HTTPStatus
from dotenv import load_dotenv
from os import environ
from os.path import dirname
import os
from pathlib import Path

load_dotenv(dirname(__file__) + r"\..\..\.env")
logger = logging.getLogger(__name__)

# Get database path from environment with default fallback
SQLITE3_PATH = environ.get("SQLITE3_PATH", "./data/todo.db")

# Validate database path and ensure directory exists
try:
    db_path = Path(SQLITE3_PATH).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not os.access(db_path.parent, os.W_OK):
        raise RuntimeError(f"No write permission for database directory: {db_path.parent}")
    
    db = connect(str(db_path))
except Exception as e:
    logger.error(f"Failed to initialize database at {SQLITE3_PATH}: {e}")
    raise

db.row_factory = Row
cursor = db.cursor()


def init_accounts_table() -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS accounts (
            session_id TEXT UNIQUE,
            password TEXT NOT NULL,
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            username TEXT NOT NULL UNIQUE,
            creation_time INTEGER NOT NULL DEFAULT(strftime('%s', 'now')),
            session_id_creation_time INTEGER,
            role INTEGER NOT NULL DEFAULT 1,
            labels TEXT
        )
        """
    )
    db.commit()


init_accounts_table()

# UPDATE: ADD BUFFERING FOR DB TRANSACTIONS (backendMemory["DBBuffer"], executemany())
# UPDATE: ADD LOGGING FOR DB TRANSACTIONS (logger) -- also configure it


def interact_with_row(
    table: str,
    column: str,
    identifier: Any,
    action: Literal["delete", "select"],
) -> Cursor:
    """Wrapper for interacting with rows.
    Returns the cursor.

    This does not enforce correctness. The caller is still responsible for passing in
    valid information. This will log errors then propagate them.
    """
    try:
        cursor.execute(
            f"{action} * FROM {table} WHERE {column} = ?", (identifier,)
        )
        db.commit()
        return cursor
    except SqlErr as err:
        db.rollback()
        logger.error(
            f"Experienced an SQL error while doing {action} on a row",
            exc_info=True,
        )
        raise err


# UPDATE: Make this return the rows on success
def update_cells(
    table: str,
    search_column: list[str],
    search_value: list[Any],
    column: list[str],
    value: list[Any],
    *,
    strict: bool = True,
    second_search_column: str | None = None,
    second_search_value: str | None = None,
) -> None:
    """Wrapper for updating cells. Returns None.

    If strict is True, ValueError will be raised when the search_value wasn't found in
    the search_column.

    This does not enforce correctness. The caller is still responsible for passing in
    valid information. This will log errors then propogate them.
    """
    execution_append = ""
    if second_search_column is not None:
        execution_append = (
            f"AND {second_search_column} = {second_search_value}"
        )
    try:
        for i in range(len(value)):
            cursor.execute(
                f"UPDATE {table} SET {column[i]} = ? WHERE {search_column[i]} = ?"
                f"{execution_append}",
                (value[i], search_value[i]),
            )
            if strict and len(cursor.fetchall()) > 1:
                raise ValueError(
                    f"{search_value[i]} couldn't be found in {search_column[i]}"
                )
        db.commit()
        return None
    except SqlErr as err:
        db.rollback()
        logger.error(
            "Experienced an SQL error while updating cells", exc_info=True
        )
        raise err


# UPDATE: Make this return the rows on success
def update_cell(
    table: str,
    search_column: str,
    search_value: Any,
    column: str,
    value: Any,
    *,
    strict: bool = True,
    second_search_column: str | None = None,
    second_search_value: str | None = None,
) -> None:
    """Wrapper for updating one cell. Returns None.

    If strict is True, ValueError will be raised when the search_value wasn't found in
    the search_column.

    This does not enforce correctness. The caller is still responsible for
    passing in valid information. This will log errors then propogate them.
    """
    execution_append = ""
    if second_search_column is not None:
        execution_append = (
            f"AND {second_search_column} = {second_search_value}"
        )
    try:
        cursor.execute(
            f"UPDATE {table} SET {column} = ? WHERE {search_column} = ?"
            f"{execution_append}",
            (value, search_value),
        )
        if strict and len(cursor.fetchall()) > 1:
            raise ValueError(
                f"{search_value} couldn't be found in {search_column}"
            )
        db.commit()
        return None
    except SqlIntegrityErr:
        db.rollback()
        raise err
    except SqlErr as err:
        db.rollback()
        logger.error(
            "Experienced an SQL error while updating cells", exc_info=True
        )
        raise err


def insert_row(
    table: str, columns: tuple[str], values: tuple[Any, ...]
) -> Cursor:
    """Wrapper for adding rows

    This does not enforce correctness. The caller is still responsible for passing in
    valid information. This will log errors then propogate them.
    """
    try:
        if len(columns) != len(values):
            raise ValueError("Column/value length mismatch")
        column_list = ", ".join(columns)
        placeholders = ", ".join("?" for _ in values)
        cursor.execute(
            f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})",
            values,
        )
        db.commit()
        return cursor
    except SqlIntegrityErr:
        db.rollback()
        raise err
    except SqlErr as err:
        db.rollback()
        logger.error(
            "Experienced an SQL error while inserting a row", exc_info=True
        )
        raise err


def server_interact_with_row(
    self,
    table: str,
    column: str,
    identifier: Any,
    action: Literal["delete", "select"],
    *,
    strict: bool = True,
    user_err_msg: str = "Invalid Information",
    server_err_msg: str = "",
    send_response_on_success: bool = False,
    success_msg: str = "",
) -> None | dict | list:
    """Wrapper for interacting with rows from the backend server.
    Returns the row(s) if succesful, else return None.

    If strict is True, NotFound will be sent when no rows were updated.

    This does not enforce correctness. The caller is still responsible for 
    passing in valid information. This will log errors then propagate them.
    """
    try:
        cursor = interact_with_row(table, column, identifier, action)
        rows = cursor.fetchall()
        if strict and len(rows) > 1:
            print("I knewww it")
            self.send_http_response(HTTPStatus.NOT_FOUND)
            return None
        if send_response_on_success:
            self.send_http_response(HTTPStatus.OK, success_msg)
        if len(rows) == 1:
            return rows[0]
        return rows
    except SqlIntegrityErr:
        self.send_http_response(HTTPStatus.BAD_REQUEST, user_err_msg)
    except SqlErr:
        self.send_http_response(
            HTTPStatus.INTERNAL_SERVER_ERROR, server_err_msg
        )
    return None


def server_insert_row(
    self,
    table: str,
    columns: tuple[str],
    values: tuple[Any],
    *,
    strict: bool = True,
    user_err_msg: str = "",
    server_err_msg: str = "",
    send_response_on_success: bool = False,
    success_msg: str = "",
) -> None | dict:
    """Wrapper for inserting rows from the backend server.
    Returns the row(s) if succesful, else returns None.

    If strict is True, NotFound will be sent when no rows were updated.

    This does not enforce correctness. The user is still responsible for passing in
    valid information. This will log errors then propagate them.
    """
    try:
        cursor = insert_row(table, columns, values)
        rows = cursor.fetchall()
        if strict and len(rows) > 1:
            self.send_http_response(HTTPStatus.NOT_FOUND)
            return None
        if send_response_on_success:
            self.send_http_response(HTTPStatus.OK, success_msg)
        return rows
    except SqlIntegrityErr:
        self.send_http_response(HTTPStatus.BAD_REQUEST, user_err_msg)
    except SqlErr:
        self.send_http_response(
            HTTPStatus.INTERNAL_SERVER_ERROR, server_err_msg
        )
    return None


def server_update_cells(
    self,
    table: str,
    search_column: str,
    search_value: str,
    column: str,
    value: str,
    *,
    strict: bool = True,
    second_search_column: str | None = None,
    second_search_value: str | None = None,
    user_err_msg: str = "",
    server_err_msg: str = "",
    send_response_on_success: bool = False,
    success_msg: str = "",
) -> None | bool:
    """Wrapper for updating cells from the backend server.
    Returns True if succesful, else returns None.

    If strict is True, ValueError will be raised when the search_value wasn't found in
    the search_column.

    This does not enforce correctness. The user is still responsible for passing in
    valid information. This will log errors then propagate them.
    """
    try:
        update_cells(
            table,
            search_column,
            search_value,
            column,
            value,
            strict=strict,
            second_search_column=second_search_column,
            second_search_value=second_search_value,
        )
        if send_response_on_success:
            self.send_http_response(HTTPStatus.OK, success_msg)
        return True
    except SqlIntegrityErr:
        self.send_http_response(HTTPStatus.BAD_REQUEST, user_err_msg)
    except SqlErr:
        self.send_http_response(
            HTTPStatus.INTERNAL_SERVER_ERROR, server_err_msg
        )
    except ValueError:
        self.send_http_response(HTTPStatus.BAD_REQUEST, user_err_msg)
    return None
