# random passwords for testing

import os
import random
import string

# both client and server must share the same seed!
random.seed(os.environ.get("TEST_SEED", None))

# parameters
PASS_LENGTH: int = 16
PASS_CHARS: str = string.printable.replace(",", "")  # all but ","

# user logins to generate
USERS: list[str] = ["calvin", "hobbes", "susie", "moe"]

# login -> clear-password
PASSES: dict[str, str] = {
    login: "".join(random.choice(PASS_CHARS) for _ in range(PASS_LENGTH))
        for login in USERS
}
