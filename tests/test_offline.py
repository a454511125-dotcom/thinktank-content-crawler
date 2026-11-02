"""Offline regression checks. No browsers, live websites, or real corpus data."""
import contextlib
import importlib
import io
import json
import logging
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import config
import scraper
import scraper_selenium
import main_selenium


class OfflineTests(unittest.TestCase):
    def bare(self, cls, tank='csis'):
        obj = cls.__new__(cls)
        obj.tank_id = tank
        obj.config = config.THINK_TANKS[tank]
        obj.logger = logging.getLogger('offline')
        obj.results = []
        return obj

    def test_site_inventory_and_selectors(self):
        from bs4 import BeautifulSoup
        self.assertEqual(len(config.THINK_TANKS), 17)
        for site in config.THINK_TANKS.values():
            self.assertTrue(site['search_url'].format(page=1).startswith('https://'))
            for selector in site['selectors'].values():
                BeautifulSoup('<html></html>', 'html.parser').select(selector)

    def test_cookie_environment(self):
        with patch.dict(os.environ, {'CFR_COOKIE': 'offline-cfr', 'PIIE_COOKIE': 'offline-piie',
                                     'BROOKINGS_ALGOLIA_API_KEY': 'offline-key'}):
            importlib.reload(config)
            self.assertEqual(config.THINK_TANKS['cfr']['cookie'], 'offline-cfr')
            self.assertEqual(config.THINK_TANKS['piie']['cookie'], 'offline-piie')
            self.assertEqual(config.BROOKINGS_ALGOLIA['api_key'], 'offline-key')
        importlib.reload(config)

    def test_cookie_applied_to_both_http_sessions(self):
        from unittest.mock import MagicMock
        for use_cloud in (False, True):
            session = MagicMock()
            with patch.dict(scraper.THINK_TANKS['cfr'], {'cookie': 'offline-cookie'}), \
                 patch.object(scraper.ThinkTankScraper, '_setup_directories'), \
                 patch.object(scraper.ThinkTankScraper, '_setup_logging'), \
                 patch.object(scraper.requests, 'Session', return_value=session), \
                 patch.object(scraper.cloudscraper, 'create_scraper', return_value=session):
                scraper.ThinkTankScraper('cfr', use_cloudscraper=use_cloud)
                session.headers.update.assert_any_call({'Cookie': 'offline-cookie'})

    def test_phase_boundaries_for_both_backends(self):
        cases = [('2017-01-01', '观察阶段'), ('2019-12-31', '观察阶段'),
                 ('2020-01-01', '初步审查阶段'), ('2021-01-01', '政府设备禁令和数据安全审查阶段'),
                 ('2022-12-31', '政府设备禁令和数据安全审查阶段'),
                 ('2023-01-01', '全面限制和立法阶段'), ('2026-12-31', '全面限制和立法阶段'),
                 ('2027-01-01', 'Unknown'), ('bad date', 'Unknown'), (None, 'Unknown')]
        for cls in (scraper.ThinkTankScraper, scraper_selenium.ThinkTankScraper):
            obj = self.bare(cls)
            for date, expected in cases:
                with self.subTest(backend=cls.__module__, date=date):
                    self.assertEqual(obj.determine_phase(date), expected)

    def test_search_parsers(self):
        html = '<article><h3><a href="/analysis/sample">TikTok analysis</a></h3><time>May 15, 2023</time><span class="type">Report</span></article>'
        for cls in (scraper.ThinkTankScraper, scraper_selenium.ThinkTankScraper):
            obj = self.bare(cls)
            rows = obj.parse_search_results(html)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['url'], 'https://www.csis.org/analysis/sample')
            self.assertEqual(rows[0]['title'], 'TikTok analysis')

    def test_full_text_not_truncated(self):
        obj = self.bare(scraper_selenium.ThinkTankScraper)
        obj.use_selenium = True
        obj.fetch_page_selenium = lambda *a, **k: '<article>' + 'A' * 12000 + '</article>'
        self.assertEqual(len(obj.parse_article_content('https://example.org')['full_text']), 12000)

    def test_json_output_paths_are_not_directories(self):
        with contextlib.nullcontext(tempfile.mkdtemp(prefix='thinktank-tests-')) as td:
            paths = {'processed': f'{td}/processed', 'raw_html': f'{td}/raw',
                     'logs': f'{td}/logs', 'final_json': f'{td}/final/results.json'}
            obj = self.bare(scraper_selenium.ThinkTankScraper)
            with patch.dict(scraper_selenium.OUTPUT_PATHS, paths, clear=True):
                obj._setup_directories()
            self.assertTrue(Path(paths['final_json']).parent.is_dir())
            self.assertFalse(Path(paths['final_json']).exists())

    def test_merge_is_repeatable_for_both_entry_points(self):
        with contextlib.nullcontext(tempfile.mkdtemp(prefix='thinktank-tests-')) as td:
            processed = Path(td) / 'processed'
            processed.mkdir()
            row = {'url': 'https://example.org/a', 'think_tank': 'Example', 'phase': 'Unknown'}
            for name in ('csis', 'brookings'):
                (processed / f'{name}_results.json').write_text(json.dumps([row]), encoding='utf-8')
            (processed / 'algolia_test_results.json').write_text(json.dumps({'nbHits': 2}), encoding='utf-8')
            (processed / 'all_results.json').write_text(json.dumps([{'url': 'stale'}]), encoding='utf-8')
            paths = {'processed': str(processed), 'final_json': f'{td}/final/merged.json'}
            with patch.dict(main_selenium.OUTPUT_PATHS, paths, clear=True), contextlib.redirect_stdout(io.StringIO()):
                main_selenium.merge_results()
                main_selenium.merge_results()
                scraper.merge_all_results()
                scraper.merge_all_results()
            self.assertEqual(json.loads((processed / 'all_results.json').read_text(encoding='utf-8')), [row])
            self.assertEqual(json.loads(Path(paths['final_json']).read_text(encoding='utf-8')), [row])

    def test_merge_empty_fresh_project(self):
        with contextlib.nullcontext(tempfile.mkdtemp(prefix='thinktank-tests-')) as td:
            paths = {'processed': f'{td}/processed', 'final_json': f'{td}/final/merged.json'}
            with patch.dict(main_selenium.OUTPUT_PATHS, paths, clear=True), contextlib.redirect_stdout(io.StringIO()):
                scraper.merge_all_results()
                main_selenium.merge_results()
            self.assertEqual(json.loads(Path(paths['final_json']).read_text(encoding='utf-8')), [])


if __name__ == '__main__':
    unittest.main()
