from unittest import result

import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re

# User-Agent is the identity string your browser sends to every website
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def detect_source(url:str)->str:
    domain=urlparse(url).netloc.lower()
    if "linkedin" in domain:
        return "linkedin"
    if "indeed.com"    in domain: 
        return "indeed"
    if "stepstone.de"  in domain: 
        return "stepstone"
    if "xing.com"      in domain: 
        return "xing"
    if "monster.com"   in domain: 
        return "monster"
    return "other"

def clean_text(text:str)->str:
    if not text:
        return ""
    text=re.sub(r'\s+', ' ', text)
    return text.strip()

def fetch_page(url:str)->BeautifulSoup | None:
    try:
        response=httpx.get(url,headers=HEADERS,timeout=10,follow_redirects=True)
        if response.status_code!=200:
            return None
        return BeautifulSoup(response.text, "lxml")
    except Exception:
        return None
    
# Site-specific parsers

def parse_linkedin(soup:BeautifulSoup)->dict:
    result={}
    # LinkedIn puts job title in <h1> with specific class
    title=soup.find("h1")
    if title:
        result["role_title"]=clean_text(title.get_text())
    
    # Company name is usually in a link near the title
    company=soup.find("a", class_=re.compile("topcard__org-name|company-name"))
    if not company:
        # Fallback - try meta tag
        meta=soup.find("meta",{"property":"og:title"})
        if meta and " at " in meta.get("content" , ""):
            parts=meta["content"].split(" at ")
            if len(parts) == 2:
                result["role_title"] = parts[0].strip()
                result["company_name"] = parts[1].strip()
    else:
        result["company_name"] = clean_text(company.get_text())

    # Job description div
    desc = soup.find("div", class_=re.compile("description|job-description"))
    if desc:
        result["job_description"] = clean_text(desc.get_text())[:3000]

    return result


def parse_indeed(soup: BeautifulSoup) -> dict:
    """
    Extract job data from an Indeed job posting page.
    Indeed serves mostly static HTML — reliable scraping.
    """
    result = {}

    # Job title is in h1 with data-testid attribute
    title = soup.find("h1", {"data-testid": "jobsearch-JobInfoHeader-title"})
    if not title:
        title = soup.find("h1")
    if title:
        result["role_title"] = clean_text(title.get_text())

    # Company name
    company = soup.find("div", {"data-testid": "inlineHeader-companyName"})
    if not company:
        company = soup.find("a", {"data-testid": "inlineHeader-companyName"})
    if company:
        result["company_name"] = clean_text(company.get_text())

    # Job description
    desc = soup.find("div", {"id": "jobDescriptionText"})
    if not desc:
        desc = soup.find("div", class_=re.compile("jobsearch-jobDescriptionText"))
    if desc:
        result["job_description"] = clean_text(desc.get_text())[:3000]

    return result


def parse_stepstone(soup: BeautifulSoup) -> dict:
    """
    Extract job data from a StepStone job posting.
    StepStone is Germany's largest job board — important for German market.
    """
    result = {}

    title = soup.find("h1")
    if title:
        result["role_title"] = clean_text(title.get_text())

    # StepStone puts company in specific article header
    company = soup.find("span", class_=re.compile("company|employer"))
    if not company:
        company = soup.find("a", class_=re.compile("company|employer"))
    if company:
        result["company_name"] = clean_text(company.get_text())

    desc = soup.find("article")
    if not desc:
        desc = soup.find("div", class_=re.compile("description|content"))
    if desc:
        result["job_description"] = clean_text(desc.get_text())[:3000]

    return result


def parse_generic(soup: BeautifulSoup) -> dict:
    """
    Generic fallback parser for unknown job boards.
    Tries common HTML patterns that most job sites use.
    Gets something useful even from sites we haven't
    specifically coded a parser for.
    """
    result = {}

    # Most sites use h1 for the job title
    title = soup.find("h1")
    if title:
        result["role_title"] = clean_text(title.get_text())

    # Try Open Graph meta tags — most modern sites include these
    # og:title format is often "Job Title at Company Name"
    og_title = soup.find("meta", {"property": "og:title"})
    if og_title:
        content = og_title.get("content", "")
        if " at " in content and not result.get("company_name"):
            parts = content.split(" at ", 1)
            result["role_title"] = parts[0].strip()
            result["company_name"] = parts[1].strip()

    # og:description gives us a summary if no full description found
    og_desc = soup.find("meta", {"property": "og:description"})
    if og_desc and not result.get("job_description"):
        result["job_description"] = og_desc.get("content", "")[:3000]

    # Try to find description in common div patterns
    if not result.get("job_description"):
        for selector in ["job-description", "jobDescription",
                         "job_description", "description"]:
            desc = soup.find("div", {"id": selector})
            if not desc:
                desc = soup.find("div", class_=selector)
            if desc:
                result["job_description"] = clean_text(
                    desc.get_text())[:3000]
                break

    return result


#Main scraper function

def scrape_job(url: str) -> dict:
    source = detect_source(url)
    soup = fetch_page(url)

    # If page fetch failed return empty dict — caller uses manual input
    if not soup:
        return {"source": source}

    # Route to the right parser based on detected source
    parsers = {
        "linkedin":  parse_linkedin,
        "indeed":    parse_indeed,
        "stepstone": parse_stepstone,
    }

    parser = parsers.get(source, parse_generic)
    result = parser(soup)
    result["source"] = source

    return result
