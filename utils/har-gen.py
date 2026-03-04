#!/usr/bin/env python3
"""
Usage: har-gen.py
"""

from browsermobproxy import Server
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service
from typing import Sequence

import json
import os
import selenium
import time
import urllib


class HARGen:
    def __init__(self, browsermob_proxy: str, chrome_driver: str) -> None:
        self._bmp = browsermob_proxy
        self._driver_path = chrome_driver
        self._timeout = 30

        self._srv = Server(self._bmp)
        self._srv.start()
        self._proxy = self._srv.create_proxy(params={'trustAllServers': 'true'})

    def close(self) -> None:
        """Shut down the proxy and browsermob server."""
        try:
            self._proxy.close()
        except Exception:
            pass
        try:
            self._srv.stop()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _build_opts(self) -> selenium.webdriver.chrome.options.Options:
        opts = webdriver.ChromeOptions()
        # Use the new headless mode (more stable in newer Chrome versions)
        opts.add_argument("--headless=new") 
        
        # CRITICAL: These two prevent the Segfaults/Status -11
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        
        # Your existing opts
        opts.add_argument("--ignore-certificate-errors")
        opts.add_argument('--allow-running-insecure-content')
        opts.add_argument('--disable-web-security')
        opts.add_argument("--proxy-server={0}".format(self._proxy.proxy))
        
        # Optional: Helps when running in environments with limited resources
        # opts.add_argument("--disable-gpu")
        # opts.page_load_strategy = 'eager'
        
        return opts

    def fetch(self, url: str) -> str:
        opts = self._build_opts()
        try:
            with webdriver.Chrome(service=Service(self._driver_path), options=opts) as driver:
                driver.set_page_load_timeout(self._timeout)
                self._proxy.new_har(url)
                driver.get(url)
                time.sleep(self._timeout)
                return json.dumps(self._proxy.har)
        except Exception as e:
            raise e
        

    def run(self, url: str, harfile: str) -> None:
        with open(harfile, 'w', encoding='utf-8') as out:
            try:
                out.write(self.fetch(url))
            except WebDriverException as e:
                out.write('{}')
                raise e

    def run(self, url: str, harfile: str) -> None:
        """Fetch the web page at a given URL and write the HAR file
        with details from the page fetch.
        """
        with open(harfile, 'w', encoding='utf-8') as out:
            try:
                out.write(self.fetch(url))
            except WebDriverException as e:
                out.write('{}')
                raise e

            
def load_crawl_list(crawl_list: str) -> Sequence[tuple[str, str]]:
    """Return a sequence of URLs and associated web-site rankings from
    the crawl list file.
    """
    return (line.strip().split(',') for line in
            open(crawl_list, 'r', encoding='utf-8'))


def generate_hars(hg: HARGen, crawl_list: Sequence[tuple[str, str]],
                  out_path: str) -> None:
    """Fetch the URLs in the crawl list and generate a HAR file
    corresponding to each page fetch in the specified output path.
    """
    # Set of observed ranks.
    ranks = set()

    # Number of pages fetched.
    num_pages = 0

    # Translate extraneous characters in domain when using it for
    # deriving output file name.
    trans = str.maketrans({'.': '_', ':': '_'})
    
    for rank, url in crawl_list:
        beg = time.time()
        
        # Second URL with the same rank points to an internal page.
        int_page = '1' if rank in ranks else '0'
        ranks.add(rank)
        url = "https://www." + url
        domain = urllib.parse.urlparse(url).netloc
        print(url)
        
        # Encode the site rank, page type, and domain name in the HAR file.
        har_file = f"{rank}_{int_page}_{domain}".translate(trans) + '.har'
        out_file = os.path.sep.join((out_path, har_file))

        try:
            hg.run(url, out_file)

            elapsed = time.time() - beg

            print(f"> spent {elapsed:.1f} second(s) to record {out_file}")

            num_pages += 1

        except WebDriverException as e:
            err = e.msg.split('\n')[0]
            print(f"> Error: Failed generating `{out_file}`! {err}")

    print(f"> fetched {num_pages} page(s)")


def _main(browsermob_proxy: str, chrome_driver: str, crawl_file: str,
          out_path: str) -> None:
    with HARGen(browsermob_proxy, chrome_driver) as hargen:
        crawl_list = load_crawl_list(crawl_file)
        generate_hars(hargen, crawl_list, out_path)

if __name__ == '__main__':
    import sys

    args = sys.argv[1:]
    if len(args) != 4:
        sys.stderr.write(f"Usage: {sys.argv[0]}"
                         ' <browsermob-proxy-path>'
                         ' <chrome-driver-path>'
                         ' <crawl-list>'
                         " <out-path>\n")
        sys.exit(1)
        
    _main(*args)