import sys
import json
from datetime import datetime

def _log(level: str, msg: str, **kwargs):
    log_entry = {
        'time': datetime.utcnow().isoformat(),
        'level': level,
        'msg': msg,
    }
    log_entry.update(kwargs)
    print(json.dumps(log_entry), file=sys.stderr)

def log_info(msg: str, **kwargs):
    _log('INFO', msg, **kwargs)

def log_warn(msg: str, **kwargs):
    _log('WARN', msg, **kwargs)

def log_error(msg: str, **kwargs):
    _log('ERROR', msg, **kwargs)
