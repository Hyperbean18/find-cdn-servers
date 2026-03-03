#!/usr/bin/env python3
"""
usage: pick-cdn-domains.py <input-file> <output-file>

pick cdn domains from a file containing a list of cdn domains
discovered in various websites.

each line in the input file has the following format.
<har-file-name> <domain> <cdn>

the <har-file-name> in each record encodes the web-site rank, page
type, and site domain name as follows.
<site-rank>_<page-type>_<site-domain>

the value of `page-type` is '0' for the landing and '1' for internal
page of a web site. to recover the actual web-site's domain name from
`site-domain`, replace all underscores in its value with a period.
"""


import collections
import random


# Select set of CDNs.
SEL_CDNS = ('Akamai', 'Amazon-Cloudfront', 'Cloudflare', 'Google', 'Fastly')


def get_rank(file_name: str) -> int:
    """decode the har filename to extract the web-site ranking.
    """
    fields = file_name.split('_', maxsplit=2)
    
    if len(fields) != 3:
        raise ValueError('invalid har filename!')

    rank, _pt, _site = fields
    
    # convert web-site rank to an int.
    return int(rank)


def group_doms_by_rank(dom_file: str) -> dict[int, dict[str, set[str]]]:
    """loads cdn domains and associated information from the given
    file.

    each line in the input file has the following format.
    <har-file-name> <domain> <cdn>
    """
    lines = (line.strip().split() for line in
             open(dom_file, 'r', encoding='utf-8'))

    # domains grouped by web-site rank and then by cdn.
    rank_doms = {}

    for file_name, cdn_dom, cdn in lines:
        rank = get_rank(file_name)

        if rank not in rank_doms:
            rank_doms[rank] = {}

        if cdn not in rank_doms[rank]:
            rank_doms[rank][cdn] = set()

        rank_doms[rank][cdn].add(cdn_dom)

    return rank_doms

def map_dom_to_cdn(doms: set[str], dom_file: str) -> dict[str, str]:
    """return a mapping between a set of cdn domains to the cdn names
    from the given domains data file.

    each line in the domains data file has the following format.
    <har-file-name> <domain> <cdn>
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


def doms_by_rank(cdn: str, dom_info: dict[int, dict[str, set[str]]],
                 rbeg: int, rend: int) -> set[str]:
    """return the set of domains associated with ranks in the range
    given by [rbeg, rend].
    """
    ranks = list(range(rbeg, rend + 1))

    doms = set()
    for r in ranks:
        if r not in dom_info:
            continue

        if cdn not in dom_info[r]:
            continue

        doms.update(dom_info[r][cdn])

    return doms


def sample_doms(doms: set[str], size: int) -> list[str]:
    """obtain random sample of given size from a set of domain names.
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


def sample_doms_in_range(cdn: str,
                         doms: dict[int, dict[str, set[str]]],
                         size: int,
                         rbeg: int,
                         rend:int,
                         existing: set[str]) -> list[str]:
    """sample domains uniformly at random from sites of ranks in the
    range defined by [rbeg, rend].
    """
    candidates = doms_by_rank(cdn, doms, rbeg, rend)
    return sample_doms(candidates - existing, size)


def get_rank_ranges(dom_info: dict[int, dict[str, set[str]]]
                    ) -> dict[str, tuple[int, int]]:
    """find the highest and lowest rank of web sites associated with
    each cdn domain.
    """
    rank_ranges = {}
    
    for rank in dom_info:
        for cdn in dom_info[rank]:
            for dom in dom_info[rank][cdn]:
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

def tranco_cherry_pick_doms(dom_info: dict[int, dict[str, set[str]]]
                     ) -> dict[str, tuple[int, int]]:
    """Cherry-pick domains from the dict of available domains (grouped
    by web-site rank) based on a pre-defined sampling algorithm.
    """
    rank_ranges = get_rank_ranges(dom_info)
    
    # Last 26 web-site ranks.
    ranks = sorted(dom_info.keys())[-26:]
    # 26th highest rank from the last.
    last_26 = ranks[0]
    # 25th highest rank from the last.
    last_25 = ranks[1]
    # Last rank.
    last = ranks[-1]
    # Cherry-picked domains.
    doms = set()
    n = len(SEL_CDNS)
    # Sample 30 CDN domains from sites with rank in [1, 25].
    for cdn in SEL_CDNS:
        doms.update(sample_doms_in_range(cdn, dom_info, 30/n,
                                         1, 25, doms))
    # Sample 30 CDN domains from sites with rank in (25, 10000].
    for cdn in SEL_CDNS:
        doms.update(sample_doms_in_range(cdn, dom_info, 30/n,
                                         26, 10000, doms))
    # Sample 50 CDN domains from sites with rank in (10000, 500000].
    for cdn in SEL_CDNS:
        doms.update(sample_doms_in_range(cdn, dom_info, 50/n,
                                         10001, 500000, doms))
    # Sample 70 CDN domains from sites with rank in (500000, bottom-25).
    for cdn in SEL_CDNS:
        doms.update(sample_doms_in_range(cdn, dom_info, 70/n,
                                         500001, last_26, doms))
    # Sample 30 CDN domains from sites with rank in [bottom-25, bottom].
    for cdn in SEL_CDNS:
        doms.update(sample_doms_in_range(cdn, dom_info, 30/n,
                                         last_25, last, doms))
    return {d: tuple(rank_ranges[d]) for d in doms}

def cherry_pick_doms(dom_info: dict[int, dict[str, set[str]]]
                     ) -> dict[str, tuple[int, int]]:
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

    n = len(SEL_CDNS)

    # Sample 20 CDN domains from sites with rank in [1, 20].
    for cdn in SEL_CDNS:
        doms.update(sample_doms_in_range(cdn, dom_info, 20/n,
                                         1, 20, doms))

    # Sample 10 CDN domains from sites with rank in (20, 100].
    for cdn in SEL_CDNS:
        doms.update(sample_doms_in_range(cdn, dom_info, 10/n,
                                         21, 100, doms))

    # Sample 20 CDN domains from sites with rank in (100, 1000].
    for cdn in SEL_CDNS:
        doms.update(sample_doms_in_range(cdn, dom_info, 20/n,
                                         101, 1000, doms))

    # Sample 30 CDN domains from sites with rank in (1000, bottom-20).
    for cdn in SEL_CDNS:
        doms.update(sample_doms_in_range(cdn, dom_info, 30/n,
                                         1001, last_21, doms))

    # Sample 20 CDN domains from sites with rank in [bottom-20, bottom].
    for cdn in SEL_CDNS:
        doms.update(sample_doms_in_range(cdn, dom_info, 20/n,
                                         last_20, last, doms))

    return {d: tuple(rank_ranges[d]) for d in doms}


def _main(*args):
    dom_file, out_file = args
    print(dom_file)

    # Load domains into a hash keyed using the web-site rank.
    dom_info = group_doms_by_rank(dom_file)

    with open(out_file, 'w', encoding='utf-8') as f:
        # Sample CDN domains using a pre-defined policy.
        doms = tranco_cherry_pick_doms(dom_info)
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
