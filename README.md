# mmstats

Generates statistics for a past TopCoder Marathon Match

Requires python3 & numpy (`pip install numpy`)


### Features

* Automatically downloads all of the results from TC webpage (+ can cache them to avoid redownloading)
* Currently has two modes: printing placement distribution (based on bootstrapped simulations) and printing simple ranking
* Has several different standard scoring functions built-in (relative, ranking, raw)
* Can output results in a forum-friendly format

### Placement distribution explained

Probabilities are produced by performing simulations on the system tests, where each simulation samples (with replacement) from the set of system tests that was used during the contest.

**Because those simulations reuse the same set of system tests, they are highly biased towards the original results**

Notes:
* Because of the above, this should not be treated as an estimate of what was the probability of each person finishing in each particular position (real distribution is much more varied than the one produced by this tool)
* This particular test is a very reliable lower bound estimate for the variance
* By toying around with command line options, you can test how the number of tests influences the variance in the final results


### Sample usage:
* `mmstats.py --help` - prints help
* `mmstats.py 17153 -l 50 -p 20 -d 1 -n 10000 -f plain` - was used to produce [this](https://pastebin.com/BbZNHvm5) (older version)
* `mmstats.py 17020 -d 0 -n 10000 -f plain`:
```
                1    2    3    4   5   6   7   8    9   10   11   12 
Psyho        100%   0%   0%   0%  0%  0%  0%  0%   0%   0%   0%   0% 
chokudai       0% 100%   0%   0%  0%  0%  0%  0%   0%   0%   0%   0% 
wleite         0%   0% 100%   0%  0%  0%  0%  0%   0%   0%   0%   0% 
tomerun        0%   0%   0% 100%  0%  0%  0%  0%   0%   0%   0%   0% 
PaulJefferys   0%   0%   0%   0% 51% 49%  0%  0%   0%   0%   0%   0% 
nhzp339        0%   0%   0%   0% 49% 51%  0%  0%   0%   0%   0%   0% 
ainu7          0%   0%   0%   0%  0%  0% 68% 32%   0%   0%   0%   0% 
CatalinT       0%   0%   0%   0%  0%  0% 32% 68%   0%   0%   0%   0% 
mugurelionut   0%   0%   0%   0%  0%  0%  0%  0% 100%   0%   0%   0% 
marek.cygan    0%   0%   0%   0%  0%  0%  0%  0%   0% 100%   0%   0% 
blackmath      0%   0%   0%   0%  0%  0%  0%  0%   0%   0% 100%   0% 
Milanin        0%   0%   0%   0%  0%  0%  0%  0%   0%   0%   0% 100% 
```


### Potential issues
* It can sometimes fail to download results (my guess would be that TC servers can refuse connection after longer downloads); Workaround is to use `-c` option (for caching) and download data in smaller chunks by gradually increasing `-l LIMIT`
* No idea if it handles cases, where someone was banned after the system tests
