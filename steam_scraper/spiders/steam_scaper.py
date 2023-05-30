from pathlib import Path
import scrapy


class SteamSpider(scrapy.Spider):
    name = "steam"

    start_urls = [
        "https://store.steampowered.com/search/?filter=topsellers&os=win"
    ]

    def parse(self, response):
        div_links = response.css('#search_resultsRows a')
        for link in div_links:
            
            #link dari tag a
            href = link.css('::attr(href)').get()
            
            # OS_support dari nama kelas
            oss = link.css('span.platform_img::attr(class)').getall()
            os_support = []
            for os in oss:
                supported = os.split()[1]
                os_support.append(supported)
            
            # Dynamic price scraper
            price = link.css('div.search_price::text').get().strip()

            parent_data = {
                "title": link.css('span.title::text').get(),
                "base_price": price,
                "os_support": os_support,
                "discount" : link.css('div.search_discount span::text').get(),
                "release": link.css('div.search_released::text').get()
            }
            yield response.follow(href, callback=self.parse_link, meta={'parent_data': parent_data})
    
    def parse_link(self, response):
        parent_data = response.meta["parent_data"]
        genre = response.css('#genresAndManufacturer span a::text').getall()
        dev = [dev.strip() for dev in response.css("#developers_list a::text").getall()]
        publish = [pub for pub in response.css("#genresAndManufacturer a::text").getall()]
        features = [featur.strip() for featur in response.css("#category_block div.label::text").getall()]
        reviewtot = [response.css("#review_histogram_rollup_section div.summary_section span::text").getall()]
        metascore_detect = response.css("#game_area_metascore div.score::text").get()
        if metascore_detect:
            metacritic = metascore_detect.strip()
        else:
            metacritic = None
        storage_element = response.css('div.game_area_sys_req_rightCol ul.bb_ul li::text').getall()
        storages = next((s for s in storage_element if "available space" in s), None)
        if storages is None:
            storages = None
        
        
        parent_data.update({
            "genres": genre,
            "developer" : dev,
            "publisher" : publish[-2],
            "features" : features, 
            "total review" : reviewtot[0][1],
            "storage" : storages,
            "metacritic": metacritic,
            "sum_rating" : response.css('span.game_review_summary::text').get()
        })
        yield parent_data