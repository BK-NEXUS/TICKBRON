"""
App lar ortaq paydalanatuǵın request body parser leri.
"""
from django.utils.translation import gettext as _
from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser


class SafeJSONParser(JSONParser):
    """Python oqıy alatuǵınnan tereń oralǵan JSON ǵa 500 emes 400 menen juwap beretuǵın JSONParser.

    `json.loads` 20000 ashıq jaqshası bar denede RecursionError (ValueError emes) kóteredi, DRF onı tutpaydı.
    Anonim shaqırıwshıdan kelgen bir neshe kilobayt basqasha server qátesi retinde qátelik log ına túsedi.
    """

    def parse(self, stream, media_type=None, parser_context=None):
        try:
            return super().parse(stream, media_type, parser_context)
        except RecursionError:
            raise ParseError(_('The JSON is nested too deeply.'))
