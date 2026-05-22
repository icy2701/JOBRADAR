// popup.js — controls the extension popup UI

const API_BASE = "https://jobradar-pyss.onrender.com";

const loginSection  = document.getElementById("login-section");
const jobSection    = document.getElementById("job-section");
const emailInput    = document.getElementById("email");
const passwordInput = document.getElementById("password");
const loginBtn      = document.getElementById("login-btn");
const loginError    = document.getElementById("login-error");
const saveBtn       = document.getElementById("save-btn");
const logoutBtn     = document.getElementById("logout-btn");
const saveStatus    = document.getElementById("save-status");
const roleTitleEl   = document.getElementById("role-title");
const companyEl     = document.getElementById("company-name");
const sourceEl      = document.getElementById("source");

let currentJobData = null;

document.addEventListener("DOMContentLoaded", () => {
  chrome.storage.local.get(["token"], (result) => {
    if (result.token) {
      showJobSection();
    } else {
      showLoginSection();
    }
  });
});

// Login
loginBtn.addEventListener("click", async () => {
  const email    = emailInput.value.trim();
  const password = passwordInput.value.trim();

  if (!email || !password) {
    loginError.textContent = "Please enter email and password";
    return;
  }

  loginBtn.textContent = "Connecting...";
  loginBtn.disabled    = true;
  loginError.textContent = "";

  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      loginBtn.textContent = attempt > 1
        ? `Retrying... (${attempt}/3)`
        : "Logging in...";

      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 60000);

      const response = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`,
        signal: controller.signal
      });

      clearTimeout(timeout);

      if (response.ok) {
        const data = await response.json();
        chrome.storage.local.set({ token: data.access_token }, () => {
          showJobSection();
        });
        return;
      } else {
        const data = await response.json();
        loginError.textContent = data.detail || "Invalid email or password";
        break;
      }
    } catch (error) {
      if (attempt === 3) {
        loginError.textContent = "API is waking up. Wait 30 seconds and try again.";
      }
      await new Promise(r => setTimeout(r, 5000));
    }
  }

  loginBtn.textContent = "Login";
  loginBtn.disabled    = false;
});

// Logout
logoutBtn.addEventListener("click", () => {
  chrome.storage.local.remove(["token"], () => {
    showLoginSection();
  });
});

// Save job
saveBtn.addEventListener("click", async () => {
  chrome.storage.local.get(["token"], async (result) => {
    if (!result.token) {
      showLoginSection();
      return;
    }

    // Read from editable fields — user may have corrected the values
    const roleTitle   = roleTitleEl.value.trim();
    const companyName = companyEl.value.trim();

    saveBtn.textContent = "Saving...";
    saveBtn.disabled    = true;

    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 60000);

      const response = await fetch(`${API_BASE}/applications`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${result.token}`
        },
        body: JSON.stringify({
          job_url:         currentJobData ? currentJobData.job_url : "",
          company_name:    companyName,
          role_title:      roleTitle,
          source:          currentJobData ? currentJobData.source : "other",
          job_description: currentJobData ? currentJobData.job_description : ""
        }),
        signal: controller.signal
      });

      clearTimeout(timeout);

      if (response.ok) {
        saveStatus.textContent = "Saved to JobRadar!";
        saveStatus.className   = "status success";
        saveBtn.textContent    = "Saved";
      } else if (response.status === 401) {
        chrome.storage.local.remove(["token"]);
        showLoginSection();
      } else {
        saveStatus.textContent = "Failed to save. Try again.";
        saveStatus.className   = "status error";
        saveBtn.textContent    = "Save to JobRadar";
        saveBtn.disabled       = false;
      }
    } catch (error) {
      saveStatus.textContent = "API waking up. Try again in 30 seconds.";
      saveStatus.className   = "status error";
      saveBtn.textContent    = "Save to JobRadar";
      saveBtn.disabled       = false;
    }
  });
});

// UI helpers
function showLoginSection() {
  loginSection.style.display = "block";
  jobSection.style.display   = "none";
  loginError.textContent     = "";
}

function showJobSection() {
  loginSection.style.display = "none";
  jobSection.style.display   = "block";
  loadJobData();
}

function loadJobData() {
  chrome.storage.local.remove(["jobData"], () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs[0]) return;

      chrome.scripting.executeScript({
        target: { tabId: tabs[0].id },
        files: ["content.js"]
      }, () => {
        setTimeout(() => {
          chrome.storage.local.get(["jobData"], (result) => {
            if (result.jobData) {
              currentJobData      = result.jobData;
              roleTitleEl.value   = currentJobData.role_title   || "";
              companyEl.value     = currentJobData.company_name || "";
              sourceEl.textContent = currentJobData.source      || "other";
            } else {
              currentJobData      = null;
              roleTitleEl.value   = "";
              companyEl.value     = "";
              sourceEl.textContent = "other";
            }
          });
        }, 500);
      });
    });
  });
}