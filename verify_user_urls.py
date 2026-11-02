"""
验证用户提供的正确URL
"""
import requests
import cloudscraper
from bs4 import BeautifulSoup
import time

NEW_URLS = {
    "cfr": "https://www.cfr.org/search?q=tiktok",
    "piie": "https://www.piie.com/search?search_api_fulltext=tiktok",
    "asia_society": "https://asiasociety.org/search/google?keys=tiktok"
}

def verify_url(name, url):
    print(f"\n🔍 测试 {name}...")
    print(f"URL: {url}")
    
    # 1. 尝试Cloudscraper (模拟浏览器)
    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url, timeout=15)
        print(f"Cloudscraper状态: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ 访问成功!")
            # 检查是否有内容
            if len(response.text) > 1000:
                print(f"✅ 内容获取正常 (长度: {len(response.text)})")
            else:
                print(f"⚠️ 内容可能为空")
            return True, response.text
        else:
            print(f"❌ 访问失败: {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False, None

def analyze_asia_society(html):
    """Asia Society使用google搜索，结构可能特殊"""
    if not html: return
    soup = BeautifulSoup(html, 'html.parser')
    # 检查是否是Google自定义搜索(GCSE)
    if "gcse" in html.lower() or "google-search" in html.lower():
        print("⚠️ 检测到 Google Custom Search Engine (GCSE)")
        print("这可能需要Selenium才能加载结果，普通requests可能拿不到")

def main():
    print("🚀 开始验证新URL...")
    
    success_count = 0
    
    for name, url in NEW_URLS.items():
        success, html = verify_url(name, url)
        if success:
            success_count += 1
            if name == "asia_society":
                analyze_asia_society(html)
        time.sleep(2)
        
    print(f"\n📊 结果: {success_count}/3 可用")

if __name__ == "__main__":
    main()
