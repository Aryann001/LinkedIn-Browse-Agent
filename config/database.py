from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from config.settings import settings
from models.comment_log import CommentLog
from models.selectors import SelectorConfig # <-- ADDED

async def init_db():
    client = AsyncIOMotorClient(settings.MONGO_DB_URL)
    
    await init_beanie(
        database=client[settings.MONGO_DB_NAME],
        document_models=[
            CommentLog,
            SelectorConfig  # <-- ADDED
        ]
    )
    print("Database initialized...")