import argparse
import logging
import re

from dotenv import load_dotenv
from flask import Flask
from infrastructures.config import configure_injector
from routes import routes

load_dotenv(".env")

configure_injector()
app = Flask(__name__)

routes(app)
with app.app_context():

    def ignore_handler(payload, **kw):
        ignore_patterns = [r"^MethodNotAllowed$", r"^BadRequest$"]
        try:
            exception_class = \
                payload['data']['body']['trace']['exception']['class']
        except KeyError:
            return payload
        if any(re.match(pattern, exception_class)
               for pattern in ignore_patterns):
            return False
        return payload
 
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Flask App')
    parser.add_argument('--port', type=int, default=5001,
                        help='Custom Port number')
    args = parser.parse_args()

    app.run(host="0.0.0.0", port=args.port)
else:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
