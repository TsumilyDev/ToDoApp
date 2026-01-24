from typing import Literal, Any
from sqlite3 import (
    Row,
    Error as SqlErr,
    IntegrityError as SqlIntegrityErr,
    connect,
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
        table:str,
        column:str,
        identifier:Any,
        action:Literal["delete", "select"]
        ) -> None | list[Any]:
    """Wrapper for interacting with rows.
    Returns None for `delete`. Returns the values for `select`.

    This does not enforce correctness. The user is still responsible for passing
    valid information. This will log errors then propagate them. 
    """
    try:
        cursor.execute(f"{action} * FROM {table} WHERE {column} = ?", (identifier,))
        db.commit()
        if action == "select":
            return cursor.fetchall()
        return None
    except SqlErr as err:
        db.rollback()
        logger.error(
            f"Experienced an SQL error while doing {action} on a row",
            exc_info=True)
        raise err 

# UPDATE : MAKE THIS BE ABLE TO HANDLE SEVERAL UPDATES AT ONCE
def update_cell(table:str, column:str, identifier:Any) -> None:
    """Wrapper for updating cells

    This does not enforce correctness. The user is still responsible for passing
    valid information. This will log errors then propogate them.
    """
    if len(column) != len(identifier):
        err_msg = ("Expected column and identifier lengths to be equal, but" \
                   f"{len(column)} for column and {len(identifier)} for identifier")
        logger.error(err_msg, exc_info=True)
        raise ValueError(err_msg)
 
    try:
        cursor.execute(f"UPDATE table SET ? = ? WHERE ? = ?", (table, column, identifier))
        db.commit()
        return None
    except SqlErr as err:
        db.rollback()
        logger.error(f"Experienced an SQL error while updating a cell", exc_info=True)
        raise err 


def insert_row(
        table:str,
        columns:tuple[str],
        values:tuple[str]
        ) -> None:
    """Wrapper for adding rows

    This does not enforce correctness. The user is still responsible for passing
    valid information. This will log errors then propogate them.
    """
    try:
        cursor.execute(f"INSERT INTO {table} {columns} VALUES {values}")
        db.commit()
        return None
    except SqlErr as err:
        db.rollback()
        logger.error(f"Experienced an SQL error while inserting a row", exc_info=True)
        raise err


def server_interact_with_row(
        self,
        table:str,
        column:str,
        identifier:Any,
        action:Literal["delete", "select"],
        *,
        user_err_msg="",
        server_err_msg=""
        ) -> None | list[Any]:
    """Wrapper for interacting with rows.
    Returns None for `delete`. Returns the values for `select`.

    This does not enforce correctness. The user is still responsible for passing
    valid information. This will log errors then propagate them. 
    """
    try:
        interact_with_row(table, column, identifier, action)
    except SqlIntegrityErr:
        ...
        self.send_http_response(
            HTTPStatus.BAD_REQUEST, "This Phone Number Or Email Is Already In Use"
        )