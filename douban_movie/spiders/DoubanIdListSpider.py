# -*- coding: utf-8 -*-
import sys
reload(sys)

sys.setdefaultencoding("utf-8")

from scrapy.spiders import CrawlSpider,Rule
from scrapy.http import Request
from scrapy.selector import HtmlXPathSelector
from scrapy.linkextractors import LinkExtractor
from douban_movie.items import DoubanMovieIdItem,TagItem
import logging
from bitarray import bitarray
import time
from pymongo import MongoClient

total_count = 0

#used to restart crawler
parsed_ids = bitarray(100000000)
parsed_ids.setall(False)

class DoubanIdListSpider(CrawlSpider):
	name = "doubanidlist"
	allowed_domain = ["movie.douban.com"]
	tag_url = "https://movie.douban.com/tag/"
	
	tag_from_db = False
	
	# use tag to crawl movie data
	start_urls = [
		"https://movie.douban.com/tag/"
	]
	
	def __init__(self,*a,**kw):
		super(DoubanIdListSpider,self).__init__(*a,**kw)
		self.tag_client = MongoClient()
		self.tag_db = self.tag_client.movie
		self.id_list = self.tag_db.id_list
		self.tag_col = self.tag_db.tags
		
		# initialize parsed movie ids
		if self.tag_from_db == True:
			print("initialize parsed ids")
			ids = self.id_list.find({},{'movie_id':1})
			for id in ids:
				parsed_ids[id['movie_id']] = True
			print("done! Go!")
	
	def create_tag_item(self,tag,state,page_num):
		tag_item = TagItem()
		tag_item['tag'] = tag
		tag_item['state'] = state
		tag_item['page'] = page_num
		return tag_item
		
	def parse(self, response):
		if self.tag_from_db is False:
			tags = response.xpath("//td/a/@href").extract()
			for tagstr in tags:
				if tagstr.startswith("/tag/"):
					tag = tagstr[5:]
					tag_item = self.create_tag_item(tag,0,1)
					self.tag_col.insert_one(dict(tag_item))
					yield Request(self.tag_url+tag+"?type=O",callback = self.parse_page)
		else:
			not_start_tags = self.tag_col.find({"state":0})
			for tag in not_start_tags:
				yield Request(self.tag_url + tag["tag"] + "?type=O",callback = self.parse_page)
			process_tags = self.tag_col.find({"state":1})
			for tag in process_tags:
				yield Request(self.tag_url + tag["tag"] + "?start=" + str((tag["page"]-1)*20) +"&type=O")
	
	def parse_page(self, response):
		global total_count
		global parsed_ids
		
		this_page_num = response.xpath('//span[@class="thispage"]/text()').extract_first()
		this_page_num = int(this_page_num if this_page_num else "1")
		tag = response.xpath("//span[@class='tags-name']/text()").extract_first()
		
		# add relate_tag
		if this_page_num == 1:
			print('process tag %s'%(tag))
			self.tag_col.find_one_and_update({'tag':tag},{'$set':{'state':1}})
			relate_tag = response.xpath("//div[@id='tag_list']/span/a/text()").extract()
			if relate_tag:
				for t in relate_tag:
					ret =  self.tag_col.find_one({'tag':tag})
					if ret is None:
						print("add new tag %s"%(tag))
						self.tag_col.insert_one(dict(self.create_tag_item(t,0,1)))
						
		print("start to parse tag %s at page %d"%(tag, this_page_num))			
		pages = response.xpath('//div[@class="article"]//tr[@class="item"]//a[@class="nbg"]/@href').extract()
		add_count = 0
		if pages:
			for page in pages:
				page_id = int(page.split('/')[-2])
				if parsed_ids[page_id]:
					print("exist id = %s"%(page))
					continue
				else:
					add_count += 1
					total_count += 1
					item = DoubanMovieIdItem()
					parsed_ids[page_id] = True
					item['movie_id'] = page_id
					item['movie_url'] = page
					item['parsed'] = False
					item['page'] = int(this_page_num)
					item['movie_tag'] = tag
					yield item
		print("add %d ids in tag %s and page %d"%(add_count,tag,this_page_num))
		#find next page
		nextpage = response.xpath('//span[@class="next"]/a/@href').extract_first()
		if nextpage:
			yield Request(nextpage,callback=self.parse_page)
		else:
			print('finish process tag %s with total count %d'%(tag,total_count))
			self.tag_col.find_one_and_update({'tag':tag},{'$set':{'state':2}})
			#find an random tag
			un_mined_tag = self.tag_col.find_one({'state':0})
			if un_mined_tag:
				print("go to mine tag %s"%(un_mined_tag))
				yield Request(self.tag_url+un_mined_tag['tag'] + "?type=O",callback=self.parse_page)