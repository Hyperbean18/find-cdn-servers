#!/usr/bin/env python3
"""
Usage: fix-cdn-info.py <input-file> <output-file>

Resolve issues in mapping between domain-names and CDNs in the input
file and write out a new version of the entries to the output file.

Since finding which CDN a domain-name maps to is based on heuristics,
occasionally a domain-name might be mapped to more than one CDN. We
can easily resolve such issues using a simple majority vote.

Each line in the input file has the following format.
<har-file-name> <domain> <CDN>
"""


import sys


_err = sys.stderr.write


# Value indicating that the CDN is unknown.
UNK_CDN = 'UNKNOWN'


def get_site(file_name: str) -> str:
    """Decode the HAR filename to extract the web-site domain.
    """
    fields = file_name.split('_', maxsplit=2)
    
    if len(fields) != 3:
        raise ValueError('Invalid HAR filename!')

    _rank, _pt, site = fields

    return site


def scan_map(map_file: str) -> dict[str, dict[str, set[str]]]:
    """Scan domain-name to CDN mappings from input file and return a
    hash that maps domain names to CDNs and web-sites.
    """
    recs = (line.strip().split() for line in
            open(map_file, 'r', encoding='utf-8'))

    # Mapping from domain name to CDNs, each of which in turn map to a
    # set of web sites.
    dom_info = {}

    for label, dom, cdn in recs:
        site = get_site(label)

        if dom not in dom_info:
            dom_info[dom] = {}

        if cdn not in dom_info[dom]:
            dom_info[dom][cdn] = set()

        dom_info[dom][cdn].add(site)

    return dom_info


def resolve_mappings(current: dict[str, dict[str, set[str]]]) -> dict[str, str]:
    """Use majority voting to resolve conflicts in domain-name-to-CDN
    mappings and return the resolved mappings.
    """

    # domain-name to CDN mappings.
    resolved = {}
    
    for dom in current:
        if len(current[dom]) == 1:
            # No conflicts!
            cdn = list(current[dom].keys())[0]
            resolved[dom] = cdn
            
            _err(f"NO-CONFLICT: Retain {dom} -> {cdn}\n")
            continue

        if UNK_CDN in current[dom]:
            # We can find out the CDN using other entries.
            _err(f"CONFLICT: Remove {dom} -> {UNK_CDN} mapping\n")
            current[dom].pop(UNK_CDN)

        cdns = sorted((len(current[dom][cdn]), cdn) for cdn in current[dom])
        
        # New CDN mapping.
        cdn = cdns[-1][1]
        resolved[dom] = cdn

        opts_lst  = ', '.join(f"{cdn}({freq})" for (freq, cdn) in cdns)
        _err(f"CONFLICT: Resolve {dom} -> {cdn}; options: {opts_lst}\n")

    return resolved


def fix_mappings(old_file: str, new_map: dict[str, str], new_file) -> None:
    """Use the resolved domain-name-to-CDN mappings to fix the entries
    in the old file and write them to a new mappings file.
    """
    recs = (line.strip().split() for line in
            open(old_file, 'r', encoding='utf-8'))

    with open(new_file, 'w', encoding='utf-8') as out:
        for label, dom, cdn in recs:
            cdn = new_map[dom]

            out.write(f"{label} {dom} {cdn}\n")


def _main(*args):
    old_file, new_file = args

    old_map = scan_map(old_file)
    new_map = resolve_mappings(old_map)
    fix_mappings(old_file, new_map, new_file)


if __name__ == '__main__':
    args = sys.argv[1:]
    
    if len(args) != 2:
        sys.stderr.write(f"{sys.argv[0]}"
                         ' <input-file> <output-file>\n')
        exit(1)

    _main(*args)
