from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_HTML = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>FFZ Admin Console</title>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" />
    <style>
      body {
        font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
        background: #f4f6fb;
        margin: 0;
        padding: 24px;
        color: #1f2933;
      }
      h1 {
        text-align: center;
        margin-bottom: 24px;
        color: #111827;
      }
      .status {
        text-align: center;
        margin-bottom: 24px;
        padding: 8px 16px;
        display: inline-block;
        background: #eef2ff;
        border-radius: 999px;
        color: #4338ca;
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 20px;
      }
      .hint {
        text-align: center;
        margin: -8px 0 24px;
        color: #6b7280;
        font-size: 0.9rem;
      }
      .toast {
        position: fixed;
        bottom: 24px;
        right: 24px;
        background: #111827;
        color: #f9fafb;
        padding: 12px 16px;
        border-radius: 8px;
        box-shadow: 0 12px 24px rgba(15, 23, 42, 0.2);
        opacity: 0;
        transform: translateY(20px);
        transition: opacity 0.2s ease, transform 0.2s ease;
        pointer-events: none;
      }
      .toast.visible {
        opacity: 1;
        transform: translateY(0);
      }
      fieldset {
        background: #fff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 20px;
      }
      legend {
        font-weight: 600;
        padding: 0 8px;
      }
      label {
        display: block;
        margin: 12px 0 4px;
        font-size: 0.95rem;
        font-weight: 500;
      }
      input, select, button, textarea {
        width: 100%;
        padding: 10px 12px;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        font-size: 0.95rem;
        font-family: inherit;
      }
      select[multiple] {
        min-height: 160px;
      }
      button {
        margin-top: 12px;
        background: #4f46e5;
        color: #fff;
        border: none;
        cursor: pointer;
        transition: background 0.2s;
      }
      button:hover {
        background: #4338ca;
      }
      pre {
        background: #0f172a;
        color: #f8fafc;
        padding: 12px;
        border-radius: 8px;
        max-height: 260px;
        overflow: auto;
        font-size: 0.85rem;
      }
    </style>
  </head>
  <body>
    <h1>Football Fan Zone — Admin Console</h1>
    <div class="status" id="status">Not logged in</div>
    <p class="hint">Tip: use "Scrape now (preview)" to inspect live BBC facts before generating.</p>

    <div class="grid">
      <fieldset>
        <legend>Register</legend>
        <form id="register-form">
          <label>Email</label>
          <input type="email" id="register-email" required />

          <label>Password</label>
          <input type="password" id="register-password" required />

          <label>Language</label>
          <select id="register-language">
            <option value="en" selected>English</option>
            <option value="fr">Français</option>
          </select>

          <label>Phone (France)</label>
          <input type="tel" id="register-phone" placeholder="0600000000" />

          <label>Favorite league</label>
          <select id="fan-league">
            <option value="">(optional)</option>
          </select>

          <label>Favorite team</label>
          <select id="fan-team">
            <option value="">Select a league first</option>
          </select>

          <button type="submit">Register &amp; Login</button>
        </form>
      </fieldset>

      <fieldset>
        <legend>Login</legend>
        <form id="login-form">
          <label>Email</label>
          <input type="email" id="login-email" required />

          <label>Password</label>
          <input type="password" id="login-password" required />

          <button type="submit">Login</button>
        </form>

        <label>Follow leagues</label>
        <select id="leagues" multiple></select>
        <button id="load-leagues" type="button">Reload leagues</button>
        <button id="follow-leagues" type="button">Follow selected</button>
        <button id="logout" type="button">Logout</button>
      </fieldset>

      <fieldset>
        <legend>Weekly Report</legend>
        <button id="generate-report" type="button">Generate weekly report</button>
        <button id="scrape-preview" type="button">Scrape now (preview)</button>
        <button id="scrape-persist" type="button">Run scrape job (persist)</button>
        <button id="show-latest" type="button">Show latest report</button>
        <button id="send-latest" type="button">Send latest via WhatsApp</button>

        <label>Latest payload</label>
        <pre id="report-output"></pre>

        <label>Delivery status</label>
        <pre id="delivery-output"></pre>
      </fieldset>
    </div>

    <div id="toast" class="toast"></div>

    <script src="/static/admin.js?v=6"></script>
  </body>
</html>
"""


@router.get("", response_class=HTMLResponse)
async def admin_console() -> HTMLResponse:
    return HTMLResponse(content=ADMIN_HTML)
