# The structure of this is:
# routes(root) = {
#     'method': {
#         route: handler
#         route: handler
#         route: handler
#     }
#
#     'method': {
#         route: handler
#         route: handler
#         route: handler
#     }
# }

from backend.router.firewall import ROLES
from backend.handlers.tasks import (
    get_task_handler,
    patch_task_handler,
    delete_task_handler,
    post_task_handler,
    get_task_label_handler,
    patch_task_label_handler,
    delete_task_label_handler,
    post_task_label_handler,
)
from backend.handlers.accounts import (
    get_account_handler,
    patch_account_handler,
    delete_account_handler,
    post_account_handler,
    get_session_handler,
    post_session_handler,
    delete_session_handler,
)

# This should only contain routes that exist.
# This also returns resources, but resources may need to be handled seperately for
# better scalability and maintainability. You can diffrentiate if the value is a
# source or a handler by checking if the value is a dict(resource) or a string(handler).
# This approach for routes is preferred because it also allows us to easily store
# metadata for every route.
routes = {
    # UPDATE: Remove the Bytes value, first ensure that the firewall is ok with that
    # Dicts are assumed to be resources and tuples are assumed to be functions.
    "GET": {
        "/home": {
            "path": ".../.../public/html/home.html",
            "type": "text/html",
            "bytes": False,
        },
        "/about": {
            "path": ".../.../public/html/about.html",
            "type": "text/html",
            "bytes": False,
        },
        "/signup": {
            "path": ".../.../public/html/signup.html",
            "type": "text/html",
            "bytes": False,
        },
        "/home.css": {
            "path": ".../.../src/css/home.css",
            "type": "style/css",
            "bytes": False,
        },
        "/about.css": {
            "path": ".../.../src/css/about.css",
            "type": "style/css",
            "bytes": False,
        },
        "/signup.css": {
            "path": ".../.../src/css/signup.css",
            "type": "style/css",
            "bytes": False,
        },
        "/home.js": {
            "path": ".../.../src/js/home.js",
            "type": "application/javascript",
            "bytes": False,
        },
        "/about.js": {
            "path": ".../.../src/js/about.js",
            "type": "application/javascript",
            "bytes": False,
        },
        "/signup.js": {
            "path": ".../.../src/js/signup.js",
            "type": "application/javascript",
            "bytes": False,
        },
        "/task": (get_task_handler, ROLES["account"]),
        "/task-label": (get_task_label_handler, ROLES["account"]),
        "/account": (get_account_handler, ROLES["account"]),
        "/session": (get_session_handler, ROLES["account"]),
    },
    "POST": {
        "/task": (post_task_handler, ROLES["account"]),
        "/task-label": (post_task_label_handler, ROLES["account"]),
        "/account": (post_account_handler, ROLES["public"]),
        "/session": (post_session_handler, ROLES["public"]),
    },
    "PATCH": {
        "/task": (patch_task_handler, ROLES["account"]),
        "/task-label": (patch_task_label_handler, ROLES["account"]),
        "/account": (patch_account_handler, ROLES["account"]),
    },
    "DELETE": {
        "/task": (delete_task_handler, ROLES["account"]),
        "/task-label": (delete_task_label_handler, ROLES["account"]),
        "/account": (delete_account_handler, ROLES["account"]),
        "/session": (delete_session_handler, ROLES["account"]),
    },
}

