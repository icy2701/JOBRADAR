// content.js — runs on job pages automatically.Reads the page DOM and extracts job details
// Stores extracted data so popup.js can access it.

(function() {
    // Utility
    function cleanText(text){
        if (!text) return "";
        return text.replace(/\s+/g, " ").trim();
    }

    function getMetaContent(property) {
        const meta = document.querySelector(
            `meta[property="${property}"], meta[name="${property}"]`
        );
        return meta ? cleanText(meta.getAttribute(content)) : "";
    }

    // Parsers 
    function parseLinkedIn() {
  // LinkedIn page title format: "Job Title | Company | LinkedIn"
  const pageTitle = document.title;
  let roleTitle = "";
  let companyName = "";

  if (pageTitle && pageTitle.includes("| LinkedIn")) {
    // Remove "| LinkedIn" from the end
    const withoutLinkedIn = pageTitle.replace("| LinkedIn", "").trim();
    // Split by " | "
    const parts = withoutLinkedIn.split(" | ").map(p => p.trim()).filter(Boolean);
    if (parts.length >= 2) {
      roleTitle = parts[0];      // First part = job title
      companyName = parts[1];    // Second part = company
    } else if (parts.length === 1) {
      roleTitle = parts[0];
    }
  }

  // Fallback to og:title
  if (!roleTitle || !companyName) {
    const ogTitle = getMetaContent("og:title");
    if (ogTitle) {
      const parts = ogTitle.split(" | ").map(p => p.trim()).filter(Boolean);
      if (parts.length >= 2) {
        roleTitle = roleTitle || parts[0];
        companyName = companyName || parts[1];
      }
    }
  }

  const description = document.querySelector(
    ".description__text, .show-more-less-html__markup"
  );

  return {
    role_title: roleTitle,
    company_name: companyName,
    job_description: description ?
      cleanText(description.innerText).substring(0, 2000) : "",
    source: "linkedin"
  };
}

  function parseIndeed() {
    const title = document.querySelector(
      "h1[data-testid='jobsearch-JobInfoHeader-title'], h1.jobsearch-JobInfoHeader-title, h1"
    );
    const company = document.querySelector(
      "[data-testid='inlineHeader-companyName'], .jobsearch-CompanyInfoWithoutHeaderImage a"
    );
    const description = document.querySelector(
      "#jobDescriptionText, .jobsearch-jobDescriptionText"
    );

    return {
      role_title: title ? cleanText(title.innerText) : "",
      company_name: company ? cleanText(company.innerText) : "",
      job_description: description ?
        cleanText(description.innerText).substring(0, 2000) : "",
      source: "indeed"
    };
  }

  function parseStepStone() {
    const title = document.querySelector("h1");
    const company = document.querySelector(
      "[data-testid='job-header-company-name'], .at-header-company-name"
    );
    const description = document.querySelector(
      "[data-testid='job-description'], .at-section-text-description"
    );

    return {
      role_title: title ? cleanText(title.innerText) : "",
      company_name: company ? cleanText(company.innerText) : "",
      job_description: description ?
        cleanText(description.innerText).substring(0, 2000) : "",
      source: "stepstone"
    };
  }

  function parseGeneric() {
    // Works on most company career pages
    const title = document.querySelector("h1");
    let companyName = "";
    let roleTitle = title ? cleanText(title.innerText) : "";

    // Try og:title — many sites format it as "Role at Company"
    const ogTitle = getMetaContent("og:title");
    if (ogTitle && ogTitle.includes(" at ")) {
      const parts = ogTitle.split(" at ");
      roleTitle = roleTitle || parts[0].trim();
      companyName = parts[1].trim();
    }

    // Try og:site_name for company name
    if (!companyName) {
      companyName = getMetaContent("og:site_name");
    }

    const description = document.querySelector(
      "#job-description, .job-description, [class*='description'], [id*='description']"
    );

    return {
      role_title: roleTitle,
      company_name: companyName,
      job_description: description ?
        cleanText(description.innerText).substring(0, 2000) : "",
      source: "other"
    };
  }

  // Route to correct parser 
  function extractJobData() {
    const url = window.location.href;
    let data;

    if (url.includes("linkedin.com"))  data = parseLinkedIn();
    else if (url.includes("indeed.com"))   data = parseIndeed();
    else if (url.includes("stepstone.de")) data = parseStepStone();
    else data = parseGeneric();

    // Always include the current URL
    data.job_url = url;
    return data;
  }

  // Store data for popup access 
  // popup.js cannot directly access the DOM of the page
  // so content.js stores the extracted data in chrome.storage and popup.js reads it from there
  const jobData = extractJobData();
  chrome.storage.local.set({ jobData: jobData });

})();
