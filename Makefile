SHELL := /usr/bin/bash

PY := python3

# Path to utilities.
UTILS := utils

# Path to generated data.
DATA := data

# Use the Hispar list generated on January 28, 2021 (the most recent).
TOPLIST := hispar-list-21-01-28


# Various simple characterizations of the Hispar list.
HISPAR_STATS:=$(DATA)/tot-pages.txt	\
	$(DATA)/min-max-site-ranks.txt	\
	$(DATA)/tot-sites.txt		\
	$(DATA)/avg-pages-per-site.txt

ALL := $(DATA)/rank-bot-20.txt		\
	$(DATA)/crawl-landing.txt	\
	$(DATA)/crawl-pages.txt


.PHONY: all clean wipe


all: $(ALL)


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


clean:
	@rm -f $(HISPAR_STATS) ./*.log

# Wipe everything to start all experiments from scratch.
wipe: clean
	@rm -f $(TOPLIST) $(ALL)
