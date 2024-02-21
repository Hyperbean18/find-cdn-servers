#!/usr/bin/env python3
"""
Usage: get_cdn.py -f <har-file>

Figures out which CDNs were involved in a webpage fetch given HAR file.
Requires dnspython

Borrows heavily from https://github.com/turbobytes/cdnfinder
Thank you to cdnplanet.com
"""

__author__ = "Waqar Aqeel"
__version__ = "1.0"
__license__ = "MIT"

import socket
from urllib.parse import urlsplit

import dns.resolver
import dns.reversename

TRR = "1.1.1.1"

_cdn_mappings = {
    ".clients.turbobytes.net": "TurboBytes",
    ".turbobytes-cdn.com": "TurboBytes",
    ".afxcdn.net": "afxcdn.net",
    ".akamai.net": "Akamai",
    ".akamaiedge.net": "Akamai",
    ".akadns.net": "Akamai",
    ".akamaitechnologies.com": "Akamai",
    ".gslb.tbcache.com": "Alimama",
    ".cloudfront.net": "Amazon Cloudfront",
    ".anankecdn.com.br": "Ananke",
    ".att-dsa.net": "AT&T",
    ".azioncdn.net": "Azion",
    ".belugacdn.com": "BelugaCDN",
    ".bluehatnetwork.com": "Blue Hat Network",
    ".systemcdn.net": "EdgeCast",
    ".cachefly.net": "Cachefly",
    ".cdn77.net": "CDN77",
    ".cdn77.org": "CDN77",
    ".panthercdn.com": "CDNetworks",
    ".cdngc.net": "CDNetworks",
    ".gccdn.net": "CDNetworks",
    ".gccdn.cn": "CDNetworks",
    ".cdnify.io": "CDNify",
    ".ccgslb.com": "ChinaCache",
    ".ccgslb.net": "ChinaCache",
    ".c3cache.net": "ChinaCache",
    ".chinacache.net": "ChinaCache",
    ".c3cdn.net": "ChinaCache",
    ".lxdns.com": "ChinaNetCenter",
    ".speedcdns.com": "QUANTIL/ChinaNetCenter",
    ".mwcloudcdn.com": "QUANTIL/ChinaNetCenter",
    ".cloudflare.com": "Cloudflare",
    ".cloudflare.net": "Cloudflare",
    ".edgecastcdn.net": "EdgeCast",
    ".adn.": "EdgeCast",
    ".wac.": "EdgeCast",
    ".wpc.": "EdgeCast",
    ".fastly.net": "Fastly",
    ".fastlylb.net": "Fastly",
    ".google.": "Google",
    "googlesyndication.": "Google",
    "youtube.": "Google",
    ".googleusercontent.com": "Google",
    ".l.doubleclick.net": "Google",
    "d.gcdn.co": "G-core",
    ".hiberniacdn.com": "Hibernia",
    ".hwcdn.net": "Highwinds",
    ".incapdns.net": "Incapsula",
    ".inscname.net": "Instartlogic",
    ".insnw.net": "Instartlogic",
    ".internapcdn.net": "Internap",
    ".kxcdn.com": "KeyCDN",
    ".lswcdn.net": "LeaseWeb CDN",
    ".footprint.net": "Level3",
    ".llnwd.net": "Limelight",
    ".lldns.net": "Limelight",
    ".netdna-cdn.com": "MaxCDN",
    ".netdna-ssl.com": "MaxCDN",
    ".netdna.com": "MaxCDN",
    ".stackpathdns.com": "StackPath",
    ".mncdn.com": "Medianova",
    ".instacontent.net": "Mirror Image",
    ".mirror-image.net": "Mirror Image",
    ".cap-mii.net": "Mirror Image",
    ".rncdn1.com": "Reflected Networks",
    ".simplecdn.net": "Simple CDN",
    ".swiftcdn1.com": "SwiftCDN",
    ".swiftserve.com": "SwiftServe",
    ".gslb.taobao.com": "Taobao",
    ".cdn.bitgravity.com": "Tata communications",
    ".cdn.telefonica.com": "Telefonica",
    ".vo.msecnd.net": "Windows Azure",
    ".ay1.b.yahoo.com": "Yahoo",
    ".yimg.": "Yahoo",
    ".zenedge.net": "Zenedge",
    ".b-cdn.net": "BunnyCDN",
    ".ksyuncdn.com": "Kingsoft",
}

_resolver = dns.resolver.Resolver()
_resolver.nameservers = [TRR]
_resolver.timeout = 0.5

_found_domains = {}
_cname_failed = set()
_dns_failed = set()


def _cdnmapping_guess(domain):
    if domain in _found_domains:
        return _found_domains[domain]

    for k, v in _cdn_mappings.items():
        if k in domain:
            _found_domains[domain] = v
            return v


def _header_guess(headers):
    for hdr in headers:
        # Cloudflare advertises a custom Server header
        if hdr["name"] == "Server" and hdr["value"].lower() == "cloudflare-nginx":
            return "Cloudflare"

        # China cache sends a Powered-By-Chinacache header
        if hdr["name"] == "powered-by-chinacache":
            return "ChinaCache"

        # OnApp edge servers use X-Edge-Location to indicate the location
        if hdr["name"] == "x-edge-location":
            return "OnApp"

        # CloudFront adds in some custom tracking id
        if hdr["name"] == "x-amz-cf-id":
            return "Amazon Cloudfront"

        # Bitgravity adds edge hostname to Via header
        if hdr["name"] == "via" and "bitgravity.com" in hdr["value"].lower():
            return "Bitgravity"

        # Skypark sends a X header with their brand name
        if hdr["name"] == "X-CDN-Provider" and "skyparkcdn" in hdr["value"].lower():
            return "Skypark"

        # BaishanCloud uses BC prefix in X-Ser header
        if hdr["name"] == "X-Ser" and hdr["value"].startswith("BC"):
            return "BaishanCloud"
    return None


def get_cdn(en):
    """ Return name of CDN used or None from given HAR entry """

    # get domain
    domain = urlsplit(en["request"]["url"]).netloc
    if not domain.endswith("."):
        domain = domain + "."

    # check cdn mappings
    cdn = _cdnmapping_guess(domain)
    if cdn:
        return (domain, cdn)

    # check http headers
    cdn = _header_guess(en["response"]["headers"])
    if cdn:
        return (domain, cdn)

    try:
       # check cnames
        if domain not in _cname_failed:
            cnames = _resolver.resolve(domain, "CNAME")
            for cname in cnames:
                cdn = _cdnmapping_guess(str(cname.target))
                if cdn:
                    _found_domains[domain] = cdn
                    return (domain, cdn)
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, dns.exception.Timeout):
        _cname_failed.add(domain)

    try:
        # do reverse DNS lookup
        if domain not in _dns_failed:
            ips = _resolver.resolve(domain, "A")
            for ip in ips:
                qname = dns.reversename.from_address(str(ip))
                cnames = _resolver.resolve(qname, "PTR")
                for cname in cnames:
                    cdn = _cdnmapping_guess(str(cname.target))
                    if cdn:
                        _found_domains[domain] = cdn
                        return (domain, cdn)
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, dns.exception.Timeout):
        _dns_failed.add(domain)

    return (domain, 'UNKNOWN')


if __name__ == "__main__":
    import json
    import os
    
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        "-f", "--file", dest="file", help="HAR file to parse", metavar="FILE"
    )

    args = parser.parse_args()

    try:
        har_fname = os.path.basename(args.file)
        
        with open(args.file) as harfile:
            har = json.load(harfile)

            if not 'log' in har:
                exit(0)

            if not 'entries' in har['log']:
                exit(0)
            
            for en in har["log"]["entries"]:
                domain, cdn = get_cdn(en)
                
                # Replace whitespace in CDN name with hyphens.
                cdn = cdn.replace(' ', '-')
                
                print(f"{har_fname} {domain} {cdn}")
    except FileNotFoundError:
        exit("Could not open " + args.file)
    except json.JSONDecodeError:
        exit("Could not parse " + args.file)
