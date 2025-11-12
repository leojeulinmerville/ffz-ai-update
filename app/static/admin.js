(() => {
  const TOKEN_KEY = "ffz_jwt";
  const EMAIL_KEY = "ffz_email";

  const state = {
    leagues: [],
    teams: {},
  };

  const els = {};

  document.addEventListener("DOMContentLoaded", () => {
    els.status = document.getElementById("status");
    els.registerForm = document.getElementById("register-form");
    els.loginForm = document.getElementById("login-form");
    els.registerEmail = document.getElementById("register-email");
    els.registerPassword = document.getElementById("register-password");
    els.registerLanguage = document.getElementById("register-language");
    els.registerPhone = document.getElementById("register-phone");
    els.fanLeague = document.getElementById("fan-league");
    els.fanTeam = document.getElementById("fan-team");
    els.loginEmail = document.getElementById("login-email");
    els.loginPassword = document.getElementById("login-password");
    els.leaguesSelect = document.getElementById("leagues");
    els.loadLeaguesBtn = document.getElementById("load-leagues");
    els.followLeaguesBtn = document.getElementById("follow-leagues");
    els.logoutBtn = document.getElementById("logout");
    els.generateBtn = document.getElementById("generate-report");
    els.scrapePreviewBtn = document.getElementById("scrape-preview");
    els.scrapePersistBtn = document.getElementById("scrape-persist");
    els.latestBtn = document.getElementById("show-latest");
    els.sendBtn = document.getElementById("send-latest");
    els.reportOutput = document.getElementById("report-output");
    els.deliveryOutput = document.getElementById("delivery-output");
    els.toast = document.getElementById("toast");

    els.registerForm.addEventListener("submit", onRegister);
    els.loginForm.addEventListener("submit", onLogin);
    els.fanLeague.addEventListener("change", updateFanTeams);
    els.loadLeaguesBtn.addEventListener("click", () => loadLeagues(true));
    els.followLeaguesBtn.addEventListener("click", followSelectedLeagues);
    els.logoutBtn.addEventListener("click", logout);
    els.generateBtn.addEventListener("click", generateWeeklyReport);
    els.scrapePreviewBtn.addEventListener("click", runScrapePreview);
    els.scrapePersistBtn.addEventListener("click", runPersistScrape);
    els.latestBtn.addEventListener("click", showLatestReport);
    els.sendBtn.addEventListener("click", sendLatestReport);

    const storedEmail = window.localStorage.getItem(EMAIL_KEY);
    if (storedEmail) {
      els.loginEmail.value = storedEmail;
      setStatus(`Logged in as ${storedEmail}`);
    }

    loadLeagues(false);
  });

  function setStatus(message) {
    if (els.status) {
      els.status.textContent = message;
    }
  }

  function saveAuth(token, email) {
    if (token) {
      window.localStorage.setItem(TOKEN_KEY, token);
    }
    if (email) {
      window.localStorage.setItem(EMAIL_KEY, email);
      els.loginEmail.value = email;
    }
    setStatus(`Logged in as ${email}`);
  }

  function logout() {
    window.localStorage.removeItem(TOKEN_KEY);
    window.localStorage.removeItem(EMAIL_KEY);
    if (els.loginEmail) els.loginEmail.value = "";
    if (els.loginPassword) els.loginPassword.value = "";
    resetOutputs();
    setStatus("Logged out.");
  }

  function getToken() {
    return window.localStorage.getItem(TOKEN_KEY);
  }

  function resetOutputs() {
    els.reportOutput.textContent = "";
    els.deliveryOutput.textContent = "";
  }

  function showToast(message) {
    if (!els.toast) return;
    els.toast.textContent = message;
    els.toast.classList.add("visible");
    clearTimeout(state.toastTimeout);
    state.toastTimeout = window.setTimeout(() => {
      els.toast.classList.remove("visible");
    }, 4000);
  }

  async function loadLeagues(showToast) {
    try {
      const res = await fetch("/meta/leagues");
      if (!res.ok) {
        throw new Error(res.status);
      }
      const data = await res.json();
      state.leagues = data.leagues || [];
    } catch (err) {
      setStatus(`Failed to load leagues: ${err}`);
      return;
    }

    els.leaguesSelect.innerHTML = "";
    els.fanLeague.innerHTML = '<option value="">(optional)</option>';

    state.leagues.forEach((league) => {
      const option = document.createElement("option");
      option.value = league.code;
      option.textContent = `${league.name} (${league.code})`;
      els.leaguesSelect.appendChild(option.cloneNode(true));
      els.fanLeague.appendChild(option);
    });

    if (showToast) {
      setStatus("Leagues refreshed.");
    }
  }

  async function updateFanTeams() {
    const code = els.fanLeague.value;
    els.fanTeam.innerHTML = "";

    if (!code) {
      els.fanTeam.innerHTML = '<option value="">Select a league first</option>';
      return;
    }

    if (!state.teams[code]) {
      try {
        const res = await fetch(`/meta/leagues/${code}/teams`);
        if (!res.ok) throw new Error(res.status);
        const data = await res.json();
        state.teams[code] = data.teams || [];
      } catch (err) {
        setStatus(`Failed to load teams for ${code}: ${err}`);
        els.fanTeam.innerHTML = '<option value="">Unable to load teams</option>';
        return;
      }
    }

    els.fanTeam.innerHTML = '<option value="">(optional)</option>';
    state.teams[code].forEach((team) => {
      const opt = document.createElement("option");
      opt.value = team.name;
      opt.textContent = team.name;
      els.fanTeam.appendChild(opt);
    });
  }

  async function onRegister(event) {
    event.preventDefault();
    resetOutputs();

    const payload = {
      email: els.registerEmail.value.trim().toLowerCase(),
      password: els.registerPassword.value,
      language: els.registerLanguage.value,
      phone_number: els.registerPhone.value.trim() || null,
      favorite_team: els.fanTeam.value || null,
    };

    try {
      const res = await fetch("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.status === 409) {
        setStatus("Email already registered. Switching to login.");
        els.loginEmail.value = payload.email;
        els.loginPassword.value = payload.password;
        await onLogin(null, payload.email, payload.password);
        return;
      }

      if (!res.ok) {
        throw new Error(res.status);
      }

      await onLogin(null, payload.email, payload.password);
      await loadLeagues(false);
      await updateFanTeams();
    } catch (err) {
      setStatus(`Registration failed: ${err}`);
    }
  }

  async function onLogin(event, emailOverride, passwordOverride) {
    if (event) event.preventDefault();
    resetOutputs();

    const email = emailOverride ?? els.loginEmail.value.trim().toLowerCase();
    const password = passwordOverride ?? els.loginPassword.value;

    try {
      const res = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) throw new Error(res.status);
      const data = await res.json();
      saveAuth(data.access_token, email);
    } catch (err) {
      setStatus(`Login failed: ${err}`);
    }
  }

  async function followSelectedLeagues() {
    const token = getToken();
    if (!token) {
      setStatus("Please login first.");
      return;
    }

    const selected = Array.from(els.leaguesSelect.selectedOptions).map((opt) => opt.value);
    if (!selected.length) {
      setStatus("Select at least one league to follow.");
      return;
    }

    await authed("/subscriptions/bulk", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ leagues: selected }),
    }, `Followed ${selected.join(", ")}`);
  }

  async function generateWeeklyReport() {
    setStatus("Generating weekly report...");
    const response = await authed("/news/generate", { method: "POST" });
    if (!response) {
      setStatus("Generation failed.");
      return;
    }
    setStatus("Report generated. Fetching latest snapshot...");
    await showLatestReport(true);
    setStatus("Weekly report generated.");
  }

  async function showLatestReport(silent = false) {
    if (!silent) {
      setStatus("Loading latest weekly report...");
    }
    const data = await authed("/news/latest");
    if (data) {
      els.reportOutput.textContent = JSON.stringify(data, null, 2);
      if (!silent) {
        setStatus("Latest weekly report ready.");
      }
    }
  }

  async function runScrapePreview() {
    resetOutputs();
    const league = selectLeagueCode();
    if (!league) {
      setStatus("Select or follow at least one league first.");
      return;
    }
    setStatus(`Scraping ${league} (live preview)...`);
    try {
      const res = await fetch(`/scrape/preview?league=${encodeURIComponent(league)}`);
      if (!res.ok) {
        if (res.status === 403) {
          showToast("Robots.txt blocked this source. Try another league.");
        } else if (res.status === 502) {
          showToast("Upstream BBC endpoint returned 502. Retry shortly.");
        }
        throw new Error(res.status);
      }
      const data = await res.json();
      els.reportOutput.textContent = JSON.stringify(data, null, 2);
      setStatus(`Scrape preview ready for ${league}.`);
    } catch (err) {
      setStatus(`Scrape preview failed: ${err}`);
    }
  }

  async function runPersistScrape() {
    resetOutputs();
    const league = selectLeagueCode();
    if (!league) {
      setStatus("Select or follow at least one league first.");
      return;
    }

    setStatus(`Storing snapshot for ${league}...`);
    const payload = { leagues: [league] };
    const data = await authed(
      "/scrape/run",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
      null,
    );
    if (data && data.snapshot_id) {
      setStatus(`Snapshot stored for ${league}. Loading cache...`);
      await loadLatestFacts(league);
      setStatus(`Snapshot stored for ${league}.`);
    }
  }

  async function sendLatestReport() {
    setStatus("Sending latest report via WhatsApp...");
    const data = await authed("/news/send_latest", { method: "POST" });
    if (data) {
      els.deliveryOutput.textContent = JSON.stringify(data, null, 2);
      setStatus(`WhatsApp send status: ${data.status || data.delivery_status || "ok"}`);
    }
  }

  async function loadLatestFacts(league) {
    const token = getToken();
    if (!token) {
      setStatus("Please login first.");
      return;
    }
    try {
      const res = await fetch(`/facts/latest?league=${encodeURIComponent(league)}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(res.status);
      const payload = await res.json();
      resetOutputs();
      els.reportOutput.textContent = JSON.stringify(payload, null, 2);
    } catch (err) {
      setStatus(`Failed to load cached facts: ${err}`);
    }
  }

  function selectLeagueCode() {
    const selected = els.leaguesSelect.selectedOptions;
    if (selected && selected.length) {
      return selected[0].value;
    }
    if (els.fanLeague.value) {
      return els.fanLeague.value;
    }
    if (state.leagues.length) {
      return state.leagues[0].code;
    }
    return null;
  }

  async function authed(path, options = {}, successMessage = null) {
    resetOutputs();
    const token = getToken();
    if (!token) {
      setStatus("Please login first.");
      return null;
    }

    const headers = {
      ...(options.headers || {}),
      Authorization: `Bearer ${token}`,
    };

    if (options.body && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    try {
      const res = await fetch(path, { ...options, headers });
      if (res.status === 401) {
        setStatus("Session expired, please login again.");
        window.localStorage.removeItem(TOKEN_KEY);
        return null;
      }
      if (!res.ok) throw new Error(res.status);
      if (successMessage) setStatus(successMessage);
      if (path === "/news/send_latest") {
        const payload = await res.json();
        els.deliveryOutput.textContent = JSON.stringify(payload, null, 2);
        return payload;
      }
      try {
        return await res.json();
      } catch {
        return null;
      }
    } catch (err) {
      setStatus(`Request failed: ${err}`);
      return null;
    }
  }
})();
