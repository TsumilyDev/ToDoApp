const signupForm = document.querySelector("#signup-form");
const loginForm = document.querySelector("#login-form");
const messageEl = document.querySelector("#auth-message");

function showMessage(message) {
    if (!messageEl) return;
    messageEl.textContent = message;
}

function setFormBusy(form, busy) {
    if (!form) return;
    const fields = form.querySelectorAll("input, button");
    fields.forEach((field) => {
        field.disabled = busy;
    });
}

function buildUsernameFromEmail(email) {
    const base = (email.split("@")[0] || "user").replace(/\s+/g, "");
    let username = base.length >= 3 ? base : `user${base}`;
    if (username.length > 30) {
        username = username.slice(0, 30);
    }
    return username;
}

async function login(email, password) {
    const response = await fetch("/session/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
        const errorText = await response.text();
        showMessage(errorText || "Invalid information, try again.");
        return;
    }

    window.location.href = "/app";
}

if (signupForm) {
    signupForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        showMessage("");

        const email = document.querySelector("#signup-email")?.value.trim();
        const password = document.querySelector("#signup-password")?.value.trim();

        if (!email || !password) {
            showMessage("Invalid information, try again.");
            return;
        }

        setFormBusy(signupForm, true);

        try {
            const username = buildUsernameFromEmail(email);
            const response = await fetch("/account/create", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "same-origin",
                body: JSON.stringify({ email, username, password }),
            });

            if (!response.ok) {
                const errorText = await response.text();
                showMessage(errorText || "Invalid information, try again.");
                return;
            }

            await login(email, password);
        } catch (error) {
            showMessage("Technical difficultes occured, try again later.");
        } finally {
            setFormBusy(signupForm, false);
        }
    });
}

if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        showMessage("");

        const email = document.querySelector("#login-email")?.value.trim();
        const password = document.querySelector("#login-password")?.value.trim();

        if (!email || !password) {
            showMessage("Invalid information, try again.");
            return;
        }

        setFormBusy(loginForm, true);

        try {
            await login(email, password);
        } catch (error) {
            showMessage("Invalid information, try again.");
        } finally {
            setFormBusy(loginForm, false);
        }
    });
}
