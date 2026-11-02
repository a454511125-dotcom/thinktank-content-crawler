"""
TikTok智库报告采集工具 - 主程序（Selenium版）
"""

import argparse
import json
from pathlib import Path
from scraper_selenium import ThinkTankScraper
from config import THINK_TANKS, OUTPUT_PATHS


# 需要人工辅助验证的智库
MANUAL_AUTH_TANKS = ['cfr', 'piie']

def scrape_single_tank(tank_id: str, max_pages: int = None):
    """爬取单个智库"""
    if tank_id not in THINK_TANKS:
        print(f"❌ 错误: 智库 '{tank_id}' 不存在")
        print(f"可用智库: {', '.join(THINK_TANKS.keys())}")
        return
    
    print(f"🚀 开始爬取: {THINK_TANKS[tank_id]['name']}")
    
    # 自动判断是否需要人工介入
    manual = tank_id in MANUAL_AUTH_TANKS
    scraper = ThinkTankScraper(tank_id, use_selenium=True, manual_auth=manual)
    
    scraper.scrape_all(max_pages=max_pages)
    
    print(f"✅ 完成! 结果保存在: data/processed/{tank_id}_results.json")


def scrape_all_tanks(max_pages: int = None, skip_list: list = None, resume_mode: bool = False):
    """批量爬取所有智库"""
    print(f"🚀 开始批量爬取任务...")
    
    # 待处理队列
    tanks = [t for t in THINK_TANKS.keys()]
    if skip_list:
        tanks = [t for t in tanks if t not in skip_list]
        print(f"ℹ️  已跳过指定智库: {', '.join(skip_list)}")
    
    from datetime import datetime
    
    count = 0
    path_map = Path("data/processed")
    
    for tank_id in tanks:
        # 检查是否被禁用
        if THINK_TANKS[tank_id].get('disabled', False) and tank_id not in MANUAL_AUTH_TANKS:
            print(f"⚠️ 跳过 {tank_id} (配置文件中已禁用)")
            continue
            
        # 智能断点续传：检查文件是否存在且有内容
        if resume_mode:
            result_file = path_map / f"{tank_id}_results.json"
            if result_file.exists() and result_file.stat().st_size > 100:
                print(f"⏭️  智能跳过 {tank_id} (数据文件已存在)")
                continue

        count += 1
        print(f"\n{'='*60}")
        print(f"[{count}/{len(tanks)}] 正在处理: {THINK_TANKS[tank_id]['name']}")
        print(f"{'='*60}")
        
        try:
            manual = tank_id in MANUAL_AUTH_TANKS
            scraper = ThinkTankScraper(tank_id, use_selenium=True, manual_auth=manual)
            scraper.scrape_all(max_pages=max_pages)
        except Exception as e:
            print(f"❌ {tank_id} 爬取失败: {e}")
            continue
    
    print("\n✅ 批量爬取任务完成!")


def merge_results():
    """合并所有智库的结果"""
    all_results = []
    processed_dir = Path(OUTPUT_PATHS['processed'])
    
    processed_dir.mkdir(parents=True, exist_ok=True)
    for json_file in sorted(processed_dir.glob('*_results.json')):
        if json_file.name == 'all_results.json':
            continue
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list):
                print(f"跳过诊断报告（非文章列表）: {json_file.name}")
                continue
            all_results.extend(data)
    
    seen_urls = set()
    unique_results = []
    for article in all_results:
        if article['url'] not in seen_urls:
            seen_urls.add(article['url'])
            unique_results.append(article)
    all_results = unique_results

    output_file = processed_dir / 'all_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已合并 {len(all_results)} 篇文章到: {output_file}")


def list_tanks():
    """列出所有可用智库"""
    print("\n可用智库列表:")
    print("=" * 60)
    for tank_id, config in THINK_TANKS.items():
        print(f"  {tank_id:15} - {config['name']}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='TikTok智库报告采集工具 (Selenium版)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main_selenium.py --tank brookings --pages 2    # 爬取Brookings前2页
  python main_selenium.py --list                         # 列出所有智库
  python main_selenium.py --all --pages 5                # 爬取所有智库，每个5页
  python main_selenium.py --merge                        # 合并所有结果
        """
    )
    
    parser.add_argument('--tank', type=str, help='智库ID (如: brookings, csis)')
    parser.add_argument('--pages', type=int, help='最大爬取页数')
    parser.add_argument('--all', action='store_true', help='爬取所有智库')
    parser.add_argument('--skip', nargs='+', help='跳过指定智库 (如: cfr piie)')
    parser.add_argument('--resume', action='store_true', help='跳过已有数据的智库')
    parser.add_argument('--list', action='store_true', help='列出所有可用智库')
    parser.add_argument('--merge', action='store_true', help='合并所有结果至all_results.json')
    
    args = parser.parse_args()
    
    if args.list:
        list_tanks()
    elif args.merge:
        merge_results()
    elif args.all:
        scrape_all_tanks(args.pages, args.skip, args.resume)
    elif args.tank:
        scrape_single_tank(args.tank, args.pages)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
