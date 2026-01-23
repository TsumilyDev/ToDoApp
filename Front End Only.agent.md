---
description: 'Describe what this custom agent does and when to use it.'
tools: []
---
# Copilot Build Constraints (Frontend-Only MVP)

## Scope
You are working on the FRONTEND ONLY. Do not modify or create backend/server code.
Goal: a minimal SPA with client-side routing and placeholder screens.

## Tech Constraints
- Use vanilla JavaScript (no React/Vue/Angular).
- No routing libraries. Implement a tiny hash router.
- Single Page Application: render views into a single root element.
- Use existing `app.html` and `app.js` unless explicitly told otherwise.

## Backend Constraints (Non-negotiable)
- Do NOT create API calls, fetch requests, axios, or networking code.
- Do NOT create server routes, controllers, middleware, or database code.
- Do NOT add authentication, sessions, or accounts.
- Use hardcoded mock data in the frontend.

## Routes
Implement these routes (hash-based):
- `#/projects` -> Project List
- `#/projects/:id` -> Project Overview
- `#/info` -> Info page
Default: redirect to `#/projects`

## UI Constraints
- Simple navigation links: Projects, Info.
- No CSS frameworks. Minimal styling only if required for readability.
- No extra pages, settings, search, filters, drag/drop, etc.

## Deliverables (Day 1)
- App loads with a nav
- Route changes update the view without page reload
- Each route renders a placeholder view component/function
