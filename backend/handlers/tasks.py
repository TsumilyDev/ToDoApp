# Task Handlers


def get_all_tasks_handler(self) -> None:
    """
    Responds with all the user-allowed information about every task stored in the
    database.
    """
    ...


def delete_task_handler(self) -> None: ...


def post_task_handler(self) -> None: ...


def patch_task_handler(self) -> None:
    """
    Allows the user to update the specified task. task updates are generally about
    editing the name of the label or changing its color.
    """
    ...


def get_task_handler(self) -> None:
    """
    Responds with all the user-allowed information about that task stored in the
    database.
    """
    ...


# Task Label Handlers


def get_task_label_handler(self) -> None:
    """
    Responds with all the user-allowed information about that label stored in the
    database.
    """
    ...


def delete_task_label_handler(self) -> None:
    """
    Allows the user to delete a label for a tasks from the database.
    """
    ...


def post_task_label_handler(self) -> None:
    """
    Allows the user to create a label for tasks in the database. The user is required
    to provide
    """
    ...


def patch_task_label_handler(self) -> None:
    """
    Allows the user to update the specified label. Label updates are generally about
    editing the name of the label or changing its color.
    """
    ...


def get_all_task_labels_handler(self) -> None: ...
