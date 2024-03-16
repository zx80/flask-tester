# random passwords for testing

import os
import random
import string

# parameters
LENGTH = 16
CHARS = string.printable.replace(",", "")  # all but ","
USERS = ["calvin", "hobbes", "susie", "moe"]

# login -> clear-password
PASSES: dict[str, str] = {}

# both client and server must share the same seed!
random.seed(os.environ.get("TEST_SEED", None))

# generate 4 users with pseudo-random 16-chars passwords
for login in USERS:
    PASSES[login] = "".join(random.choice(CHARS) for _ in range(LENGTH))
