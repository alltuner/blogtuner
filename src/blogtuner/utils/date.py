from datetime import datetime

import dateutil.parser


def date_to_dt(date_str: str) -> datetime:
    return dateutil.parser.isoparse(date_str).replace(tzinfo=None)
