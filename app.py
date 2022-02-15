from app import create_app
from app.core import core
import sys

if len(sys.argv) > 1:
    print(sys.argv[1])
    from glob import glob
    import os
    os.environ["NET_TEXTFSM"] = os.path.abspath(os.path.dirname('.'))+ \
        '/' + ''.join(glob(".venv/**/ntc_templates/templates", recursive=True))
    core.main(inventory=sys.argv[1])
    exit()
else:
    app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
