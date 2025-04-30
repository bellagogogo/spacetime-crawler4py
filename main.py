import configparser
from crawler import Crawler
from utils.config import Config
from utils.server_registration import get_cache_server
import sys

def main():
    parser = configparser.ConfigParser()
    parser.read("./config.ini")    

    config = Config(parser)          
    config.cache_server = get_cache_server(config, len(sys.argv) > 1 and sys.argv[1] == "restart")

    if len(sys.argv) > 1 and sys.argv[1] == "restart":
        restart = True
    else:
        restart = False

    crawler = Crawler(config, restart)
    crawler.start()

if __name__ == "__main__":
    main()
