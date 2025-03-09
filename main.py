import requests
import random
import time
import concurrent.futures
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import string
import cloudscraper  # For Cloudflare bypass
from selenium import webdriver  # Alternative Cloudflare bypass
from selenium.webdriver.chrome.options import Options

class ImprovedViewBot:
    def __init__(self, target_url, proxy_list=None, max_workers=3, visit_delay=(5, 20)):
        self.target_url = target_url
        self.proxy_list = proxy_list or []
        self.max_workers = max_workers
        self.visit_delay = visit_delay
        self.success_count = 0
        self.fail_count = 0
        self.successful_proxies = []  # Store successful proxies
        self.failed_proxies = []  # Store failed proxies
        
        # Parse domain for referrer
        parsed_url = urlparse(target_url)
        self.domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Create a session store to simulate real browsers with cookies
        self.sessions = {}
        
        # Load or initialize browser fingerprints
        self.fingerprints = self.load_fingerprints()
        
        print(f"Initialized with {len(self.fingerprints)} browser fingerprints")
    
    def load_fingerprints(self):
        """Load browser fingerprints from file or generate new ones"""
        try:
            with open('browser_fingerprints.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Generate some realistic browser fingerprints
            fingerprints = self.generate_fingerprints(50)
            # Save for future use
            with open('browser_fingerprints.json', 'w') as f:
                json.dump(fingerprints, f)
            return fingerprints
    
    def generate_fingerprints(self, count=50):
        """Generate realistic browser fingerprints"""
        fingerprints = []
        
        # Common browsers and platforms
        configs = [
            # Chrome on Windows
            {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'platform': 'Win32',
                'vendor': 'Google Inc.',
                'languages': ['en-US', 'en', 'tr-TR', 'tr'],
                'resolution': ['1920x1080', '1366x768', '1536x864', '1440x900', '1280x720'],
                'timezone_offset': [-180, -240, -300]
            },
            # Firefox on Windows
            {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
                'platform': 'Win32',
                'vendor': '',
                'languages': ['en-US', 'en', 'tr-TR', 'tr'],
                'resolution': ['1920x1080', '1366x768', '1536x864', '1440x900', '1280x720'],
                'timezone_offset': [-180, -240, -300]
            },
            # Chrome on Mac
            {
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
                'platform': 'MacIntel',
                'vendor': 'Google Inc.',
                'languages': ['en-US', 'en', 'tr-TR', 'tr'],
                'resolution': ['2560x1600', '1680x1050', '1440x900', '1280x800'],
                'timezone_offset': [-180, -240, -300]
            },
            # Safari on Mac
            {
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
                'platform': 'MacIntel',
                'vendor': 'Apple Computer, Inc.',
                'languages': ['en-US', 'en', 'tr-TR', 'tr'],
                'resolution': ['2560x1600', '1680x1050', '1440x900', '1280x800'],
                'timezone_offset': [-180, -240, -300]
            },
            # Chrome on Android
            {
                'user_agent': 'Mozilla/5.0 (Linux; Android 11; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
                'platform': 'Linux armv8l',
                'vendor': 'Google Inc.',
                'languages': ['en-US', 'en', 'tr-TR', 'tr'],
                'resolution': ['412x915', '360x800', '390x844'],
                'timezone_offset': [-180, -240, -300]
            },
            # Safari on iPhone
            {
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
                'platform': 'iPhone',
                'vendor': 'Apple Computer, Inc.',
                'languages': ['en-US', 'en', 'tr-TR', 'tr'],
                'resolution': ['390x844', '375x812', '414x896'],
                'timezone_offset': [-180, -240, -300]
            }
        ]
        
        for _ in range(count):
            config = random.choice(configs)
            
            fingerprint = {
                'user_agent': config['user_agent'],
                'platform': config['platform'],
                'vendor': config['vendor'],
                'language': random.choice(config['languages']),
                'resolution': random.choice(config['resolution']),
                'color_depth': random.choice([24, 32]),
                'timezone_offset': random.choice(config['timezone_offset']),
                'session_storage': True,
                'local_storage': True,
                'indexed_db': True,
                'cpu_cores': random.choice([2, 4, 6, 8]),
                'touch_points': 0 if 'Mobile' not in config['user_agent'] else random.choice([1, 5]),
                'hardware_concurrency': random.choice([2, 4, 8, 12, 16]),
                'device_memory': random.choice([2, 4, 8, 16]),
                'cookie_enabled': True
            }
            fingerprints.append(fingerprint)
        
        return fingerprints
    
    def load_proxies_from_file(self, file_path):
        """Load proxies from a text file"""
        proxies = []
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    proxy = line.strip()
                    if ':' in proxy:
                        proxies.append(proxy)
            print(f"Loaded {len(proxies)} proxies from {file_path}")
            return proxies
        except Exception as e:
            print(f"Error loading proxies from file: {str(e)}")
            return []
    
    def get_random_proxy(self):
        if not self.proxy_list:
            return None
        return random.choice(self.proxy_list)
    
    def get_random_fingerprint(self):
        return random.choice(self.fingerprints)
    
    def get_random_referrer(self):
        referrers = [
            "https://www.google.com/search?q=" + "+".join(self.target_url.split("/")[-1].split("-")),
            "https://www.google.com/",
            "https://www.google.com/search?q=site:" + self.domain,
            "https://www.google.co.uk/search?q=" + "+".join(self.target_url.split("/")[-1].split("-")),
            "https://www.google.com.tr/search?q=" + "+".join(self.target_url.split("/")[-1].split("-")),
            "https://www.bing.com/search?q=" + "+".join(self.target_url.split("/")[-1].split("-")),
            "https://www.facebook.com/",
            "https://www.youtube.com/",
            "https://www.instagram.com/",
            "https://twitter.com/",
            f"{self.domain}/",
            "https://www.reddit.com/",
            "https://t.co/" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=7)),
            "https://duckduckgo.com/?q=" + "+".join(self.target_url.split("/")[-1].split("-")),
            "https://www.tiktok.com/"
        ]
        return random.choice(referrers)
    
    def get_session_key(self, proxy, fingerprint):
        return f"proxy_{proxy}_{fingerprint['user_agent'][:20]}" if proxy else f"direct_{fingerprint['user_agent'][:20]}"
    
    def get_session(self, proxy, fingerprint):
        session_key = self.get_session_key(proxy, fingerprint)
        if session_key not in self.sessions:
            self.sessions[session_key] = requests.Session()
        return self.sessions[session_key]
    
    def simulate_keyboard_navigation(self, session, url, headers, proxies):
        """Simulate keyboard navigation on page with keypress events"""
        try:
            # Simulate scrolling down with a few arrow key presses
            for _ in range(random.randint(3, 8)):
                time.sleep(random.uniform(0.5, 2))
            
            time.sleep(random.uniform(2, 5))  # Wait a bit longer
            
            # Simulating a tab press or link click by requesting a different URL on the same domain
            if random.random() > 0.7:
                # Try to fetch links from the page
                try:
                    response = session.get(url, headers=headers, proxies=proxies, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        links = [a['href'] for a in soup.find_all('a', href=True) 
                                if a['href'].startswith('/') or self.domain in a['href']]
                        
                        if links:
                            random_link = random.choice(links)
                            # Convert relative URL to absolute if needed
                            if random_link.startswith('/'):
                                random_link = f"{self.domain}{random_link}"
                            
                            # Visit the random link
                            session.get(random_link, headers=headers, proxies=proxies, timeout=10)
                            time.sleep(random.uniform(3, 10))
                except Exception as e:
                    pass  # Ignore errors during navigation
        except:
            pass  # Failsafe
    
    def make_request(self, proxy=None):
        """Make a request to the target URL with optional proxy and Cloudflare bypass"""
        fingerprint = self.get_random_fingerprint()
        user_agent = fingerprint['user_agent']
        referrer = self.get_random_referrer()
        
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': f"{fingerprint['language']},en;q=0.9",
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': referrer,
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-User': '?1',
            'Pragma': 'no-cache',
            'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': f'"{fingerprint["platform"]}"',
        }
        
        proxies = None
        if proxy:
            proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
        
        try:
            # Use cloudscraper to bypass Cloudflare
            scraper = cloudscraper.create_scraper()
            response = scraper.get(self.target_url, headers=headers, proxies=proxies, timeout=20)
            
            if response.status_code == 200:
                print(f"✅ Success | Proxy: {proxy} | Status: {response.status_code}")
                return True
            else:
                print(f"❌ Failed | Proxy: {proxy} | Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Failed | Proxy: {proxy} | Error: {str(e)[:50]}...")
            return False
    
    def test_proxies(self, proxy_list, max_workers=10):
        """Test proxies to find working ones"""
        working_proxies = []
        
        def test_proxy(proxy):
            try:
                response = requests.get(
                    "https://www.google.com",
                    proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"},
                    timeout=10
                )
                if response.status_code == 200:
                    print(f"✅ Proxy {proxy} is working")
                    return proxy
                else:
                    print(f"❌ Proxy {proxy} failed with status code {response.status_code}")
                    return None
            except Exception as e:
                print(f"❌ Proxy {proxy} failed with error: {str(e)[:50]}...")
                return None
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(test_proxy, proxy) for proxy in proxy_list]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    working_proxies.append(result)
        
        print(f"Found {len(working_proxies)} working proxies out of {len(proxy_list)}")
        return working_proxies
    
    def run(self, total_views, allow_direct=True):
        print(f"Starting improved view bot for URL: {self.target_url}")
        
        # If proxy list is empty, try to load proxies from http.txt
        if not self.proxy_list:
            print("No proxies provided. Attempting to load proxies from http.txt...")
            self.proxy_list = self.load_proxies_from_file('http.txt')
        
        # Test proxies to find working ones
        if self.proxy_list:
            print(f"Testing {len(self.proxy_list)} proxies...")
            self.proxy_list = self.test_proxies(self.proxy_list)
        
        if self.proxy_list:
            print(f"Target: {total_views} views with {len(self.proxy_list)} proxies")
        else:
            print(f"Target: {total_views} views (using direct connection)")
        
        count = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while count < total_views:
                remaining = min(self.max_workers, total_views - count)
                if remaining <= 0:
                    break
                
                futures = []
                if self.proxy_list:
                    for _ in range(remaining):
                        proxy = self.get_random_proxy()
                        futures.append(executor.submit(self.make_request, proxy))
                elif allow_direct:
                    futures = [executor.submit(self.make_request, None) for _ in range(remaining)]
                else:
                    print("No proxies available and direct connections not allowed. Stopping.")
                    break
                
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result:
                        self.success_count += 1
                    else:
                        self.fail_count += 1
                    count += 1
                    
                    if count % 5 == 0 or count == total_views:
                        progress = (count / total_views) * 100
                        print(f"Progress: {progress:.1f}% | Success: {self.success_count} | Failed: {self.fail_count}")
                
                # Randomized delay between batches to avoid detection
                delay = random.uniform(*self.visit_delay)
                print(f"Waiting {delay:.2f} seconds before next batch...")
                time.sleep(delay)
        
        print(f"\nCompleted {count} requests")
        print(f"Successful: {self.success_count}")
        print(f"Failed: {self.fail_count}")
        if count > 0:
            print(f"Success rate: {(self.success_count/count)*100:.2f}%")
        else:
            print("No requests were made.")
        
        # Save successful and failed proxies to files
        with open('successful_proxies.json', 'w') as f:
            json.dump(self.successful_proxies, f)
        
        with open('failed_proxies.json', 'w') as f:
            json.dump(self.failed_proxies, f)


def main():
    # Get target URL from user
    target_url = input("Enter the target URL (e.g., https://example.com): ").strip()
    
    # Get proxy file from user
    proxy_file = input("Enter the proxy file name (e.g., http.txt, leave blank to skip): ").strip()
    
    # Load proxies if provided
    proxy_list = []
    if proxy_file:
        try:
            with open(proxy_file, 'r') as f:
                proxy_list = [line.strip() for line in f if line.strip()]
            print(f"{len(proxy_list)} proxies loaded.")
        except FileNotFoundError:
            print(f"{proxy_file} not found. Proceeding without proxies.")
    
    # Get settings from user
    max_concurrent_requests = int(input("Enter the number of concurrent requests (e.g., 5): ").strip() or 5)
    total_views_to_generate = int(input("Enter the total number of views to generate (e.g., 100): ").strip() or 100)
    delay_between_requests = (8, 20)  # Fixed or can be customized
    
    # Initialize and run the bot
    bot = ImprovedViewBot(target_url=target_url, 
                          proxy_list=proxy_list,
                          max_workers=max_concurrent_requests,
                          visit_delay=delay_between_requests)
    
    # Run the bot to generate views
    bot.run(total_views=total_views_to_generate, allow_direct=not bool(proxy_list))

if __name__ == "__main__":
    main()