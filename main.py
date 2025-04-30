import configparser
from crawler import Crawler
from utils.config import Config
import sys

def main():
    parser = configparser.ConfigParser()
    parser.read("config.ini")

    config = Config(parser)
    print("SEED URLs:", config.seed_urls)
    config.cache_server = (config.host, config.port)  

    restart = len(sys.argv) > 1 and sys.argv[1] == "restart"

    crawler = Crawler(config, restart)
    crawler.start()

if __name__ == "__main__":
    main()
