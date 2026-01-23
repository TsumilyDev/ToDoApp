# To-Do App Backend

The backend is synchronous and requests will be held until they can be processed by the
backend.

## The Cache
The backend uses a custom Memory class for its cache. The Memory class offers basic
functionality and works greatly as a cache, providing speed and simplicity. It would
be important to note that any functionality not provided by the cache will soon be added
and is being worked on.

## The Database
SQLite3 was used due to its simplicity.

Data Consistencies:
- Time is stored in UNIX time as integers. It is expected to be in seconds.
- Color is stored as an RGB value.
- Completion is broken into three steps: 'not started', 'in-progress', 'completed'

### Tables / Schema

```SQL
CREATE TABLE IF NOT EXISTS accounts (
    -- This should be synced with the clients cookies
    "session_id" TEXT UNIQUE; 
    password TEXT NOT NULL;
    id TEXT PRIMARY KEY;
    email TEXT NOT NULL UNIQUE;
    username TEXT NOT NULL UNIQUE;
    creation_time NUMBER NOT NULL DEFAULT(strftime('%s', 'now'));
    session_id_creation_time NUMBER;
    -- Ranks get translated from strings to numbers by the backend
    role NUMBER; 
    -- Stored as a JSON of 'label_name: text-color'
    labels TEXT; 
);


CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY;
    "description" TEXT;
    account_id TEXT NOT NULL;
    label_name TEXT;
    completion_status TEXT;

    FOREIGN KEY(account_id) REFERENCES accounts(id);
);

CREATE TABLE IF NOT EXISTS deleted_tasks (
    id TEXT PRIMARY KEY;
    "description" TEXT;
    account_id TEXT NOT NULL;
    label_name TEXT;
    completion_status TEXT;
    deletion_time NUMBER NOT NULL DEFAULT(strftime('%s', 'now'));
);


CREATE TABLE IF NOT EXISTS deleted_accounts (
    -- Account Information
    session_id TEXT UNIQUE; 
    account_id TEXT PRIMARY KEY;
    email TEXT NOT NULL;
    username TEXT NOT NULL UNIQUE;
    creation_time NUMBER NOT NULL DEFAULT(strftime('%s', 'now'));
    session_id_creation_time NUMBER;
    role NUMBER;
    -- Deletion Information
    deleted_at NUMBER NOT NULL DEFAULT(strftime('%s', 'now'));
    labels TEXT;
);
```

### Indexes

```SQL 
CREATE INDEX IF NOT EXISTS idx_tasks_account_id
ON tasks(account_id);

CREATE INDEX IF NOT EXISTS idx_deleted_tasks_account_id
ON deleted_tasks(account_id);
```

### Triggers

```SQL
CREATE TRIGGER IF NOT EXISTS deleted_account_tigger (
AFTER DELETE ON accounts
FOR EACH ROW
BEGIN
    INSERT INTO deleted_accounts (
        account_id,
        username,
        email,
        role,
        created_at,
        deleted_at
    )
    VALUES (
        OLD.account_id, 
        OLD.username, 
        OLD.email, 
        OLD.role, 
        OLD.created_at,
        strftime('%s', 'now')
    );
END);

CREATE TRIGGER IF NOT EXISTS delete_task_trigger (
AFTER DELETE ON tasks
FOR EACH ROW
BEGIN
    INSERT INTO deleted_tasks (
        id,
        "description",
        account_id,
        completion_status,
        label_name,
        deletion_time
    )
    VALUES (
        OLD.id,
        OLD.description,
        OLD.account_id,
        OLD.completion_status,
        OLD.label_name,
        strftime('%s', 'now')
    );
END);
```

### Pragma

```SQL
PRAGMA foreign_keys = ON;
PRAGMA temp_store = memory;
PRAGMA cache_size = 3000;
PRAGMA page_size = 4096 -- This is the default.
```

## The Firewall

The firewall serves to filter requests, it is the layer before the actual request
processing.

After reaching the sever the first thing the request experiences is the server firewall.
The firewall exists in order to provide security measures, but also to help with setting
up the context of the request by loading data and initialising many important variables.
The firewall feeds directly into the router.

The firewall is baked into the `BaseHTTPRequestHandler`, it extends it.

The firewall provides these core security and set-up features: request-blocking(blocks it
instantly if it is clearly dangerous); path parsing; request parsing; rate limiting
authorisation-checks.