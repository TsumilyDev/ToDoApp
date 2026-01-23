
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

# This should only contain routes that exist.
# This also returns resources, but resources may need to be handled seperately for
# better scalability and maintainability. You can diffrentiate if the value is a
# source or a handler by checking if the value is a dict(resource) or a string(handler).
# This approach for routes is preferred because it also allows us to easily store
# metadata for every route.
routes = {
    # UPDATE: Remove the Bytes value, first ensure that the firewall is ok with that
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
        "/task": "get_task_handler",
        "/task-label": "get_task_label_handler",
        "/account": "get_account_handler",
        },
    "POST": {
        "/task": "post_task_handler",
        "/task-label": "post_task_label_handler",
        "/account": "post_account_handler",
    },
    "PATCH": {
        "/task": "patch_task_handler",
        "/task-label": "patch_task_label_handler",
        "/account": "patch_account_handler",
    },
    "DELETE": {
        "/task": "delete_task_handler",
        "/task-label": "delete_task_label_handler",
        "/account": "delete_account_handler"
    },
}


def get_all_routes_for_method(method: str) -> str | dict: {

}