from rest_framework.throttling import UserRateThrottle

from config.settings import TESTING


class _ChatThrottle(UserRateThrottle):
    def allow_request(self, request, view):
        if TESTING:
            return True
        return super().allow_request(request, view)


class ChatSendThrottle(_ChatThrottle):
    """Jazılǵan xabarlar: akkaunt boyınsha minutına 20."""
    scope = 'chat_send'


class ChatPollThrottle(_ChatThrottle):
    """Thread di yamasa oqılmaǵan sandı oqıw: bet polling isleydi, sol sebepli bul ádettegi saatlıq limittan ápiwayı kóp."""
    scope = 'chat_poll'
