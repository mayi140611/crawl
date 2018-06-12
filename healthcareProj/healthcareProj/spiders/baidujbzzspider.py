# -*- coding: utf-8 -*-
import scrapy


class BaidujbzzspiderSpider(scrapy.Spider):
    name = 'baidujbzzspider'
    allowed_domains = ['baike.baidu.com']
    start_urls = ['http://baike.baidu.com/']

    def parse(self, response):
        pass
        yield scrapy.Request()
