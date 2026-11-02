"""
Brookings Algolia API 验证测试脚本 - 直接HTTP请求版本
使用requests直接调用Algolia REST API
"""

from pathlib import Path
from config import BROOKINGS_ALGOLIA
import requests
import json
from datetime import datetime

# Brookings的Algolia凭据（从HTML中提取）
APP_ID = BROOKINGS_ALGOLIA['app_id']
API_KEY = BROOKINGS_ALGOLIA['api_key']
INDEX_NAME = BROOKINGS_ALGOLIA['index_name']

def test_algolia_api():
    """测试Algolia API连接和数据获取"""
    if not API_KEY:
        print('请先设置 BROOKINGS_ALGOLIA_API_KEY 环境变量。')
        return False
    Path('data/processed').mkdir(parents=True, exist_ok=True)
    print("🔍 开始测试Brookings Algolia API (HTTP请求版本)...")
    print(f"App ID: {APP_ID}")
    print(f"Index: {INDEX_NAME}\n")
    
    try:
        # 1. 构建请求
        print("1️⃣ 构建Algolia搜索请求...")
        url = f"https://{APP_ID}-dsn.algolia.net/1/indexes/{INDEX_NAME}/query"
        
        headers = {
            'X-Algolia-API-Key': API_KEY,
            'X-Algolia-Application-Id': APP_ID,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'query': 'TikTok',
            'page': 0,
            'hitsPerPage': 10,
            'filters': 'post_type:article OR post_type:book OR post_type:event'
        }
        
        print(f"   URL: {url}")
        print(f"   Query: {payload['query']}\n")
        
        # 2. 执行搜索
        print("2️⃣ 发送搜索请求...")
        start_time = datetime.now()
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        data = response.json()
        
        print(f"   ✓ 搜索完成，耗时: {duration:.2f}秒")
        print(f"   ✓ HTTP状态: {response.status_code}")
        print(f"   ✓ 找到 {data.get('nbHits', 0)} 个结果\n")
        
        # 3. 分析结果
        print("3️⃣ 分析前3条结果:")
        print("=" * 80)
        
        articles = []
        hits = data.get('hits', [])
        
        if not hits:
            print("   ⚠️  没有找到匹配的文章")
            return False
        
        for i, hit in enumerate(hits[:3], 1):
            article = {
                'title': hit.get('post_title', 'N/A'),
                'url': hit.get('permalink', 'N/A'),
                'date': hit.get('post_date', 'N/A'),
                'type': hit.get('post_type', 'N/A'),
                'authors': hit.get('taxonomies', {}).get('experts', []) if isinstance(hit.get('taxonomies'), dict) else [],
                'excerpt': hit.get('content', '')[:200]
            }
            articles.append(article)
            
            print(f"\n📄 文章 {i}:")
            print(f"   标题: {article['title']}")
            print(f"   URL: {article['url']}")
            print(f"   日期: {article['date']}")
            print(f"   类型: {article['type']}")
            print(f"   作者: {', '.join(article['authors']) if article['authors'] else 'N/A'}")
            print(f"   摘要: {article['excerpt']}...")
        
        print("\n" + "=" * 80)
        
        # 4. 保存测试结果
        print("\n4️⃣ 保存测试结果...")
        output = {
            'test_time': datetime.now().isoformat(),
            'query': 'T ikTok',
            'total_results': data.get('nbHits', 0),
            'test_duration_seconds': duration,
            'sample_articles': articles,
            'raw_response_keys': list(data.keys())
        }
        
        with open('data/processed/algolia_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print("   ✓ 结果已保存到: data/processed/algolia_test_results.json\n")
        
        # 5. 性能对比
        print("📊 性能对比:")
        print(f"   Algolia API:  {duration:.2f}秒")
        print(f"   Selenium预估: ~20秒")
        if duration > 0:
            print(f"   **速度提升: {20/duration:.1f}x** 🚀\n")
        
        # 6. 成功总结
        print("✅ Algolia API验证成功!")
        print(f"   - 可获取完整数据: {len(hits)} 篇文章")
        print(f"   - 响应速度极快: <{duration:.2f}秒")
        print(f"   - 数据结构清晰")
        print(f"   - **建议：立即迁移到API方案** ⭐\n")
        
        return True
        
    except requests.RequestException as e:
        print(f"\n❌ HTTP请求失败: {e}")
        print(f"   错误类型: {type(e).__name__}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   响应状态: {e.response.status_code}")
            print(f"   响应内容: {e.response.text[:500]}")
        return False
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        print(f"   错误类型: {type(e).__name__}")
        import traceback
        print(f"\n详细错误:\n{traceback.format_exc()}")
        return False

if __name__ == '__main__':
    success = test_algolia_api()
    exit(0 if success else 1)
