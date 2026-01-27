# To-Do App Backend

The backend is synchronous and requests will be held until they can be processed by the
backend.

## Backend Design And Code Conventions

All input are in JSON format, but outputs may vary if the code isn't 200. All outputs 
with the code 200 are in JSON format.

In order to make it easy to denote the duties of functions, there are a few conventions
that are used.
- The suffix '_handler' means the function is a handler. Nothing significant is executed
after handlers.
- The prefix 'server_' means the function will send HTTP_responses in failure cases, 
although it may have an arguement enabling success cases to also be sent. 

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

Potential Considerations For The Future:
- This curently only allows one session per account. Consider enabling multi-session
functionality unless explicitly disabled by the user
- JSON indexing, for the labels
- Composite indexing

### Tables / Schema

```SQL
CREATE TABLE IF NOT EXISTS accounts (
    -- This should be synced with the clients cookies
    "session_id" TEXT UNIQUE, 
    password TEXT NOT NULL,
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    creation_time INTEGER NOT NULL DEFAULT(strftime('%s', 'now')),
    session_id_creation_time INTEGER,
    -- Ranks get translated from strings to numbers by the backend
    role INTEGER CHECK (
        role BETWEEN 0 AND 8
    ), 
    -- Stored as a JSON of 'label_name: text-color'
    labels TEXT
);


CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    "description" TEXT,
    account_id INTEGER NOT NULL,
    label_name TEXT,
    creation_time INTEGER NOT NULL DEFAULT(strftime('%s', 'now')),
    completion_status TEXT NOT NULL CHECK (
        completion_status IN ('not started', 'in-progress', 'completed')
    ),

    FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS deleted_tasks (
    id TEXT PRIMARY KEY,
    "description" TEXT,
    account_id TEXT NOT NULL,
    label_name TEXT,
    creation_time INTEGER NOT NULL,
    completion_status TEXT NOT NULL CHECK (
        completion_status IN ('not started', 'in-progress', 'completed')
    ),
    deletion_time INTEGER NOT NULL DEFAULT(strftime('%s', 'now'))
) WITHOUT ROWID;


CREATE TABLE IF NOT EXISTS deleted_accounts (
    -- Account Information
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    username TEXT NOT NULL,
    creation_time INTEGER NOT NULL,
    session_id_creation_time INTEGER, -- This is the last login time
    role INTEGER,
    -- Deletion Information
    deleted_at INTEGER NOT NULL DEFAULT(strftime('%s', 'now')),
    labels TEXT
) WITHOUT ROWID;
```

### Indexes

```SQL 
CREATE INDEX IF NOT EXISTS idx_tasks_account_id
ON tasks(account_id);

CREATE INDEX IF NOT EXISTS idx_deleted_tasks_account_id
ON deleted_tasks(account_id);

CREATE INDEX IF NOT EXISTS idx_tasks_completion_status
ON tasks(completion_status);

CREATE INDEX IF NOT EXISTS idx_deleted_tasks_completion_status
ON deleted_tasks(completion_status);
```

### Triggers

```SQL
CREATE TRIGGER IF NOT EXISTS deleted_account_trigger
AFTER DELETE ON accounts
FOR EACH ROW
BEGIN
    INSERT INTO deleted_accounts (
        id,
        username,
        email,
        role,
        creation_time,
        session_id_creation_time,
        labels,
        deleted_at
    )
    VALUES (
        OLD.id,
        OLD.username,
        OLD.email,
        OLD.role,
        OLD.creation_time,
        OLD.session_id_creation_time,
        OLD.labels,
        strftime('%s','now')
    );
END;


CREATE TRIGGER IF NOT EXISTS delete_task_trigger 
AFTER DELETE ON tasks
FOR EACH ROW
BEGIN
    INSERT INTO deleted_tasks (
        id,
        "description",
        account_id,
        completion_status,
        label_name,
        creation_time,
        deletion_time
    )
    VALUES (
        OLD.id,
        OLD.description,
        OLD.account_id,
        OLD.completion_status,
        OLD.label_name,
        OLD.creation_time,
        strftime('%s', 'now')
    );
END;


CREATE TRIGGER IF NOT EXISTS session_refresh_time_trigger
AFTER UPDATE OF "session_id" ON accounts
FOR EACH ROW
WHEN OLD.session_id IS NOT NEW.session_id
BEGIN
    UPDATE accounts
    SET session_id_creation_time = strftime('%s', 'now')
    WHERE id = NEW.id;
END;
```

### Pragma

```SQL
PRAGMA foreign_keys = ON;
PRAGMA temp_store = memory;
PRAGMA cache_size = 3000;
PRAGMA page_size = 4096; -- This is the default.
PRAGMA auto_vacuum=FULL;
PRAGMA journal_mode=WAL;
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