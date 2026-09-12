import logging

from tests.fixtures.base import *
from tests.fixtures.database import *
from tests.fixtures.random_objects import *

# Quiet down external libraries during testing
logging.getLogger("asyncio").setLevel(logging.INFO)
