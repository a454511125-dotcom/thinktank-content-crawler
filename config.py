"""
TikTok智库报告采集系统 - 配置文件
方案B：半自动化辅助工具
"""

import os

# 17家智库配置
THINK_TANKS = {
    "brookings": {
        "name": "Brookings Institution",
        "search_url": "https://www.brookings.edu/?s=TikTok&paged={page}",
        "base_url": "https://www.brookings.edu",
        "selectors": {
            "article_list": "article, div.search-result, div.article-info",
            "title": "h3 a, h4 a, a.article-title",
            "url": "h3 a, h4 a, a.article-title",
            "date": "time, span.date, div.date",
            "type": "span.type, div.type"
        },
        "pagination": True,
        "max_pages": 50,
        "use_cloudscraper": True
    },
    
    "csis": {
        "name": "Center for Strategic and International Studies",
        "search_url": "https://www.csis.org/search?search_api_fulltext=TikTok&page={page}",
        "base_url": "https://www.csis.org",
        "selectors": {
            "article_list": "article, div.views-row, div.search-result",
            "title": "h2 a, h3 a, h4 a",
            "url": "h2 a, h3 a, h4 a",
            "date": "time, span.date, div.date",
            "type": "div.type, span.type"
        },
        "pagination": True,
        "max_pages": 50,
        "use_cloudscraper": True
    },
    
    "cfr": {
        "name": "Council on Foreign Relations",
        "disabled": False,  # 可按需通过环境变量提供 Cookie
        "cookie": os.environ.get("CFR_COOKIE", ""),
        "search_url": "https://www.cfr.org/search?q=TikTok&page={page}", # Update URL
        "base_url": "https://www.cfr.org",
        "selectors": {
            "article_list": "div.search-result-item",
            "title": "h3 a",
            "url": "h3 a",
            "date": "span.date",
            "type": "span.type"
        },
        "pagination": True,
        "max_pages": 30
    },
    
    "rand": {
        "name": "RAND Corporation",
        "search_url": "https://www.rand.org/search.html?query=TikTok&page={page}",
        "base_url": "https://www.rand.org",
        "selectors": {
            "article_list": "div.search-result",
            "title": "h3 a",
            "url": "h3 a",
            "date": "span.date",
            "type": "span.pub-type"
        },
        "pagination": True,
        "max_pages": 20,
        "paid_content": True  # 特殊标记：有付费内容
    },
    
    "carnegie": {
        "name": "Carnegie Endowment for International Peace",
        "search_url": "https://carnegieendowment.org/search?term=TikTok&page={page}",
        "base_url": "https://carnegieendowment.org",
        "selectors": {
            "article_list": "div.search-item",
            "title": "h2 a",
            "url": "h2 a",
            "date": "time",
            "type": "span.content-type"
        },
        "pagination": True,
        "max_pages": 20
    },
    
    "atlantic_council": {
        "name": "Atlantic Council",
        "search_url": "https://www.atlanticcouncil.org/?s=TikTok&paged={page}",
        "base_url": "https://www.atlanticcouncil.org",
        "selectors": {
            "article_list": "article.post",
            "title": "h2.entry-title a",
            "url": "h2.entry-title a",
            "date": "time.entry-date",
            "type": "span.post-type"
        },
        "pagination": True,
        "max_pages": 30
    },
    
    "cnas": {
        "name": "Center for a New American Security",
        "search_url": "https://www.cnas.org/search?q=TikTok&page={page}",
        "base_url": "https://www.cnas.org",
        "selectors": {
            "article_list": "div.search-result",
            "title": "h3 a",
            "url": "h3 a",
            "date": "span.date",
            "type": "span.type"
        },
        "pagination": True,
        "max_pages": 15
    },
    
    "piie": {
        "name": "Peterson Institute for International Economics",
        "disabled": False,  # 可按需通过环境变量提供 Cookie
        "cookie": os.environ.get("PIIE_COOKIE", ""),
        "search_url": "https://www.piie.com/search?search_api_fulltext=TikTok&page={page}", # Update URL
        "base_url": "https://www.piie.com",
        "selectors": {
            "article_list": "div.publication",
            "title": "h2 a",
            "url": "h2 a",
            "date": "time",
            "type": "span.pub-type"
        },
        "pagination": True,
        "max_pages": 10
    },
    
    "chicago_council": {
        "name": "Chicago Council on Global Affairs",
        "search_url": "https://globalaffairs.org/search?query=TikTok&page={page}",
        "base_url": "https://globalaffairs.org",
        "selectors": {
            "article_list": "div.search-result",
            "title": "h3 a",
            "url": "h3 a",
            "date": "span.date",
            "type": "span.type"
        },
        "pagination": True,
        "max_pages": 10
    },
    
    "hoover": {
        "name": "Hoover Institution",
        "search_url": "https://www.hoover.org/search?q=TikTok&page={page}",  # 修复：使用新的可用URL
        "base_url": "https://www.hoover.org",
        "selectors": {
            "article_list": "div.search-result",
            "title": "h3 a",
            "url": "h3 a",
            "date": "span.date",
            "type": "span.type"
        },
        "pagination": True,
        "max_pages": 15
    },
    
    "hudson": {
        "name": "Hudson Institute",
        "search_url": "https://www.hudson.org/search?q=TikTok&page={page}",
        "base_url": "https://www.hudson.org",
        "selectors": {
            "article_list": "div.search-item",
            "title": "h2 a",
            "url": "h2 a",
            "date": "time",
            "type": "span.content-type"
        },
        "pagination": True,
        "max_pages": 20
    },
    
    "cato": {
        "name": "Cato Institute",
        "search_url": "https://www.cato.org/search?query=TikTok&page={page}",
        "base_url": "https://www.cato.org",
        "selectors": {
            "article_list": "div.search-result",
            "title": "h3 a",
            "url": "h3 a",
            "date": "time",
            "type": "span.pub-type"
        },
        "pagination": True,
        "max_pages": 20
    },
    
    "heritage": {
        "name": "The Heritage Foundation",
        "search_url": "https://www.heritage.org/search?query=TikTok&page={page}",
        "base_url": "https://www.heritage.org",
        "selectors": {
            "article_list": "div.search-result",
            "title": "h2 a",
            "url": "h2 a",
            "date": "time",
            "type": "span.content-type"
        },
        "pagination": True,
        "max_pages": 30
    },
    
    "wilson": {
        "name": "Wilson Center",
        "search_url": "https://www.wilsoncenter.org/search?query=TikTok&page={page}",
        "base_url": "https://www.wilsoncenter.org",
        "selectors": {
            "article_list": "article.search-result",
            "title": "h3 a",
            "url": "h3 a",
            "date": "time",
            "type": "span.type"
        },
        "pagination": True,
        "max_pages": 20
    },
    
    "aei": {
        "name": "American Enterprise Institute",
        "search_url": "https://www.aei.org/?s=TikTok&paged={page}",
        "base_url": "https://www.aei.org",
        "selectors": {
            "article_list": "article.post",
            "title": "h2.entry-title a",
            "url": "h2.entry-title a",
            "date": "time.entry-date",
            "type": "span.post-format"
        },
        "pagination": True,
        "max_pages": 25
    },
    
    "asia_society": {
        "name": "Asia Society",
        "disabled": False, # 启用，使用Selenium
        "search_url": "https://asiasociety.org/search/google?keys=TikTok&page={page}", # Update URL
        "base_url": "https://asiasociety.org",
        "selectors": {
            "article_list": "div.gsc-webResult, div.gsc-result, div.search-result",
            "title": "a.gs-title, h3 a",
            "url": "a.gs-title, h3 a",
            "date": "div.gs-snippet, span.date", # Google搜索通常摘要在 snippet
            "type": "span.type"
        },
        "pagination": True,
        "max_pages": 10
    },
    
    "cap": {
        "name": "Center for American Progress",
        "search_url": "https://www.americanprogress.org/?s=TikTok&paged={page}",
        "base_url": "https://www.americanprogress.org",
        "selectors": {
            "article_list": "article.search-result",
            "title": "h2 a",
            "url": "h2 a",
            "date": "time",
            "type": "span.post-type"
        },
        "pagination": True,
        "max_pages": 15
    }
}

# 时间阶段划分（用于自动标注）
TIME_PHASES = {
    "phase1": {
        "name": "观察阶段",
        "start": "2017-01-01",
        "end": "2019-12-31"
    },
    "phase2": {
        "name": "初步审查阶段",
        "start": "2020-01-01",
        "end": "2020-12-31"
    },
    "phase3": {
        "name": "政府设备禁令和数据安全审查阶段",
        "start": "2021-01-01",
        "end": "2022-12-31"
    },
    "phase4": {
        "name": "全面限制和立法阶段",
        "start": "2023-01-01",
        "end": "2026-12-31"
    }
}

# 爬虫设置
SCRAPER_SETTINGS = {
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "delay_between_requests": 3,  # 秒
    "timeout": 30,
    "max_retries": 3,
    "save_html": True,  # 是否保存原始HTML
    "debug_mode": True,  # 调试模式：保存HTML并打印更多信息
}

# 输出路径
OUTPUT_PATHS = {
    "data_dir": "data",
    "raw_html": "data/raw_html",
    "processed": "data/processed",
    "final_json": "data/final/tiktok_reports.json",
    "rand_paid": "data/final/rand_paid_reports.json",  # RAND付费报告单独存储
    "logs": "logs"
}

# Brookings 的可选 Algolia 搜索配置；API Key 只从环境变量读取。
BROOKINGS_ALGOLIA = {
    "app_id": os.environ.get("BROOKINGS_ALGOLIA_APP_ID", "XGC391W2WE"),
    "api_key": os.environ.get("BROOKINGS_ALGOLIA_API_KEY", ""),
    "index_name": os.environ.get("BROOKINGS_ALGOLIA_INDEX", "prod_searchable_posts"),
}
