# zwift-scrape
Scrape race results from www.zwiftpower.com, also includes a score calculator for WTRL time trials.

## Description

Uses the Selenium Python API with the FireFox geckodriver to scrape race results from zwiftpower. 
* `python zwift_scrape url-to-results` scrapes the given URL and creates two CSVs, one containing the race results for all riders, the other containing the results for the first through and fastest through for each split. 
* `python calculate_wtrl_scores url-or-filepath` calculates the scores for each rider in a WTRL time trial and saves all riders scores in a CSV. Can be called with either a URL to race results (in which case `zwift_scrape` will be used to collect results), or can be called with the filepath to previously scraped CSVs.

Results shown in `./example_ouput/` are generated by running:  
 `python calculate_wtrl_scores https://www.zwiftpower.com/events.php?zid=1588142 -s example_output`

## Requirements
1. Firefox must be installed
2. Requires Selenium `pip install selenium`

## Optional commandline arguments
### zwift_scrape
1. `-s`, `--saveName` - Saves output files to a directory with the given name, if not specified the race title given on the webpage will be used.

### calculate_wtrl_scores
1. `-s`, `--saveName` - As above
2. `-p`, `--ptsFirst` - Sorts output by score, otherwise output is sorted by finish time.
3. `-o`, `--onlyScores` - If called with a URL, only the scores will be saved. Otherwise, the results from zwift_scrape will also be saved.
4. `-e`,`--excludeSplit` - Call with split name to exclude that split from scoring primes. Can be called any number of times.
