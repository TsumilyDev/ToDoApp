from typing import Literal, Any
from sqlite3 import (
    Row,
    Error as SqlErr,
    IntegrityError as SqlIntegrityErr,
    connect,
    Cursor,
)
from os import environ
import logging
from http import HTTPStatus

logger = logging.getLogger(__name__)

SQLITE3_PATH = environ["SQLITE3_PATH"]
db = connect(SQLITE3_PATH)
db.row_factory = Row
cursor = db.cursor()

# UPDATE: ADD BUFFERING FOR DB TRANSACTIONS (backendMemory["DBBuffer"], executemany())
# UPDATE: ADD LOGGING FOR DB TRANSACTIONS (logger) -- also configure it


def interact_with_row(
    table: str, column: str, identifier: Any, action: Literal["delete", "select"]
) -> Cursor:
    """Wrapper for interacting with rows.
    Returns the cursor.

    This does not enforce correctness. The caller is still responsible for passing in
    valid information. This will log errors then propagate them.
    """
    try:
        cursor.execute(f"{action} * FROM {table} WHERE {column} = ?", (identifier,))
        db.commit()
        return cursor
    except SqlErr as err:
        db.rollback()
        logger.error(
            f"Experienced an SQL error while doing {action} on a row", exc_info=True
        )
        raise err


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
        execution_append = f"AND {second_search_column} = {second_search_value}"
    try:
        for i in value:
            cursor.execute(
                f"UPDATE {table} SET {column[i]} = ? WHERE {search_column[i]} = ?"
                f"{execution_append}",
                (value[i], search_value[i]),
            )
            if strict and cursor.rowcount < 1:
                raise ValueError(
                    f"{search_value[i]} couldn't be found in {search_column[i]}"
                )
        db.commit()
        return None
    except SqlErr as err:
        db.rollback()
        logger.error("Experienced an SQL error while updating cells", exc_info=True)
        raise err


def insert_row(table: str, columns: tuple[str], values: tuple[str]) -> Cursor:
    """Wrapper for adding rows

    This does not enforce correctness. The caller is still responsible for passing in
    valid information. This will log errors then propogate them.
    """
    try:
        cursor.execute(f"INSERT INTO {table} {columns} VALUES {values}")
        db.commit()
        return cursor
    except SqlErr as err:
        db.rollback()
        logger.error("Experienced an SQL error while inserting a row", exc_info=True)
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
) -> None | Cursor:
    """Wrapper for interacting with rows from the backend server.
    Returns the cursor if succesful, else return None.

    If strict is True, NotFound will be sent when no rows were updated.

    This does not enforce correctness. The caller is still responsible for passing in
    valid information. This will log errors then propagate them.
    """
    try:
        cursor = interact_with_row(table, column, identifier, action)
        if strict and cursor.rowcount < 1:
            self.send_http_response(HTTPStatus.NOT_FOUND)
            return None
        if send_response_on_success:
            self.send_http_response(HTTPStatus.OK, success_msg)
        return cursor
    except SqlIntegrityErr:
        self.send_http_response(HTTPStatus.BAD_REQUEST, user_err_msg)
    except SqlErr:
        self.send_http_response(HTTPStatus.INTERNAL_SERVER_ERROR, server_err_msg)
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
) -> None | bool:
    """Wrapper for inserting rows from the backend server.
    Returns the cursor if succesful, else returns None.

    If strict is True, NotFound will be sent when no rows were updated.

    This does not enforce correctness. The user is still responsible for passing in
    valid information. This will log errors then propagate them.
    """
    try:
        cursor = insert_row(table, columns, values)
        if strict and cursor.rowcount < 1:
            self.send_http_response(HTTPStatus.NOT_FOUND)
            return None
        if send_response_on_success:
            self.send_http_response(HTTPStatus.OK, success_msg)
        return cursor
    except SqlIntegrityErr:
        self.send_http_response(HTTPStatus.BAD_REQUEST, user_err_msg)
    except SqlErr:
        self.send_http_response(HTTPStatus.INTERNAL_SERVER_ERROR, server_err_msg)
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
) -> None:
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
        self.send_http_response(HTTPStatus.INTERNAL_SERVER_ERROR, server_err_msg)
    except ValueError:
        self.send_http_response(HTTPStatus.BAD_REQUEST, user_err_msg)
    return None
