from rest_framework.throttling import UserRateThrottle

from config.settings import TESTING


class _ChatThrottle(UserRateThrottle):
    def allow_request(self, request, view):
        if TESTING:
            return True
        return super().allow_request(request, view)


class ChatSendThrottle(_ChatThrottle):
    """Messages written: 20 a minute per account."""
    scope = 'chat_send'


class ChatPollThrottle(_ChatThrottle):
    """Reading a thread or the unread count: the page polls, so this is far above the default hourly limit."""
    scope = 'chat_poll'
