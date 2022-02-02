from app import create_app
from app.core import core
import sys

if len(sys.argv) > 1:
    print(sys.argv[1])
    core.main(sys.argv[1])
    exit()
else:
    app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
