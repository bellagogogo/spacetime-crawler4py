import re

class Config(object):
    def __init__(self, parser):
        self.user_agent = parser.get("IDENTIFICATION", "USERAGENT").strip()
        print(self.user_agent)
        assert self.user_agent != "DEFAULT AGENT", "Set useragent in config.ini"
        assert re.match(r"^[a-zA-Z0-9_ ,]+$", self.user_agent), "User agent should not have any special characters outside '_', ',' and 'space'"

        self.threads_count = int(parser.get("LOCAL PROPERTIES", "THREADCOUNT"))
        self.save_file = parser.get("LOCAL PROPERTIES", "SAVE")

        self.host = parser.get("CONNECTION", "HOST")
        self.port = int(parser.get("CONNECTION", "PORT"))

        self.seed_urls = parser.get("CRAWLER", "SEEDURL").split(",")
        self.time_delay = float(parser.get("CRAWLER", "POLITENESS"))

        self.cache_server = None
