"""
TikTok智库报告采集系统 - 主控制脚本
快速启动和批量处理
"""

from scraper import ThinkTankScraper, merge_all_results
from config import THINK_TANKS
import argparse
from tqdm import tqdm


def scrape_single_tank(tank_id: str, max_pages: int = None):
    """
    爬取单个智库
    
    Args:
        tank_id: 智库ID
        max_pages: 最大页数
    """
    print(f"\n🚀 开始爬取: {THINK_TANKS[tank_id]['name']}")
    
    scraper = ThinkTankScraper(tank_id)
    scraper.scrape_all(max_pages=max_pages)
    output_file = scraper.save_results()
    
    print(f"✅ {THINK_TANKS[tank_id]['name']} 完成！")
    print(f"📁 结果: {output_file}")
    
    return len(scraper.results)


def scrape_all_tanks(max_pages: int = None):
    """
    批量爬取所有智库
    
    Args:
        max_pages: 每个智库的最大页数
    """
    print("="*60)
    print("🎯 TikTok智库报告批量采集")
    print("="*60)
    
    total_articles = 0
    
    for tank_id in tqdm(THINK_TANKS.keys(), desc="总进度"):
        try:
            count = scrape_single_tank(tank_id, max_pages)
            total_articles += count
        except Exception as e:
            print(f"❌ {tank_id} 爬取失败: {e}")
            continue
            
    print("\n" + "="*60)
    print(f"✅ 全部完成！共采集 {total_articles} 篇文章")
    print("="*60)
    
    print("\n📦 正在合并所有结果...")
    merge_all_results()


def main():
    parser = argparse.ArgumentParser(description='TikTok智库报告采集工具')
    
    parser.add_argument(
        '--tank',
        type=str,
        help='指定智库ID（如 brookings, csis）。不指定则爬取全部'
    )
    
    parser.add_argument(
        '--pages',
        type=int,
        default=None,
        help='每个智库的最大页数（默认使用配置文件中的值）'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='列出所有可用的智库ID'
    )
    
    parser.add_argument(
        '--merge',
        action='store_true',
        help='仅合并已有结果，不进行爬取'
    )
    
    args = parser.parse_args()
    
    # 列出智库
    if args.list:
        print("\n可用的智库ID:")
        print("-" * 60)
        for tank_id, config in THINK_TANKS.items():
            print(f"  {tank_id:20s} - {config['name']}")
        print("-" * 60)
        return
        
    # 仅合并
    if args.merge:
        print("📦 正在合并现有结果...")
        merge_all_results()
        return
        
    # 爬取单个智库
    if args.tank:
        if args.tank not in THINK_TANKS:
            print(f"❌ 错误: 未知的智库ID '{args.tank}'")
            print(f"💡 使用 --list 查看所有可用智库")
            return
            
        scrape_single_tank(args.tank, args.pages)
        
    # 爬取所有智库
    else:
        scrape_all_tanks(args.pages)


if __name__ == '__main__':
    main()
