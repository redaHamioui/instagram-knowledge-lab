"""Simple shapes for our data."""
from dataclasses import dataclass

@dataclass
class Post:
    url: str                 # unique ID of the post
    creator: str             # username
    timestamp: int | None    # unix epoch seconds, may be None
    interaction: str         # "saved" or "liked"

    def __post_init__(self):
        if self.interaction not in {"saved", "liked"}:
            raise ValueError(f"Unknown interaction: {self.interaction}")
        if not self.url.startswith("http"):
            raise ValueError(f"Invalid URL: {self.url}")