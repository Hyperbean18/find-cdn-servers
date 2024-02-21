SHELL := /usr/bin/bash

PY := python3

PLL := parallel
# GNU parallel options.
PLL_OPTS := --line-buffer -j4

# Path to utilities.
UTILS := utils

# Path to generated data.
DATA := data
# Path to HAR files.
HAR_DIR := $(DATA)/hars
# Set of all HAR files.
HAR_FILES := $(wildcard $(HAR_DIR)/*.har)

# Path to external tools.
EXT := ext

# Path to BrowserMob proxy.
BMP_PKG := browsermob-proxy
BMP_VER := 2.1.4
BMP_BIN := $(EXT)/$(BMP_PKG)-$(BMP_VER)/bin/$(BMP_PKG)

# Path to chromedriver.
CHROME_DRV_BIN := /usr/bin/chromedriver


# Utility function to check if BrowserMob proxy is installed.
BMP_ERR := Error: cannot find '$(BMP_BIN)' in path
fn_bmp_check =					\
        @which $(BMP_BIN) > /dev/null ||	\
                (echo "$(BMP_ERR)" >& 2 &&    	\
                        exit 1)

# Utility function to check if chromedriver is installed.
CDB_ERR := Error: cannot find '$(CHROME_DRV_BIN)' in path
fn_cdb_check =					\
        @which $(CHROME_DRV_BIN) > /dev/null ||	\
                (echo "$(CDB_ERR)" >& 2 &&    	\
                        exit 1)


# Use the Hispar list generated on January 28, 2021 (the most recent).
TOPLIST := hispar-list-21-01-28


# Various simple characterizations of the Hispar list.
HISPAR_STATS := $(DATA)/tot-pages.txt	\
	$(DATA)/min-max-site-ranks.txt	\
	$(DATA)/tot-sites.txt		\
	$(DATA)/avg-pages-per-site.txt


# CDN server names.
CDN_HOSTS := $(DATA)/cdn-domains.txt	\
	$(DATA)/cdn-domains-w-whois.txt \
	$(DATA)/top-cdn-domains-w-whois.txt

# Various simple characterizations of the CDN hostnames discovered.
CDN_STATS := $(DATA)/cdn-domains-uniq.txt		\
	$(DATA)/cdn-domain-names.txt			\
	$(DATA)/cdn-num-domain-names.txt		\
	$(DATA)/domains-per-cdn.txt			\
	$(DATA)/cdn-num-uniq-unk-domains-bef-whois.txt	\
	$(DATA)/cdn-num-uniq-unk-domains-aft-whois.txt


ALL := $(DATA)/rank-bot-20.txt		\
	$(DATA)/crawl-landing.txt	\
	$(DATA)/crawl-pages.txt


.PHONY: all gen-hars wipe-hars regen-hars get-cdns clean wipe


all: $(ALL) gen-hars get-cdns


# Download the web-page list.
$(TOPLIST):
	@curl -O https://hispar.cs.duke.edu/archive/$@.zip	&& \
	unzip $@.zip						&& \
	rm -f $@.zip


# Characterize the Hispar list.
hispar-stats: $(HISPAR_STATS)

# Total number of pages in the top list.
$(DATA)/tot-pages.txt: $(TOPLIST)
	@wc -l $< > $@

# Min. and max. Alexa ranking of the web sites in the top list.
$(DATA)/min-max-site-ranks.txt: $(TOPLIST)
	@awk '{print $$1}' $< | sort -nu  | head -1  > $@
	@awk '{print $$1}' $< | sort -nru | head -1 >> $@

# Number of unique web sites in the top list.
$(DATA)/tot-sites.txt: $(TOPLIST)
	@awk '{print $$1}' $< | sort -nu | wc -l > $@

# Average number of pages per site in the top list.
$(DATA)/avg-pages-per-site.txt: $(DATA)/tot-pages.txt $(DATA)/tot-sites.txt
	@echo "scale=1; "				\
		`awk '{print $$1}' $(word 1, $^)`	\
		" / "					\
		`cat $(word 2, $^)` | bc > $@


# Get the rank of the last site before the sites with the lowest 20 ranks.
$(DATA)/rank-bot-20.txt: $(TOPLIST)
	@awk '$$2 == 0 {print $$1}' $< | sort -nu | tail -21 | head -1 > $@

# Obtain a set of landing pages to crawl and look for CDN servers.
#
# We derive the set of pages to crawl from the Hispar list.
#
# The format of the Hispar list is as follows.
# <alexa_rank> <search_rank> <url>
#
#   where search_rank is zero for landing pages.
#
# Pick the top 20 landing pages.
# Pick another 10 from ranks in the interval (20, 100].
# Pick another 20 from ranks in the interval (100, 1000].
# Pick another 30 from ranks in the interval (1000, bottom-20).
# Pick the bottom 20 landing pages.
#
# Store URLs selected for crawling with rank information.
$(DATA)/crawl-landing.txt: $(TOPLIST) $(DATA)/rank-bot-20.txt
	@awk '$$2 == 0 && $$1 <= 20'                $<	> $@
	@awk '$$2 == 0 && $$1 >  20 && $$1 <= 100'  $<	| \
		shuf					| \
		head -10				>> $@
	@awk '$$2 == 0 && $$1 > 100 && $$1 <= 1000' $<	| \
		shuf					| \
		head -20				>> $@
	@awk -vN=`cat $(word 2, $^)`			\
	      '$$2 == 0 && $$1 > 1000 && $$1 <   N' $<	| \
		shuf 					| \
		head -30 				>> $@
	@awk '$$2 == 0'                             $<	| \
		sort -nu -k1,1	 			| \
		tail -20				>> $@

# Add internal pages to the crawl list.
$(DATA)/crawl-pages.txt: $(UTILS)/pick-internal.py $(DATA)/crawl-landing.txt $(TOPLIST)
	@$(PY) $^ $@


# Crawl pages and generate HAR files for these page-fetches.
gen-hars: $(DATA)/gen-hars.log

$(DATA)/gen-hars.log: $(UTILS)/har-gen.py $(BMP_BIN) $(CHROME_DRV_BIN) \
	$(DATA)/crawl-pages.txt $(HAR_DIR)
	$(call fn_bmp_check)
	$(call fn_cdb_check)
	@$(PY) $^ > $@

$(HAR_DIR):
	@[ -d $@ ] || mkdir -p $@

# Wipe all HAR files.
wipe-hars:
	@rm -rf $(HAR_DIR)
	@rm -f $(DATA)/*.log

# Redo page fetches and regenerate HAR files.
regen-hars: wipe-hars $(DATA)/gen-hars.log


# Obtain CDN domains from HAR files and characterize the data set.
get-cdns: $(CDN_HOSTS) $(CDN_STATS)

# Extract the domains from the HAR files and identify which CDN they
# correspond to.
$(DATA)/cdn-domains.txt: $(UTILS)/get_cdn.py $(HAR_FILES)
	@$(PLL) $(PLL_OPTS) $(PY) $(word 1, $^) -f {} ::: $(HAR_FILES) > $@

# Try to resolve domains of `UNKNOWN` CDNs using `whois` as an extra
# effort to identify the CDNs.
$(DATA)/cdn-domains-w-whois.txt: $(UTILS)/whois-lookup.py \
	$(DATA)/cdn-domains.txt
	@$(PY) $^ $@ 2> whois-lookup.log

# Filter out duplicates per page fetch.
$(DATA)/cdn-domains-uniq.txt: $(DATA)/cdn-domains-w-whois.txt
	@sort $< | uniq -c | sort -k1nr,1 -k4,4 -k2,2 > $@

# Retrieve counts of domains per CDN.
$(DATA)/domains-per-cdn.txt: $(DATA)/cdn-domains-uniq.txt
	@awk '{print $$4}' $< | sort | uniq -c | sort -nr -k1,1 > $@

# Extract unique CDN domain names (and drop all other information).
$(DATA)/cdn-domain-names.txt: $(DATA)/cdn-domains-uniq.txt
	@awk '{print $$3}' $< | sort -u > $@

# Count the unique CDN domain names across all pages.
$(DATA)/cdn-num-domain-names.txt: $(DATA)/cdn-domain-names.txt
	@wc -l $< > $@

# Filter domain names of top CDNs.
$(DATA)/top-cdn-domains-w-whois.txt: $(DATA)/cdn-domains-w-whois.txt
	@awk '$$3~/(Google|Amazon|Cloudflare|Akamai|Fastly)/' $< > $@


# Filter the UNKNOWN CDN domains _prior_ to using `whois`.
$(DATA)/cdn-unk-domains-bef-whois.txt: $(DATA)/cdn-domains.txt
	@awk '$$3 == "UNKNOWN" {print $$1, $$2}' $< | \
	sed -E 's/^([0-9]+)_([0-9]+)_(.*)/\1 \2 \3/' > $@

# Filter the UNKNOWN CDN domains _after_ using `whois`.
$(DATA)/cdn-unk-domains-aft-whois.txt: $(DATA)/cdn-domains-w-whois.txt
	@awk '$$3 == "UNKNOWN" {print $$1, $$2}' $< | \
	sed -E 's/^([0-9]+)_([0-9]+)_(.*)/\1 \2 \3/' > $@

# Filter the unique UNKNOWN CDN domains prior to or after using `whois`.
$(DATA)/cdn-uniq-unk-%-whois.txt: $(DATA)/cdn-unk-%-whois.txt
	@awk '{print $$4}' $< | sort -u > $@

# Count the unique UNKNOWN CDN domains prior to or after using `whois`.
$(DATA)/cdn-num-%-whois.txt: $(DATA)/cdn-%-whois.txt
	@wc -l $< > $@


clean:
	@rm -f $(HISPAR_STATS)
	@rm -f $(CDN_HOSTS) $(CDN_STATS)
	@rm -f ./*.log


# Wipe everything to start all experiments from scratch.
wipe: clean
	@rm -f $(TOPLIST) $(ALL)
