from threading import Thread, Lock
from urllib.parse import urlparse

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time


class Worker(Thread):
    domain_access_lock = Lock()
    domain_last_accessed = {}
    total_runs = 0
    
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
    
    @staticmethod
    def extract_domain_from_url(url):
        parsed_url = urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}/"
    
    def control_domain_request_rate(self, domain):
        with Worker.domain_access_lock:
            current_time = time.time()
            last_accessed = Worker.domain_last_accessed.get(domain, 0)
            time_to_wait = max(0, 0.5 - (current_time - last_accessed))
            time.sleep(time_to_wait)
            Worker.domain_last_accessed[domain] = time.time()
            
    def run(self):
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            
            domain = self.extract_domain_from_url(tbd_url)
            self.control_domain_request_rate(domain)
            
            try:
                resp = download(tbd_url, self.config, self.logger)
                self.logger.info(
                    f"Downloaded {tbd_url}, status <{resp.status}>, "
                    f"using cache {self.config.cache_server}.")
                scraped_urls = scraper.scraper(tbd_url, resp)
                for scraped_url in scraped_urls:
                    self.frontier.add_url(scraped_url)
                self.frontier.mark_url_complete(tbd_url)
            except Exception as e:
                self.logger.error(f"Error downloading {tbd_url}: {e}")
            
            if Worker.total_runs > 0 and Worker.total_runs % 99 == 0:
                scraper.print_stats()
            
            self.total_runs += 1
            
            time.sleep(self.config.time_delay)
