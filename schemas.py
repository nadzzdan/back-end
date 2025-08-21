from pydantic import BaseModel

class TextIn(BaseModel):
    content: str

class TextOut(TextIn):
    id: int
