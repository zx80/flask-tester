# random passwords for testing

import os
import random  # a misnomer, should be called "pseudo-random"
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
    login: "".join(random.choices(PASS_CHARS, k=PASS_LENGTH))
        for login in USERS
}
