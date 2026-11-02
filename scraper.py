"""
TikTok智库报告采集器 - 核心爬虫模块
方案B：半自动化工具
优化版：使用cloudscraper绕过反爬虫
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

try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False
    print("⚠️ cloudscraper未安装，某些网站可能会被拦截。运行: pip install cloudscraper")

from config import THINK_TANKS, TIME_PHASES, SCRAPER_SETTINGS, OUTPUT_PATHS


class ThinkTankScraper:
    """智库报告采集器基类"""
    
    def __init__(self, think_tank_id: str, use_cloudscraper: bool = True):
        """
        初始化爬虫
        
        Args:
            think_tank_id: 智库ID (如 'brookings', 'csis')
            use_cloudscraper: 是否使用cloudscraper (推荐开启)
        """
        self.tank_id = think_tank_id
        self.config = THINK_TANKS[think_tank_id]
        
        # 选择会话类型
        if use_cloudscraper and CLOUDSCRAPER_AVAILABLE:
            self.session = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'mobile': False
                }
            )
            self.logger_prefix = f"[CloudScraper] "
        else:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': SCRAPER_SETTINGS['user_agent'],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
            
                
            self.logger_prefix = f"[Requests] "
        
        if self.config.get('cookie'):
            self.session.headers.update({'Cookie': self.config['cookie']})

        # 创建输出目录
        self._setup_directories()
        
        # 设置日志
        self._setup_logging()
        
        self.results = []
        
    def _setup_directories(self):
        """创建必要的目录结构"""
        for path in OUTPUT_PATHS.values():
            if path.endswith('.json'):
                path = os.path.dirname(path)
            Path(path).mkdir(parents=True, exist_ok=True)
            
    def _setup_logging(self):
        """配置日志系统"""
        log_file = f"{OUTPUT_PATHS['logs']}/{self.tank_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.tank_id)
        
    def fetch_page(self, url: str) -> Optional[str]:
        """
        获取页面HTML内容
        
        Args:
            url: 目标URL
            
        Returns:
            HTML内容或None（如果失败）
        """
        for attempt in range(SCRAPER_SETTINGS['max_retries']):
            try:
                self.logger.info(f"{self.logger_prefix}正在获取: {url} (尝试 {attempt + 1}/{SCRAPER_SETTINGS['max_retries']})")
                
                response = self.session.get(
                    url,
                    timeout=SCRAPER_SETTINGS['timeout']
                )
                response.raise_for_status()
                
                # 调试模式：保存HTML
                if SCRAPER_SETTINGS.get('debug_mode', False):
                    debug_dir = Path(OUTPUT_PATHS['raw_html']) / self.tank_id
                    debug_dir.mkdir(parents=True, exist_ok=True)
                    
                    # 生成文件名（使用时间戳）
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{self.tank_id}_{timestamp}_{attempt}.html"
                    filepath = debug_dir / filename
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    self.logger.info(f"💾 调试: HTML已保存到 {filepath}")
                
                # 延迟，避免被封
                time.sleep(SCRAPER_SETTINGS['delay_between_requests'])
                
                return response.text
                
            except requests.RequestException as e:
                self.logger.warning(f"{self.logger_prefix}请求失败: {e}")
                if attempt < SCRAPER_SETTINGS['max_retries'] - 1:
                    time.sleep(5)  # 失败后等待更长时间
                else:
                    self.logger.error(f"{self.logger_prefix}达到最大重试次数，放弃: {url}")
                    return None
                    
    def parse_search_results(self, html: str) -> List[Dict]:
        """
        解析搜索结果页面
        
        Args:
            html: 页面HTML
            
        Returns:
            文章列表
        """
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        
        selectors = self.config['selectors']
        article_elements = soup.select(selectors['article_list'])
        
        self.logger.info(f"找到 {len(article_elements)} 篇文章")
        
        for elem in article_elements:
            try:
                # 提取标题和URL
                title_elem = elem.select_one(selectors['title'])
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                url_elem = elem.select_one(selectors['url'])
                url = url_elem.get('href') if url_elem else None
                
                if url and not url.startswith('http'):
                    url = urljoin(self.config['base_url'], url)
                
                # 提取日期
                date_elem = elem.select_one(selectors['date'])
                date_str = date_elem.get_text(strip=True) if date_elem else None
                
                # 提取类型
                type_elem = elem.select_one(selectors['type'])
                content_type = type_elem.get_text(strip=True) if type_elem else "Article"
                
                article = {
                    'title': title,
                    'url': url,
                    'publish_date': date_str,
                    'content_type': content_type
                }
                
                articles.append(article)
                
            except Exception as e:
                self.logger.warning(f"解析文章时出错: {e}")
                continue
                
        return articles
        
    def parse_article_content(self, url: str) -> Dict:
        """
        获取文章全文内容
        
        Args:
            url: 文章URL
            
        Returns:
            包含全文的字典
        """
        html = self.fetch_page(url)
        if not html:
            return {"full_text": "", "abstract": "", "authors": []}
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # 通用策略：寻找主要内容区域
        content_selectors = [
            'article',
            'div.article-content',
            'div.entry-content',
            'div.post-content',
            'div.content',
            'main'
        ]
        
        full_text = ""
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # 移除script和style标签
                for tag in content_elem(['script', 'style', 'nav', 'aside', 'footer']):
                    tag.decompose()
                full_text = content_elem.get_text(separator='\n', strip=True)
                break
                
        # 提取作者（多种可能的位置）
        authors = []
        author_selectors = [
            'span.author',
            'a.author-name',
            'div.author',
            'meta[name="author"]'
        ]
        
        for selector in author_selectors:
            if selector.startswith('meta'):
                meta = soup.select_one(selector)
                if meta:
                    authors.append(meta.get('content', ''))
            else:
                author_elems = soup.select(selector)
                authors.extend([elem.get_text(strip=True) for elem in author_elems])
                
        # 提取摘要
        abstract = ""
        abstract_elem = soup.select_one('meta[name="description"]')
        if abstract_elem:
            abstract = abstract_elem.get('content', '')
            
        return {
            'full_text': full_text,
            'abstract': abstract,
            'authors': list(set(authors))  # 去重
        }
        
    def determine_phase(self, date_str: str) -> str:
        """
        根据日期判断所属阶段
        
        Args:
            date_str: 日期字符串
            
        Returns:
            阶段名称
        """
        try:
            # 尝试多种日期格式
            date_formats = [
                '%Y-%m-%d',
                '%B %d, %Y',
                '%b %d, %Y',
                '%m/%d/%Y',
                '%Y/%m/%d'
            ]
            
            article_date = None
            for fmt in date_formats:
                try:
                    article_date = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
                    
            if not article_date:
                return "Unknown"
                
            # 判断阶段
            for phase_id, phase_info in TIME_PHASES.items():
                start = datetime.strptime(phase_info['start'], '%Y-%m-%d')
                end = datetime.strptime(phase_info['end'], '%Y-%m-%d')
                
                if start <= article_date <= end:
                    return phase_info['name']
                    
            return "Unknown"
            
        except Exception as e:
            self.logger.warning(f"日期解析失败: {date_str} - {e}")
            return "Unknown"
            
    def scrape_all(self, max_pages: Optional[int] = None):
        """
        爬取所有页面
        
        Args:
            max_pages: 最大页数（None则使用配置中的值）
        """
        if max_pages is None:
            max_pages = self.config.get('max_pages', 10)
            
        self.logger.info(f"开始爬取 {self.config['name']}")
        
        all_articles = []
        
        for page in range(1, max_pages + 1):
            self.logger.info(f"正在处理第 {page}/{max_pages} 页")
            
            # 构建搜索URL
            search_url = self.config['search_url'].format(page=page)
            
            # 获取搜索结果页
            html = self.fetch_page(search_url)
            if not html:
                self.logger.warning(f"第 {page} 页获取失败，跳过")
                continue
                
            # 解析搜索结果
            articles = self.parse_search_results(html)
            
            if not articles:
                self.logger.info(f"第 {page} 页没有找到文章，停止爬取")
                break
                
            all_articles.extend(articles)
            
        self.logger.info(f"共找到 {len(all_articles)} 篇文章")
        
        # 获取每篇文章的全文
        self.logger.info("开始获取文章全文...")
        
        for i, article in enumerate(all_articles, 1):
            self.logger.info(f"正在处理 {i}/{len(all_articles)}: {article['title'][:50]}...")
            
            # RAND付费内容特殊处理
            is_paid = self.config.get('paid_content', False)
            
            content_data = self.parse_article_content(article['url'])
            
            # 合并数据
            full_article = {
                'think_tank': self.config['name'],
                'title': article['title'],
                'url': article['url'],
                'authors': content_data['authors'],
                'publish_date': article['publish_date'],
                'content_type': article['content_type'],
                'abstract': content_data['abstract'],
                'full_text': content_data['full_text'],
                'keywords': ['TikTok'],  # 基础关键词
                'scraped_at': datetime.now().isoformat(),
                'phase': self.determine_phase(article['publish_date']) if article['publish_date'] else "Unknown",
                'is_paid_content': is_paid and len(content_data['full_text']) < 200  # 简单判断
            }
            
            self.results.append(full_article)
            
        self.logger.info(f"{self.config['name']} 爬取完成！共 {len(self.results)} 篇")
        
    def save_results(self):
        """保存结果到JSON文件"""
        # 分离RAND付费和普通内容
        if self.tank_id == 'rand':
            paid = [r for r in self.results if r.get('is_paid_content', False)]
            regular = [r for r in self.results if not r.get('is_paid_content', False)]
            
            # 保存付费内容的标题
            if paid:
                paid_output = OUTPUT_PATHS['rand_paid']
                with open(paid_output, 'w', encoding='utf-8') as f:
                    json.dump(paid, f, ensure_ascii=False, indent=2)
                self.logger.info(f"RAND付费报告已保存到: {paid_output} ({len(paid)}篇)")
                
            # 保存普通内容
            results_to_save = regular
        else:
            results_to_save = self.results
            
        # 保存到智库专属文件
        output_file = f"{OUTPUT_PATHS['processed']}/{self.tank_id}_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_to_save, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"结果已保存到: {output_file} ({len(results_to_save)}篇)")
        
        return output_file


def merge_all_results():
    """合并所有智库的结果到单一JSON文件"""
    all_results = []
    processed_dir = OUTPUT_PATHS['processed']
    
    for json_file in sorted(Path(processed_dir).glob('*_results.json')):
        if json_file.name == 'all_results.json':
            continue
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list):
                print(f"跳过诊断报告（非文章列表）: {json_file.name}")
                continue
            all_results.extend(data)
            
    # 去重（基于URL）
    seen_urls = set()
    unique_results = []
    
    for article in all_results:
        if article['url'] not in seen_urls:
            seen_urls.add(article['url'])
            unique_results.append(article)
            
    # 保存最终结果
    final_output = OUTPUT_PATHS['final_json']
    Path(final_output).parent.mkdir(parents=True, exist_ok=True)
    with open(final_output, 'w', encoding='utf-8') as f:
        json.dump(unique_results, f, ensure_ascii=False, indent=2)
        
    print(f"✅ 合并完成！共 {len(unique_results)} 篇文章")
    print(f"📁 保存位置: {final_output}")
    
    # 打印统计信息
    print("\n📊 各智库统计:")
    stats = {}
    for article in unique_results:
        tank = article['think_tank']
        stats[tank] = stats.get(tank, 0) + 1
        
    for tank, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {tank}: {count}篇")
        
    print(f"\n📅 各阶段统计:")
    phase_stats = {}
    for article in unique_results:
        phase = article['phase']
        phase_stats[phase] = phase_stats.get(phase, 0) + 1
        
    for phase, count in sorted(phase_stats.items()):
        print(f"  {phase}: {count}篇")


if __name__ == '__main__':
    # 示例：爬取单个智库
    scraper = ThinkTankScraper('brookings')
    scraper.scrape_all(max_pages=5)  # 测试：只爬5页
    scraper.save_results()
