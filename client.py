import argparse
import sys
import time
import logging
from urllib import request


LOGGING_FORMAT = '%(levelname)s|%(asctime)s|%(name)s|%(fileName)s|%(module)s:%(funcName)s:%(lineno)s|%(message)s'
log = logging.getLogger(__name__)
for h in log.handlers:
    log.removeHandler(h)
log.addHandler(logging.StreamHandler(sys.stderr))
log.setLevel(logging.INFO)


def send_request(host='localhost', port=8000, path='/', timeout=None):
    opener = request.build_opener()
    r = request.Request(
        url=f'http://{host}:{port}{path}',
        method='GET'
    )

    start = time.time()
    try:
        log.info(f'timeout = {timeout}')
        result = None
        if timeout:
            with opener.open(r, timeout=timeout) as f:
                result = f.read().decode('utf-8')
        else:
            with opener.open(r) as f:
                result = f.read().decode('utf-8')
        end = time.time()
        log.info(f'elapsed time: {end - start}')
        return result
    except Exception as e:
        log.exception(e)
        end = time.time()
        log.info(f'elapsed time: {end - start}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', type=str, default='localhost')
    parser.add_argument('-p', '--port', type=int, default=8000, dest='port')
    parser.add_argument('-t', '--timeout', type=float, default=None, dest='timeout')

    args = parser.parse_args()

    send_request(
        host=args.host,
        port=args.port,
        timeout=args.timeout
    )
