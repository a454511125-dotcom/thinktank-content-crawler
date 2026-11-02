"""
批量测试所有智库的脚本
快速检测每个智库的可访问性和技术需求
"""

import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
from datetime import datetime
import time

# 从config导入智库列表
import sys
sys.path.append('.')
from config import THINK_TANKS

def test_think_tank(tank_id, config):
    """测试单个智库的可访问性"""
    print(f"\n{'='*60}")
    print(f"测试: {config['name']}")
    print(f"{'='*60}")
    
    result = {
        'tank_id': tank_id,
        'name': config['name'],
        'test_time': datetime.now().isoformat(),
        'accessible': False,
        'status_code': None,
        'has_javascript': False,
        'has_algolia': False,
        'article_count_found': 0,
        'recommendation': '',
        'error': None
    }
    
    try:
        # 构建测试URL
        search_url = config['search_url'].format(page=1)
        print(f"URL: {search_url}")
        
        # 1. 测试可访问性
        print("1️⃣ 测试HTTP访问...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(search_url, headers=headers, timeout=15)
        result['status_code'] = response.status_code
        
        if response.status_code == 200:
            result['accessible'] = True
            print(f"   ✓ 访问成功 (200 OK)")
        else:
            print(f"   ✗ HTTP错误: {response.status_code}")
            result['error'] = f"HTTP {response.status_code}"
            return result
        
        # 2. 检查JavaScript特征
        print("2️⃣ 分析页面结构...")
        html = response.text
        
        # 检查Algolia
        if 'algolia' in html.lower():
            result['has_algolia'] = True
            print("   🔍 检测到Algolia搜索引擎")
            result['recommendation'] = 'Algolia API'
            
            # 尝试提取Algolia配置
            if 'algolia' in html.lower():
                import re
                app_id_match = re.search(r'"applicationID"\s*:\s*"([^"]+)"', html)
                api_key_match = re.search(r'"apiKey"\s*:\s*"([^"]+)"', html)
                if app_id_match and api_key_match:
                    print(f"   📋 App ID: {app_id_match.group(1)}")
                    print("   📋 检测到搜索 API 配置（不输出密钥）")
        
        # 检查其他JavaScript框架
        js_indicators = ['react', 'vue', 'angular', 'next.js']
        for indicator in js_indicators:
            if indicator in html.lower():
                result['has_javascript'] = True
                print(f"   ⚙️ 检测到{indicator.title()}框架")
                break
        
        # 3. 尝试解析文章（使用config的选择器）
        print("3️⃣ 测试CSS选择器...")
        soup = BeautifulSoup(html, 'html.parser')
        selectors = config['selectors']
        
        articles = soup.select(selectors['article_list'])
        result['article_count_found'] = len(articles)
        
        if len(articles) > 0:
            print(f"   ✓ 找到 {len(articles)} 个元素")
            result['recommendation'] = result.get('recommendation') or 'Traditional Requests'
        else:
            print(f"   ⚠️  未找到文章元素")
            if not result['has_algolia']:
                result['recommendation'] = 'Selenium (需要等待JS渲染)'
                result['has_javascript'] = True
        
        # 4. 测试标题提取
        if len(articles) > 0:
            print("4️⃣ 测试数据提取...")
            sample = articles[0]
            title_elem = sample.select_one(selectors['title'])
            if title_elem:
                title = title_elem.get_text(strip=True)
                print(f"   ✓ 示例标题: {title[:50]}...")
            else:
                print("   ⚠️  无法提取标题，选择器可能有误")
                result['recommendation'] = 'Selenium + 选择器调整'
        
    except requests.Timeout:
        result['error'] = 'Timeout'
        result['recommendation'] = 'Network issue - 重试或使用代理'
        print(f"   ✗ 超时")
    except requests.RequestException as e:
        result['error'] = str(e)
        result['recommendation'] = 'Network error'
        print(f"   ✗ 网络错误: {e}")
    except Exception as e:
        result['error'] = str(e)
        print(f"   ✗ 错误: {e}")
    
    return result

def main():
    """批量测试所有智库"""
    print("🚀 开始批量测试所有智库...")
    print(f"总数: {len(THINK_TANKS)} 个\n")
    
    results = []
    
    for tank_id, config in THINK_TANKS.items():
        result = test_think_tank(tank_id, config)
        results.append(result)
        time.sleep(2)  # 避免请求过快
    
    # 生成汇总报告
    print("\n" + "="*60)
    print("📊 测试汇总")
    print("="*60)
    
    accessible = sum(1 for r in results if r['accessible'])
    has_algolia = sum(1 for r in results if r['has_algolia'])
    needs_selenium = sum(1 for r in results if 'Selenium' in r.get('recommendation', ''))
    
    print(f"\n✅ 可访问: {accessible}/{len(results)}")
    print(f"🔍 使用Algolia: {has_algolia}")
    print(f"🌐 需要Selenium: {needs_selenium}")
    print(f"📄 可用Requests: {accessible - has_algolia - needs_selenium}")
    
    # 分类显示
    print("\n📋 详细分类:")
    print("\n🔍 Algolia API:")
    for r in results:
        if r['has_algolia']:
            print(f"   - {r['name']}")
    
    print("\n🌐 Selenium:")
    for r in results:
        if 'Selenium' in r.get('recommendation', '') and not r['has_algolia']:
            print(f"   - {r['name']}")
    
    print("\n📄 Traditional Requests:")
    for r in results:
        if r.get('recommendation') == 'Traditional Requests':
            print(f"   - {r['name']} ({r['article_count_found']} 篇)")
    
    print("\n❌ 问题智库:")
    for r in results:
        if not r['accessible']:
            print(f"   - {r['name']}: {r['error']}")
    
    # 保存详细报告
    Path('data/processed').mkdir(parents=True, exist_ok=True)
    output_file = 'data/processed/think_tank_test_report.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 详细报告已保存: {output_file}")
    print("\n✅ 测试完成！")

if __name__ == '__main__':
    main()
