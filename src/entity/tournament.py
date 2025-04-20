from typing import Literal
from pydantic import BaseModel, Field

class Tournament(BaseModel):
    name: str = Field(description="The tournament's name.", json_schema_extra={"example": "'Wimbledon'"})
    series: Literal['ATP250', 'ATP500', 'Grand Slam', 'Masters 1000', 'Masters', 'Masters Cup', 'International Gold', 'International'] = 'Grand Slam'
    court: Literal['Outdoor', 'Indoor'] = 'Outdoor'
    surface: Literal['Grass', 'Carpet', 'Clay', 'Hard'] = 'Grass'
    