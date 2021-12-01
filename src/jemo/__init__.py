import logging
import logging.handlers

__author__ = "Rob Kent"
__email__ = "rob@gulon.co.uk"
__version__ = "v0.0.1"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s:%(lineno)-8d %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("Jemo")
syslog_handler = logging.handlers.SysLogHandler()
logger.addHandler(syslog_handler)
