// ========================================
// STATE
// ========================================

let tasks = [
    { id: 1, title: "Review project proposal", completed: false },
    { id: 2, title: "Finish quarterly report", completed: true },
    { id: 3, title: "Update documentation", completed: false },
];

let nextId = 4;
let filterQuery = "";

// ========================================
// RENDER
// ========================================

function renderTasks() {
    const taskList = document.querySelector("#task-list");
    taskList.innerHTML = "";

    // Filter tasks by input
    const filtered = tasks.filter((task) =>
        task.title.toLowerCase().includes(filterQuery.toLowerCase())
    );

    // Separate incomplete and completed
    const incomplete = filtered.filter((t) => !t.completed);
    const completed = filtered.filter((t) => t.completed);

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
    if (filtered.length === 0) {
        const empty = document.createElement("li");
        empty.className = "task-empty";
        empty.textContent = "No tasks match your search.";
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

function addTask(title) {
    if (!title.trim()) return;

    tasks.push({
        id: nextId++,
        title: title.trim(),
        completed: false,
    });

    renderTasks();
}

function deleteTask(id) {
    tasks = tasks.filter((t) => t.id !== id);
    renderTasks();
}

function toggleTask(id) {
    const task = tasks.find((t) => t.id === id);
    if (task) {
        task.completed = !task.completed;
        renderTasks();
    }
}

function setFilter(query) {
    filterQuery = query;
    renderTasks();
}

// ========================================
// INIT
// ========================================

document.addEventListener("DOMContentLoaded", () => {
    const input = document.querySelector("#task-input");
    const taskList = document.querySelector("#task-list");

    if (!input || !taskList) {
        return;
    }

    input.focus();
    renderTasks();

    input.addEventListener("input", (event) => {
        setFilter(event.target.value);
    });

    input.addEventListener("keydown", (event) => {
        if (event.key !== "Enter") {
            return;
        }

        event.preventDefault();
        addTask(input.value);
        input.value = "";
        setFilter("");
        input.focus();
    });
});
