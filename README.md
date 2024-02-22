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

➜ pip install browsermob-proxy selenium
Successfully installed ...

➜ pip install dnspython
Successfully installed ...
```


## Unix/Linux tools

We use the [GNU parallel](https://www.gnu.org/software/parallel/)
utility for running some of the data-processing tasks in parallel. You
can install it manually from the source or using your system's package
manager.


## Crawl list

We use the [Hispar list](https://hispar.cs.duke.edu) and sample a set
of 200 URLs (with equal number of landing and internal page URLs) from
it. You can generate a crawl list as follows.

```
➜ make hispar-list-21-01-28
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

➜ make data/crawl-pages.txt
...

➜ head data/crawl-pages.txt
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

# The format of the crawl list is as follows.
# <web-site rank> <URL>
#
# There will be two entries for each web-site rank.
# The first entry is the landing page, whereas the second one is the
# URL of a randomly chosen internal page (from the Hispar list for the
# associated web site).

➜ wc -l  crawl-pages.txt
200 crawl-pages.txt
```


# Finding CDN servers

In general, you can perform all of the tasks---downloading the Hispar
list, selecting pages to crawl, fetching them to generate the HAR
files, and extracting the hostnames of CDN servers---by simply
issuing `make` or `make all`.

Below, we discuss how to run specific tasks.


## Generating HAR files

You can fetch the pages in the crawl list and generate the HAR files
as follows.

```
➜ make gen-hars
...
```

Once the page-fetches are complete, you can review the logs in
`data/gen-hars.log`. URLs for which we could not successfully generate
a HAR file would be clearly marked in this log file.

```
➜ head -3 data/gen-hars.log
> spent 11.0 second(s) to record data/hars/1_0_www_google_com.har
> fetched 1 page(s)
> spent 10.8 second(s) to record data/hars/1_1_news_google_com.har

➜ grep Error data/gen-hars.log
> Error: Failed generating `data/hars/3739_0_www_btcmex_com_443.har`! unknown error: net::ERR_TUNNEL_CONNECTION_FAILED
> Error: Failed generating `data/hars/3739_1_help_btcmex_com.har`! unknown error: net::ERR_TUNNEL_CONNECTION_FAILED
> Error: Failed generating `data/hars/3800_1_pops_stumbleupon_com.har`! unknown error: net::ERR_TUNNEL_CONNECTION_FAILED
```

You can remove all the HAR files and re-run the page fetches as
follows.

```
➜ make regen-hars
```


# Identifying CDNs from HAR files

You can extract the URLs from HAR files, identify the CDNs used for
serving various objects, refine the CDN discovery process, and
cherry-pick CDNs for further experiments by calling the `get-cdns`
target.

```
➜ make get-cdns
```

We use the excellent
[get_cdn.py](https://gist.github.com/waqaraqeel/9368bb0711a67ce17aec367448ac65e6)
utility (with some minor modifications) to parse the URLs of objects
in the HAR files and identify the CDNs. The details of each domain
name, its associated CDN (if any) are stored along with details of the
web site where they were discovered.

```
➜ head -2 data/cdn-domains.txt
1_0_www_google_com.har www.google.com. Google
1_0_www_google_com.har www.google.com. Google
```

Since the process of determining the domains of various CDNs is based
on a set of heuristics, occasionally, it might result in conflicting
mappings. We resolve these mappings using majority voting.

```
➜ head -3 data/cdn-domains-fixed.txt
1_0_www_google_com.har www.google.com. Google
1_0_www_google_com.har www.google.com. Google
1_0_www_google_com.har www.google.com. Google

# The conflict resolution process logs its actions to a file, in case
# we need it later for reviewing the CDN details.

➜ grep '^CONFLICT' data/cdn-domains-conflicts.log | head -3
CONFLICT: Remove www.amazon.com. -> UNKNOWN mapping
CONFLICT: Resolve www.amazon.com. -> Amazon-Cloudfront; options: Amazon-Cloudfront(1)
CONFLICT: Remove m.media-amazon.com. -> UNKNOWN mapping
```

We also use `whois` lookups to identify the CDNs when the domain names
are not much helpful. The results of these refinements can be found in
`data/cdn-domains-w-whois.txt`.

```
➜ head -3 data/cdn-domains-w-whois.txt
1_0_www_google_com.har www.google.com. Google
1_0_www_google_com.har www.google.com. Google
1_0_www_google_com.har www.google.com. Google
```

We finally cherry-pick a set of 100 CDN targets and store them in the
file `data/cdn-targets-info.txt`; the file stores the highest and
lowest ranks of web sites where each CDN domain or server name was
discovered. The manner in which we pick these targets is documented in
`utils/pick-cdn-domains.py` (function: `cherry_pick_doms`).

```
$ head -3 data/cdn-targets-info.txt
acdn.adnxs.com. 89 3817
googleads.g.doubleclick.net. 6 3820
pm.w55c.net. 243 243
```
