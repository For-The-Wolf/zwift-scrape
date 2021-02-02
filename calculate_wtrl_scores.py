import pandas as pd
from os import path, mkdir
from argparse import ArgumentParser
from zwift_scrape import zwift_scrape,mkdirAndSave
import re

def isURL(string):
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex,string) is not None


def scoreDist():
    scores = [40,35,30,29,28,27,26,25,24,23]
    for n in range(8):
        scores += [20-n for _ in range(5)]
    for n in range(11):
        scores += [12-n for _ in range(3)]
    return scores

def positionToScore(row):
    pos = row['Position']
    scores = scoreDist()
    try:
        return scores[pos-1]
    except IndexError:
        return 1

def primeToScore(row,exclude):
    if row['Split'] in exclude:
        return 0
    if row['Prime'] == 'First over line':
        return (11 - row['Position'])
    elif row['Prime'] == 'Fastest time':
        scoreDist = [20,15,10]+[11-x for x in range(4,11)]
        pos = row['Position']-1
        return scoreDist[pos]

def appendScores(finishes,primes,exclude):
    results = finishes
    finishScores = [positionToScore(row) for _,row in finishes.iterrows()]
    results['Finish'] = finishScores 
    dataLen = len(finishScores)
    results['First over line'] = [0 for _ in range(dataLen)]
    results['Fastest time'] = [0 for _ in range(dataLen)]
    for _,row in primes.iterrows():
        rider = row['Rider']
        prime = row['Prime']
        results.loc[results['Name'] == rider,prime] += primeToScore(row,exclude)
    totals = [r['Finish']+r['First over line']+r['Fastest time'] for _,r in results.iterrows()]
    results['Total'] = totals
    return results

def importFromCSV(raceName):
    finishes = pd.read_csv(path.join(raceName,'finishes.csv'))
    primes = pd.read_csv(path.join(raceName,'primes.csv'))
    return finishes,primes

def main():
    parser = ArgumentParser(description='Calculate WTRL scores from zwift-power URL or CSV.')
    parser.add_argument('datapath',help='This can be either a URL to zwift results or a filepath to the output from zwift_scrape.')
    parser.add_argument('--saveName','-s', help = "Name to save output data to. If not specified then scraped race title will be used")
    parser.add_argument('--ptsFirst','-p', action='store_true', help ='Sort output by score, otherwise sorts by finish position.')
    parser.add_argument('--onlyScores','-o', action='store_true',help='Only save CSV of scores (do not save scraped times and primes).')
    parser.add_argument('--excludeSplit','-e',action='append',default = [],help='Exclude a split from the scoring, can be called any number of times.')
    settings = parser.parse_args()
    name = settings.saveName
    if isURL(settings.datapath):
        url = True
        savePath,finishes,primes = zwift_scrape(settings.datapath)
    elif path.exists(settings.datapath):
        url = False
        finishes,primes = importFromCSV(settings.datapath)
        savePath = path.split(settings.datapath)[-1]
    else:
        raise ValueError('Please enter a valid URL or filepath')
    if settings.saveName:
            savePath = settings.saveName
    results = appendScores(finishes,primes,settings.excludeSplit)
    if settings.ptsFirst:
        results = results.sort_values(by=['Category','Total'],ascending=False)
    mkdirAndSave('results',results,savePath)
    if url and not settings.onlyScores:
        mkdirAndSave('finishes',finishes,savePath)
        mkdirAndSave('primes',primes,savePath)

if __name__ == '__main__':
    main()
