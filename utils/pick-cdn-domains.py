#!/usr/bin/env python3
"""
Usage: pick-cdn-domains.py <input-file> <output-file>

Pick CDN domains from a file containing a list of CDN domains
discovered in various websites.

Each line in the input file has the following format.
<har-file-name> <domain> <CDN>

The <har-file-name> in each record encodes the web-site rank, page
type, and site domain name as follows.
<site-rank>_<page-type>_<site-domain>

The value of `page-type` is '0' for the landing and '1' for internal
page of a web site. To recover the actual web-site's domain name from
`site-domain`, replace all underscores in its value with a period.
"""


import collections
import random


# Select set of CDNs.
SEL_CDNS = ('Akamai', 'Amazon-Cloudfront', 'Cloudflare', 'Google', 'Fastly')


def get_rank(file_name: str) -> int:
    """Decode the HAR filename to extract the web-site ranking.
    """
    fields = file_name.split('_', maxsplit=2)
    
    if len(fields) != 3:
        raise ValueError('Invalid HAR filename!')

    rank, _pt, _site = fields
    
    # Convert web-site rank to an int.
    return int(rank)


def group_doms_by_rank(dom_file: str) -> dict[int, str]:
    """Loads CDN domains and associated information from the given
    file.

    Each line in the input file has the following format.
    <har-file-name> <domain> <CDN>
    """
    lines = (line.strip().split() for line in
             open(dom_file, 'r', encoding='utf-8'))

    # Domains grouped by web-site rank.
    rank_doms = collections.defaultdict(set)

    for file_name, cdn_dom, _cdn in lines:
        rank_doms[get_rank(file_name)].add(cdn_dom)

    return rank_doms

def map_dom_to_cdn(doms: set[str], dom_file: str) -> dict[str, str]:
    """Return a mapping between a set of CDN domains to the CDN names
    from the given domains data file.

    Each line in the domains data file has the following format.
    <har-file-name> <domain> <CDN>
    """
    lines = (line.strip().split() for line in
             open(dom_file, 'r', encoding='utf-8'))

    dom_to_cdn = {}

    for _file, dom, cdn in lines:
        if dom not in doms:
            continue

        if dom in dom_to_cdn:
            if dom_to_cdn[dom] != cdn:
                raise ValueError('Invalid domain-to-CDN mapping!')
            else:
                continue

        dom_to_cdn[dom] = cdn

    return dom_to_cdn


def doms_by_rank(dom_info: dict[int, str], rbeg: int, rend: int) -> set[str]:
    """Return the set of domains associated with ranks in the range
    given by [rbeg, rend].
    """
    ranks = list(range(rbeg, rend + 1))
    return set([d for r in ranks for d in dom_info[r] if r in dom_info])


def sample_doms(doms: set[str], size: int) -> list[str]:
    """Obtain random sample of given size from a set of domain names.
    """
    if len(doms) <= size:
        return list(doms)

    samples = []
    
    for i, d in enumerate(doms):
        if i + 1 <= size:
            samples.append(d)
            continue

        k = random.randint(0, i)
        if k < size:
            samples[k] = d

    return samples


def sample_doms_in_range(doms: dict[int, str], size: int,
                         rbeg: int, rend:int,
                         existing: set[str]) -> list[str]:
    """Sample domains uniformly at random from sites of ranks in the
    range defined by [rbeg, rend].
    """
    candidates = doms_by_rank(doms, rbeg, rend)
    return sample_doms(candidates - existing, size)


def get_rank_ranges(dom_info: dict[int, str]) -> dict[str, tuple[int, int]]:
    """Find the highest and lowest rank of web sites associated with
    each CDN domain.
    """
    rank_ranges = {}
    
    for rank in dom_info:
        for dom in dom_info[rank]:
            if dom not in rank_ranges:
                hi_rank, lo_rank = rank, rank
            else:
                hi_rank, lo_rank = rank_ranges[dom]
                if rank < hi_rank:
                    hi_rank = rank
                elif rank > lo_rank:
                    lo_rank = rank
                    
            rank_ranges[dom] = hi_rank, lo_rank
            
    return rank_ranges


def cherry_pick_doms(dom_info: dict[int, str]) -> dict[str, tuple[int, int]]:
    """Cherry-pick domains from the dict of available domains (grouped
    by web-site rank) based on a pre-defined sampling algorithm.
    """
    rank_ranges = get_rank_ranges(dom_info)
    
    # Last 21 web-site ranks.
    ranks = sorted(dom_info.keys())[-21:]
    # 21st highest rank from the last.
    last_21 = ranks[0]
    # 20th highest rank from the last.
    last_20 = ranks[1]
    # Last rank.
    last = ranks[-1]

    # Cherry-picked domains.
    doms = set()

    # Sample 10 CDN domains from sites with rank in [1, 20].
    doms.update(sample_doms_in_range(dom_info, 20, 1, 20, doms))

    # Sample 10 CDN domains from sites with rank in (20, 100].
    doms.update(sample_doms_in_range(dom_info, 10, 21, 100, doms))

    # Sample 20 CDN domains from sites with rank in (100, 1000].
    doms.update(sample_doms_in_range(dom_info, 20, 101, 1000, doms))

    # Sample 30 CDN domains from sites with rank in (1000, bottom-20).
    doms.update(sample_doms_in_range(dom_info, 30, 1001, last_21, doms))

    # Sample 20 CDN domains from sites with rank in [bottom-20, bottom].
    doms.update(sample_doms_in_range(dom_info, 20, last_20, last, doms))

    return {d: tuple(rank_ranges[d]) for d in doms}


def _main(*args):
    dom_file, out_file = args

    # Load domains into a hash keyed using the web-site rank.
    dom_info = group_doms_by_rank(dom_file)

    with open(out_file, 'w', encoding='utf-8') as f:
        # Sample CDN domains using a pre-defined policy.
        doms = cherry_pick_doms(dom_info)
        dom_to_cdn = map_dom_to_cdn(doms, dom_file)

        for dom, (hi_rank, lo_rank) in doms.items():
            f.write(f"{dom} {dom_to_cdn[dom]} {hi_rank} {lo_rank}\n")


if __name__ == '__main__':
    import sys

    args = sys.argv[1:]
    
    if len(args) != 2:
        sys.stderr.write(f"{sys.argv[0]}"
                         ' <input-file> <output-file>\n')
        exit(1)

    _main(*args)
