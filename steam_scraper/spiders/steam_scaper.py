from pathlib import Path
import scrapy
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains


class SteamSpider(scrapy.Spider):
    name = "steam"

    start_urls = [
        "https://store.steampowered.com/search/?filter=topsellers&os=win"
    ]
    def start_requests(self):
        for url in self.start_urls:
            yield SeleniumRequest(
                url=url,
                callback=self.parse_initial,
                wait_time=5,
                wait_until=EC.presence_of_element_located((By.CSS_SELECTOR, '#search_resultsRows')),
                script='window.scrollTo(0, document.body.scrollHeight);',
            )

    def parse_initial(self, response):
        yield from self.parse(response)

        # Scroll down to load more content
        yield SeleniumRequest(
            url=response.url,
            callback=self.parse_scroll,
            wait_time=10,
            wait_until=EC.presence_of_element_located((By.CSS_SELECTOR, '#search_resultsRows')),
            script='window.scrollTo(0, document.body.scrollHeight);',
        )

    def parse_scroll(self, response):
        yield from self.parse(response)

        # Check if there is more content to load
        has_more_content = self.has_more_content(response)
        if has_more_content:
            # Continue scrolling to load more content
            yield SeleniumRequest(
                url=response.url,
                callback=self.parse_scroll,
                wait_time=10,
                wait_until=EC.presence_of_element_located((By.CSS_SELECTOR, '#search_resultsRows')),
                script='window.scrollTo(0, document.body.scrollHeight);',
            )

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
        storage_element = response.css('.game_area_sys_req_full li strong::text').getall()
        storages = [s.strip() for s in storage_element if 'Storage:' in s]
        metacritic = response.css("span.metascore_w::text").get()
        
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
    
    def is_age_verification_page(self, response):
        pass
        # Tentukan kondisi atau selektor yang menunjukkan bahwa halaman konfirmasi usia muncul
        # Misalnya, Anda dapat memeriksa teks atau elemen tertentu pada halaman
        # Return True jika halaman konfirmasi usia muncul, False jika tidak
        # ...

    def bypass_age_verification(self, response):
        # Lakukan langkah-langkah khusus untuk melewati halaman konfirmasi usia
        # Misalnya, Anda dapat menemukan dan mengklik elemen "Ya, Saya Berusia 18 Tahun atau Lebih"
        # Jika diperlukan, Anda juga dapat mengatur cookies atau mengirim data form untuk melewati halaman ini
        # ...

        # Setelah melewati halaman konfirmasi usia, lanjutkan proses scraping seperti biasa
        yield scrapy.Request(url=response.url, callback=self.parse, meta={'dont_redirect': True})