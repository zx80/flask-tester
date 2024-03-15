# random passwords for testing

import os
import random
import string

LENGTH = 16
PASSES: dict[str, str] = {}
CHARS = "".join(string.printable.split(","))  # all but ","

# both client and server must share the same seed.
random.seed(os.environ.get("TEST_SEED", "please set TEST_SEED"))

# generate 4 users with pseudo-random 16-chars passwords
for login in ("calvin", "hobbes", "susie", "moe"):
    PASSES[login] = "".join(random.choice(CHARS) for _ in range(LENGTH))
