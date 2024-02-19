
# Use the Hispar list generated on January 28, 2021 (the most recent).
TOPLIST := hispar-list-21-01-28


# Various simple characterizations of the Hispar list.
HISPAR_STATS:=tot-pages.txt	\
	min-max-site-ranks.txt	\
	tot-sites.txt		\
	avg-pages-per-site.txt

ALL :=


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
tot-pages.txt: $(TOPLIST)
	@wc -l $< > $@

# Min. and max. Alexa ranking of the web sites in the top list.
min-max-site-ranks.txt: $(TOPLIST)
	@awk '{print $$1}' $< | sort -nu  | head -1  > $@
	@awk '{print $$1}' $< | sort -nru | head -1 >> $@

# Number of unique web sites in the top list.
tot-sites.txt: $(TOPLIST)
	@awk '{print $$1}' $< | sort -nu | wc -l > $@

# Average number of pages per site in the top list.
avg-pages-per-site.txt: tot-pages.txt tot-sites.txt
	@echo "scale=1; "				\
		`awk '{print $$1}' $(word 1, $^)`	\
		" / "					\
		`cat $(word 2, $^)` | bc > $@


clean:
	@rm -f $(ALL) $(HISPAR_STATS)

# Wipe everything to start all experiments from scratch.
wipe: clean
	@rm -f $(TOPLIST)
