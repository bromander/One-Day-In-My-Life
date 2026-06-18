import zlib
import json
from typing import Union, Any
from base64 import b64encode, b64decode

def decode(text: Union[str, bytes]) -> Any:
    return json.loads(zlib.decompress(b64decode(text)))

def encode(data: Any) -> str:
    return b64encode(zlib.compress(json.dumps(data, ensure_ascii=False).encode("utf-8"), 9)).decode("ascii")