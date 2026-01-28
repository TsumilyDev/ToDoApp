# To Do App

This is a To-Do app created by Tsumily and Spade. It is intended to be basic initially,
many additional layers may be layed on top later upon the strong initial foundation.

#### Setup

**Quick Start (uses defaults):**
```bash
python app.py
```
http://localhost:8000/app

**Custom Configuration:**
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your preferred settings (all have sensible defaults)

3. Run the server:
   ```bash
   python app.py
   ```
   or directly via the backend module:
   ```bash
   python -m backend.main
   ```

**Environment Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `SQLITE3_PATH` | `./data/todo.db` | Path to SQLite database file. Parent directories are created automatically. |
| `PORT` | `8000` | Server port number (1-65535) |
| `BASE_URL` | `localhost` | Server listening address. Use `localhost` for local access only, or `0.0.0.0` for remote access. |

**Notes:**
- All environment variables have sensible defaults and are optional
- The database file and parent directories are created automatically if they don't exist
- Server startup will fail with a clear error if the database directory is not writable

## Philosophy

Practicallity and ease-of-use are among the top priorities for this application; the
design is user-first. A user shouldn't have to struggle to know how the application 
works. They should be able to join and have an intuitive understanding of everything so
they can begin being instantly.

We don't aim to be a an infrastructure-level application, this is not meant to be
used as such either. The goal is to create something more personal for small groups
or individuals to use reasonablly.

## Codebase

Maintainability and scalability are the biggest concerns for codebases, and ours is no
exception. Many methods have been employed to make this apps codebase maintainable and
scalable.

Ensuring your code is readable and easily understandable is very import as code is read
more often than it is written. The basic practices should go without saying, however
here are some basic practices for reference: ensuring individual lines aren't too long;
using clear names; choosing explictness over implicitness; using comments.

The codebase is designed to utilise central files. The main examples of central
files are: route.py; .env; and design-system.css. Each of these files define 
code/variables that is used throughout a section of the codebase. This makes 
reconfiguration of app-wide settings more convenient, increasing maintainability and 
scalability. Most of the files should only handle their own individual logic.

To make the codebase easier to navigate during development, you can use a set of 
keywords: UPDATE; TODO; and CONSIDER. You can then use your text editor of choice to 
search the codebase for those keywords. These keywords are helpful during developing
as they allow you to can 'bookmark' code and then be able to easily find it when you're
ready to continue it.
