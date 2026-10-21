from pydantic import BaseModel


class Health(BaseModel):
    status: str
    environment: str
    project: str
