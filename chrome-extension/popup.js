// popup.js — controls the extension popup UI
// Handles login, reads extracted job data, saves to JobRadar API

// Config 
const API_BASE = "https://jobradar-pyss.onrender.com";

// DOM elements 
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

// State 
let currentJobData = null;

// Init 
document.addEventListener("DOMContentLoaded", () => {
  chrome.storage.local.get(["token"], (result) => {
    if (result.token) {
      showJobSection();
    } else {
      showLoginSection();
    }
  });
});

//  Login 
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

  // Retry up to 3 times — handles Render cold start (30-50 second wake up)
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
        // Store token in chrome.storage — persists across popup open/close
        chrome.storage.local.set({ token: data.access_token }, () => {
          showJobSection();
        });
        return;
      } else {
        loginError.textContent = "Invalid email or password";
        break;
      }
    } catch (error) {
      if (attempt === 3) {
        loginError.textContent = "API is waking up — wait 30 seconds and try again";
      }
      // Wait 5 seconds before retrying
      await new Promise(r => setTimeout(r, 5000));
    }
  }

  loginBtn.textContent = "Login";
  loginBtn.disabled    = false;
});

//  Logout 
logoutBtn.addEventListener("click", () => {
  chrome.storage.local.remove(["token"], () => {
    showLoginSection();
  });
});

//  Save job 
saveBtn.addEventListener("click", async () => {
  if (!currentJobData) {
    saveStatus.textContent = "No job data found on this page";
    saveStatus.className   = "status error";
    return;
  }

  chrome.storage.local.get(["token"], async (result) => {
    if (!result.token) {
      showLoginSection();
      return;
    }

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
          job_url:         currentJobData.job_url         || "",
          company_name:    currentJobData.company_name    || "",
          role_title:      currentJobData.role_title      || "",
          source:          currentJobData.source          || "other",
          job_description: currentJobData.job_description || ""
        }),
        signal: controller.signal
      });

      clearTimeout(timeout);

      if (response.ok) {
        saveStatus.textContent = "✅ Saved to JobRadar!";
        saveStatus.className   = "status success";
        saveBtn.textContent    = "✅ Saved";
      } else if (response.status === 401) {
        // Token expired — send back to login
        chrome.storage.local.remove(["token"]);
        showLoginSection();
      } else {
        saveStatus.textContent = "Failed to save. Try again.";
        saveStatus.className   = "status error";
      }
    } catch (error) {
      saveStatus.textContent = "API is waking up — try again in 30 seconds";
      saveStatus.className   = "status error";
    } finally {
      saveBtn.disabled = false;
    }
  });
});

//  UI helpers 
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
              currentJobData          = result.jobData;
              roleTitleEl.textContent = currentJobData.role_title   || "Not detected";
              companyEl.textContent   = currentJobData.company_name || "Not detected";
              sourceEl.textContent    = currentJobData.source       || "other";
            } else {
              roleTitleEl.textContent = "Not detected";
              companyEl.textContent   = "Not detected";
              sourceEl.textContent    = "other";
            }
          });
        }, 500);
      });
    });
  });
}