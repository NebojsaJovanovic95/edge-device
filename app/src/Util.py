from pydantic import BaseModel

class DetectionResponse(BaseModel):
    id: str
    result: dict