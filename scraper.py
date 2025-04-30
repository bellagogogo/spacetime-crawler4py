import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, urldefrag

def scraper(url, resp):
    if resp.status != 200 or resp.raw_response is None:
        print(f"Skipping {url} - status: {resp.status}")
        return []

    links = extract_next_links(url, resp)

    valid_links = [link for link in links if is_valid(link)]
    print(f"Returning {len(valid_links)} valid links from {url}")
    return valid_links

def extract_next_links(url, resp):
    output_links = []
    try:
        soup = BeautifulSoup(resp.raw_response.content, "lxml")
        for link_tag in soup.find_all("a"):
            href = link_tag.get("href")
            if href:
                try:
                    absolute_url = urljoin(url, href)  
                    defragmented_url, _ = urldefrag(absolute_url)  
                    output_links.append(defragmented_url)
                except Exception as e:
                    print(f"Error processing link: {href} from {url} — {e}")
    except Exception as e:
        print(f"Error parsing {url}: {e}")

    print(f"Found {len(output_links)} links on {url}")
    return output_links

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
            return False

        if "today.uci.edu" in hostname and not parsed.path.startswith("/department/information_computer_sciences"):
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$",
            parsed.path.lower())
    except Exception as e:
        print(f"Error in is_valid({url}): {e}")
        return False
