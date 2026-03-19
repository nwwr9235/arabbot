# database/models.py
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field

class User(BaseModel):
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    is_admin: bool = False
    is_banned: bool = False
    is_muted: bool = False
    warnings: int = 0
    notes: Optional[str] = None

class GroupSettings(BaseModel):
    group_id: int
    welcome_enabled: bool = True
    welcome_message: str = "مرحباً بك في المجموعة!"
    welcome_message_enabled: bool = True
    locks: Dict[str, bool] = Field(default_factory=dict)
    locks_enabled: bool = True

class AutoReply(BaseModel):
    trigger: str
    response: str
    is_regex: bool = False

class Song(BaseModel):
    title: str
    url: str
    requested_by: str
    duration: Optional[str] = None
    thumbnail: Optional[str] = None

class Queue(BaseModel):
    songs: List[Song] = Field(default_factory=list)
    current_index: int = 0
    is_playing: bool = False
    current_song: Optional[Song] = None

class Note(BaseModel):
    note: str

