import re
from urllib.parse import urlparse, urldefrag, urljoin, parse_qs
from bs4 import BeautifulSoup
from collections import defaultdict, Counter
import logging

MAXIMUM_CONTENT_LENGTH = 500000000 # 50MB limit
SIGNIFICANT_CONTENT_LENGTH = 200

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

stop_words = {'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't",
              'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by',
              "can't", 'cannot', 'could', "couldn't", 'did', "didn't", 'do', 'does', "doesn't", 'doing', "don't",
              'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', "hadn't", 'has', "hasn't", 'have',
              "haven't", 'having', 'he', "he'd", "he'll", "he's", 'her', 'here', "here's", 'hers', 'herself', 'him',
              'himself', 'his', 'how', "how's", 'i', "i'd", "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', "isn't",
              'it', "it's", 'its', 'itself', "let's", 'me', 'more', 'most', "mustn't", 'my', 'myself', 'no', 'nor',
              'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out',
              'over', 'own', 'same', "shan't", 'she', "she'd", "she'll", "she's", 'should', "shouldn't", 'so', 'some',
              'such', 'than', 'that', "that's", 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there',
              "there's", 'these', 'they', "they'd", "they'll", "they're", "they've", 'this', 'those', 'through', 'to',
              'too', 'under', 'until', 'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'were',
              "weren't", 'what', "what's", 'when', "when's", 'where', "where's", 'which', 'while', 'who', "who's",
              'whom', 'why', "why's", 'with', "won't", 'would', "wouldn't", 'you', "you'd", "you'll", "you're",
              "you've", 'your', 'yours', 'yourself', 'yourselves', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k',
              'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'}

found_pages = {} # key = hash of word tokens, value = url
# Used to check for similarity between pages

# the page with the highest amount of words
largest_page = 0
largest_page_url = ''

word_frequency = Counter() # for 50 most common words
subdomains = defaultdict(int) # for subdomains of ics.uci.edu


def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    global found_pages, subdomains, stop_words, largest_page, largest_page_url, word_frequency
    links = set()
    
    try:
        if resp.status != 200 or not resp.raw_response or not resp.raw_response.content:
            logger.error(f"Invalid response for {url}: {resp.status}")
            return links

        content = resp.raw_response.content
        if len(content) == 0: # empty page
            logger.info(f"Empty page for {url}")
            return links

        if len(content) > MAXIMUM_CONTENT_LENGTH:
            logger.info(f"Skipping large page for {url}")
            return links
        
        soup = BeautifulSoup(content, 'html.parser')
        text_content = soup.get_text()
        
        tokenized = [word.lower() for word in re.findall(r'\b[a-zA-Z][a-zA-Z\']*[a-zA-Z]\b', text_content)
                     if word.lower() not in stop_words]
        
        if tokenized:
            # Update wrod frequency
            word_frequency.update(tokenized)
            
            if len(tokenized) < SIGNIFICANT_CONTENT_LENGTH:
                return links
            
            token_hash = hash(tuple(tokenized)) 

            if token_hash in found_pages:
                return links
            
            found_pages[token_hash] = url
            
            if len(tokenized) > largest_page:
                largest_page = len(tokenized)
                largest_page_url = url
                
            if (is_subdomain(url)):
                subdomains[urlparse(url).hostname] += 1
                
            for tag in soup.find_all('a', href=True):
                link = tag['href']
                defragmented_link = urldefrag(link).url # remove fragment
                absolute_link = urljoin(url, defragmented_link)
                if is_valid(absolute_link):
                    links.add(absolute_link)
                
            print(f'URL Scraped: {url}')
            print(f'Wrod count: {len(tokenized)}')
            print(f'Links found: {len(links)}')
    except:
        print(f'FAILED TO SCRAPE {url}')
    return links




def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        if url == "http://circadiomics.ics.uci.edu/upload": # problematic large url
            return False

        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        # Check if the domain is one of the allowed domains
        
        if 'archive.ics.uci.edu' in url: # very large subdomain
            return False

        allowed_domains = ['.ics.uci.edu', '.cs.uci.edu', '.stat.uci.edu', '.informatics.uci.edu']
        valid = False
        for domain in allowed_domains:
            if domain in str(parsed.netloc):
                valid = True
        if not valid:
            return False

        # Avoid the calendar trap
        #elif re.match('^.calendar.*$', parsed.path):
        #    return False
        if parsed.path.startswith('.calendar'):
            return False

        # Avoid increment numbers
        if re.search(r'(/page\d+)|(/(0?[1-9]|[12]\d|3[01]))', parsed.path) or re.search(r'/[a-z]$',                                                                     parsed.path):
            return False

        # Avoid excessive query parameter
        query_params = parse_qs(parsed.query)
        if len(query_params) > 15:
            return False

        # Additional filtering for file extensions
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4|mpg"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", url)
        return False


def is_subdomain(url): # checks if url is a subdomain of .ics.uci.edu
    sub_domain = urlparse(url).hostname
    if sub_domain and sub_domain.endswith('.ics.uci.edu') and sub_domain != 'www.ics.uci.edu':
        return True
    return False


def print_reports():
    try:
        words_frequency = sorted(((frequency, word) for word, frequency in word_frequency.items()), reverse=True)
        subdomains = sorted((dom, count) for dom, count in subdomains.items())
        
        with open("report.txt", "w") as f:
            f.write("_______________R E P O R T_______________\n\n")
            f.write(f"Unique Pages Found: {len(found_pages)}\n")
            f.write(f"Largest Page: {largest_page} with {largest_page_url} words\n\n")
            f.write(f"50 most common words:\n")
            for i in range(50):
                f.write(f"  {i+1}.{words_frequency[i][0]}: {words_frequency[i][1]} ")
            f.write("\n\n")
            f.write(f"Subdomains:\n")
            for i in range(len(subdomains)):
                f.write(f"  {subdomains[i][0]}: {subdomains[i][1]}")

    except:
        print("Error in print_reports")