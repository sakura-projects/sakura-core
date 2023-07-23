import json
import logging
from typing import Union

from sakura.core.decoders.decoder import Decoder
from sakura.core.exceptions import DecodeError

logger = logging.getLogger(__name__)


class JSONDecoder(Decoder):
    def decode(self, body: Union[str, bytes]) -> dict:
        try:
            return json.loads(body)
        except json.JSONDecodeError as e:
            raise DecodeError(f'JSON decoding failed due to {{{e}}}')

