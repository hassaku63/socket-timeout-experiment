# README

urllib.urlopen で timeout を指定しなかった場合、または socket.getddefaulttimeout() の値がいくつなのかわからないので、それを調べてみた、というもの。

https://twitter.com/hassaku_63/status/1516040286665048069

## 経緯

もともとは SaaS が公開している API がちょくちょく戻ってこず、実行ランタイムの AWS Lambda が invocation timeout してしまう事象が発生していたことがきっかけ

この対策として、Lambda 側の invocation timeout を延ばす、リトライの間隔を広げたうえでリトライ回数を確保する、などの対策があるが、HTTP Client の方でも明示的に Timeout を指定しておきたいと考えた（Lambda の Invocation timeout が発生してしまうと、その function の中ではハンドリングのしようがないため）。

この SaaS サービスは Python SDK を OSS で公開しており、HTTP レイヤーは urllib に依存している。しかし、SDK のインタフェースとして提供している引数の仕様に timeout はなく、デフォルト値に委ねられていた。この「デフォルト値」がどういった値なのか、urllib やその下の socket を見ても実数値を確認できなかったため、それを実験で確認してみようと思いこのレポジトリを作った。

## 調査

Python 3.10 の [urllib](https://docs.python.org/3/library/urllib.request.html#module-urllib.request) によれば、HTTP リクエストを飛ばす際には `timeout` 引数が指定でき、もし指定しなければ "global default timeout" なる値に従うとの記述がある。

> The optional timeout parameter specifies a timeout in seconds for blocking operations like the connection attempt (if not specified, the global default timeout setting will be used). This actually only works for HTTP, HTTPS and FTP connections.

この timeout は下位レイヤーにあたる [socket](https://docs.python.org/3/library/socket.html) で定義されている。

これは上記ドキュメントから urllib のソースをたどると `urlopen()` や `OpenerDirector.open()` の引数から確認できる。

https://github.com/python/cpython/blob/3.10/Lib/urllib/request.py#L139

https://github.com/python/cpython/blob/3.10/Lib/urllib/request.py#L500

`socket._GLOBAL_DEFAULT_TIMEOUT` という値がデフォルトとなるようだが、当の `socket._GLOBAL_DEFAULT_TIMEOUT` は socket.py の中ではただの object として初期化されているだけで、パッと判明しない。

https://github.com/python/cpython/blob/3.10/Lib/socket.py#L806

`scoket.getdefaulttimeout()` という関数も叩いてみたが、None が返ってくる。 ipython でこの関数の docstring を出してみると、「timeout を設定していない」というように見受けられた

> > socket.getdefaulttimeout?
> Docstring:
> getdefaulttimeout() -> timeout
>
> Returns the default timeout in seconds (float) for new socket objects.
> A value of None indicates that new socket objects have no timeout.
> When the socket module is first imported, the default is None.

`scoket.getdefaulttimeout()` は C で書かれたモジュールなので、そちらのソースをあたってみるも、特にデフォルト値を指定するようなコードはなかった。

https://github.com/python/cpython/blob/3.10/Modules/socketmodule.c#L6660-L6672

---

ここまで読み進めて、timeout のデフォルト値に関しては以下の2通りの可能性を推察した。

1. ブロッキング I/O の場合は「デフォルト値はない＝永遠に待機する」という仕様がデフォルトである
2. TCP レイヤーの話なので、デフォルト値は OS の管轄である ＝ Python 処理系では関知しない

2 であれば OS の設定値を確認するコマンドがあるのではなかろうかと思い、雑に検索してみたところ以下の記事がヒットした。

https://serverfault.com/questions/216956/how-to-check-tcp-timeout-in-linux-macos

`sysctl` で関連プロパティを確認できるようだった。これを実機で確認してみると以下。

検証環境: Mac OS 12.0.1

```bash
$ sysctl net.inet.tcp | grep -i timeout
net.inet.tcp.ecn_timeout: 60
net.inet.tcp.fin_timeout: 60000
net.inet.tcp.max_persist_timeout: 0
```

コネクションの確立／切断にそれぞれ timeout が設定されているので、少なくともこれらには従うのではないかと考えた。
また、今回の関心事は API コールが戻って来ないことなので、ひとつの仮説としてコネクションの確立段階の timeout (=60s) は疑えそうである。

## 実験内容

条件

| key | value |
|:---|:---|
|OS | Mac OS 12.0.1|
|Python | 3.9.5|

[experiment.md](./experiment.md)