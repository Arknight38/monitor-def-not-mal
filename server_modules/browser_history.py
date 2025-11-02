"""
Browser History Parser
Extracts browsing history from popular browsers
"""
import os
import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional
import tempfile

class BrowserHistoryParser:
    """Parse browser history from multiple browsers"""
    
    def __init__(self):
        self.browsers = {
            'chrome': self._get_chrome_paths(),
            'firefox': self._get_firefox_paths(),
            'edge': self._get_edge_paths(),
            'opera': self._get_opera_paths(),
            'brave': self._get_brave_paths()
        }
    
    def _get_chrome_paths(self):
        """Get Chrome history database paths"""
        base_paths = [
            Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data",
            Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data" / "Default",
            Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data" / "Profile 1"
        ]
        
        paths = []
        for base in base_paths:
            if base.exists():
                history_file = base / "History"
                if history_file.exists():
                    paths.append(str(history_file))
        
        return paths
    
    def _get_firefox_paths(self):
        """Get Firefox history database paths"""
        firefox_dir = Path.home() / "AppData" / "Roaming" / "Mozilla" / "Firefox" / "Profiles"
        paths = []
        
        if firefox_dir.exists():
            for profile_dir in firefox_dir.iterdir():
                if profile_dir.is_dir():
                    places_file = profile_dir / "places.sqlite"
                    if places_file.exists():
                        paths.append(str(places_file))
        
        return paths
    
    def _get_edge_paths(self):
        """Get Edge history database paths"""
        base_paths = [
            Path.home() / "AppData" / "Local" / "Microsoft" / "Edge" / "User Data" / "Default",
            Path.home() / "AppData" / "Local" / "Microsoft" / "Edge" / "User Data" / "Profile 1"
        ]
        
        paths = []
        for base in base_paths:
            if base.exists():
                history_file = base / "History"
                if history_file.exists():
                    paths.append(str(history_file))
        
        return paths
    
    def _get_opera_paths(self):
        """Get Opera history database paths"""
        base_paths = [
            Path.home() / "AppData" / "Roaming" / "Opera Software" / "Opera Stable",
            Path.home() / "AppData" / "Roaming" / "Opera Software" / "Opera GX Stable"
        ]
        
        paths = []
        for base in base_paths:
            if base.exists():
                history_file = base / "History"
                if history_file.exists():
                    paths.append(str(history_file))
        
        return paths
    
    def _get_brave_paths(self):
        """Get Brave history database paths"""
        base_paths = [
            Path.home() / "AppData" / "Local" / "BraveSoftware" / "Brave-Browser" / "User Data" / "Default",
            Path.home() / "AppData" / "Local" / "BraveSoftware" / "Brave-Browser" / "User Data" / "Profile 1"
        ]
        
        paths = []
        for base in base_paths:
            if base.exists():
                history_file = base / "History"
                if history_file.exists():
                    paths.append(str(history_file))
        
        return paths
    
    def _parse_chrome_history(self, db_path: str, limit: int = 1000) -> List[Dict]:
        """Parse Chrome/Edge/Brave history database"""
        history = []
        temp_db = None
        
        try:
            # Copy database to temp file (browsers lock the original)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_file:
                temp_db = temp_file.name
                shutil.copy2(db_path, temp_db)
            
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            query = """
                SELECT url, title, visit_count, last_visit_time, typed_count
                FROM urls 
                WHERE last_visit_time > 0
                ORDER BY last_visit_time DESC 
                LIMIT ?
            """
            
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            
            for row in rows:
                url, title, visit_count, last_visit_time, typed_count = row
                
                # Chrome stores time as microseconds since Jan 1, 1601
                if last_visit_time:
                    # Convert Chrome timestamp to Unix timestamp
                    chrome_epoch = datetime(1601, 1, 1, tzinfo=timezone.utc)
                    visit_time = chrome_epoch.timestamp() + (last_visit_time / 1000000)
                    visit_datetime = datetime.fromtimestamp(visit_time).isoformat()
                else:
                    visit_datetime = None
                
                history.append({
                    'url': url,
                    'title': title or '',
                    'visit_count': visit_count or 0,
                    'last_visit': visit_datetime,
                    'typed_count': typed_count or 0,
                    'browser': 'chrome'
                })
            
            conn.close()
            
        except Exception as e:
            print(f"Error parsing Chrome history from {db_path}: {e}")
        finally:
            # Clean up temp file
            if temp_db and os.path.exists(temp_db):
                try:
                    os.unlink(temp_db)
                except:
                    pass
        
        return history
    
    def _parse_firefox_history(self, db_path: str, limit: int = 1000) -> List[Dict]:
        """Parse Firefox history database"""
        history = []
        temp_db = None
        
        try:
            # Copy database to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_file:
                temp_db = temp_file.name
                shutil.copy2(db_path, temp_db)
            
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            query = """
                SELECT p.url, p.title, p.visit_count, h.visit_date, p.typed
                FROM moz_places p
                LEFT JOIN moz_historyvisits h ON p.id = h.place_id
                WHERE h.visit_date IS NOT NULL
                ORDER BY h.visit_date DESC
                LIMIT ?
            """
            
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            
            for row in rows:
                url, title, visit_count, visit_date, typed = row
                
                # Firefox stores time as microseconds since Unix epoch
                if visit_date:
                    visit_time = visit_date / 1000000  # Convert to seconds
                    visit_datetime = datetime.fromtimestamp(visit_time).isoformat()
                else:
                    visit_datetime = None
                
                history.append({
                    'url': url,
                    'title': title or '',
                    'visit_count': visit_count or 0,
                    'last_visit': visit_datetime,
                    'typed_count': typed or 0,
                    'browser': 'firefox'
                })
            
            conn.close()
            
        except Exception as e:
            print(f"Error parsing Firefox history from {db_path}: {e}")
        finally:
            # Clean up temp file
            if temp_db and os.path.exists(temp_db):
                try:
                    os.unlink(temp_db)
                except:
                    pass
        
        return history
    
    def get_all_history(self, limit_per_browser: int = 500) -> Dict:
        """Get browsing history from all detected browsers"""
        all_history = []
        browser_counts = {}
        
        for browser_name, db_paths in self.browsers.items():
            browser_history = []
            
            for db_path in db_paths:
                try:
                    if browser_name == 'firefox':
                        history = self._parse_firefox_history(db_path, limit_per_browser)
                    else:
                        # Chrome, Edge, Opera, Brave use Chrome format
                        history = self._parse_chrome_history(db_path, limit_per_browser)
                    
                    # Update browser name for specific browsers
                    for entry in history:
                        if browser_name in ['edge', 'opera', 'brave']:
                            entry['browser'] = browser_name
                    
                    browser_history.extend(history)
                    
                except Exception as e:
                    print(f"Error processing {browser_name} database {db_path}: {e}")
            
            if browser_history:
                browser_counts[browser_name] = len(browser_history)
                all_history.extend(browser_history)
        
        # Sort all history by last visit time
        all_history.sort(key=lambda x: x['last_visit'] or '', reverse=True)
        
        return {
            'success': True,
            'history': all_history,
            'total_entries': len(all_history),
            'browser_counts': browser_counts,
            'browsers_detected': list(browser_counts.keys())
        }
    
    def get_browser_history(self, browser_name: str, limit: int = 1000) -> Dict:
        """Get history from a specific browser"""
        if browser_name not in self.browsers:
            return {
                'success': False,
                'error': f'Browser {browser_name} not supported'
            }
        
        db_paths = self.browsers[browser_name]
        if not db_paths:
            return {
                'success': False,
                'error': f'No {browser_name} history databases found'
            }
        
        history = []
        for db_path in db_paths:
            try:
                if browser_name == 'firefox':
                    browser_history = self._parse_firefox_history(db_path, limit)
                else:
                    browser_history = self._parse_chrome_history(db_path, limit)
                    
                history.extend(browser_history)
                
            except Exception as e:
                print(f"Error processing {browser_name} database {db_path}: {e}")
        
        # Sort by last visit time
        history.sort(key=lambda x: x['last_visit'] or '', reverse=True)
        
        return {
            'success': True,
            'browser': browser_name,
            'history': history,
            'total_entries': len(history)
        }
    
    def search_history(self, query: str, limit: int = 100) -> Dict:
        """Search browser history for specific terms"""
        all_history_result = self.get_all_history(limit_per_browser=2000)
        
        if not all_history_result['success']:
            return all_history_result
        
        query_lower = query.lower()
        matching_entries = []
        
        for entry in all_history_result['history']:
            # Search in URL and title
            if (query_lower in entry['url'].lower() or 
                query_lower in entry['title'].lower()):
                matching_entries.append(entry)
            
            if len(matching_entries) >= limit:
                break
        
        return {
            'success': True,
            'query': query,
            'results': matching_entries,
            'total_matches': len(matching_entries)
        }
    
    def get_top_sites(self, limit: int = 50) -> Dict:
        """Get most visited sites"""
        all_history_result = self.get_all_history(limit_per_browser=5000)
        
        if not all_history_result['success']:
            return all_history_result
        
        # Group by domain and sum visit counts
        domain_visits = {}
        
        for entry in all_history_result['history']:
            try:
                from urllib.parse import urlparse
                domain = urlparse(entry['url']).netloc
                if domain:
                    if domain not in domain_visits:
                        domain_visits[domain] = {
                            'domain': domain,
                            'visit_count': 0,
                            'last_visit': entry['last_visit'],
                            'browsers': set()
                        }
                    
                    domain_visits[domain]['visit_count'] += entry['visit_count']
                    domain_visits[domain]['browsers'].add(entry['browser'])
                    
                    # Keep the most recent visit time
                    if (entry['last_visit'] and 
                        (not domain_visits[domain]['last_visit'] or 
                         entry['last_visit'] > domain_visits[domain]['last_visit'])):
                        domain_visits[domain]['last_visit'] = entry['last_visit']
                        
            except Exception:
                continue
        
        # Convert to list and sort by visit count
        top_sites = list(domain_visits.values())
        for site in top_sites:
            site['browsers'] = list(site['browsers'])
        
        top_sites.sort(key=lambda x: x['visit_count'], reverse=True)
        
        return {
            'success': True,
            'top_sites': top_sites[:limit],
            'total_domains': len(top_sites)
        }

# Global parser instance
browser_parser = BrowserHistoryParser()