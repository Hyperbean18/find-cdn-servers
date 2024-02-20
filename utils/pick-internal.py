#!/usr/bin/env python3
"""
Usage: pick-internal.py <crawl_file> <hispar_file> <out_file>

This script scans the crawl file (with only landing-page URLs) and
randomly samples an internal-page URL for each web site found in the
crawl file.  The set of landing-page and internal-page URLs are then
written out to the specified output file.

The output format is as follows.
<web-site rank> <page URL>

For a given web-site rank, the first entry points to the landing page
and the second entry points to an internal page.
"""


import collections
import io
import random
import sys


Sample = collections.namedtuple('Sample', ['count', 'url'])


def load_url_data(file_path):
    """Load URLs from data set.
    """
    lines = (line.strip() for line in io.open(file_path, 'r', encoding='utf-8'))

    # Records have the following format.
    # <alexa_rank> <search_rank> <URL>
    return (line.split() for line in lines)


def load_hispar(file_path):
    """Load the Hispar data sete and return a set containing a
    randomly chosen internal page for eeach web site.
    """
    recs = load_url_data(file_path)

    # A randomly sampled internal page per Alexa rank.
    # pages[rank] = (#samples, URL)
    pages = {}
    
    for (a_rank, s_rank, url) in recs:
        if not s_rank:
            # Skip landing pages (s_rank == 0)
            continue

        if not a_rank in pages:
            pages[a_rank] = Sample(1, url)
        else:
            current = pages[a_rank]

            # We have observed a new sample for a given site rank.
            n = current.count + 1

            if not random.randint(1, n) - 1:
                sample_url = url
            else:
                sample_url = current.url

            pages[a_rank] = Sample(n, sample_url)

    return pages


def load_crawl_info(file_path):
    """Load list of web pages to crawl from file.
    """
    recs  = load_url_data(file_path)

    return {a_rank:url for (a_rank, s_rank, url) in recs}


def update_crawl_info(crawl_info, int_pages, out):
    """Update crawl list information by adding one internal page for
    each of the web sites in the list.
    """
    for a_rank, url in crawl_info.items():
        # Write out landing page URL.
        out.write(f"{a_rank} {url}\n")
        
        if not a_rank in int_pages:
            continue

        url = int_pages[a_rank].url
        # Write out internal page URL.
        out.write(f"{a_rank} {url}\n")


def main(*args):
    crawl_file, hispar_file, out_file = args
    
    crawl_info = load_crawl_info(crawl_file)
    int_pages = load_hispar(hispar_file)


    with io.open(out_file, 'w', encoding='utf-8') as out_file:
        update_crawl_info(crawl_info, int_pages, out_file)


if __name__ == '__main__':
    main(*sys.argv[1:])
