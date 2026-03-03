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
    """HTTP Archive data generator.
    """

    def __init__(self, browsermob_proxy: str, chrome_driver: str) -> None:
        self._bmp = browsermob_proxy
        self._driver_path = chrome_driver
        
        # Timeout (in seconds) for page fetches.
        self._timeout = 10

        self._srv = None
        self._proxy = None

    def _build_opts(self) -> selenium.webdriver.chrome.options.Options:
        """Define headless browser configuration.
        """
        opts = webdriver.ChromeOptions()

        # Use a headless browser.
        opts.add_argument('headless')

        # Ignore SSL certificate errors.
        opts.add_argument("--ignore-certificate-errors")
        opts.add_argument("--proxy-server={0}".format(self._proxy.proxy))
        
        return opts

    def fetch(self, url: str) -> str:
        """Fetch the web page at a given URL and retrieve the HAR data
        corresponding to this fetch.
        """
        self._srv = Server(self._bmp)
        self._srv.start()
        self._proxy = self._srv.create_proxy(params={'trustAllServers': 'true'})
        
        opts = self._build_opts()
        
        with webdriver.Chrome(service=Service(self._driver_path),
                              options=opts) as driver:
            # self._srv.start()
        
            self._proxy.new_har(url)
            driver.get(url)
            time.sleep(self._timeout)

            return json.dumps(self._proxy.har)

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
    hargen = HARGen(browsermob_proxy, chrome_driver)

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