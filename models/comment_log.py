from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional

class CommentLog(Document):
    post_author: str
    post_content: str = Field(..., index=True)
    generated_comment: str
    posted_to_linkedin: bool = Field(default=False)
    liked_post: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "comment_logs" # This is the collection name