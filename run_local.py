"""Dev entry point on a chosen port: same app, but loopback hosts are allowed so
the bundled fake shortener walls (test_wall.py) can be bypassed end to end.

    python test_wall.py                  # terminal 1
    python run_local.py [port]           # terminal 2  -> http://127.0.0.1:5000

Never use this for real traffic: it disables the private-host guard.
"""

import os
import sys

os.environ["LB_ALLOW_LOCAL"] = "1"

from app import app  # noqa: E402

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
