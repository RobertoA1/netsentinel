from app.services.parsers.base import (DirectionClassifier, LineParser, ParseError, ParseStats,  # noqa: F401
                                       parse_stream)
from app.services.parsers.ctu13 import Ctu13Parser
from app.services.parsers.opnsense import OpnsenseFilterlogParser
from app.services.parsers.suricata import SuricataEveParser

PARSERS = {
    "opnsense_filterlog": OpnsenseFilterlogParser,
    "suricata_eve": SuricataEveParser,
    "ctu13_binetflow": Ctu13Parser,
}


def get_parser(source_format: str) -> LineParser:
    try:
        return PARSERS[source_format]()
    except KeyError as e:
        raise ValueError(f"Formato de fuente no soportado: {source_format}") from e
