#!/usr/bin/env python3
"""
Looks up the domain names of unknown CDNs using `whois` as a
last-resort to identify whether the IP address to which the domain
name resolves is owned by a known CDN.

Usage: ./whois-lookup.py <CDN-domains-file> <output-file>
"""

__author__ = "Vaibhav Ghanatra"
__version__ = "1.0"
__license__ = "MIT"


import os
import socket


# Value indicating that the CDN is unknown.
UNK_CDN = 'UNKNOWN'


def resolve_host(host):
    """Resolve domain or hostname to an IP address.
    """
    try:
        return socket.gethostbyname(host)
    except:
        # Failed to resolve hostname!
        return ''


# Valid labels for network and organization name records.
NET_RECS = set(['netname', 'net-name'])
ORG_RECS = set(['orgname', 'org-name'])


ORG_TO_CDNS = {
    'akamai'     : 'Akamai',
    'amazon'     : 'Amazon-Cloudfront',
    'bunnycdn'   : 'BunnyCDN',
    'cachefly'   : 'Cachefly',
    'cdn77'      : 'CDN77',
    'cloudflare' : 'Cloudflare',
    'edgecast'   : 'EdgeCast',
    'fastly'     : 'Fastly',
    'google'     : 'Google',
    'highwinds'  : 'Highwinds',
    'level3'     : 'Level3',
    'tata'       : 'Tata-communications',
    'yahoo'      : 'Yahoo'}


def lookup_cdn(org: str) -> str:
    """Given an organization name returns the name of the CDN, if known.
    """
    if org in ORG_TO_CDNS:
        return ORG_TO_CDNS[org]

    # NOTE: A trie would be the best data structure for `ORG_TO_CDNS`.
    for org_name in ORG_TO_CDNS:
        if org.startswith(org_name):
            return ORG_TO_CDNS[org_name]

    return ''


def parse_net_org(line: str) -> str:
    """Given a line from a `whois` lookup output, it parses the
    network or organization name if that information is available in
    the input and uses it for identifying the CDN.

    Network or organization information usually starts with one of the
    following fields: `NetName`, `netname`, `net-name`, `OrgName`,
    `orgname`, and `org-name`.
    """
    fields = line.split(':', maxsplit=1)
    
    if len(fields) != 2:
        return ''

    label, value = [v.lower().strip() for v in fields]
    
    if label in NET_RECS:
        cdn = lookup_cdn(value)
        if cdn:
            return cdn

    if label in ORG_RECS:
        return lookup_cdn(value)

    return ''


def whois_cdn(ip: str):
    """Perform a `whois` lookup on an IP address and identify the CDN,
    if any, that owns that IP address.
    """
    with os.popen(f"whois '{ip}'") as proc:
        try:
            for line in proc.read().split('\n'):
                cdn_info = parse_net_org(line)
                
                if cdn_info:
                    return cdn_info
        except UnicodeDecodeError as e:
            # Failed to parse value due to decoding error.
            return ''

        
def resolve_unknowns(cdn_recs, out):
    """Resolve UNKNOWN CDN domains while retaining everything else
    intact, and write updated output to given output stream.

    The expected format of the input records is as follows.
    <har-file> <domain> <CDN>
    """

    # Cache of prior attempts.
    host_to_ip_cache = {}
    ip_to_cdn_cache = {}
    
    for rec in cdn_recs:
        if not rec.endswith(UNK_CDN):
            out.write(f"{rec}\n")
            continue

        har_file, domain, cdn = rec.split()

        # Resolve the hostname to an IP address and cache resolutions.
        if domain not in host_to_ip_cache:
            host_to_ip_cache[domain] = resolve_host(domain)
        srv_ip = host_to_ip_cache[domain]

        if not srv_ip:
            # Retain the original record as such!
            out.write(f"{rec}\n")
            continue

        # Identify CDN information using a `whois` lookup.
        if srv_ip not in ip_to_cdn_cache:
            ip_to_cdn_cache[srv_ip] = whois_cdn(srv_ip)
        cdn = ip_to_cdn_cache[srv_ip]

        if not cdn:
            # Retain the original record as such!
            out.write(f"{rec}\n")
            continue

        # Retain the original record as such!
        out.write(f"{har_file} {domain} {cdn}\n")


def _main(*args) -> None:
    domains_file, output_file = args

    with open(output_file, 'w', encoding='utf-8') as out:
        cdn_recs = (line.strip() for line in
                    open(domains_file, 'r', encoding='utf-8'))
        resolve_unknowns(cdn_recs, out)


if __name__ == '__main__':
    import sys

    args = sys.argv[1:]
    if len(args) != 2:
        sys.stderr.write(f"Usage: {sys.argv[0]}"
                         " <CDN-domains-file> <output-file>\n")
        exit(1)

    _main(*args)
        


# import json
# import socket
# from urllib.parse import urlsplit
# from ipwhois import IPWhois
# from pprint import pprint
# import os


# for url in unresolved:
#     host = urlsplit(url).hostname
#     if host not in domains:
#         domains.append(host)

# ips = []

# output = []
# error=  []

# for domain in domains:
#     details = os.popen(f'whois "{ip}"').read()
#     n = ""
#     n = ""
#     if "NetName" in details:
#         n = "NetName:"
#     elif "netname" in details:
#         n = "netname:"
#     elif "net-name" in details:
#         n = "net-name:"
#     o = ""
#     if "OrgName" in details:
#         o = "OrgName:"
#     elif "org-name" in details:
#         o = "org-name:"
#     elif "orgname" in details:
#         o = "orgname:"
    
#     try:
#         details = details.split(n)
#         netname = details[1].split('\n')[0].strip()
#         orgname = ""
#         if o != "":
#             orgname = details[1].split(o)[1].split('\n')[0].strip()
#             output.append({
#                 "domain": domain,
#                 "ip": ip,
#                 "netname": netname,
#                 "orgname": orgname
#             })
    
#     except:
#         error.append({
#             'domain': domain,
#             'ip': ip
#         })

# pprint(output)
# with open('../data/net_org_names.json','w') as f:
#     json.dump(output, f)
