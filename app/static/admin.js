(() => {
  const TOKEN_KEY = "ffz_jwt";
  const EMAIL_KEY = "ffz_email";

  const state = {
    leagues: [],
    teams: {},
  };

  const els = {};

  function setStatus(message, type = "info") {
    if (els.status) {
      els.status.textContent = message;
      els.status.className = type;
      els.status.style.display = "block";
    }
  }

  function showLoading(button, show = true) {
    if (!button) return;
    if (show) {
      button.disabled = true;
      button.innerHTML = button.textContent + '<span class="loading"></span>';
    } else {
      button.disabled = false;
      button.innerHTML = button.textContent.replace('<span class="loading"></span>', '');
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    els.status = document.getElementById("status");
    els.userForm = document.getElementById("user-form");
    els.firstName = document.getElementById("first_name");
    els.lastName = document.getElementById("last_name");
    els.email = document.getElementById("email");
    els.language = document.getElementById("language");
    els.leagueContainer = document.getElementById("league-container");
    els.favoriteTeam = document.getElementById("favorite_team");
    els.generateBtn = document.getElementById("btn-generate");
    els.sendEmailBtn = document.getElementById("btn-send-email");

    // Load leagues on startup
    loadLeagues();

    // Form submission
    if (els.userForm) {
      els.userForm.addEventListener("submit", handleUserFormSubmit);
    }

    // Generate report
    if (els.generateBtn) {
      els.generateBtn.addEventListener("click", generateWeeklyReport);
    }

    // Send email
    if (els.sendEmailBtn) {
      els.sendEmailBtn.addEventListener("click", sendLatestEmail);
    }
  });

  async function loadLeagues() {
    try {
      const res = await fetch("/meta/leagues");
      if (!res.ok) {
        throw new Error(res.status);
      }
      const data = await res.json();
      state.leagues = data.leagues || [];
      
      renderLeagueCheckboxes();
    } catch (err) {
      setStatus(`Failed to load leagues: ${err}`, "error");
    }
  }

  function renderLeagueCheckboxes() {
    if (!els.leagueContainer) return;
    els.leagueContainer.innerHTML = "";
    state.leagues.forEach((league) => {
      const label = document.createElement("label");
      const input = document.createElement("input");
      input.type = "checkbox";
      input.name = "league";
      input.value = league.code;
      input.addEventListener("change", updateFavoriteTeamOptions);
      label.appendChild(input);
      label.append(` ${league.name}`);
      els.leagueContainer.appendChild(label);
    });
  }

  async function updateFavoriteTeamOptions() {
    const selectedLeagues = Array.from(document.querySelectorAll('input[name="league"]:checked'))
      .filter(cb => cb.checked)
      .map(cb => cb.value);

    if (!els.favoriteTeam) return;

    els.favoriteTeam.innerHTML = '<option value="">Select at least one league</option>';

    if (selectedLeagues.length === 0) {
      return;
    }

    try {
      const allTeams = new Map();
      for (const league of selectedLeagues) {
        const res = await fetch(`/meta/leagues/${league}/teams`);
        if (!res.ok) continue;
        const data = await res.json();
        for (const team of data.teams || []) {
          const key = `${team.name}|${league}`;
          if (!allTeams.has(key)) {
            allTeams.set(key, { name: team.name, league });
          }
        }
      }

      const sorted = Array.from(allTeams.values()).sort((a, b) =>
        a.name.localeCompare(b.name, undefined, { sensitivity: "base" })
      );
      sorted.forEach(({ name, league }) => {
        const option = document.createElement("option");
        option.value = name;
        option.textContent = `${name} (${league})`;
        els.favoriteTeam.appendChild(option);
      });
    } catch (err) {
      setStatus(`Failed to load teams: ${err}`, "error");
    }
  }

  async function handleUserFormSubmit(event) {
    event.preventDefault();
    setStatus("Saving user profile...", "info");
    showLoading(event.target.querySelector('button[type="submit"]'), true);

    const selectedLeagues = Array.from(document.querySelectorAll('input[name="league"]:checked'))
      .filter(cb => cb.checked)
      .map(cb => cb.value);

    const payload = {
      email: els.email.value.trim().toLowerCase(),
      first_name: els.firstName.value.trim() || null,
      last_name: els.lastName.value.trim() || null,
      language: els.language.value,
      favorite_team: els.favoriteTeam.value || null,
      leagues: selectedLeagues,
    };

    try {
      const res = await fetch("/admin/user", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error(res.status);
      }

      const data = await res.json();
      if (data.access_token) {
        window.localStorage.setItem(TOKEN_KEY, data.access_token);
        window.localStorage.setItem(EMAIL_KEY, payload.email);
      } else {
        // fallback: attempt a login with bootstrap password
        await loginAfterSave(payload.email);
      }
      setStatus(`User profile saved successfully!`, "success");
    } catch (err) {
      setStatus(`Failed to save user: ${err}`, "error");
    } finally {
      showLoading(event.target.querySelector('button[type="submit"]'), false);
    }
  }

  async function generateWeeklyReport() {
    setStatus("Generating weekly report...", "info");
    showLoading(els.generateBtn, true);

    try {
      const token = getToken();
      if (!token) {
        setStatus("Please save the user first to login.", "error");
        return;
      }

      const res = await fetch("/news/generate", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });

      if (res.status === 401) {
        setStatus("Session expired, please login again", "error");
        window.localStorage.removeItem(TOKEN_KEY);
        return;
      }

      if (!res.ok) {
        throw new Error(res.status);
      }

      const data = await res.json();
      setStatus(`Weekly report generated successfully! (${data.report?.articles?.length || 0} articles)`, "success");
    } catch (err) {
      setStatus(`Failed to generate report: ${err}`, "error");
    } finally {
      showLoading(els.generateBtn, false);
    }
  }

  async function sendLatestEmail() {
    setStatus("Sending email...", "info");
    showLoading(els.sendEmailBtn, true);

    try {
      const token = getToken();
      if (!token) {
        setStatus("Please save the user first to login.", "error");
        return;
      }

      const res = await fetch("/news/send_latest", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ channel: "email" }),
      });

      if (res.status === 401) {
        setStatus("Session expired, please login again", "error");
        window.localStorage.removeItem(TOKEN_KEY);
        return;
      }

      if (res.status === 404) {
        setStatus("No report available. Generate one first.", "error");
        return;
      }

      if (!res.ok) {
        throw new Error(res.status);
      }

      const data = await res.json();
      const statusText = data.status === "sent" ? "sent successfully" : data.status;
      setStatus(`Email ${statusText}!`, "success");
    } catch (err) {
      setStatus(`Failed to send email: ${err}`, "error");
    } finally {
      showLoading(els.sendEmailBtn, false);
    }
  }

  function getToken() {
    return window.localStorage.getItem(TOKEN_KEY);
  }

  async function loginAfterSave(email) {
    try {
      const res = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password: "changeme" }),
      });
      if (!res.ok) return;
      const data = await res.json();
      if (data.access_token) {
        window.localStorage.setItem(TOKEN_KEY, data.access_token);
        window.localStorage.setItem(EMAIL_KEY, email);
      }
    } catch {
      // best-effort; ignore errors
    }
  }
})();
