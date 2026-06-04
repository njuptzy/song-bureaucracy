from typing import TypedDict
import json

class CoTResponse(TypedDict):
  role: str
  type: str
  content: str

def parse_response(content) -> list[CoTResponse]:
  pass