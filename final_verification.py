"""
最终验证脚本
测试 CFR、PIIE（使用Cookie）和 Asia Society（使用Selenium）
"""
import requests
import json
from config import THINK_TANKS, SCRAPER_SETTINGS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

def test_config_tank(tank_id):
    config = THINK_TANKS[tank_id]
    name = config['name']
    print(f"\n🔍 测试 {name} ({tank_id})...")
    
    if config.get('cookie'):
        print(f"   ℹ️  使用Cookie进行测试")
        
    url = config['search_url'].format(page=0 if tank_id != 'piie' else 0) # PIIE page 0
    if tank_id == 'aei': url = config['search_url'].format(page=1)
    
    print(f"   URL: {url}")

    try:
        # PIIE/CFR 使用 Requests + Cookie
        if tank_id in ['cfr', 'piie']:
            headers = {
                'User-Agent': SCRAPER_SETTINGS['user_agent'],
                'Cookie': config['cookie']
            }
            response = requests.get(url, headers=headers, timeout=15)
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ 成功！内容长度: {len(response.text)}")
                return True
            else:
                print(f"   ❌ 失败: {response.status_code}")
                return False
                
        # Asia Society 使用 Selenium
        elif tank_id == 'asia_society':
            print("   🤖 启动Selenium...")
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            try:
                driver.get(url)
                time.sleep(5)
                title = driver.title
                print(f"   页面标题: {title}")
                
                # 检查特定元素
                if "Google" in driver.page_source or "gsc-result" in driver.page_source:
                     print(f"   ✅ 成功检测到搜索结果框架")
                     return True
                else:
                     print(f"   ⚠️  未检测到搜索结果，可能需要调整")
                     return False
            finally:
                driver.quit()
                
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False

def main():
    print("🚀 开始最终验证...")
    tanks_to_test = ['cfr', 'piie', 'asia_society']
    
    results = {}
    for tank in tanks_to_test:
        results[tank] = test_config_tank(tank)
        time.sleep(2)
        
    print("\n📊 验证结果:")
    for tank, success in results.items():
        print(f"  {tank}: {'✅ 通过' if success else '❌ 失败'}")

if __name__ == "__main__":
    main()
