import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    output_links = []

    if resp.status != 200 or resp.raw_response is None:
        return output_links

    try:
        soup = BeautifulSoup(resp.raw_response.content, "lxml")
        for tag in soup.find_all("a"):
            href = tag.get("href")
            if href:
                joined_url = urljoin(url, href)
                clean_url, _ = urldefrag(joined_url)
                output_links.append(clean_url)
    except Exception as e:
        print(f"Error extracting links from {url}: {e}")

    return output_links

    print("Checking:", url)

def is_valid(url):
    try:
        parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"}:
            return False

        valid_domains = [
            "ics.uci.edu",
            "cs.uci.edu",
            "informatics.uci.edu",
            "stat.uci.edu",
            "today.uci.edu"
        ]

        hostname = parsed.hostname or ""
        if not any(hostname.endswith(domain) for domain in valid_domains):
            print("❌ Rejected (not valid domain):", hostname)
            return False

        if "today.uci.edu" in hostname and not parsed.path.startswith("/department/information_computer_sciences"):
            print("❌ Rejected (bad path for today.uci.edu):", parsed.path)
            return False

        import re
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$",
            parsed.path.lower()
        )

    except Exception as e:
        print(f"❌ Rejected (error): {e}")
        return False
