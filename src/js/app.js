document.addEventListener("DOMContentLoaded", () => {
    const input = document.querySelector("#task-input");
    const taskList = document.querySelector("#task-list");

    if (!input || !taskList) {
        return;
    }

    input.focus();

    input.addEventListener("keydown", (event) => {
        if (event.key !== "Enter") {
            return;
        }

        event.preventDefault();
        const value = input.value.trim();
        if (!value) {
            return;
        }

        console.log(value);
        input.value = "";
    });
});
