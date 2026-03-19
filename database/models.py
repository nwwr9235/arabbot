from datetime import datetime
from typing import Optional, List, Dict

class User:
    def __init__(self, user_id, username=None, first_name=None, 
                 last_name=None, is_admin=False, warnings=0):
        self.user_id = user_id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.is_admin = is_admin
        self.is_banned = False
        self.is_muted = False
        self.warnings = warnings
        self.notes = None

class GroupSettings:
    def __init__(self, group_id):
        self.group_id = group_id
        self.welcome_enabled = True
        self.welcome_message = "مرحباً بك في المجموعة!"
        self.locks = {}
        self.locks_enabled = True

class AutoReply:
    def __init__(self, trigger, response, is_regex=False):
        self.trigger = trigger
        self.response = response
        self.is_regex = is_regex

class Song:
    def __init__(self, title, url, requested_by, duration=None, thumbnail=None):
        self.title = title
        self.url = url
        self.requested_by = requested_by
        self.duration = duration
        self.thumbnail = thumbnail

class Queue:
    def __init__(self):
        self.songs = []
        self.current_index = 0
        self.is_playing = False
        self.current_song = None
