from pathlib import Path
import scrapy


class SteamSpider(scrapy.Spider):
    name = "steam"

    custom_settings = {
        'DOWNLOAD_DELAY': 0.5  # Delay of 0.5 seconds between requests
    }

    def start_requests(self):
        for x in range(0,2000,91):
            url = f"https://store.steampowered.com/search/?filter=topsellers&os=win&query&start={x}&count=2000"
            yield scrapy.Request(url=url, callback=self.parse)

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
        dlc_detect = response.css('div.game_area_dlc_bubble div.content h1::text').get()
        if dlc_detect:
            dlc = "yes"
        else:
            dlc = "no"
        sound_detect = response.css('div.game_area_dlc_bubble div.content h1::text').get()
        if sound_detect:
            soundtrack = "yes"
        else:
            soundtrack = "no"
        
        
        
        parent_data.update({
            "genres": genre,
            "dlc": dlc,
            "soundtrack": soundtrack,
            "developer" : dev,
            "publisher" : publish[-2],
            "features" : features, 
            "total review" : reviewtot[0][1],
            "storage" : storages,
            "metacritic": metacritic,
            "sum_rating" : response.css('span.game_review_summary::text').get()
        })
        yield parent_data