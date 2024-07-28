import pydantic
import dataclasses

class Thing1(pydantic.BaseModel):
    tid: int
    name: str
    owner: str

@pydantic.dataclasses.dataclass
class Thing2:
    tid: int
    name: str
    owner: str

@dataclasses.dataclass
class Thing3:
    tid: int
    name: str
    owner: str
