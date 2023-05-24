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
        
        
        parent_data.update({
            "genres": genre,
            "developer" : dev,
            "publisher" : publish[-2],
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
        