import logging

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)
COLORS = {
    'WARNING': YELLOW,
    'INFO': BLUE,
    'DEBUG': WHITE,
    'CRITICAL': RED,
    'ERROR': RED
}


class ColoredFormatter(logging.Formatter):
    def __init__(self, msg):
        logging.Formatter.__init__(self, msg)

    def format(self, record):
        levelname = record.levelname
        if levelname in COLORS:
            levelname_color = "\033[1;%dm" % (30 + COLORS[levelname]) + levelname + "\033[0m"
            record.levelname = levelname_color
        return logging.Formatter.format(self, record)


def get_razor_logger():
    log = logging.getLogger("Razor")
    handler = logging.StreamHandler()
    formatter = ColoredFormatter('%(levelname)s:: %(message)s')
    handler.setFormatter(formatter)
        log.addHandler(handler)
    log.setLevel(logging.DEBUG)
    return log
