from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["admin"])

ADMIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>FFZ Admin Console</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 24px; line-height: 1.4; }
        h2 { margin-top: 32px; }
        fieldset { margin-bottom: 16px; padding: 16px; }
        button { margin-top: 8px; }
        pre { background: #f3f3f3; padding: 12px; overflow-x: auto; max-height: 320px; }
        .status { margin: 12px 0; font-weight: bold; }
        .league-card { border: 1px solid #ddd; padding: 12px; margin: 8px 0; }
        .league-card input { margin-top: 4px; display: block; }
    </style>
</head>
<body>
    <h1>Football Fan Zone — Admin Console</h1>
    <p class="status" id="status">Not logged in</p>

    <fieldset>
        <legend>Register</legend>
        <form id="register-form">
            <label>Email <input type="email" id="register-email" required /></label><br />
            <label>Password <input type="password" id="register-password" required /></label><br />
            <label>Language
                <select id="register-language">
                    <option value="fr">French</option>
                    <option value="en">English</option>
                </select>
            </label><br />
            <label>Favourite team <input type="text" id="register-fav-team" placeholder="e.g. Paris SG" /></label><br />
            <button type="submit">Register &amp; Login</button>
        </form>
    </fieldset>

    <fieldset>
        <legend>Login (existing user)</legend>
        <form id="login-form">
            <label>Email <input type="email" id="login-email" required /></label><br />
            <label>Password <input type="password" id="login-password" required /></label><br />
            <button type="submit">Login</button>
        </form>
    </fieldset>

    <fieldset>
        <legend>League Subscriptions</legend>
        <button id="load-leagues">Load Leagues</button>
        <div id="leagues-container"></div>
    </fieldset>

    <fieldset>
        <legend>Report Actions</legend>
        <button id="generate-report">Generate weekly report</button>
        <button id="show-latest">Show latest report (JSON)</button>
        <button id="send-latest">Send latest via WhatsApp</button>
        <div>
            <h3>Latest report payload</h3>
            <pre id="report-output"></pre>
        </div>
        <div>
            <h3>Delivery status</h3>
            <pre id="delivery-output"></pre>
        </div>
    </fieldset>

    <script>
        const tokenKey = "ffz_jwt";
        const emailKey = "ffz_email";

        function setStatus(message) {
            const el = document.getElementById("status");
            el.textContent = message;
        }

        function setToken(token, email) {
            if (token) {
                window.localStorage.setItem(tokenKey, token);
            }
            if (email) {
                window.localStorage.setItem(emailKey, email);
            }
            const storedEmail = window.localStorage.getItem(emailKey);
            if (storedEmail && token) {
                setStatus(`Logged in as ${storedEmail}`);
            }
        }

        function getToken() {
            return window.localStorage.getItem(tokenKey);
        }

        function currentEmail() {
            return window.localStorage.getItem(emailKey) || "";
        }

        function clearOutputs() {
            document.getElementById("report-output").textContent = "";
            document.getElementById("delivery-output").textContent = "";
        }

        async function registerUser(event) {
            event.preventDefault();
            clearOutputs();

            const email = document.getElementById("register-email").value;
            const password = document.getElementById("register-password").value;
            const language = document.getElementById("register-language").value;
            const favoriteTeam = document.getElementById("register-fav-team").value || null;

            const payload = { email, password, language, favorite_team: favoriteTeam };
            try {
                const res = await fetch("/auth/register", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                if (!res.ok) {
                    const detail = await res.text();
                    throw new Error(detail || "Registration failed");
                }
                await loginUserDirect(email, password, true);
            } catch (err) {
                setStatus(`Registration error: ${err.message}`);
            }
        }

        async function loginUser(event) {
            event.preventDefault();
            clearOutputs();

            const email = document.getElementById("login-email").value;
            const password = document.getElementById("login-password").value;

            await loginUserDirect(email, password, false);
        }

        async function loginUserDirect(email, password, fromRegister) {
            try {
                const res = await fetch("/auth/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password })
                });
                if (!res.ok) {
                    const detail = await res.text();
                    throw new Error(detail || "Login failed");
                }
                const payload = await res.json();
                setToken(payload.access_token, email);
                setStatus(`Logged in as ${email}`);
                if (!fromRegister) {
                    alert("Login successful!");
                }
            } catch (err) {
                setStatus(`Login error: ${err.message}`);
            }
        }

        function authHeaders() {
            const token = getToken();
            if (!token) {
                throw new Error("Login first to obtain a token");
            }
            return { "Content-Type": "application/json", "Authorization": `Bearer ${token}` };
        }

        async function loadLeagues() {
            clearOutputs();
            const container = document.getElementById("leagues-container");
            container.innerHTML = "Loading leagues...";
            try {
                const res = await fetch("/meta/leagues");
                if (!res.ok) {
                    throw new Error("Failed to load leagues");
                }
                const payload = await res.json();
                container.innerHTML = "";
                payload.leagues.forEach((league) => {
                    const card = document.createElement("div");
                    card.className = "league-card";
                    card.innerHTML = `
                        <strong>${league.name}</strong><br />
                        Code: <code>${league.code}</code><br />
                        Country: ${league.country}<br />
                        <label>Track team (optional): <input type="text" placeholder="Team name" /></label>
                        <button>Follow this league</button>
                    `;
                    const button = card.querySelector("button");
                    button.addEventListener("click", async () => {
                        const team = card.querySelector("input").value || null;
                        try {
                            const headers = authHeaders();
                            const resSub = await fetch("/subscriptions", {
                                method: "POST",
                                headers,
                                body: JSON.stringify({ league: league.code, team, frequency: "weekly" })
                            });
                            if (!resSub.ok) {
                                const detail = await resSub.text();
                                throw new Error(detail || "Subscription failed");
                            }
                            alert(`Subscribed to ${league.name}`);
                        } catch (err) {
                            alert(`Subscription error: ${err.message}`);
                        }
                    });
                    container.appendChild(card);
                });
            } catch (err) {
                container.textContent = `Error: ${err.message}`;
            }
        }

        async function generateReport() {
            clearOutputs();
            try {
                const headers = authHeaders();
                const res = await fetch("/news/generate", { method: "POST", headers });
                if (!res.ok) {
                    const detail = await res.text();
                    throw new Error(detail || "Generation failed");
                }
                const payload = await res.json();
                document.getElementById("report-output").textContent = JSON.stringify(payload, null, 2);
                alert("Report generated successfully.");
            } catch (err) {
                alert(`Generate error: ${err.message}`);
            }
        }

        async function showLatestReport() {
            clearOutputs();
            try {
                const headers = authHeaders();
                const res = await fetch("/news/latest", { method: "GET", headers });
                if (!res.ok) {
                    const detail = await res.text();
                    throw new Error(detail || "Fetch latest failed");
                }
                const payload = await res.json();
                document.getElementById("report-output").textContent = JSON.stringify(payload, null, 2);
            } catch (err) {
                alert(`Latest report error: ${err.message}`);
            }
        }

        async function sendLatestReport() {
            document.getElementById("delivery-output").textContent = "";
            try {
                const headers = authHeaders();
                const res = await fetch("/news/send_latest", { method: "POST", headers });
                if (!res.ok) {
                    const detail = await res.text();
                    throw new Error(detail || "Send failed");
                }
                const payload = await res.json();
                document.getElementById("delivery-output").textContent = JSON.stringify(payload, null, 2);
            } catch (err) {
                alert(`Send error: ${err.message}`);
            }
        }

        document.getElementById("register-form").addEventListener("submit", registerUser);
        document.getElementById("login-form").addEventListener("submit", loginUser);
        document.getElementById("load-leagues").addEventListener("click", loadLeagues);
        document.getElementById("generate-report").addEventListener("click", generateReport);
        document.getElementById("show-latest").addEventListener("click", showLatestReport);
        document.getElementById("send-latest").addEventListener("click", sendLatestReport);

        (function init() {
            const token = getToken();
            const email = currentEmail();
            if (token && email) {
                setStatus(`Logged in as ${email}`);
            }
        })();
    </script>
</body>
</html>
"""


@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard():
    return HTMLResponse(content=ADMIN_HTML)
