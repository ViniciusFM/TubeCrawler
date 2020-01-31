#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, errno, csv, json

try:
    import scrapy
    from scrapy.crawler import CrawlerProcess
    from scrapy.selector import Selector
except ImportError as e:
    print("Couldn't find scrapy modules. Try installing them with pip.")
    print("> pip install scrapy")
    exit(1)

# --------- TERMINAL RELATED STUFF ------------

if sys.platform.lower() == "win32":
    os.system('color')

class style():
    RED = lambda x: '\033[31m' + str(x)
    YELLOW = lambda x: '\033[33m' + str(x)
    RESET = lambda x: '\033[0m' + str(x)

def help():
    print('''
USAGE: '''+sys.argv[0]+''' <channel_name> <output_file_name>

NOT OPTIONAL ARGS:
\tchannel_name: the exactly name of the channel (case sensitive)
\toutput_file_name: the CSV output file name

EXAMPLE:
\t'''+sys.argv[0]+''' foochannel /path/to/foochannellinks.csv

\tThis line will output the video links from oldest to newest
\tfrom foochannel to file located at /path/to/foochannellinks.csv
''')

# -------- CRAWL CLASS ----------

class YTSpider(scrapy.Spider):
    name = 'ytspider'
    yturl = 'https://www.youtube.com{}'

    def __init__(self, url, filename):
        self.start_urls = url
        self.filename = filename
        self.outfile = open(filename, "w", encoding="utf-8", newline="")
        self.fields = ['href', 'title']
        self.writer = csv.DictWriter(self.outfile, delimiter=';', fieldnames=self.fields)
        self.writer.writeheader()

    def parse(self, response):
        for i in response.xpath('//*[contains(@class, "yt-lockup-title ")]'):
            href = i.css('a::attr(href)').extract_first()
            title = i.css('a::attr(title)').extract_first()
            row = { 'href' : self.yturl.format(href),  'title' : title.replace(';', '')}
            self.writer.writerow(row)
            yield row

        load_more = response.xpath('//button[contains(@class,"load-more-button")]/@data-uix-load-more-href')
        if(load_more != []):
            fetchUrl = load_more.extract_first()
            yield scrapy.Request(url=self.yturl.format(fetchUrl), callback=self.parseContinuation)

    def parseContinuation(self, response):
        jsonData = json.loads(response.text)
        sel = Selector(text=jsonData['content_html'], type="html")
        for i in sel.xpath('//*[contains(@class, "yt-lockup-title ")]'):
            href = i.css('a::attr(href)').extract_first()
            title = i.css('a::attr(title)').extract_first()
            row = { 'href' : self.yturl.format(href),  'title' : title.replace(';', '')}
            self.writer.writerow(row)
            yield row
        sel = Selector(text=jsonData['load_more_widget_html'], type="html")
        load_more = sel.xpath('//button[contains(@class,"load-more-button")]/@data-uix-load-more-href')
        if(load_more != []):
            fetchUrl = load_more.extract_first()
            yield scrapy.Request(url=self.yturl.format(fetchUrl), callback=self.parseContinuation)


    def close(self):
        self.outfile.close()
        print("-----Closing file-----")


# -------- FUNCS ----------

def is_file_name_okay(output_file_name):
    try:
        with open(output_file_name, 'w') as f:
            return True
    except IOError as e:
        print(style.RED(""))
        print('<ERR> error number', e.errno, 'which means', e.strerror)
        print(style.YELLOW(""))
        if e.errno == errno.EACCES:
            print(output_file_name, 'has no write permission')
        elif e.errno == errno.EISDIR:
            print(output_file_name, 'is directory')
        print(style.RESET(""))
    return False

# -------- MAIN ----------

def main(channel, output_file_name):
    ytb_start_url = ['https://www.youtube.com/user/'+channel+'/videos?view=0&sort=da&flow=grid']
    print(ytb_start_url)
    if(is_file_name_okay(output_file_name)):
        process = CrawlerProcess({
            'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
        })
        process.crawl(YTSpider, url=ytb_start_url, filename=output_file_name)
        process.start()

if __name__ == '__main__':
    if(len(sys.argv) < 3):
        help()
        exit(1)
    channel = sys.argv[1]
    output_file_name = sys.argv[2]
    main(channel, output_file_name)
