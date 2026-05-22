// content.js — runs on job pages automatically
// Reads the page DOM and extracts job details
// Stores extracted data so popup.js can access it

(function() {

  function cleanText(text) {
    if (!text) return "";
    return text.replace(/\s+/g, " ").trim();
  }

  function getMetaContent(property) {
    const meta = document.querySelector(
      `meta[property="${property}"], meta[name="${property}"]`
    );
    return meta ? cleanText(meta.getAttribute("content")) : "";
  }

  // LinkedIn: "Job Title | Company | LinkedIn"
  function parseLinkedIn() {
    const pageTitle = document.title;
    let roleTitle = "";
    let companyName = "";

    if (pageTitle && pageTitle.includes("| LinkedIn")) {
      const withoutLinkedIn = pageTitle.replace("| LinkedIn", "").trim();
      const parts = withoutLinkedIn.split(" | ").map(p => p.trim()).filter(Boolean);
      if (parts.length >= 2) {
        roleTitle   = parts[0];
        companyName = parts[1];
      } else if (parts.length === 1) {
        roleTitle = parts[0];
      }
    }

    const description = document.querySelector(
      ".description__text, .show-more-less-html__markup"
    );

    return {
      role_title:      roleTitle,
      company_name:    companyName,
      job_description: description ?
        cleanText(description.innerText).substring(0, 2000) : "",
      source: "linkedin"
    };
  }

  // Indeed
  function parseIndeed() {
    const title = document.querySelector(
      "h1[data-testid='jobsearch-JobInfoHeader-title'], h1"
    );
    const company = document.querySelector(
      "[data-testid='inlineHeader-companyName'], .jobsearch-CompanyInfoWithoutHeaderImage a"
    );
    const description = document.querySelector(
      "#jobDescriptionText, .jobsearch-jobDescriptionText"
    );

    return {
      role_title:      title   ? cleanText(title.innerText)   : "",
      company_name:    company ? cleanText(company.innerText) : "",
      job_description: description ?
        cleanText(description.innerText).substring(0, 2000) : "",
      source: "indeed"
    };
  }

  // StepStone
  function parseStepStone() {
    const title   = document.querySelector("h1");
    const company = document.querySelector(
      "[data-testid='job-header-company-name'], .at-header-company-name"
    );
    const description = document.querySelector(
      "[data-testid='job-description'], .at-section-text-description, article"
    );

    return {
      role_title:      title   ? cleanText(title.innerText)   : "",
      company_name:    company ? cleanText(company.innerText) : "",
      job_description: description ?
        cleanText(description.innerText).substring(0, 2000) : "",
      source: "stepstone"
    };
  }

  // XING
  function parseXing() {
    const title   = document.querySelector("h1");
    const company = document.querySelector(
      ".company-name, [class*='companyName'], [class*='company-name']"
    );
    return {
      role_title:      title   ? cleanText(title.innerText)   : "",
      company_name:    company ? cleanText(company.innerText) : "",
      job_description: "",
      source: "xing"
    };
  }

  // Generic for all other sites
  function parseGeneric() {
    let roleTitle   = "";
    let companyName = "";

    // H1 is most reliable for job title
    const h1 = document.querySelector("h1");
    if (h1) roleTitle = cleanText(h1.innerText);

    // Try JSON-LD structured data first
    const jsonLd = document.querySelector('script[type="application/ld+json"]');
    if (jsonLd) {
      try {
        const data = JSON.parse(jsonLd.innerText);
        if (data["@type"] === "JobPosting") {
          roleTitle   = roleTitle   || data.title || "";
          companyName = companyName ||
            (data.hiringOrganization && data.hiringOrganization.name) || "";
        }
      } catch (e) {}
    }

    // og:title only for company — not role since H1 is better
    if (!companyName) {
      const ogTitle = getMetaContent("og:title");
      if (ogTitle) {
        if (ogTitle.includes(" | ")) {
          const parts = ogTitle.split(" | ");
          if (!roleTitle) roleTitle = parts[0].trim();
          companyName = parts[parts.length - 2].trim();
        } else if (ogTitle.includes(" at ")) {
          const parts = ogTitle.split(" at ");
          if (!roleTitle) roleTitle = parts[0].trim();
          companyName = parts[1].trim();
        } else if (ogTitle.includes(" - ")) {
          const parts = ogTitle.split(" - ");
          if (!roleTitle) roleTitle = parts[0].trim();
          companyName = parts[1].trim();
        }
      }
    }

    // og:site_name for company
    if (!companyName) {
      companyName = getMetaContent("og:site_name") || "";
    }

    // Common company selectors
    if (!companyName) {
      const companySelectors = [
        "[class*='company-name']",
        "[class*='companyName']",
        "[class*='employer']",
        "[itemprop='name']"
      ];
      for (const sel of companySelectors) {
        const el = document.querySelector(sel);
        if (el && el.innerText && el.innerText.length < 60) {
          companyName = cleanText(el.innerText);
          break;
        }
      }
    }

    // Description
    const descSelectors = [
      "#job-description", ".job-description",
      "[class*='jobDescription']", "[id*='jobDescription']",
      "[class*='description']", "[id*='description']",
      "article", "main"
    ];

    let jobDescription = "";
    for (const sel of descSelectors) {
      const el = document.querySelector(sel);
      if (el && el.innerText && el.innerText.length > 100) {
        jobDescription = cleanText(el.innerText).substring(0, 2000);
        break;
      }
    }

    // Detect source from URL
    const url = window.location.href;
    let source = "other";
    if (url.includes("linkedin.com"))    source = "linkedin";
    else if (url.includes("indeed.com")) source = "indeed";
    else if (url.includes("stepstone"))  source = "stepstone";
    else if (url.includes("xing.com"))   source = "xing";
    else if (url.includes("monster"))    source = "monster";

    return {
      role_title:      roleTitle,
      company_name:    companyName,
      job_description: jobDescription,
      source:          source
    };
  }

  // Route to correct parser
  function extractJobData() {
    const url = window.location.href;
    let data;

    if (url.includes("linkedin.com"))      data = parseLinkedIn();
    else if (url.includes("indeed.com"))   data = parseIndeed();
    else if (url.includes("stepstone.de")) data = parseStepStone();
    else if (url.includes("xing.com"))     data = parseXing();
    else                                   data = parseGeneric();

    data.job_url = url;
    return data;
  }

  // Store data for popup access
  const jobData = extractJobData();
  chrome.storage.local.set({ jobData: jobData });

})();