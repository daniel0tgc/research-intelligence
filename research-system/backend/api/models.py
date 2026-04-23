from pydantic import BaseModel


class ChatRequest(BaseModel):
    paper_id: str | None = None
    query: str
