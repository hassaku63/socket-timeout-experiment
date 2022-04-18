import argparse
import sys
import logging
import socketserver
from http.server import (
    HTTPServer,
    BaseHTTPRequestHandler,
)
from time import (
    sleep,
    time,
)


LOGGING_FORMAT = '%(levelname)s|%(asctime)s|%(name)s|%(fileName)s|%(module)s:%(funcName)s:%(lineno)s|%(message)s'
log = logging.getLogger(__name__)
for h in log.handlers:
    log.removeHandler(h)
log.addHandler(logging.StreamHandler(sys.stderr))
log.setLevel(logging.INFO)


host_name = 'localhost'
_timeout = None

class TooShowRequestHander(BaseHTTPRequestHandler):
    def do_GET(self):
        global _timeout
        start = time()
        sleep(_timeout if _timeout else 100000)
        self.send_response(200)
        self.send_header("Content-Type", "plain/text")
        self.end_headers()
        self.wfile.write(f'requested path = {self.path}'.encode('utf-8'))
        end = time()
        log.info(f'elapsed time: {end - start}')


def run(port: int = 8000, timeout: float = 30):
    global _timeout
    _timeout = timeout
    addr = (host_name, port)
    httpd = HTTPServer(addr, TooShowRequestHander)
    log.info(f"Server started http://{addr[0]}:{addr[1]}")
    # httpd.server_bind()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

    httpd.server_close()
    log.info('server stopped.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=8000, dest='port')
    parser.add_argument('-t', '--timeout', type=float, default=None, dest='timeout')

    args = parser.parse_args()
    str_timeout =  f'{args.timeout}s' if args.timeout else f'{args.timeout}'
    log.info(f'port: {args.port}, timeout: {str_timeout}')

    run(args.port, args.timeout)
