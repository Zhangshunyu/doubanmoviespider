# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item,Field


class DoubanMovieItem(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
	#电影ID
	movie_id = Field()
	#电影名称
	movie_name = Field()
	#电影评星
	movie_rate = Field()
	#电影上映年份
	movie_year = Field()
	#电影导演
	movie_director = Field()
	#电影编辑
	movie_writor = Field()
	#电影演员
	movie_actors = Field()
	#电影类型
	movie_type = Field()
	#制片国家/地区
	movie_region = Field()
	#电影语言
	movie_language = Field()
	#电影时长
	movie_time = Field()
	#电影别名
	movie_dialect = Field()
	#电影描述
	movie_desc = Field()
	#电影标签
	movie_tags = Field()
	#电影图片链接
	movie_pic_url = Field()