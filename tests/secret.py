# random passwords for testing

import os
import random
import string

# both client and server must share the same seed!
random.seed(os.environ.get("TEST_SEED", None))

# parameters
LENGTH: int = 16
CHARS: str = string.printable.replace(",", "")  # all but ","
USERS: list[str] = ["calvin", "hobbes", "susie", "moe"]

# login -> clear-password
PASSES: dict[str, str] = {
    login: "".join(random.choice(CHARS) for _ in range(LENGTH))
        for login in USERS
}
