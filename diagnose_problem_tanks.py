"""
诊断并修复有问题的智库
对6个被阻止的智库进行深度测试
"""

from pathlib import Path
import requests
import cloudscraper
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time

# 有问题的智库URL
PROBLEM_TANKS = {
    "cfr": {
        "name": "Council on Foreign Relations",
        "url": "https://www.cfr.org/search?keyword=TikTok&page=0",
        "error": "HTTP 403"
    },
    "piie": {
        "name": "Peterson Institute",
        "url": "https://www.piie.com/search?keywords=TikTok&page=0",
        "error": "HTTP 403"
    },
    "asia_society": {
        "name": "Asia Society",
        "url": "https://asiasociety.org/search/site/TikTok?page=0",
        "error": "HTTP 403"
    },
    "hoover": {
        "name": "Hoover Institution",
        "url": "https://www.hoover.org/search/site/TikTok?page=0",
        "error": "HTTP 404"
    },
    "aei": {
        "name": "American Enterprise Institute",
        "url": "https://www.aei.org/?s=TikTok&paged=1",
        "error": "HTTP 500"
    }
}

def test_with_multiple_methods(tank_id, info):
    """使用多种方法测试"""
    url = info['url']
    results = {
        "tank_id": tank_id,
        "name": info['name'],
        "original_error": info['error'],
        "url": url,
        "tests": []
    }
    
    print(f"\n{'='*60}")
    print(f"测试: {info['name']}")
    print(f"URL: {url}")
    print(f"原始错误: {info['error']}")
    print(f"{'='*60}\n")
    
    # 方法1: 基础requests
    print("1️⃣ 测试基础requests...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        response = requests.get(url, headers=headers, timeout=15)
        results['tests'].append({
            "method": "Basic Requests",
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "content_length": len(response.text)
        })
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✓ 成功！内容长度: {len(response.text)}")
    except Exception as e:
        results['tests'].append({
            "method": "Basic Requests",
            "status_code": None,
            "success": False,
            "error": str(e)
        })
        print(f"   ✗ 失败: {e}")
    
    time.sleep(2)
    
    # 方法2: Cloudscraper
    print("\n2️⃣ 测试Cloudscraper...")
    try:
        scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
        )
        response = scraper.get(url, timeout=15)
        results['tests'].append({
            "method": "Cloudscraper",
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "content_length": len(response.text)
        })
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✓ 成功！内容长度: {len(response.text)}")
            # 快速检查是否有搜索结果
            soup = BeautifulSoup(response.text, 'html.parser')
            body_text = soup.get_text()[:500]
            print(f"   页面预览: {body_text[:150]}...")
    except Exception as e:
        results['tests'].append({
            "method": "Cloudscraper",
            "status_code": None,
            "success": False,
            "error": str(e)
        })
        print(f"   ✗ 失败: {e}")
    
    time.sleep(2)
    
    # 方法3: 尝试不同的User-Agent
    print("\n3️⃣ 测试移动端User-Agent...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        response = requests.get(url, headers=headers, timeout=15)
        results['tests'].append({
            "method": "Mobile User-Agent",
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "content_length": len(response.text)
        })
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✓ 成功！")
    except Exception as e:
        results['tests'].append({
            "method": "Mobile User-Agent",
            "status_code": None,
            "success": False,
            "error": str(e)
        })
        print(f"   ✗ 失败: {e}")
    
    time.sleep(2)
    
    # 方法4: 测试基础URL（不带搜索）
    print("\n4️⃣ 测试基础域名...")
    base_url = '/'.join(url.split('/')[:3])  # 提取 https://domain.com
    try:
        response = requests.get(base_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        results['tests'].append({
            "method": "Base Domain",
            "url": base_url,
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "content_length": len(response.text)
        })
        print(f"   基础URL: {base_url}")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✓ 基础站点可访问")
    except Exception as e:
        results['tests'].append({
            "method": "Base Domain",
            "url": base_url,
            "status_code": None,
            "success": False,
            "error": str(e)
        })
        print(f"   ✗ 失败: {e}")
    
    return results

def test_alternate_urls():
    """为404/500错误测试备用URL"""
    print("\n" + "="*60)
    print("📍 测试备用URL")
    print("="*60)
    
    alternate_tests = []
    
    # Hoover - 尝试不同的搜索URL格式
    print("\n🔍 Hoover Institution - 尝试备用URL...")
    hoover_urls = [
        "https://www.hoover.org/search/site/TikTok?page=0",  # 原URL
        "https://www.hoover.org/search?q=TikTok",  # 简化版
        "https://www.hoover.org/search/TikTok",  # 更简化
        "https://www.hoover.org/?s=TikTok",  # WordPress格式
    ]
    
    for test_url in hoover_urls:
        try:
            print(f"   测试: {test_url}")
            response = cloudscraper.create_scraper().get(test_url, timeout=15)
            print(f"   → 状态: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✓ 找到可用URL!")
                alternate_tests.append({
                    "tank": "hoover",
                    "url": test_url,
                    "status": response.status_code,
                    "works": True
                })
                break
            time.sleep(1)
        except Exception as e:
            print(f"   ✗ {e}")
            continue
    
    # AEI  - 尝试不同格式
    print("\n🔍 AEI - 尝试备用URL...")
    aei_urls = [
        "https://www.aei.org/?s=TikTok&paged=1",  # 原URL
        "https://www.aei.org/search/?q=TikTok",  # 备用1
        "https://www.aei.org/?s=TikTok",  # 简化版
    ]
    
    for test_url in aei_urls:
        try:
            print(f"   测试: {test_url}")
            response = cloudscraper.create_scraper().get(test_url, timeout=15)
            print(f"   → 状态: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✓ 找到可用URL!")
                alternate_tests.append({
                    "tank": "aei",
                    "url": test_url,
                    "status": response.status_code,
                    "works": True
                })
                break
            time.sleep(1)
        except Exception as e:
            print(f"   ✗ {e}")
            continue
    
    return alternate_tests

def main():
    """主测试函数"""
    print("🔧 开始诊断有问题的智库...")
    print(f"测试数量: {len(PROBLEM_TANKS)}\n")
    
    all_results = []
    
    for tank_id, info in PROBLEM_TANKS.items():
        result = test_with_multiple_methods(tank_id, info)
        all_results.append(result)
        time.sleep(3)
    
    # 测试备用URL
    alternate_results = test_alternate_urls()
    
    # 生成报告
    print("\n" + "="*60)
    print("📊 诊断总结")
    print("="*60)
    
    fixed = 0
    for result in all_results:
        print(f"\n{result['name']}:")
        print(f"  原始错误: {result['original_error']}")
        
        successful_methods = [t for t in result['tests'] if t.get('success')]
        if successful_methods:
            print(f"  ✅ 可修复! 成功方法:")
            for method in successful_methods:
                print(f"     - {method['method']} (状态: {method['status_code']})")
            fixed += 1
        else:
            print(f"  ❌ 仍然无法访问")
            for test in result['tests']:
                print(f"     - {test['method']}: {test.get('status_code', 'Error')}")
    
    print(f"\n✅ 可修复: {fixed}/{len(PROBLEM_TANKS)}")
    
    # 备用URL总结
    if alternate_results:
        print("\n📍 找到的备用URL:")
        for alt in alternate_results:
            if alt['works']:
                print(f"   {alt['tank']}: {alt['url']}")
    
    # 保存详细诊断报告
    output = {
        "test_time": datetime.now().isoformat(),
        "results": all_results,
        "alternate_urls": alternate_results,
        "summary": {
            "total": len(PROBLEM_TANKS),
            "fixed": fixed,
            "still_blocked": len(PROBLEM_TANKS) - fixed
        }
    }
    
    Path('data/processed').mkdir(parents=True, exist_ok=True)
    with open('data/processed/problem_tanks_diagnosis.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 详细报告已保存: data/processed/problem_tanks_diagnosis.json")
    print("\n✅ 诊断完成！")

if __name__ == '__main__':
    main()
