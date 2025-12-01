"""
Proxy Manager
Handles proxy rotation, validation, and health checking
"""

import random
import requests
from typing import List, Optional, Dict
import threading
import time

class ProxyManager:
    def __init__(self, proxy_file: str = None, proxy_list: List[str] = None):
        """
        Initialize proxy manager
        
        Args:
            proxy_file: Path to file containing proxies (one per line)
            proxy_list: List of proxy strings
        """
        self.proxies: List[Dict[str, str]] = []
        self.current_index = 0
        self.failed_proxies = set()
        self.lock = threading.Lock()
        
        if proxy_file:
            self.load_from_file(proxy_file)
        elif proxy_list:
            self.load_from_list(proxy_list)
    
    def load_from_file(self, filepath: str):
        """Load proxies from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = []
                for line in f:
                    line = line.strip()
                    # Skip empty lines, comments, and lines with [OK] marker
                    if not line or line.startswith('#'):
                        continue
                    # Remove [OK] marker if present
                    if line.startswith('[OK]'):
                        line = line[4:].strip()
                    elif line.startswith('     '):
                        line = line.strip()
                    # Only add valid proxy format lines (ip:port)
                    if ':' in line and not line.startswith('Invalid'):
                        lines.append(line)
                
                self.load_from_list(lines)
            print(f"[OK] Loaded {len(self.proxies)} proxies from {filepath}")
        except FileNotFoundError:
            print(f"[WARNING] Proxy file not found: {filepath}")
        except Exception as e:
            print(f"[ERROR] Error loading proxies: {e}")
    
    def load_from_list(self, proxy_list: List[str]):
        """
        Load proxies from list
        Format: ip:port or ip:port:username:password or http://ip:port
        """
        for proxy_str in proxy_list:
            proxy_dict = self._parse_proxy(proxy_str)
            if proxy_dict:
                self.proxies.append(proxy_dict)
    
    def _parse_proxy(self, proxy_str: str) -> Optional[Dict[str, str]]:
        """Parse proxy string into dict format"""
        try:
            # Remove protocol if present
            proxy_str = proxy_str.replace('http://', '').replace('https://', '').replace('socks5://', '')
            
            parts = proxy_str.split(':')
            
            if len(parts) == 2:
                # ip:port
                ip, port = parts
                return {
                    'http': f'http://{ip}:{port}',
                    'https': f'http://{ip}:{port}'
                }
            elif len(parts) == 4:
                # ip:port:username:password
                ip, port, username, password = parts
                return {
                    'http': f'http://{username}:{password}@{ip}:{port}',
                    'https': f'http://{username}:{password}@{ip}:{port}'
                }
            else:
                print(f"[WARNING] Invalid proxy format: {proxy_str}")
                return None
        except Exception as e:
            print(f"[ERROR] Error parsing proxy {proxy_str}: {e}")
            return None
    
    def get_proxy(self, strategy: str = 'random') -> Optional[Dict[str, str]]:
        """
        Get next proxy based on strategy
        
        Args:
            strategy: 'random' or 'round-robin'
        
        Returns:
            Proxy dict or None if no proxies available
        """
        with self.lock:
            available_proxies = [p for i, p in enumerate(self.proxies) if i not in self.failed_proxies]
            
            if not available_proxies:
                print("[WARNING] No available proxies")
                return None
            
            if strategy == 'random':
                return random.choice(available_proxies)
            else:  # round-robin
                self.current_index = (self.current_index + 1) % len(available_proxies)
                return available_proxies[self.current_index]
    
    def mark_failed(self, proxy: Dict[str, str]):
        """Mark a proxy as failed"""
        with self.lock:
            try:
                index = self.proxies.index(proxy)
                self.failed_proxies.add(index)
                print(f"[FAIL] Marked proxy as failed: {proxy.get('http', 'unknown')}")
            except ValueError:
                pass
    
    def validate_proxy(self, proxy: Dict[str, str], timeout: int = 10) -> bool:
        """
        Test if proxy is working
        
        Args:
            proxy: Proxy dict
            timeout: Request timeout in seconds
        
        Returns:
            True if proxy works, False otherwise
        """
        try:
            response = requests.get(
                'http://httpbin.org/ip',
                proxies=proxy,
                timeout=timeout
            )
            if response.status_code == 200:
                ip = response.json().get('origin', 'unknown')
                print(f"[OK] Proxy validated: {ip}")
                return True
            return False
        except Exception as e:
            print(f"[ERROR] Proxy validation failed: {e}")
            return False
    
    def get_selenium_proxy_config(self, proxy: Dict[str, str]) -> str:
        """
        Convert proxy dict to Selenium proxy string
        
        Args:
            proxy: Proxy dict
        
        Returns:
            Proxy string for Selenium (e.g., "ip:port")
        """
        http_proxy = proxy.get('http', '')
        # Extract ip:port from http://ip:port or http://user:pass@ip:port
        if '@' in http_proxy:
            # Authenticated proxy
            parts = http_proxy.split('@')
            return parts[1]  # ip:port
        else:
            # Simple proxy
            return http_proxy.replace('http://', '').replace('https://', '')
    
    def get_stats(self) -> Dict:
        """Get proxy statistics"""
        return {
            'total': len(self.proxies),
            'failed': len(self.failed_proxies),
            'available': len(self.proxies) - len(self.failed_proxies)
        }
