"""
Request body parsers shared across apps.
"""
from django.utils.translation import gettext as _
from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser


class SafeJSONParser(JSONParser):
    """JSONParser that answers 400, not 500, to JSON nested deeper than Python can read.

    `json.loads` raises RecursionError (not ValueError) on a body such as 20000 opening brackets, which DRF does not catch.
    A few kilobytes from an anonymous caller would otherwise reach the error log as a server error.
    """

    def parse(self, stream, media_type=None, parser_context=None):
        try:
            return super().parse(stream, media_type, parser_context)
        except RecursionError:
            raise ParseError(_('The JSON is nested too deeply.'))
