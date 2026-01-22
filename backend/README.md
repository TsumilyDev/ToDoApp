# To-Do App Backend

The backend is synchronous and requests will be held until they can be processed by the
backend.

## The Design
The backend is a 

## The Database
Public in this context means that a non-developer can see it. Be it only the user
or everyone. As soon as it gets out of the database-backend scope, it is considered
to be public information.

Time is stored in UNIX time as integers. It is expected to be in seconds.

### Tables / Schema
```SQL
CREATE TABLE IF NOT EXISTS accounts (
    -- Sensitive Information
    session_id TEXT UNIQUE; -- This should be synced with the clients cookies
    --- Unsensitive Information
    password TEXT NOT NULL; -- Stored as a hash so *technically* not sensitive
    id TEXT PRIMARY KEY;
    email TEXT NOT NULL UNIQUE;
    username TEXT NOT NULL UNIQUE;
    creation_time NUMBER NOT NULL DEFAULT(strftime('%s', 'now'));
    session_id_creation_time NUMBER;
    role NUMBER; -- Ranks get translated from strings to numbers by the backend
)


CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY;
    description TEXT;
    account_id TEXT NOT NULL;
    label

    FOREIGN KEY(account_id) REFERENCES accounts(id);
)


CREATE TABLE IF NOT EXISTS labels (
    label_name TEXT NOT NULL;
)


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
    deleted_at INTEGER NOT NULL DEFAULT(strftime('%s', 'now'));
);

```

### Indexes
```SQL 
```

### Triggers
```SQL
CREATE TRIGGER IF NOT EXISTS deleted_account_tigger (
AFTER DELETE ON accounts
FOR EACH ROW
BEGIN
    INSERT INTO deleted_accounts
    (
        account_id, username, email, role, created_at, deleted_at
    )
    VALUES
    (
        OLD.account_id, OLD.username, OLD.email, OLD.role, OLD.created_at,
        strftime('%s', 'now')
    );
END);

CREATE TRIGGER IF NOT EXISTS delete_task_trigger (
AFTER DELETE ON tasks
FOR EACH ROW
BEGIN
    INSERT INTO deleted_tasks (
        
    )
    VALUES (

    )
END);
```

### Pragma

```SQL
PRAGMA FOREIGN KEYS = TRUE
```