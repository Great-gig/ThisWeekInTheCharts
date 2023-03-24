import os
import requests
import bs4
from bs4 import BeautifulSoup
import re
import pandas as pd
import webbrowser
from datetime import datetime
from dateutil.relativedelta import relativedelta


def getSongs(filename, n=20):
    songs = pd.read_csv(filename)
    print("All Songs in database:", songs.shape[0])

    chartposition = 20
    songs = songs[songs['Position'] < chartposition + 1]
    print(f"Songs that reached {chartposition}:", songs.shape[0])

    weeksOnChartLimit = 2
    songs = songs[songs['woc'] < weeksOnChartLimit + 1]
    print(f"Songs new on chart:", songs.shape[0])

    songs = songs.sample(n=n)
    print("Songs randomly sampled", songs.shape[0])
    return songs


def cleanString(string):
    return re.sub(r'[^\w\s]', '', string)


def songs2Strings(songs):
    output = []
    for index, row in songs.iterrows():
        output.append(cleanString(f"{row['artist']} {row['song']}"))
    return output


def firstVid(search):
    words = search.split()
    search_link = "http://www.youtube.com/results?search_query=" + '+'.join(words)
    search_result = requests.get(search_link).text
    soup = BeautifulSoup(search_result, 'html.parser')
    m = re.findall('url":"\/watch\?v=(.*?)",', str(soup))
    if not m:
        return None
    tag = m[0]
    if '\\' in tag:
        tag = tag.split('\\')[0]
    return tag


def strings2PlaylistLink(strings):
    output = "https://www.youtube.com/watch_videos?video_ids="
    for s in strings:
        output += firstVid(s) + ','
    return output


def pullChartData(date):
    search_link = "https://www.officialcharts.com/charts/singles-chart/" + date.strftime("%Y%m%d")
    search_result = requests.get(search_link).text
    soup = BeautifulSoup(search_result, 'html.parser')

    d = date.strftime("%m/%d/%Y")
    positions = soup.find_all("span", class_="position")
    titles = soup.find_all("div", class_="title")
    artists = soup.find_all("div", class_="artist")
    woc = soup.find_all(string=right_comment)
    woc = [i.findNextSibling('td') for i in woc]

    chartData = pd.DataFrame({'Date': [d] * len(positions),
                              'Position': [removeTags(x) for x in positions],
                              'artist': [removeTags(x) for x in artists],
                              'song': [removeTags(x) for x in titles],
                              'woc': [removeTags(x) for x in woc]})
    print(f"date {d} done.")
    return chartData


def right_comment(e):
    return isinstance(e, bs4.element.Comment) and e == ' Wks '


def removeTags(string):
    string = re.sub("<[^<>]*>", '', str(string))
    return string.replace('\n', '')


def pullDataFromAllYears(date):
    chartData = pd.DataFrame({'Date': [],
                              'Position': [],
                              'artist': [],
                              'song': []})
    for i in range(50):
        date = date + relativedelta(years=-1)
        chartData = pd.concat([chartData, pullChartData(date)])

    chartData.to_csv(f'{date.strftime("%m%d")}.csv')
    return chartData


if __name__ == "__main__":
    date = datetime.now()
    date = date + relativedelta(days=8 - date.weekday())  # next Tuesday

    file = f'{date.strftime("%m%d")}.csv'
    if not os.path.isfile(file):
        print("making new csv")
        pullDataFromAllYears(date)

    s = getSongs(file)
    s = songs2Strings(s)
    s = strings2PlaylistLink(s)
    print(s)
    webbrowser.open(s)
