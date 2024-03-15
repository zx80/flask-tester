import random
import string

LENGTH = 16
PASSES: dict[str, str] = {}
CHARS = "".join(string.printable.split(","))

for login in ("calvin", "hobbes", "susie", "moe"):
    PASSES[login] = "".join(random.choice(CHARS) for _ in range(LENGTH))
