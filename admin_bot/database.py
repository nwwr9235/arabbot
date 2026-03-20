"""
admin_bot/database.py
قاعدة بيانات مؤقتة في الذاكرة
(يمكن استبدالها لاحقاً بـ MongoDB عبر Motor)
"""

from typing import Dict, Any

# ------------------------------------------------------------------
# إعدادات المجموعات
# ------------------------------------------------------------------
_group_settings: Dict[int, Dict[str, Any]] = {}

def get_group_settings(chat_id: int) -> Dict[str, Any]:
    if chat_id not in _group_settings:
        _group_settings[chat_id] = {
            "welcome_enabled": True,
            "welcome_message": "مرحباً بك {user} في المجموعة {group}! 🎉",
            "locks": {
                "links":    False,
                "flood":    False,
                "spam":     False,
                "bots":     False,
                "photos":   False,
                "videos":   False,
                "files":    False,
                "stickers": False,
                "voices":   False,
            },
        }
    return _group_settings[chat_id]

# ------------------------------------------------------------------
# نظام الإنذارات
# ------------------------------------------------------------------
_warnings: Dict[int, Dict[int, int]] = {}   # {chat_id: {user_id: count}}

def get_warnings(chat_id: int, user_id: int) -> int:
    return _warnings.get(chat_id, {}).get(user_id, 0)

def add_warning(chat_id: int, user_id: int) -> int:
    _warnings.setdefault(chat_id, {})
    _warnings[chat_id][user_id] = _warnings[chat_id].get(user_id, 0) + 1
    return _warnings[chat_id][user_id]

def reset_warnings(chat_id: int, user_id: int) -> None:
    if chat_id in _warnings:
        _warnings[chat_id][user_id] = 0

# ------------------------------------------------------------------
# الردود التلقائية
# ------------------------------------------------------------------
_auto_replies: Dict[int, Dict[str, str]] = {}   # {chat_id: {trigger: response}}

def get_replies(chat_id: int) -> Dict[str, str]:
    return _auto_replies.get(chat_id, {})

def add_reply(chat_id: int, trigger: str, response: str) -> None:
    _auto_replies.setdefault(chat_id, {})[trigger.lower()] = response

def delete_reply(chat_id: int, trigger: str) -> bool:
    trigger = trigger.lower()
    if chat_id in _auto_replies and trigger in _auto_replies[chat_id]:
        del _auto_replies[chat_id][trigger]
        return True
    return False
