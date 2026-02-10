// ========================================
// STATE
// ========================================

let tasks = [];

// ========================================
// RENDER
// ========================================

function renderTasks() {
    const taskList = document.querySelector("#task-list");
    taskList.innerHTML = "";

    // Separate incomplete and completed
    const incomplete = tasks.filter((t) => !t.completed);
    const completed = tasks.filter((t) => t.completed);

    // Render incomplete tasks
    if (incomplete.length > 0) {
        incomplete.forEach((task) => {
            taskList.appendChild(createTaskElement(task));
        });
    }

    // Render completed tasks
    if (completed.length > 0) {
        completed.forEach((task) => {
            const el = createTaskElement(task);
            el.classList.add("task-completed");
            taskList.appendChild(el);
        });
    }

    // Empty state
    if (tasks.length === 0) {
        const empty = document.createElement("li");
        empty.className = "task-empty";
        empty.textContent = "No tasks yet.";
        taskList.appendChild(empty);
    }
}

function createTaskElement(task) {
    const li = document.createElement("li");
    li.className = "task-item";
    li.dataset.id = task.id;

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.className = "task-checkbox";
    checkbox.checked = task.completed;
    checkbox.addEventListener("change", () => toggleTask(task.id));

    const label = document.createElement("label");
    label.className = "task-label";
    label.textContent = task.title;

    const deleteBtn = document.createElement("button");
    deleteBtn.className = "task-delete";
    deleteBtn.textContent = "Delete";
    deleteBtn.addEventListener("click", () => deleteTask(task.id));

    li.appendChild(checkbox);
    li.appendChild(label);
    li.appendChild(deleteBtn);

    return li;
}

// ========================================
// STATE MUTATIONS
// ========================================

async function loadTasks() {
    const response = await fetch("/api/tasks", {
        method: "GET",
        credentials: "same-origin",
    });

    if (response.status === 401) {
        window.location.href = "/account";
        return;
    }

    if (!response.ok) {
        return;
    }

    const data = await response.json();
    tasks = Array.isArray(data.tasks) ? data.tasks : [];
    renderTasks();
}

async function addTask(title) {
    if (!title.trim()) return;

    const response = await fetch("/api/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({ title: title.trim(), labels: [] }),
    });

    if (response.status === 401) {
        window.location.href = "/account";
        return;
    }

    if (!response.ok) {
        return;
    }

    await loadTasks();
}

async function deleteTask(id) {
    const response = await fetch(`/api/tasks/${id}`, {
        method: "DELETE",
        credentials: "same-origin",
    });

    if (response.status === 401) {
        window.location.href = "/account";
        return;
    }

    if (!response.ok) {
        return;
    }

    await loadTasks();
}

async function toggleTask(id) {
    const task = tasks.find((t) => t.id === id);
    if (!task) return;

    const response = await fetch(`/api/tasks/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({ completed: !task.completed }),
    });

    if (response.status === 401) {
        window.location.href = "/account";
        return;
    }

    if (!response.ok) {
        return;
    }

    await loadTasks();
}

// ========================================
// INIT
// ========================================

document.addEventListener("DOMContentLoaded", () => {
    const input = document.querySelector("#task-input");
    const taskList = document.querySelector("#task-list");
    const logoutButton = document.querySelector("#logout-button");

    if (!input || !taskList) {
        return;
    }

    input.focus();
    loadTasks();

    input.addEventListener("keydown", (event) => {
        if (event.key !== "Enter") {
            return;
        }

        event.preventDefault();
        addTask(input.value);
        input.value = "";
        input.focus();
    });

    if (logoutButton) {
        logoutButton.addEventListener("click", async () => {
            await fetch("/session/delete", {
                method: "DELETE",
                credentials: "same-origin",
            });
            window.location.href = "/account";
        });
    }
});
