import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, urldefrag
from collections import defaultdict, Counter

TEST_MODE = False

visited_urls = set()            
subdomain_counts = defaultdict(int)  
word_counter = Counter()         
longest_page_url = ""
max_word_count = 0

stop_words = set()
try:
    with open("stopwords.txt", "r") as f:
        stop_words = set(line.strip().lower() for line in f)
except Exception as e:
    print(f"Warning: Could not load stop words: {e}")
    stop_words = {"a", "an", "the", "and", "or", "but", "is", "are", "was", 
                  "were", "be", "been", "being", "in", "on", "at", "to", "for",
                  "with", "by", "about", "against", "between", "into", "through",
                  "during", "before", "after", "above", "below", "from", "up", "down",
                  "of", "off", "over", "under", "again", "further", "then", "once"}

def scraper(url, resp):
    """
    Parse the response and extract links to be used in the next crawling wave.
    Args:
        url: the URL that was added to the frontier and downloaded from the cache
        resp: the response object corresponding to the page that was downloaded
    Returns:
        list of URLs that should be added to the frontier
    """
    global visited_urls, subdomain_counts, word_counter, longest_page_url, max_word_count

    if len(visited_urls) == 0:
        print("Adding additional seed URLs...")
        additional_seeds = [
            "https://www.cs.uci.edu",
            "https://www.informatics.uci.edu",
            "https://www.stat.uci.edu",
            "https://today.uci.edu/department/information_computer_sciences"
        ]
        valid_seeds = [seed for seed in additional_seeds if is_valid(seed)]
        if valid_seeds:
            return valid_seeds

    if resp.status != 200 or resp.raw_response is None:
        print(f"Skipping {url} - Status: {resp.status}")
        return []
    
    try:
        links = extract_next_links(url, resp)
        defragmented_url, _ = urldefrag(url)
        
        if defragmented_url not in visited_urls:
            visited_urls.add(defragmented_url)
            print(f"Crawled {len(visited_urls)} unique pages so far...")

            parsed = urlparse(defragmented_url)
            if parsed.hostname and parsed.hostname.endswith(".uci.edu"):
                subdomain_counts[parsed.hostname] += 1

            try:
                soup = BeautifulSoup(resp.raw_response.content, "lxml")
  
                for script in soup(["script", "style"]):
                    script.extract()

                text = soup.get_text(separator=' ', strip=True)
                words = [word.lower() for word in re.findall(r'\b\w+\b', text)]
                filtered_words = [word for word in words if word not in stop_words]
                word_counter.update(filtered_words)

                if len(words) > max_word_count:
                    max_word_count = len(words)
                    longest_page_url = defragmented_url
                    print(f"New longest page: {longest_page_url} with {max_word_count} words")

                if detect_trap(url, text, soup):
                    print(f"Potential trap detected: {url}")
                    return []
                    
            except Exception as e:
                print(f"Error processing content of {url}: {e}")

        valid_links = [link for link in links if is_valid(link)]
        return valid_links
    
    except Exception as e:
        print(f"Error in scraper processing {url}: {e}")
        return []

def extract_next_links(url, resp):
    """
    Extract all links from the response.
    Args:
        url: the URL of the page
        resp: the response object
    Returns:
        a list of URLs extracted from the page
    """
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
                    print(f"Error processing link {href}: {e}")
    except Exception as e:
        print(f"Error parsing {url}: {e}")
    
    return output_links

def is_valid(url):
    """
    Function returns True or False based on whether the url has to be downloaded or not.
    This is a great place to filter out crawler traps.
    """
    if TEST_MODE:
        try:
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"}:
                return False

            allowed_domains = [
                "ics.uci.edu",
                "cs.uci.edu",
                "informatics.uci.edu",
                "stat.uci.edu",
                "today.uci.edu"
            ]
            
            domain_valid = False
            for domain in allowed_domains:
                if parsed.netloc.endswith(domain):
                    domain_valid = True
                    break
                    
            if not domain_valid:
                return False

            return not re.match(
                r".*\.(css|js|bmp|gif|jpe?g|ico|png|tiff?|mid|mp2|mp3|mp4)$", 
                parsed.path.lower())
        except Exception as e:
            print(f"Error in TEST_MODE validation for {url}: {e}")
            return False

    try:
        parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"}:
            return False

        allowed_domains = [
            "ics.uci.edu",
            "cs.uci.edu",
            "informatics.uci.edu",
            "stat.uci.edu",
            "today.uci.edu"
        ]
        
        domain_valid = False
        for domain in allowed_domains:
            if parsed.netloc.endswith(domain):
                domain_valid = True
                break
        
        if not domain_valid:
            return False

        if "today.uci.edu" in parsed.netloc:
            if not parsed.path.startswith("/department/information_computer_sciences"):
                return False
                
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
    
    except Exception as e:
        print(f"Error validating URL {url}: {e}")
        return False

def detect_trap(url, text, soup):
    """
    Detect if a page is a crawler trap.
    Args:
        url: the URL of the page
        text: the text content of the page
        soup: the BeautifulSoup object for the page
    Returns:
        True if the page is likely a trap, False otherwise
    """
    try:
        parsed = urlparse(url)

        if re.search(r'calendar|event|date=\d+', url.lower()):
            calendar_links = 0
            for link in soup.find_all('a'):
                href = link.get('href', '')
                if re.search(r'calendar|event|date=\d+', href.lower()):
                    calendar_links += 1

            if calendar_links > 30:
                return True

        if re.search(r'page=\d+|p=\d+|offset=\d+', url.lower()):
            pagination_links = 0
            for link in soup.find_all('a'):
                href = link.get('href', '')
                if re.search(r'page=\d+|p=\d+|offset=\d+', href.lower()):
                    pagination_links += 1

            if pagination_links > 20:
                return True

        if len(text) > 500000: 
            return True

        if len(soup.find_all('a')) > 300:
            return True
  
        html_size = len(str(soup))
        if html_size > 0:
            text_ratio = len(text) / html_size
            if text_ratio < 0.05 and html_size > 50000:  
                return True
        
        return False
    
    except Exception as e:
        print(f"Error in trap detection for {url}: {e}")
        return False

def generate_report():
    """
    Generate a report with the required analytics.
    """
    print("\n" + "="*50)
    print("CRAWLER REPORT")
    print("="*50)

    print(f"\n1. Total unique pages crawled: {len(visited_urls)}")

    print(f"\n2. Longest page: {longest_page_url} with {max_word_count} words")

    print("\n3. 50 most common words (excluding stop words):")
    for i, (word, count) in enumerate(word_counter.most_common(50), 1):
        print(f"   {i}. {word}: {count}")
        
    sorted_subdomains = sorted(subdomain_counts.items())
    print(f"\n4. Subdomains found ({len(sorted_subdomains)} total):")
    for subdomain, count in sorted_subdomains:
        print(f"   {subdomain}, {count}")
    
    print("="*50)