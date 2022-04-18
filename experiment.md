# 実験

人為的にレスポンスを遅延する HTTP Server を作成し、urllib で timeout 指定をせずリクエストを飛ばすようにする。

検証したいことは「urllib を使って永遠にレスポンスを返さないサーバーに向けて HTTP リクエストを送信するとき、timeout の指定の有無で結果がどう変わるか」

得られた洞察は「おそらく、Client 側で urllib ないし socket で timeout を指定しなかった場合のクライアントの挙動は「永遠に待ち続ける」」。実際にはサーバーサイドのミドルウェア (nginx など) がアプリケーションの応答待ちを打ち切って強制切断すると思われるので、今回の検証内容は実際のサービスの API を叩く際の条件とは異なることに留意。

## case 1

- Server 側は応答を長時間返さない設定
- Client 側は 30 -　70s 程度を timeout 指定してリクエスト

```bash
# server
python -m server
```

```bash
# client
#
# Request [1]
#
python -m client -H localhost -p 8000 -t 35
# >>> timeout = 35.0
# >>> timed out
# >>> Traceback (most recent call last):
# >>>   File "/path/to/project/socket-timeout-experiment/client.py", line 28, in send_request
# >>>     with opener.open(r, timeout=timeout) as f:
# >>>   File "/home/dir/.pyenv/versions/3.8.5/lib/python3.8/urllib/request.py", line 525, in open
# >>>     response = self._open(req, data)
# >>>   File "/home/dir/.pyenv/versions/3.8.5/lib/python3.8/urllib/request.py", line 542, in _open
# >>>     result = self._call_chain(self.handle_open, protocol, protocol +
# >>>   File "/home/dir/.pyenv/versions/3.8.5/lib/python3.8/urllib/request.py", line 502, in _call_chain
# >>>     result = func(*args)
# >>>   File "/home/dir/.pyenv/versions/3.8.5/lib/python3.8/urllib/request.py", line 1379, in http_open
# >>>     return self.do_open(http.client.HTTPConnection, req)
# >>>   File "/home/dir/.pyenv/versions/3.8.5/lib/python3.8/urllib/request.py", line 1354, in do_open
# >>>     r = h.getresponse()
# >>>   File "/home/dir/.pyenv/versions/3.8.5/lib/python3.8/http/client.py", line 1347, in getresponse
# >>>     response.begin()
# >>>   File "/home/dir/.pyenv/versions/3.8.5/lib/python3.8/http/client.py", line 307, in begin
# >>>     version, status, reason = self._read_status()
# >>>   File "/home/dir/.pyenv/versions/3.8.5/lib/python3.8/http/client.py", line 268, in _read_status
# >>>     line = str(self.fp.readline(_MAXLINE + 1), "iso-8859-1")
# >>>   File "/home/dir/.pyenv/versions/3.8.5/lib/python3.8/socket.py", line 669, in readinto
# >>>     return self._sock.recv_into(b)socket.timeout: timed out
# >>> elapsed time: 35.00969386100769

#
# Request [2]
#
python -m client -H localhost -p 8000 -t 70
# >>> timeout = 70.0
# >>> timed out
# >>> Traceback (most recent call last):
# >>>   File "/path/to/project/socket-timeout-experiment/client.py", line 28, in send_request
# >>>     with opener.open(r, timeout=timeout) as f:
# >>>   File "/home/dir/.pyenv/versions/3.8.5/lib/python3.8/urllib/request.py", line 525, in open
# >>>     response = self._open(req, data)
# >>>   File "/home/dir/.pyenv/versions/3.8.5/lib/python3.8/urllib/request.py", line 542, in _open
# >>>     result = self._call_chain(self.handle_open, protocol, protocol +
# >>>   File "/home/dir/.pyenv/versions/3.8.5/lib/python3.8/urllib/request.py", line 502, in _call_chain
# >>>     result = func(*args)
# >>>   File "/home/dir/.pyenv/versions/3.8.5/lib/python3.8/urllib/request.py", line 1379, in http_open
# >>>     return self.do_open(http.client.HTTPConnection, req)
# >>>   File "/home/dir/.pyenv/versions/3.8.5/lib/python3.8/urllib/request.py", line 1354, in do_open
# >>>     r = h.getresponse()
# >>>   File "/home/dir/.pyenv/versions/3.8.5/lib/python3.8/http/client.py", line 1347, in getresponse
# >>>     response.begin()
# >>>   File "/home/dir/.pyenv/versions/3.8.5/lib/python3.8/http/client.py", line 307, in begin
# >>>     version, status, reason = self._read_status()
# >>>   File "/home/dir/.pyenv/versions/3.8.5/lib/python3.8/http/client.py", line 268, in _read_status
# >>>     line = str(self.fp.readline(_MAXLINE + 1), "iso-8859-1")
# >>>   File "/home/dir/.pyenv/versions/3.8.5/lib/python3.8/socket.py", line 669, in readinto
# >>>     return self._sock.recv_into(b)
# >>> socket.timeout: timed out
# >>> elapsed time: 70.00765109062195
```

意図した通り、Client 側で socket timeout が発生した

```bash
127.0.0.1 - - [19/Apr/2022 00:37:45] "GET / HTTP/1.1" 200 -
elapsed time: 65.00607681274414
```

## case 2

- Server 側は応答を長時間返さない設定
- Client 側は timeout を指定しない (=None)

```bash
# server
python -m server
```

```bash
# client
python -m client -H localhost -p 8000
```

Server 側では途中で Broken pipe が発生

> BrokenPipeError: [Errno 32] Broken pipe

Client 側は Server 側が設定した長時間の Timeout まで待ち続けた
