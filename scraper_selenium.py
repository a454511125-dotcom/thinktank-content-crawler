"""
TikTok智库报告采集器 - Selenium版核心爬虫模块
支持JavaScript动态渲染的网页
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import os
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, List, Optional
from urllib.parse import urljoin
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False
    print("⚠️ cloudscraper未安装，某些网站可能会被拦截。运行: pip install cloudscraper")

from config import THINK_TANKS, TIME_PHASES, SCRAPER_SETTINGS, OUTPUT_PATHS, BROOKINGS_ALGOLIA


class ThinkTankScraper:
    """智库报告采集器基类 - Selenium增强版"""
    
    def __init__(self, think_tank_id: str, use_selenium: bool = True, manual_auth: bool = False):
        """
        初始化爬虫
        
        Args:
            think_tank_id: 智库ID
            use_selenium: 是否使用Selenium
            manual_auth: 是否开启人工辅助验证 (默认False)
        """
        self.tank_id = think_tank_id
        self.config = THINK_TANKS[think_tank_id]
        self.use_selenium = use_selenium
        self.manual_auth = manual_auth
        self.results = []
        self.paid_results = []
        
        # 初始化Selenium
        if self.use_selenium:
            self.driver = self._init_selenium_driver()
        else:
            # 传统requests初始化...
            if CLOUDSCRAPER_AVAILABLE:
                self.session = cloudscraper.create_scraper()
            else:
                self.session = requests.Session()
                self.session.headers.update({
                    'User-Agent': SCRAPER_SETTINGS['user_agent']
                })
        
        if not self.use_selenium and self.config.get('cookie'):
            self.session.headers.update({'Cookie': self.config['cookie']})

        self._setup_directories()
        self._setup_logging()
        
    def _init_selenium_driver(self):
        """初始化Selenium WebDriver (增强反检测)"""
        chrome_options = Options()
        
        # 反检测核心配置：隐藏自动化特征
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 根据manual_auth决定是否开启无头模式
        if not self.manual_auth:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--window-size=1920,1080')
        else:
            chrome_options.add_argument('--start-maximized') 
            
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument(f'user-agent={SCRAPER_SETTINGS["user_agent"]}')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 通过CDP命令彻底抹除webdriver属性
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })
        
        driver.set_page_load_timeout(SCRAPER_SETTINGS['timeout'])
        return driver

    def wait_for_manual_auth(self):
        """等待用户手动验证"""
        if self.manual_auth:
            print(f"\n{'='*50}")
            print(f"🛑 [人工介入] 正在访问: {self.config['name']}")
            print("请在弹出的浏览器中手动完成验证 (如Cloudflare/登录)")
            print("确认页面正常加载后，请回到这里")
            input("👉 按 [回车键] 继续爬取...")
            print(f"{'='*50}\n")
            self.logger.info("用户确认验证完成")
        
    def _setup_directories(self):
        """创建必要的目录"""
        for path in OUTPUT_PATHS.values():
            target = Path(path)
            if target.suffix == '.json':
                target = target.parent
            target.mkdir(parents=True, exist_ok=True)
            
        # 为每个智库创建HTML调试目录
        debug_dir = Path(OUTPUT_PATHS['raw_html']) / self.tank_id
        debug_dir.mkdir(parents=True, exist_ok=True)
        
    def _setup_logging(self):
        """设置日志"""
        log_dir = Path(OUTPUT_PATHS['logs'])
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f"{self.tank_id}_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.tank_id)
        
    def fetch_page_selenium(self, url: str, wait_for_selector: str = None) -> Optional[str]:
        """
        使用Selenium获取页面（支持JavaScript渲染）
        
        Args:
            url: 目标URL
            wait_for_selector: 等待特定元素加载的CSS选择器
            
        Returns:
            渲染后的HTML内容
        """
        try:
            self.logger.info(f"[Selenium] 正在访问: {url}")
            self.driver.get(url)
            
            # 如果开启了人工介入，且是第一次请求，暂停等待
            if self.manual_auth and not getattr(self, '_auth_done', False):
                self.wait_for_manual_auth()
                self._auth_done = True
            
            # 等待JavaScript加载完成
            if wait_for_selector:
                wait = WebDriverWait(self.driver, 15)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector)))
                self.logger.info(f"✓ 元素 '{wait_for_selector}' 已加载")
            else:
                # 默认等待页面完全加载
                time.sleep(5)
            
            # 保存调试HTML
            if SCRAPER_SETTINGS.get('debug_mode', False):
                self._save_debug_html(self.driver.page_source, url)
            
            time.sleep(SCRAPER_SETTINGS['delay_between_requests'])
            return self.driver.page_source
            
        except TimeoutException:
            self.logger.error(f"[Selenium] 超时: {url}")
            return None
        except Exception as e:
            self.logger.error(f"[Selenium] 错误: {e}")
            return None
            
    def _save_debug_html(self, html: str, url: str):
        """保存调试HTML"""
        debug_dir = Path(OUTPUT_PATHS['raw_html']) / self.tank_id
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.tank_id}_{timestamp}_selenium.html"
        filepath = debug_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        self.logger.info(f"💾 [Debug] HTML已保存: {filepath}")
        
    def parse_search_results(self, html: str) -> List[Dict]:
        """
        解析搜索结果页
        
        Args:
            html: 页面HTML内容（已渲染）
            
        Returns:
            文章列表
        """
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        selectors = self.config['selectors']
        
        # 查找文章列表
        article_elements = soup.select(selectors['article_list'])
        self.logger.info(f"找到 {len(article_elements)} 个匹配元素")
        
        for elem in article_elements:
            try:
                # 提取标题和URL
                title_elem = elem.select_one(selectors['title'])
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                url = title_elem.get('href', '')
                
                if not url.startswith('http'):
                    url = urljoin(self.config['base_url'], url)
                
                # 提取日期
                date = None
                date_elem = elem.select_one(selectors.get('date', ''))
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    date = self.parse_date(date_text)
                
                # 提取内容类型
                content_type = 'Article'
                type_elem = elem.select_one(selectors.get('type', ''))
                if type_elem:
                    content_type = type_elem.get_text(strip=True)
                
                articles.append({
                    'title': title,
                    'url': url,
                    'publish_date': date,
                    'content_type': content_type
                })
                
            except Exception as e:
                self.logger.warning(f"解析单篇文章失败: {e}")
                continue
        
        return articles
        
    def parse_date(self, date_str: str) -> Optional[str]:
        """解析日期字符串"""
        from dateutil import parser
        try:
            dt = parser.parse(date_str, fuzzy=True)
            return dt.strftime('%Y-%m-%d')
        except:
            return None
            
    def determine_phase(self, publish_date: str) -> str:
        """与 HTTP 版共用同一时期划分及日期口径。"""
        from scraper import ThinkTankScraper as HTTPScraper
        return HTTPScraper.determine_phase(self, publish_date)

    def parse_article_content(self, url: str) -> Dict:
        """获取文章全文（使用Selenium）"""
        if self.use_selenium:
            html = self.fetch_page_selenium(url, wait_for_selector='article, main, .content')
        else:
            html = self.fetch_page(url)
            
        if not html:
            return {'full_text': '', 'abstract': '', 'authors': []}
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 提取全文
        content_elem = soup.select_one('article, main, div.content, div.article-body')
        full_text = content_elem.get_text(strip=True, separator=' ') if content_elem else ''
        
        # 提取摘要
        abstract = ''
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc:
            abstract = meta_desc.get('content', '')
        
        # 提取作者
        authors = []
        author_elems = soup.select('a[rel="author"], .author, .byline')
        for elem in author_elems:
            author = elem.get_text(strip=True)
            if author:
                authors.append(author)
        
        return {
            'full_text': full_text,
            'abstract': abstract,
            'authors': list(set(authors))
        }
        
    def scrape_all(self, max_pages: Optional[int] = None):
        """执行完整采集流程（实时保存版）"""
        self.logger.info(f"开始爬取 {self.config['name']}")
        
        # 特殊处理：Brookings 使用 Algolia API
        if self.tank_id == 'brookings' and BROOKINGS_ALGOLIA['api_key']:
            self._scrape_brookings_algolia(max_pages)
            return

        if self.tank_id == 'brookings':
            self.logger.info('未配置 Algolia API Key，使用浏览器搜索页面采集')

        if max_pages is None:
            max_pages = self.config.get('max_pages', 10)
        
        total_count = 0
        
        for page in range(1, max_pages + 1):
            self.logger.info(f"正在处理第 {page}/{max_pages} 页")
            
            # 构建URL
            search_url = self.config['search_url'].format(page=page)
            
            # 获取页面（Selenium或Requests）
            if self.use_selenium:
                html = self.fetch_page_selenium(
                    search_url,
                    wait_for_selector=self.config['selectors']['article_list']
                )
            else:
                html = self.fetch_page(search_url)
            
            if not html:
                self.logger.warning(f"第 {page} 页获取失败，跳过")
                continue
            
            # 解析搜索结果
            articles = self.parse_search_results(html)
            
            if not articles:
                self.logger.info(f"第 {page} 页没有找到文章，停止爬取")
                break
            
            self.logger.info(f"第 {page} 页找到 {len(articles)} 篇文章，开始逐篇抓取...")
            
            # 逐篇获取全文并保存
            for i, article in enumerate(articles, 1):
                total_count += 1
                self.logger.info(f"处理第 {total_count} 篇: {article['title'][:50]}...")
                
                # 获取全文
                content_data = self.parse_article_content(article['url'])
                
                result = {
                    'think_tank': self.config['name'],
                    'title': article['title'],
                    'url': article['url'],
                    'authors': content_data['authors'],
                    'publish_date': article.get('publish_date'),
                    'content_type': article.get('content_type', 'Article'),
                    'abstract': content_data['abstract'],
                    'full_text': content_data['full_text'],
                    'keywords': ['TikTok'],
                    'scraped_at': datetime.now().isoformat(),
                    'phase': self.determine_phase(article.get('publish_date')),
                    'is_paid_content': False
                }
                
                self.results.append(result)
                
                # 每爬一篇就保存一次
                self.save_results()
                
        self.logger.info(f"{self.config['name']} 爬取完成！共 {len(self.results)} 篇")

    def _scrape_brookings_algolia(self, max_pages: Optional[int] = None):
        """使用 Algolia API 爬取 Brookings (超速模式)"""
        self.logger.info("🚀 启动 Brookings Algolia API 极速模式")
        
        APP_ID = BROOKINGS_ALGOLIA['app_id']
        API_KEY = BROOKINGS_ALGOLIA['api_key']
        INDEX_NAME = BROOKINGS_ALGOLIA['index_name']
        ENDPOINT = f"https://{APP_ID}-dsn.algolia.net/1/indexes/{INDEX_NAME}/query"
        
        if max_pages is None: max_pages = 50
        
        headers = {
            'X-Algolia-API-Key': API_KEY,
            'X-Algolia-Application-Id': APP_ID,
            'Content-Type': 'application/json'
        }
        
        total_count = 0
        
        for page in range(max_pages):
            self.logger.info(f"正在获取第 {page+1}/{max_pages} 页 (API)")
            
            try:
                payload = {
                    'query': 'TikTok',
                    'page': page,
                    'hitsPerPage': 10,
                    'filters': 'post_type:article OR post_type:book OR post_type:event'
                }
                
                response = requests.post(ENDPOINT, headers=headers, json=payload, timeout=10)
                response.raise_for_status()
                data = response.json()
                hits = data.get('hits', [])
                
                if not hits:
                    self.logger.info("没有更多数据，停止")
                    break
                
                self.logger.info(f"API返回 {len(hits)} 篇文章，开始处理...")
                
                for hit in hits:
                    total_count += 1
                    title = hit.get('post_title', 'N/A')
                    url = hit.get('permalink', '')
                    self.logger.info(f"处理第 {total_count} 篇: {title[:50]}...")
                    
                    if not url: continue
                    
                    # 获取全文 (仍然需要去网页抓取因为API只有摘要)
                    # 优先使用简单requests，因为brookings文章页是静态的
                    content_data = self.parse_article_content(url)
                    
                    # 转换时间戳
                    pub_date = "Unknown"
                    if hit.get('post_date'):
                         pub_date = datetime.fromtimestamp(hit['post_date']).strftime('%Y-%m-%d')

                    result = {
                        'think_tank': "Brookings Institution",
                        'title': title,
                        'url': url,
                        'authors': hit.get('authors', []) or hit.get('experts', []),
                        'publish_date': pub_date,
                        'content_type': hit.get('post_type', 'Article'),
                        'abstract': hit.get('content', '')[:500],
                        'full_text': content_data['full_text'],
                        'keywords': ['TikTok'],
                        'scraped_at': datetime.now().isoformat(),
                        'phase': self.determine_phase(pub_date),
                        'is_paid_content': False
                    }
                    
                    self.results.append(result)
                    self.save_results()
                    
                time.sleep(1) # API 也要礼貌一点
                
            except Exception as e:
                self.logger.error(f"API请求失败: {e}")
                
        self.logger.info(f"Brookings (API) 爬取完成！共 {len(self.results)} 篇")

        
    def save_results(self):
        """保存结果"""
        output_file = Path(OUTPUT_PATHS['processed']) / f"{self.tank_id}_results.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"结果已保存到: {output_file} ({len(self.results)}篇)")
        
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
            except:
                pass
                
    def fetch_page(self, url: str) -> Optional[str]:
        """传统方式获取页面（备用）"""
        try:
            response = self.session.get(url, timeout=SCRAPER_SETTINGS['timeout'])
            response.raise_for_status()
            time.sleep(SCRAPER_SETTINGS['delay_between_requests'])
            return response.text
        except Exception as e:
            self.logger.error(f"请求失败: {e}")
            return None
