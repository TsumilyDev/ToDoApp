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
        "/app": {
            "path": "public/html/app.html",
            "type": "text/html",
            "bytes": False,
            "min_role": ROLES["account"],
        },
        "/about": {
            "path": "public/html/about.html",
            "type": "text/html",
            "bytes": False,
        },
        "/account": {
            "path": "public/html/account.html",
            "type": "text/html",
            "bytes": False,
        },
        "/app.css": {
            "path": "src/css/app.css",
            "type": "style/css",
            "bytes": False,
        },
        "/about.css": {
            "path": "src/css/about.css",
            "type": "style/css",
            "bytes": False,
        },
        "/account.css": {
            "path": "src/css/account.css",
            "type": "style/css",
            "bytes": False,
        },
        "/app.js": {
            "path": "src/js/app.js",
            "type": "application/javascript",
            "bytes": False,
        },
        "/about.js": {
            "path": "src/js/about.js",
            "type": "application/javascript",
            "bytes": False,
        },
        "/account.js": {
            "path": "src/js/account.js",
            "type": "application/javascript",
            "bytes": False,
        },
        "/logo.png": {
            "path": "public/media/logo.png",
            "type": "image/png",
            "bytes": True,
        },
        "/task/information": (get_task_handler, ROLES["account"]),
        "/task-label/information": (
            get_task_label_handler,
            ROLES["account"],
        ),
        "/account/information": (get_account_handler, ROLES["account"]),
        "/session": (get_session_handler, ROLES["account"]),
    },
    "POST": {
        "/task/create": (post_task_handler, ROLES["account"]),
        "/task-label/create": (post_task_label_handler, ROLES["account"]),
        "/account/create": (post_account_handler, ROLES["public"]),
        "/session/create": (post_session_handler, ROLES["public"]),
    },
    "PATCH": {
        "/task/update": (patch_task_handler, ROLES["account"]),
        "/task-label/update": (patch_task_label_handler, ROLES["account"]),
        "/account/update": (patch_account_handler, ROLES["account"]),
    },
    "DELETE": {
        "/task/delete": (delete_task_handler, ROLES["account"]),
        "/task-label/delete": (
            delete_task_label_handler,
            ROLES["account"],
        ),
        "/account/delete": (delete_account_handler, ROLES["account"]),
        "/session/delete": (delete_session_handler, ROLES["account"]),
    },
}
