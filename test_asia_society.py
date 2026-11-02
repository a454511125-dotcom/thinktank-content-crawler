"""
测试Asia Society (Selenium + Google Custom Search)
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time

def test_asia_society():
    print("🚀 测试 Asia Society (Selenium)...")
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    url = "https://asiasociety.org/search/google?keys=TikTok"
    print(f"URL: {url}")
    
    try:
        driver.get(url)
        print("页面已加载，等待内容渲染...")
        time.sleep(5) # 等待Google脚本
        
        # 尝试查找Google搜索结果
        # Google搜索结果通常在 .gsc-result 类中
        results = driver.find_elements(By.CSS_SELECTOR, "div.gsc-webResult.gsc-result")
        
        print(f"找到 {len(results)} 个结果")
        
        if len(results) > 0:
            first = results[0]
            print(f"示例文本: {first.text[:100]}...")
            
            # 尝试找标题链接
            try:
                title_link = first.find_element(By.CSS_SELECTOR, "a.gs-title")
                print(f"标题: {title_link.text}")
                print(f"链接: {title_link.get_attribute('href')}")
            except:
                print("未找到标题链接")
                
        else:
            print("未找到结果，可能是在iframe中？")
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            print(f"页面包含 {len(iframes)} 个iframes")
            
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    test_asia_society()
