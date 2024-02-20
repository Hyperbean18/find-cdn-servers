# About

This repository contains utilities for retrieving the hostnames of CDN
servers used for delivering content in various web sites.


# Dependencies

This project depends on a few external tools and libraries.


## Tools for Headless browsing

To fetch web pages using a headless browser, we use [BrowserMob
Proxy](https://github.com/lightbody/browsermob-proxy) and
`chromedriver`. You can download and install them as follows.

```
➜ cd ext/

➜ make
...  https://github.com/lightbody/browsermob-proxy/releases/download/browsermob-proxy-2.1.4/browsermob-proxy-2.1.4-bin.zip
Resolving github.com (github.com)...
...
...  - ‘browsermob-proxy-2.1.4-bin.zip’ saved [20115989/20115989]

Archive:  browsermob-proxy-2.1.4-bin.zip
   creating: browsermob-proxy-2.1.4/
   creating: browsermob-proxy-2.1.4/bin/```
   ...
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
The following NEW packages will be installed:
  chromium-chromedriver
...
Unpacking chromium-chromedriver ...
Setting up chromium-chromedriver ...
```

## Python libraries

We use [pyenv](https://github.com/pyenv/pyenv) to manage and install
python library dependencies. You can install `pyenv` and other python
dependencies as follows.

```
➜ curl https://pyenv.run | bash

# Load `pyenv` into the shell by adding the following lines to your
# bash configuration (e.g., `~/.bashrc`) file.
#
# export PYENV_ROOT="$HOME/.pyenv"
# [[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
# eval "$(pyenv init -)"
#
# Restart your shell for the above configuration to take effect.

➜ pyenv install 3.10.12
Downloading Python-3.10.12.tar.xz...
...
Installed Python-3.10.12 to ...

➜ pyenv local 3.10.12

➜ pip install --upgrade pip
...
Collecting pip
...
Installing collected packages: pip
...
Successfully installed pip-...

➜ pip3 install browsermob-proxy selenium
Successfully installed ...
```


## Crawl List

We use the [Hispar list](https://hispar.cs.duke.edu) and sample a set
of 200 URLs (with equal number of landing and internal page URLs) from
it. You can generate a crawl list as follows.

```
➜ make
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100 1492k  100 1492k    0     0   881k      0  0:00:01  0:00:01 --:--:--  881k
Archive:  hispar-list-21-01-28.zip
  inflating: hispar-list-21-01-28

➜ ls -l
total 5976
-rw-rw-r-- 1 balac balac    3246 Feb 19 15:40 crawl-landing.txt
-rw-rw-r-- 1 balac balac    9010 Feb 19 15:40 crawl-pages.txt
-rw-rw-r-- 1 balac balac 6078026 Jan 29  2021 hispar-list-21-01-28
-rw-rw-r-- 1 balac balac    1084 Feb 19 13:53 LICENSE
-rw-rw-r-- 1 balac balac    2687 Feb 19 15:32 Makefile
-rw-rw-r-- 1 balac balac    2276 Feb 19 15:24 pick-internal.py
-rw-rw-r-- 1 balac balac       5 Feb 19 15:40 rank-bot-20.txt
-rw-rw-r-- 1 balac balac     351 Feb 19 15:40 README.md

➜ head crawl-pages.txt
1 http://www.google.com/
1 https://domains.google.com/registrar
2 https://www.youtube.com/
2 https://www.youtube.com/skynews
3 https://www.tmall.com/
3 https://detail.tmall.com/item.htm?id=562883489178
4 http://baidu.com/
4 https://ir.baidu.com/node/11486/html
5 https://www.qq.com?fromdefault
5 https://www.roblox.qq.com/badges/48836625/Headshot

➜ wc -l  crawl-pages.txt
200 crawl-pages.txt
```