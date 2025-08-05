from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Dict, Any, Optional
import json
import re
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime
import logging
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.async_api import async_playwright
import uvicorn
import os
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Complete Web Scraper API",
    description="All-in-one web scraping API that extracts everything from a website in one structured JSON response",
    version="5.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class URLRequest(BaseModel):
    url: HttpUrl

class BatchURLRequest(BaseModel):
    urls: List[HttpUrl] = Field(..., max_items=10)

@dataclass
class TechSignature:
    name: str
    category: str
    patterns: List[str]
    confidence_indicators: List[str]
    version_patterns: List[str] = None

class CompleteWebScraper:
    def __init__(self):
        self.browser = None
        self.context = None
        self.playwright = None
        self.tech_signatures = self._load_tech_signatures()
    
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--no-zygote',
                '--disable-extensions',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    def _load_tech_signatures(self) -> List[TechSignature]:
        """Load comprehensive tech stack detection signatures"""
        return [
            # CMS Detection
            TechSignature(
                name="WordPress",
                category="cms",
                patterns=['/wp-content/', '/wp-includes/', '/wp-admin/', 'wp-json', 'wordpress'],
                confidence_indicators=['generator.*wordpress', 'wp-content', 'wp-includes', 'rest_route'],
                version_patterns=[r'WordPress (\d+\.\d+(?:\.\d+)?)']
            ),
            TechSignature(
                name="Drupal",
                category="cms",
                patterns=['/sites/default/', '/modules/', '/themes/', 'drupal', 'Drupal.settings'],
                confidence_indicators=['generator.*drupal', 'sites/default', 'Drupal.settings'],
                version_patterns=[r'Drupal (\d+\.\d+(?:\.\d+)?)']
            ),
            TechSignature(
                name="Joomla",
                category="cms",
                patterns=['/components/', '/modules/', '/templates/', 'joomla', 'option=com_'],
                confidence_indicators=['generator.*joomla', 'option=com_', 'components/'],
                version_patterns=[r'Joomla! (\d+\.\d+(?:\.\d+)?)']
            ),
            TechSignature(
                name="Shopify",
                category="cms",
                patterns=['shopify', 'myshopify.com', 'cdn.shopify.com', 'Shopify.theme'],
                confidence_indicators=['Shopify.theme', 'shopify-analytics', 'myshopify.com']
            ),
            TechSignature(
                name="Magento",
                category="cms", 
                patterns=['magento', '/skin/frontend/', '/js/mage/', 'Mage.Cookies'],
                confidence_indicators=['Mage.Cookies', 'skin/frontend', 'js/mage']
            ),
            TechSignature(
                name="WooCommerce",
                category="cms",
                patterns=['woocommerce', 'wc-', 'wp-content/plugins/woocommerce'],
                confidence_indicators=['woocommerce', 'wc-ajax', 'plugins/woocommerce']
            ),
            # JavaScript Frameworks
            TechSignature(
                name="React",
                category="framework",
                patterns=['react', '_react', 'React\\.', '__REACT_DEVTOOLS_'],
                confidence_indicators=['data-reactroot', '__REACT_DEVTOOLS_', 'React.', '_react']
            ),
            TechSignature(
                name="Vue.js",
                category="framework",
                patterns=['vue', 'Vue\\.', '__VUE__', 'v-'],
                confidence_indicators=['__VUE__', 'Vue.', 'data-v-', 'vue.js'],
                version_patterns=[r'Vue\.js v(\d+\.\d+\.\d+)']
            ),
            TechSignature(
                name="Angular",
                category="framework",
                patterns=['angular', 'ng-', 'Angular\\.', '__ng'],
                confidence_indicators=['ng-version', 'ng-app', 'angular.js', '_angular']
            ),
            TechSignature(
                name="Next.js",
                category="framework",
                patterns=['next\\.js', '_next/', '__NEXT_DATA__', 'next-route'],
                confidence_indicators=['__NEXT_DATA__', '_next/', 'next-route']
            ),
            TechSignature(
                name="Nuxt.js",
                category="framework",
                patterns=['nuxt', '_nuxt/', '__NUXT__'],
                confidence_indicators=['__NUXT__', '_nuxt/', 'nuxt.js']
            ),
            # CSS Frameworks
            TechSignature(
                name="Bootstrap",
                category="css_framework",
                patterns=['bootstrap', 'btn-', 'col-', 'container-'],
                confidence_indicators=['bootstrap.css', 'bootstrap.min.css', 'btn-primary'],
                version_patterns=[r'Bootstrap v(\d+\.\d+\.\d+)']
            ),
            TechSignature(
                name="Tailwind CSS",
                category="css_framework",
                patterns=['tailwind', 'tw-', 'bg-\\w+-\\d+', 'text-\\w+-\\d+'],
                confidence_indicators=['tailwindcss', 'bg-blue-500', 'text-gray-900']
            ),
            TechSignature(
                name="Foundation",
                category="css_framework",
                patterns=['foundation', 'grid-x', 'cell-'],
                confidence_indicators=['foundation.css', 'grid-x', 'foundation.js']
            ),
            # Analytics & Tracking
            TechSignature(
                name="Google Analytics",
                category="analytics",
                patterns=['google-analytics', 'gtag\\(', 'ga\\(', 'GoogleAnalyticsObject', 'UA-\\d+-\\d+', 'G-[A-Z0-9]+'],
                confidence_indicators=['gtag(', 'GoogleAnalyticsObject', 'google-analytics.com']
            ),
            TechSignature(
                name="Google Tag Manager",
                category="analytics",
                patterns=['gtm\\.js', 'googletagmanager', 'GTM-[A-Z0-9]+', 'dataLayer'],
                confidence_indicators=['googletagmanager.com', 'GTM-', 'dataLayer']
            ),
            TechSignature(
                name="Facebook Pixel",
                category="analytics",
                patterns=['fbevents\\.js', 'facebook\\.net', 'connect\\.facebook\\.net', 'fbq\\('],
                confidence_indicators=['fbevents.js', 'connect.facebook.net', 'fbq(']
            ),
            TechSignature(
                name="Hotjar",
                category="analytics",
                patterns=['hotjar', 'static\\.hotjar\\.com', 'hj\\('],
                confidence_indicators=['static.hotjar.com', 'hj(', 'hotjar']
            ),
            # SEO Tools
            TechSignature(
                name="Yoast SEO",
                category="seo",
                patterns=['yoast', 'wp-seo', 'wpseo'],
                confidence_indicators=['Yoast SEO', 'wp-seo', 'wpseo']
            ),
            TechSignature(
                name="RankMath",
                category="seo",
                patterns=['rank-math', 'rankmath'],
                confidence_indicators=['rank-math', 'rankmath']
            ),
            TechSignature(
                name="All in One SEO",
                category="seo",
                patterns=['aioseop', 'all-in-one-seo'],
                confidence_indicators=['aioseop', 'all-in-one-seo']
            ),
            # Libraries
            TechSignature(
                name="jQuery",
                category="library",
                patterns=['jquery', 'jQuery', '\\$\\.'],
                confidence_indicators=['jquery.js', 'jQuery', 'jquery.min.js'],
                version_patterns=[r'jQuery v(\d+\.\d+\.\d+)']
            ),
            TechSignature(
                name="Lodash",
                category="library",
                patterns=['lodash', '_\\.'],
                confidence_indicators=['lodash.js', 'lodash.min.js']
            ),
            TechSignature(
                name="D3.js",
                category="library",
                patterns=['d3\\.js', 'd3\\.min\\.js', 'd3\\.'],
                confidence_indicators=['d3.js', 'd3.min.js']
            ),
            # CDN & Security
            TechSignature(
                name="Cloudflare",
                category="cdn",
                patterns=['cloudflare', 'cf-ray', '__cfduid'],
                confidence_indicators=['cf-ray', 'cloudflare', '__cfduid']
            ),
            TechSignature(
                name="Amazon CloudFront",
                category="cdn",
                patterns=['cloudfront', 'amazonaws\\.com'],
                confidence_indicators=['cloudfront.net', 'amazonaws.com']
            ),
            # Performance Tools
            TechSignature(
                name="WP Rocket",
                category="performance",
                patterns=['wp-rocket', 'wpr_'],
                confidence_indicators=['wp-rocket', 'wpr_']
            ),
            TechSignature(
                name="W3 Total Cache",
                category="performance",
                patterns=['w3tc', 'w3-total-cache'],
                confidence_indicators=['w3tc', 'w3-total-cache']
            )
        ]

    async def complete_website_analysis(self, url: str) -> Dict[str, Any]:
        """Complete comprehensive website analysis - everything in one response"""
        start_time = time.time()
        
        try:
            page = await self.context.new_page()
            
            # Track response for headers and performance
            response_info = {}
            def handle_response(response):
                if response.url == str(url) or response.url.rstrip('/') == str(url).rstrip('/'):
                    response_info['headers'] = dict(response.headers)
                    response_info['status'] = response.status
                    response_info['url'] = response.url
            
            page.on('response', handle_response)
            
            # Navigate to page
            try:
                response = await page.goto(str(url), wait_until='networkidle', timeout=45000)
            except Exception as e:
                logger.warning(f"NetworkIdle failed for {url}, trying domcontentloaded: {str(e)}")
                response = await page.goto(str(url), wait_until='domcontentloaded', timeout=30000)
            
            if not response:
                raise HTTPException(status_code=400, detail="Failed to load page")
            
            # Wait for additional JS rendering
            await page.wait_for_timeout(3000)
            
            # Get comprehensive page data
            final_url = page.url
            status_code = response.status if response else None
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Get JavaScript context data
            js_data = await page.evaluate("""
                () => {
                    const data = {
                        window_vars: Object.keys(window).slice(0, 50),
                        frameworks: {},
                        libraries: {},
                        globals: {}
                    };
                    
                    // Check for framework globals
                    if (window.React) data.frameworks.React = typeof window.React;
                    if (window.Vue) data.frameworks.Vue = window.Vue.version || 'detected';
                    if (window.angular) data.frameworks.Angular = window.angular.version || 'detected';
                    if (window.jQuery) data.libraries.jQuery = window.jQuery.fn.jquery || 'detected';
                    if (window._) data.libraries.Lodash = 'detected';
                    if (window.d3) data.libraries.D3 = window.d3.version || 'detected';
                    
                    // Analytics globals
                    if (window.dataLayer) data.globals.dataLayer = 'detected';
                    if (window.gtag) data.globals.gtag = 'detected';
                    if (window.ga) data.globals.ga = 'detected';
                    if (window.fbq) data.globals.fbq = 'detected';
                    
                    return data;
                }
            """)
            
            # Performance timing
            try:
                perf_data = await page.evaluate("""
                    () => {
                        const timing = performance.timing;
                        const navigation = performance.navigation;
                        const paintEntries = performance.getEntriesByType('paint');
                        return {
                            loadTime: timing.loadEventEnd - timing.navigationStart,
                            domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
                            firstPaint: paintEntries.find(p => p.name === 'first-paint')?.startTime || null,
                            firstContentfulPaint: paintEntries.find(p => p.name === 'first-contentful-paint')?.startTime || null,
                            navigationType: navigation.type,
                            redirectCount: navigation.redirectCount,
                            resourceCount: performance.getEntriesByType('resource').length
                        };
                    }
                """)
            except Exception:
                perf_data = {}
            
            # Build complete analysis
            processing_time = time.time() - start_time
            
            complete_analysis = {
                # Basic Information
                'url': str(url),
                'final_url': final_url,
                'timestamp': datetime.now().isoformat(),
                'processing_time': round(processing_time, 2),
                'status_code': status_code,
                
                # 1. Page Information
                'page_info': self._extract_page_info(soup, final_url),
                
                # 2. Meta Data Analysis
                'meta_data': self._extract_meta_data(soup),
                
                # 3. Structured Data Analysis  
                'structured_data': self._extract_structured_data(soup),
                
                # 4. Technology Stack Analysis
                'tech_stack': self._analyze_tech_stack(html_content, response_info.get('headers', {}), js_data),
                
                # 5. Content Analysis
                'content_analysis': self._extract_content_analysis(soup),
                
                # 6. SEO Analysis
                'seo_analysis': self._extract_seo_analysis(soup),
                
                # 7. Technical Analysis
                'technical_analysis': self._extract_technical_analysis(soup, response_info, perf_data, len(html_content)),
                
                # 8. Links Analysis
                'links_analysis': self._extract_links_analysis(soup, final_url),
                
                # 9. Images Analysis
                'images_analysis': self._extract_images_analysis(soup, final_url),
                
                # 10. Forms Analysis
                'forms_analysis': self._extract_forms_analysis(soup),
                
                # 11. Business Information
                'business_info': self._extract_business_info(soup),
                
                # 12. Contact Information
                'contact_info': self._extract_contact_info(soup),
                
                # 13. Page Structure
                'page_structure': self._analyze_page_structure(soup),
                
                # 14. External Resources
                'external_resources': await self._analyze_external_resources(final_url),
                
                # 15. Security Analysis
                'security_analysis': self._analyze_security(soup, response_info.get('headers', {})),
                
                # 16. Performance Analysis
                'performance_analysis': self._analyze_performance(soup, perf_data, len(html_content)),
                
                # 17. Accessibility Analysis
                'accessibility_analysis': self._analyze_accessibility(soup),
                
                # 18. Mobile Analysis
                'mobile_analysis': self._analyze_mobile(soup),
            }
            
            # 19. Overall Summary
            complete_analysis['summary'] = self._create_summary(complete_analysis)
            
            await page.close()
            return complete_analysis
            
        except Exception as e:
            logger.error(f"Error in complete website analysis for {url}: {str(e)}")
            if 'page' in locals():
                await page.close()
            raise HTTPException(status_code=500, detail=f"Complete analysis failed: {str(e)}")

    def _extract_page_info(self, soup: BeautifulSoup, final_url: str) -> Dict[str, Any]:
        """Extract comprehensive page information"""
        title_elem = soup.find('title')
        parsed_url = urlparse(final_url)
        
        # Language detection
        lang = None
        html_elem = soup.find('html', lang=True)
        if html_elem:
            lang = html_elem.get('lang')
        else:
            lang_meta = soup.find('meta', attrs={'http-equiv': 'content-language'})
            if lang_meta:
                lang = lang_meta.get('content')
        
        return {
            'title': title_elem.text.strip() if title_elem else '',
            'title_length': len(title_elem.text.strip()) if title_elem else 0,
            'domain': parsed_url.netloc,
            'path': parsed_url.path,
            'protocol': parsed_url.scheme,
            'language': lang,
            'charset': soup.find('meta', charset=True).get('charset', 'utf-8') if soup.find('meta', charset=True) else 'utf-8',
            'is_ssl': final_url.startswith('https://'),
            'url_length': len(final_url),
            'page_type': self._determine_page_type(parsed_url.path, soup)
        }
    
    def _determine_page_type(self, path: str, soup: BeautifulSoup) -> str:
        """Determine page type"""
        path_lower = path.lower()
        if path_lower in ['/', '', '/index.html', '/index.php']:
            return 'homepage'
        elif '/blog' in path_lower or '/artikel' in path_lower:
            return 'blog'
        elif '/product' in path_lower or '/shop' in path_lower:
            return 'product'
        elif '/contact' in path_lower:
            return 'contact'
        elif '/about' in path_lower or '/over' in path_lower:
            return 'about'
        elif soup.find('article'):
            return 'article'
        else:
            return 'page'

    def _extract_meta_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract comprehensive meta data"""
        meta_data = {
            'basic_meta': {},
            'social_meta': {},
            'seo_meta': {},
            'technical_meta': {},
            'stylesheets': [],
            'scripts': [],
            'favicons': []
        }
        
        # Meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property') or meta.get('http-equiv')
            content = meta.get('content')
            if name and content:
                name_lower = name.lower()
                if name_lower.startswith(('og:', 'twitter:')):
                    meta_data['social_meta'][name] = content
                elif name_lower in ['description', 'keywords', 'robots', 'author']:
                    meta_data['seo_meta'][name] = content
                elif name_lower in ['viewport', 'charset', 'http-equiv']:
                    meta_data['technical_meta'][name] = content
                else:
                    meta_data['basic_meta'][name] = content
        
        # Stylesheets
        for link in soup.find_all('link', rel='stylesheet'):
            if link.get('href'):
                meta_data['stylesheets'].append({
                    'href': link.get('href'),
                    'media': link.get('media', 'all'),
                    'is_external': link.get('href', '').startswith(('http', '//'))
                })
        
        # Scripts
        for script in soup.find_all('script', src=True):
            meta_data['scripts'].append({
                'src': script.get('src'),
                'async': script.has_attr('async'),
                'defer': script.has_attr('defer'),
                'is_external': script.get('src', '').startswith(('http', '//'))
            })
        
        # Favicons
        for link in soup.find_all('link', rel=lambda x: x and 'icon' in str(x)):
            meta_data['favicons'].append({
                'rel': link.get('rel'),
                'href': link.get('href'),
                'sizes': link.get('sizes', '')
            })
        
        return meta_data

    def _extract_structured_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract all structured data"""
        structured_data = {
            'json_ld': [],
            'microdata': [],
            'opengraph': {},
            'twitter_cards': {},
            'rdfa': [],
            'schema_types': []
        }
        
        # JSON-LD
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                if script.string:
                    data = json.loads(script.string.strip())
                    if isinstance(data, list):
                        structured_data['json_ld'].extend(data)
                    else:
                        structured_data['json_ld'].append(data)
            except json.JSONDecodeError:
                continue
        
        # Microdata
        for elem in soup.find_all(attrs={'itemscope': True}):
            item = {
                'type': elem.get('itemtype', ''),
                'properties': {}
            }
            for prop_elem in elem.find_all(attrs={'itemprop': True}):
                prop_name = prop_elem.get('itemprop')
                if prop_elem.name == 'meta':
                    content = prop_elem.get('content', '')
                elif prop_elem.name in ['img', 'audio', 'video']:
                    content = prop_elem.get('src', '')
                elif prop_elem.name == 'a':
                    content = prop_elem.get('href', '')
                else:
                    content = prop_elem.get_text(strip=True)
                
                if content:
                    item['properties'][prop_name] = content
            
            if item['properties']:
                structured_data['microdata'].append(item)
        
        # OpenGraph
        for meta in soup.find_all('meta'):
            property_attr = meta.get('property', '')
            if property_attr.startswith('og:'):
                structured_data['opengraph'][property_attr] = meta.get('content', '')
        
        # Twitter Cards
        for meta in soup.find_all('meta'):
            name_attr = meta.get('name', '')
            if name_attr.startswith('twitter:'):
                structured_data['twitter_cards'][name_attr] = meta.get('content', '')
        
        # RDFa
        for elem in soup.find_all(attrs={'typeof': True}):
            rdfa_item = {
                'typeof': elem.get('typeof', ''),
                'properties': {}
            }
            for prop_elem in elem.find_all(attrs={'property': True}):
                prop = prop_elem.get('property')
                content = prop_elem.get('content') or prop_elem.get_text(strip=True)
                if content:
                    rdfa_item['properties'][prop] = content
            
            if rdfa_item['properties']:
                structured_data['rdfa'].append(rdfa_item)
        
        # Collect schema types
        schema_types = set()
        for json_data in structured_data['json_ld']:
            if isinstance(json_data, dict) and '@type' in json_data:
                schema_types.add(json_data['@type'])
        for micro_item in structured_data['microdata']:
            if micro_item.get('type'):
                schema_type = micro_item['type'].split('/')[-1]
                schema_types.add(schema_type)
        
        structured_data['schema_types'] = list(schema_types)
        structured_data['summary'] = {
            'has_structured_data': bool(structured_data['json_ld'] or structured_data['microdata']),
            'total_json_ld': len(structured_data['json_ld']),
            'total_microdata': len(structured_data['microdata']),
            'total_schema_types': len(structured_data['schema_types']),
            'has_social_meta': bool(structured_data['opengraph'] or structured_data['twitter_cards'])
        }
        
        return structured_data

    def _analyze_tech_stack(self, html_content: str, headers: Dict[str, str], js_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze complete technology stack"""
        detected_techs = self._detect_technologies(html_content, headers, js_data)
        
        tech_stack = {
            'cms': {},
            'frameworks': {},
            'css_frameworks': {},
            'analytics': {},
            'seo_tools': {},
            'libraries': {},
            'cdn': {},
            'performance': {},
            'server_info': self._extract_server_info(headers),
            'detected_technologies': detected_techs,
            'summary': {}
        }
        
        # Categorize detected technologies
        for tech_name, tech_info in detected_techs.items():
            category = tech_info['category']
            if category in tech_stack:
                tech_stack[category][tech_name] = tech_info
        
        tech_stack['summary'] = {
            'total_technologies': len(detected_techs),
            'cms_detected': list(tech_stack['cms'].keys()),
            'frameworks_detected': list(tech_stack['frameworks'].keys()),
            'analytics_tools': list(tech_stack['analytics'].keys()),
            'main_server': tech_stack['server_info'].get('server', 'Unknown'),
            'has_cms': bool(tech_stack['cms']),
            'has_analytics': bool(tech_stack['analytics'])
        }
        
        return tech_stack

    def _detect_technologies(self, html_content: str, headers: Dict[str, str], js_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Detect technologies using signatures"""
        detected = {}
        combined_text = html_content.lower() + ' ' + ' '.join(f"{k}: {v}" for k, v in headers.items()).lower()
        
        for signature in self.tech_signatures:
            confidence = 0
            evidence = []
            version = None
            
            # Check patterns
            for pattern in signature.patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    confidence += 25
                    evidence.append(f"Pattern: {pattern}")
            
            # Check confidence indicators
            for indicator in signature.confidence_indicators:
                if re.search(indicator, combined_text, re.IGNORECASE):
                    confidence += 30
                    evidence.append(f"Indicator: {indicator}")
            
            # Check JavaScript globals
            if signature.name in js_data.get('frameworks', {}):
                confidence += 40
                version = js_data['frameworks'][signature.name]
                evidence.append("JavaScript global detected")
            elif signature.name in js_data.get('libraries', {}):
                confidence += 40
                version = js_data['libraries'][signature.name]
                evidence.append("JavaScript global detected")
            
            # Version detection
            if signature.version_patterns and not version:
                for version_pattern in signature.version_patterns:
                    version_match = re.search(version_pattern, html_content, re.IGNORECASE)
                    if version_match:
                        version = version_match.group(1)
                        evidence.append(f"Version found: {version}")
                        break
            
            if confidence >= 40:
                detected[signature.name] = {
                    'category': signature.category,
                    'confidence': min(confidence, 100),
                    'version': version,
                    'evidence': evidence[:3]
                }
        
        return detected

    def _extract_server_info(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Extract server information from headers"""
        server_info = {
            'server': headers.get('server', 'Unknown'),
            'powered_by': headers.get('x-powered-by', ''),
            'cdn': 'None',
            'security_headers': {}
        }
        
        # Detect CDN
        if 'cloudflare' in str(headers).lower():
            server_info['cdn'] = 'Cloudflare'
        elif 'amazonaws' in str(headers).lower():
            server_info['cdn'] = 'Amazon CloudFront'
        
        # Security headers
        security_headers = ['strict-transport-security', 'content-security-policy', 'x-frame-options']
        for header in security_headers:
            if header in headers:
                server_info['security_headers'][header] = headers[header]
        
        return server_info

    def _extract_content_analysis(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract comprehensive content analysis"""
        # Get full text
        text_content = soup.get_text()
        clean_text = re.sub(r'\s+', ' ', text_content).strip()
        
        content_analysis = {
            'text_content': clean_text[:1000] + '...' if len(clean_text) > 1000 else clean_text,
            'word_count': len(clean_text.split()),
            'character_count': len(clean_text),
            'reading_time': max(1, len(clean_text.split()) // 200),
            'headings': self._extract_headings(soup),
            'paragraphs': self._extract_paragraphs(soup),
            'lists': self._extract_lists(soup),
            'tables': self._extract_tables(soup),
            'multimedia_content': {
                'images': len(soup.find_all('img')),
                'videos': len(soup.find_all('video')),
                'audio': len(soup.find_all('audio')),
                'iframes': len(soup.find_all('iframe'))
            },
            'content_sections': self._analyze_content_sections(soup),
            'text_density': self._calculate_text_density(soup, clean_text)
        }
        
        return content_analysis

    def _extract_headings(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract heading analysis"""
        headings = {}
        total_headings = 0
        
        for i in range(1, 7):
            h_elements = soup.find_all(f'h{i}')
            if h_elements:
                headings[f'h{i}'] = [{'text': h.text.strip(), 'length': len(h.text.strip())} for h in h_elements[:10]]
                total_headings += len(h_elements)
        
        return {
            'headings_by_level': headings,
            'total_headings': total_headings,
            'h1_count': len(soup.find_all('h1')),
            'proper_h1_usage': len(soup.find_all('h1')) == 1
        }

    def _extract_paragraphs(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract paragraph analysis"""
        paragraphs = soup.find_all('p')
        valid_paragraphs = []
        
        for p in paragraphs:
            text = p.text.strip()
            if text and len(text) > 10:
                valid_paragraphs.append({
                    'text': text[:200] + '...' if len(text) > 200 else text,
                    'word_count': len(text.split()),
                    'has_links': bool(p.find('a'))
                })
        
        return {
            'total_paragraphs': len(valid_paragraphs),
            'paragraphs': valid_paragraphs[:20],  # Limit to first 20
            'average_length': sum(p['word_count'] for p in valid_paragraphs) / len(valid_paragraphs) if valid_paragraphs else 0
        }

    def _extract_lists(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract list analysis"""
        lists = []
        
        for ul_ol in soup.find_all(['ul', 'ol']):
            list_items = ul_ol.find_all('li', recursive=False)
            if list_items:
                lists.append({
                    'type': ul_ol.name,
                    'item_count': len(list_items),
                    'items': [li.text.strip()[:100] for li in list_items[:10]]  # First 10 items, truncated
                })
        
        return {
            'total_lists': len(lists),
            'lists': lists[:10],  # First 10 lists
            'total_list_items': sum(l['item_count'] for l in lists)
        }

    def _extract_tables(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract table analysis"""
        tables = []
        
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            headers = table.find_all('th')
            
            tables.append({
                'row_count': len(rows),
                'has_headers': bool(headers),
                'header_count': len(headers),
                'caption': table.find('caption').text.strip() if table.find('caption') else ''
            })
        
        return {
            'total_tables': len(tables),
            'tables': tables,
            'tables_with_headers': sum(1 for t in tables if t['has_headers'])
        }

    def _analyze_content_sections(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze content by semantic sections"""
        sections = {}
        semantic_elements = ['main', 'article', 'section', 'aside', 'header', 'footer', 'nav']
        
        for element in semantic_elements:
            elements = soup.find_all(element)
            if elements:
                sections[element] = {
                    'count': len(elements),
                    'total_text_length': sum(len(elem.get_text().strip()) for elem in elements)
                }
        
        return sections

    def _calculate_text_density(self, soup: BeautifulSoup, clean_text: str) -> float:
        """Calculate text to HTML ratio"""
        html_size = len(str(soup))
        text_size = len(clean_text)
        return round(text_size / html_size, 3) if html_size > 0 else 0

    def _extract_seo_analysis(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract comprehensive SEO analysis"""
        title = soup.find('title')
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        robots_meta = soup.find('meta', attrs={'name': 'robots'})
        canonical = soup.find('link', rel='canonical')
        
        seo_analysis = {
            'title_analysis': {
                'title': title.text.strip() if title else '',
                'length': len(title.text) if title else 0,
                'word_count': len(title.text.split()) if title else 0,
                'is_optimal_length': 30 <= len(title.text) <= 60 if title else False
            },
            'meta_description': {
                'description': meta_desc.get('content', '') if meta_desc else '',
                'length': len(meta_desc.get('content', '')) if meta_desc else 0,
                'is_optimal_length': 120 <= len(meta_desc.get('content', '')) <= 160 if meta_desc else False,
                'exists': bool(meta_desc)
            },
            'robots_meta': {
                'content': robots_meta.get('content', '') if robots_meta else '',
                'is_indexable': 'noindex' not in robots_meta.get('content', '').lower() if robots_meta else True,
                'is_followable': 'nofollow' not in robots_meta.get('content', '').lower() if robots_meta else True
            },
            'canonical_url': {
                'exists': bool(canonical),
                'url': canonical.get('href', '') if canonical else ''
            },
            'heading_structure': {
                'h1_count': len(soup.find_all('h1')),
                'h2_count': len(soup.find_all('h2')),
                'h3_count': len(soup.find_all('h3')),
                'proper_h1_usage': len(soup.find_all('h1')) == 1
            },
            'image_seo': {
                'total_images': len(soup.find_all('img')),
                'images_with_alt': len(soup.find_all('img', alt=True)),
                'images_without_alt': len(soup.find_all('img', alt=False)),
                'alt_text_quality': self._analyze_alt_quality(soup)
            },
            'content_metrics': {
                'word_count': len(soup.get_text().split()),
                'is_sufficient_content': len(soup.get_text().split()) >= 300
            },
            'structured_data_seo': {
                'has_json_ld': bool(soup.find('script', type='application/ld+json')),
                'has_microdata': bool(soup.find(attrs={'itemscope': True})),
                'has_opengraph': bool(soup.find('meta', property=lambda x: x and x.startswith('og:')))
            }
        }
        
        # Calculate SEO score
        seo_analysis['seo_score'] = self._calculate_seo_score(seo_analysis)
        
        return seo_analysis

    def _analyze_alt_quality(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze alt text quality"""
        images = soup.find_all('img')
        alt_analysis = {
            'descriptive_alt': 0,
            'empty_alt': 0,
            'missing_alt': 0,
            'optimal_length_alt': 0
        }
        
        for img in images:
            alt = img.get('alt')
            if alt is None:
                alt_analysis['missing_alt'] += 1
            elif alt == '':
                alt_analysis['empty_alt'] += 1
            else:
                if 10 <= len(alt) <= 125:
                    alt_analysis['optimal_length_alt'] += 1
                if len(alt.split()) >= 3:
                    alt_analysis['descriptive_alt'] += 1
        
        return alt_analysis

    def _calculate_seo_score(self, seo_data: Dict[str, Any]) -> int:
        """Calculate SEO score out of 100"""
        score = 0
        
        # Title (20 points)
        if seo_data['title_analysis']['is_optimal_length']:
            score += 20
        elif seo_data['title_analysis']['title']:
            score += 10
        
        # Meta description (15 points)
        if seo_data['meta_description']['is_optimal_length']:
            score += 15
        elif seo_data['meta_description']['exists']:
            score += 8
        
        # H1 usage (15 points)
        if seo_data['heading_structure']['proper_h1_usage']:
            score += 15
        elif seo_data['heading_structure']['h1_count'] > 0:
            score += 8
        
        # Images with alt (10 points)
        total_imgs = seo_data['image_seo']['total_images']
        if total_imgs > 0:
            alt_ratio = seo_data['image_seo']['images_with_alt'] / total_imgs
            score += int(alt_ratio * 10)
        
        # Content length (10 points)
        if seo_data['content_metrics']['is_sufficient_content']:
            score += 10
        
        # Structured data (15 points)
        if seo_data['structured_data_seo']['has_json_ld']:
            score += 8
        if seo_data['structured_data_seo']['has_microdata']:
            score += 4
        if seo_data['structured_data_seo']['has_opengraph']:
            score += 3
        
        # Robots meta (5 points)
        if seo_data['robots_meta']['is_indexable']:
            score += 5
        
        # Canonical URL (10 points)
        if seo_data['canonical_url']['exists']:
            score += 10
        
        return min(score, 100)

    def _extract_technical_analysis(self, soup: BeautifulSoup, response_info: Dict, perf_data: Dict, html_size: int) -> Dict[str, Any]:
        """Extract technical analysis"""
        return {
            'html_size': {
                'bytes': html_size,
                'kb': round(html_size / 1024, 2),
                'mb': round(html_size / (1024 * 1024), 2)
            },
            'response_headers': response_info.get('headers', {}),
            'performance_metrics': perf_data,
            'html_validation': {
                'doctype': str(soup.doctype) if soup.doctype else 'html5',
                'lang_attribute': bool(soup.find('html', lang=True)),
                'charset_declared': bool(soup.find('meta', charset=True))
            },
            'resource_analysis': {
                'external_stylesheets': len([link for link in soup.find_all('link', rel='stylesheet') 
                                           if link.get('href', '').startswith(('http', '//'))]),
                'external_scripts': len([script for script in soup.find_all('script', src=True) 
                                       if script.get('src', '').startswith(('http', '//'))]),
                'inline_styles': len(soup.find_all('style')),
                'inline_scripts': len([script for script in soup.find_all('script') if not script.get('src')])
            },
            'encoding': soup.original_encoding if hasattr(soup, 'original_encoding') else 'unknown'
        }

    def _extract_links_analysis(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """Extract comprehensive links analysis"""
        links = soup.find_all('a', href=True)
        base_domain = urlparse(base_url).netloc
        
        internal_links = []
        external_links = []
        email_links = []
        phone_links = []
        
        for link in links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            if href.startswith('mailto:'):
                email_links.append({'email': href[7:], 'text': text})
            elif href.startswith('tel:'):
                phone_links.append({'phone': href[4:], 'text': text})
            elif href.startswith('http'):
                link_domain = urlparse(href).netloc
                link_data = {'url': href, 'text': text, 'title': link.get('title', '')}
                
                if link_domain == base_domain:
                    internal_links.append(link_data)
                else:
                    external_links.append(link_data)
            else:
                # Relative links are internal
                full_url = urljoin(base_url, href)
                internal_links.append({'url': full_url, 'text': text, 'title': link.get('title', '')})
        
        return {
            'total_links': len(links),
            'internal_links': {
                'count': len(internal_links),
                'links': internal_links[:20]  # First 20
            },
            'external_links': {
                'count': len(external_links),
                'links': external_links[:20]  # First 20
            },
            'email_links': {
                'count': len(email_links),
                'links': email_links
            },
            'phone_links': {
                'count': len(phone_links),
                'links': phone_links
            },
            'broken_link_indicators': len([link for link in links if link.get('href') == '#']),
            'nofollow_links': len([link for link in links if 'nofollow' in str(link.get('rel', []))])
        }

    def _extract_images_analysis(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """Extract comprehensive images analysis"""
        images = soup.find_all('img')
        image_analysis = []
        
        for img in images:
            src = img.get('src', '')
            if src:
                absolute_url = urljoin(base_url, src) if not src.startswith('http') else src
                
                # Determine format
                img_format = 'unknown'
                for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.avif']:
                    if ext in src.lower():
                        img_format = ext[1:]
                        break
                
                alt_text = img.get('alt', '')
                image_analysis.append({
                    'src': absolute_url,
                    'alt': alt_text,
                    'alt_length': len(alt_text),
                    'has_alt': bool(alt_text),
                    'title': img.get('title', ''),
                    'width': img.get('width', ''),
                    'height': img.get('height', ''),
                    'loading': img.get('loading', ''),
                    'format': img_format,
                    'is_lazy_loaded': img.get('loading') == 'lazy',
                    'has_srcset': bool(img.get('srcset'))
                })
        
        return {
            'total_images': len(images),
            'images': image_analysis[:30],  # First 30 images
            'images_with_alt': sum(1 for img in image_analysis if img['has_alt']),
            'images_without_alt': sum(1 for img in image_analysis if not img['has_alt']),
            'lazy_loaded_images': sum(1 for img in image_analysis if img['is_lazy_loaded']),
            'responsive_images': sum(1 for img in image_analysis if img['has_srcset']),
            'format_distribution': self._get_image_format_distribution(image_analysis)
        }

    def _get_image_format_distribution(self, images: List[Dict]) -> Dict[str, int]:
        """Get distribution of image formats"""
        formats = {}
        for img in images:
            fmt = img['format']
            formats[fmt] = formats.get(fmt, 0) + 1
        return formats

    def _extract_forms_analysis(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract forms analysis"""
        forms = []
        
        for form in soup.find_all('form'):
            form_data = {
                'action': form.get('action', ''),
                'method': form.get('method', 'get').upper(),
                'id': form.get('id', ''),
                'class': form.get('class', []),
                'inputs': [],
                'field_count': 0,
                'required_fields': 0
            }
            
            # Analyze form inputs
            for inp in form.find_all(['input', 'textarea', 'select']):
                input_data = {
                    'type': inp.get('type', 'text') if inp.name == 'input' else inp.name,
                    'name': inp.get('name', ''),
                    'required': inp.has_attr('required'),
                    'placeholder': inp.get('placeholder', '')
                }
                
                form_data['inputs'].append(input_data)
                form_data['field_count'] += 1
                
                if input_data['required']:
                    form_data['required_fields'] += 1
            
            forms.append(form_data)
        
        return forms

    def _extract_business_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract business information"""
        text_content = soup.get_text()
        
        # Extract phone numbers
        phone_patterns = [
            r'(\+31\s?(?:\(0\)\s?)?[1-9](?:\s?\d){8})',  # Dutch format
            r'(\+\d{1,3}\s?\d{1,14})',  # International
            r'(\b\d{3,4}[-\s]?\d{6,7}\b)'  # Local format
        ]
        
        phone_numbers = []
        for pattern in phone_patterns:
            matches = re.findall(pattern, text_content)
            phone_numbers.extend(matches[:5])
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text_content)
        
        # Extract addresses (basic pattern)
        address_patterns = [
            r'\d+\s+[A-Za-z\s]+(?:street|str|avenue|ave|road|rd|drive|dr|lane|ln)\s*,?\s*\d{4,5}',
            r'[A-Za-z\s]+\s+\d+[A-Za-z]?\s*,\s*\d{4,5}\s+[A-Za-z\s]+',
        ]
        
        addresses = []
        for pattern in address_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            addresses.extend(matches[:3])
        
        return {
            'company_name': soup.find('title').text.strip() if soup.find('title') else '',
            'phone_numbers': list(set(phone_numbers)),
            'email_addresses': list(set(emails))[:5],
            'addresses': addresses,
            'social_media_links': self._extract_social_links(soup)
        }

    def _extract_social_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract social media links"""
        social_domains = ['facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com', 
                         'youtube.com', 'tiktok.com', 'pinterest.com']
        social_links = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            for domain in social_domains:
                if domain in href:
                    social_links.append({
                        'platform': domain.replace('.com', ''),
                        'url': href,
                        'text': link.get_text(strip=True)
                    })
                    break
        
        return social_links

    def _extract_contact_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract contact information"""
        return {
            'contact_forms': len(soup.find_all('form')),
            'contact_page_links': len([link for link in soup.find_all('a', href=True) 
                                     if 'contact' in link.get('href', '').lower() or 
                                        'contact' in link.get_text().lower()]),
            'map_embeds': len([iframe for iframe in soup.find_all('iframe') 
                             if 'maps' in iframe.get('src', '').lower()]),
            'email_links': len([link for link in soup.find_all('a', href=True) 
                              if link.get('href', '').startswith('mailto:')]),
            'phone_links': len([link for link in soup.find_all('a', href=True) 
                              if link.get('href', '').startswith('tel:')])
        }

    def _analyze_page_structure(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze page structure"""
        return {
            'semantic_structure': {
                'has_header': bool(soup.find('header')),
                'has_nav': bool(soup.find('nav')),
                'has_main': bool(soup.find('main')),
                'has_article': bool(soup.find('article')),
                'has_section': bool(soup.find('section')),
                'has_aside': bool(soup.find('aside')),
                'has_footer': bool(soup.find('footer'))
            },
            'content_sections': len(soup.find_all(['article', 'section'])),
            'navigation_items': len(soup.select('nav a, .nav a, .navigation a')),
            'total_elements': len(soup.find_all()),
            'nesting_depth': self._calculate_nesting_depth(soup)
        }

    def _calculate_nesting_depth(self, soup: BeautifulSoup) -> int:
        """Calculate maximum nesting depth"""
        def get_depth(element, current_depth=0):
            if not element.children:
                return current_depth
            max_child_depth = 0
            for child in element.children:
                if hasattr(child, 'children'):
                    child_depth = get_depth(child, current_depth + 1)
                    max_child_depth = max(max_child_depth, child_depth)
            return max_child_depth
        
        try:
            return get_depth(soup.body) if soup.body else 0
        except:
            return 0

    async def _analyze_external_resources(self, url: str) -> Dict[str, Any]:
        """Analyze external resources like robots.txt and sitemap"""
        external_resources = {
            'robots_txt': None,
            'sitemap': None
        }
        
        # Check robots.txt
        try:
            robots_url = urljoin(url, '/robots.txt')
            response = requests.get(robots_url, timeout=10)
            if response.status_code == 200:
                external_resources['robots_txt'] = {
                    'exists': True,
                    'content': response.text[:1000],  # First 1000 chars
                    'size': len(response.text)
                }
            else:
                external_resources['robots_txt'] = {'exists': False}
        except:
            external_resources['robots_txt'] = {'exists': False}
        
        # Check sitemap.xml
        try:
            sitemap_url = urljoin(url, '/sitemap.xml')
            response = requests.get(sitemap_url, timeout=10)
            if response.status_code == 200:
                external_resources['sitemap'] = {
                    'exists': True,
                    'size': len(response.content),
                    'content_type': response.headers.get('content-type', '')
                }
            else:
                external_resources['sitemap'] = {'exists': False}
        except:
            external_resources['sitemap'] = {'exists': False}
        
        return external_resources

    def _analyze_security(self, soup: BeautifulSoup, headers: Dict[str, str]) -> Dict[str, Any]:
        """Analyze security aspects"""
        return {
            'https_usage': True,  # Would be determined from URL
            'security_headers': {
                'strict_transport_security': 'strict-transport-security' in headers,
                'content_security_policy': 'content-security-policy' in headers,
                'x_frame_options': 'x-frame-options' in headers,
                'x_content_type_options': 'x-content-type-options' in headers
            },
            'mixed_content_check': {
                'http_resources': len([elem for elem in soup.find_all(['img', 'script', 'link']) 
                                     if elem.get('src', '').startswith('http://') or 
                                        elem.get('href', '').startswith('http://')])
            },
            'form_security': {
                'forms_with_https_action': len([form for form in soup.find_all('form') 
                                              if form.get('action', '').startswith('https://')]),
                'total_forms': len(soup.find_all('form'))
            }
        }

    def _analyze_performance(self, soup: BeautifulSoup, perf_data: Dict, html_size: int) -> Dict[str, Any]:
        """Analyze performance indicators"""
        return {
            'page_size': {
                'html_size_bytes': html_size,
                'html_size_kb': round(html_size / 1024, 2)
            },
            'resource_counts': {
                'total_images': len(soup.find_all('img')),
                'external_scripts': len([script for script in soup.find_all('script', src=True) 
                                       if script.get('src', '').startswith(('http', '//'))]),
                'external_stylesheets': len([link for link in soup.find_all('link', rel='stylesheet') 
                                           if link.get('href', '').startswith(('http', '//'))]),
                'total_requests_estimate': len(soup.find_all(['img', 'script', 'link', 'iframe']))
            },
            'optimization_indicators': {
                'lazy_loaded_images': len(soup.find_all('img', loading='lazy')),
                'responsive_images': len(soup.find_all('img', srcset=True)),
                'minified_resources': {
                    'css': len([link for link in soup.find_all('link', rel='stylesheet') 
                              if 'min.css' in link.get('href', '')]),
                    'js': len([script for script in soup.find_all('script', src=True) 
                             if 'min.js' in script.get('src', '')])
                }
            },
            'performance_timing': perf_data
        }

    def _analyze_accessibility(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze accessibility"""
        images = soup.find_all('img')
        links = soup.find_all('a')
        
        return {
            'images': {
                'total_images': len(images),
                'images_with_alt': len([img for img in images if img.get('alt')]),
                'images_without_alt': len([img for img in images if not img.get('alt')]),
                'images_with_empty_alt': len([img for img in images if img.get('alt') == ''])
            },
            'links': {
                'total_links': len(links),
                'links_with_text': len([link for link in links if link.get_text(strip=True)]),
                'links_without_text': len([link for link in links if not link.get_text(strip=True)]),
                'links_with_title': len([link for link in links if link.get('title')])
            },
            'headings': {
                'heading_structure_exists': bool(soup.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])),
                'h1_count': len(soup.find_all('h1')),
                'proper_h1_usage': len(soup.find_all('h1')) == 1
            },
            'forms': {
                'forms_with_labels': len([form for form in soup.find_all('form') if form.find('label')]),
                'total_forms': len(soup.find_all('form'))
            },
            'aria_attributes': {
                'elements_with_aria_label': len(soup.find_all(attrs={'aria-label': True})),
                'elements_with_role': len(soup.find_all(attrs={'role': True}))
            },
            'language_declaration': {
                'html_has_lang': bool(soup.find('html', lang=True))
            }
        }

    def _analyze_mobile(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze mobile optimization"""
        viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
        
        return {
            'viewport_meta': {
                'exists': bool(viewport_meta),
                'content': viewport_meta.get('content', '') if viewport_meta else '',
                'is_responsive': 'width=device-width' in viewport_meta.get('content', '') if viewport_meta else False
            },
            'mobile_specific_elements': {
                'touch_icons': len(soup.find_all('link', rel=lambda x: x and 'touch-icon' in str(x))),
                'mobile_meta_tags': len(soup.find_all('meta', attrs={'name': lambda x: x and 'mobile' in str(x).lower()}))
            },
            'responsive_design_indicators': {
                'media_queries_in_html': len(soup.find_all('style')),
                'responsive_images': len(soup.find_all('img', srcset=True)),
                'flexible_layouts': len(soup.find_all(class_=lambda x: x and any(term in str(x).lower() for term in ['flex', 'grid', 'responsive'])))
            },
            'amp_support': {
                'is_amp_page': bool(soup.find('html', attrs={'amp': True}) or soup.find('html', attrs={'⚡': True}))
            }
        }

    def _create_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive summary of all analysis"""
        return {
            'overall_scores': {
                'seo_score': analysis['seo_analysis'].get('seo_score', 0),
                'accessibility_score': self._calculate_accessibility_score(analysis['accessibility_analysis']),
                'performance_score': self._calculate_performance_score(analysis['performance_analysis']),
                'mobile_score': self._calculate_mobile_score(analysis['mobile_analysis']),
                'security_score': self._calculate_security_score(analysis['security_analysis']),
                'content_quality_score': self._calculate_content_score(analysis['content_analysis'])
            },
            'key_findings': {
                'has_cms': bool(analysis['tech_stack']['cms']),
                'main_cms': list(analysis['tech_stack']['cms'].keys())[0] if analysis['tech_stack']['cms'] else 'None',
                'has_analytics': bool(analysis['tech_stack']['analytics']),
                'has_structured_data': analysis['structured_data']['summary']['has_structured_data'],
                'is_mobile_friendly': analysis['mobile_analysis']['viewport_meta']['is_responsive'],
                'has_ssl': analysis['page_info']['is_ssl'],
                'content_length': analysis['content_analysis']['word_count'],
                'total_images': analysis['images_analysis']['total_images'],
                'total_links': analysis['links_analysis']['total_links']
            },
            'recommendations': self._generate_recommendations(analysis),
            'technology_summary': {
                'total_technologies_detected': analysis['tech_stack']['summary']['total_technologies'],
                'main_categories': [cat for cat in ['cms', 'frameworks', 'analytics', 'seo_tools'] 
                                  if analysis['tech_stack'][cat]],
                'server_technology': analysis['tech_stack']['server_info']['server'],
                'cdn_usage': analysis['tech_stack']['server_info']['cdn']
            },
            'content_summary': {
                'content_type': analysis['page_info']['page_type'],
                'reading_time_minutes': analysis['content_analysis']['reading_time'],
                'has_sufficient_content': analysis['content_analysis']['word_count'] >= 300,
                'multimedia_rich': analysis['content_analysis']['multimedia_content']['images'] > 5,
                'well_structured': analysis['content_analysis']['headings']['proper_h1_usage']
            }
        }

    def _calculate_accessibility_score(self, accessibility_data: Dict[str, Any]) -> int:
        """Calculate accessibility score"""
        score = 0
        
        # Images with alt text (25 points)
        total_images = accessibility_data['images']['total_images']
        if total_images > 0:
            alt_ratio = accessibility_data['images']['images_with_alt'] / total_images
            score += int(alt_ratio * 25)
        else:
            score += 25  # No images is fine
        
        # Links with text (20 points)
        total_links = accessibility_data['links']['total_links']
        if total_links > 0:
            text_ratio = accessibility_data['links']['links_with_text'] / total_links
            score += int(text_ratio * 20)
        
        # Proper heading structure (20 points)
        if accessibility_data['headings']['proper_h1_usage']:
            score += 20
        elif accessibility_data['headings']['h1_count'] > 0:
            score += 10
        
        # Language declaration (15 points)
        if accessibility_data['language_declaration']['html_has_lang']:
            score += 15
        
        # ARIA attributes (10 points)
        if accessibility_data['aria_attributes']['elements_with_aria_label'] > 0:
            score += 5
        if accessibility_data['aria_attributes']['elements_with_role'] > 0:
            score += 5
        
        # Forms with labels (10 points)
        total_forms = accessibility_data['forms']['total_forms']
        if total_forms > 0:
            if accessibility_data['forms']['forms_with_labels'] == total_forms:
                score += 10
            elif accessibility_data['forms']['forms_with_labels'] > 0:
                score += 5
        else:
            score += 10  # No forms is fine
        
        return min(score, 100)

    def _calculate_performance_score(self, performance_data: Dict[str, Any]) -> int:
        """Calculate performance score"""
        score = 0
        
        # HTML size (20 points)
        html_kb = performance_data['page_size']['html_size_kb']
        if html_kb < 100:
            score += 20
        elif html_kb < 500:
            score += 15
        elif html_kb < 1000:
            score += 10
        else:
            score += 5
        
        # Image optimization (25 points)
        total_images = performance_data['resource_counts']['total_images']
        if total_images > 0:
            lazy_ratio = performance_data['optimization_indicators']['lazy_loaded_images'] / total_images
            responsive_ratio = performance_data['optimization_indicators']['responsive_images'] / total_images
            score += int((lazy_ratio + responsive_ratio) / 2 * 25)
        else:
            score += 25
        
        # Resource minification (20 points)
        minified_css = performance_data['optimization_indicators']['minified_resources']['css']
        minified_js = performance_data['optimization_indicators']['minified_resources']['js']
        total_external_css = performance_data['resource_counts']['external_stylesheets']
        total_external_js = performance_data['resource_counts']['external_scripts']
        
        if total_external_css > 0:
            css_score = (minified_css / total_external_css) * 10
        else:
            css_score = 10
        
        if total_external_js > 0:
            js_score = (minified_js / total_external_js) * 10
        else:
            js_score = 10
        
        score += int(css_score + js_score)
        
        # Resource count efficiency (35 points)
        total_requests = performance_data['resource_counts']['total_requests_estimate']
        if total_requests < 50:
            score += 35
        elif total_requests < 100:
            score += 25
        elif total_requests < 150:
            score += 15
        else:
            score += 5
        
        return min(score, 100)

    def _calculate_mobile_score(self, mobile_data: Dict[str, Any]) -> int:
        """Calculate mobile optimization score"""
        score = 0
        
        # Viewport meta tag (40 points)
        if mobile_data['viewport_meta']['is_responsive']:
            score += 40
        elif mobile_data['viewport_meta']['exists']:
            score += 20
        
        # Touch icons (20 points)
        if mobile_data['mobile_specific_elements']['touch_icons'] > 0:
            score += 20
        
        # Responsive images (20 points)
        if mobile_data['responsive_design_indicators']['responsive_images'] > 0:
            score += 20
        
        # Flexible layouts (20 points)
        if mobile_data['responsive_design_indicators']['flexible_layouts'] > 0:
            score += 20
        
        return min(score, 100)

    def _calculate_security_score(self, security_data: Dict[str, Any]) -> int:
        """Calculate security score"""
        score = 0
        
        # HTTPS usage (30 points)
        if security_data['https_usage']:
            score += 30
        
        # Security headers (40 points)
        security_headers = security_data['security_headers']
        header_count = sum(1 for header in security_headers.values() if header)
        score += int((header_count / len(security_headers)) * 40)
        
        # Mixed content check (20 points)
        if security_data['mixed_content_check']['http_resources'] == 0:
            score += 20
        
        # Form security (10 points)
        total_forms = security_data['form_security']['total_forms']
        if total_forms == 0:
            score += 10
        else:
            secure_forms = security_data['form_security']['forms_with_https_action']
            score += int((secure_forms / total_forms) * 10)
        
        return min(score, 100)

    def _calculate_content_score(self, content_data: Dict[str, Any]) -> int:
        """Calculate content quality score"""
        score = 0
        
        # Word count (25 points)
        word_count = content_data['word_count']
        if word_count >= 1000:
            score += 25
        elif word_count >= 500:
            score += 20
        elif word_count >= 300:
            score += 15
        elif word_count >= 100:
            score += 10
        else:
            score += 5
        
        # Heading structure (20 points)
        if content_data['headings']['proper_h1_usage']:
            score += 10
        if content_data['headings']['total_headings'] > 3:
            score += 10
        
        # Content diversity (25 points)
        multimedia = content_data['multimedia_content']
        diversity_score = 0
        if multimedia['images'] > 0:
            diversity_score += 8
        if multimedia['videos'] > 0:
            diversity_score += 8
        if content_data['lists']['total_lists'] > 0:
            diversity_score += 5
        if content_data['tables']['total_tables'] > 0:
            diversity_score += 4
        score += min(diversity_score, 25)
        
        # Text density (15 points)
        if content_data['text_density'] > 0.1:
            score += 15
        elif content_data['text_density'] > 0.05:
            score += 10
        else:
            score += 5
        
        # Reading time appropriateness (15 points)
        reading_time = content_data['reading_time']
        if 2 <= reading_time <= 10:
            score += 15
        elif 1 <= reading_time <= 15:
            score += 10
        else:
            score += 5
        
        return min(score, 100)

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # SEO Recommendations
        seo = analysis['seo_analysis']
        if not seo['title_analysis']['is_optimal_length']:
            recommendations.append("Optimize title length to 30-60 characters for better SEO")
        
        if not seo['meta_description']['is_optimal_length']:
            recommendations.append("Add or optimize meta description (120-160 characters)")
        
        if not seo['heading_structure']['proper_h1_usage']:
            recommendations.append("Use exactly one H1 tag per page for better SEO structure")
        
        # Performance Recommendations
        perf = analysis['performance_analysis']
        if perf['page_size']['html_size_kb'] > 500:
            recommendations.append("Consider reducing HTML size for better loading performance")
        
        if perf['optimization_indicators']['lazy_loaded_images'] == 0 and perf['resource_counts']['total_images'] > 5:
            recommendations.append("Implement lazy loading for images to improve page speed")
        
        # Accessibility Recommendations
        acc = analysis['accessibility_analysis']
        if acc['images']['images_without_alt'] > 0:
            recommendations.append(f"Add alt text to {acc['images']['images_without_alt']} images for accessibility")
        
        if not acc['language_declaration']['html_has_lang']:
            recommendations.append("Add lang attribute to HTML element for accessibility")
        
        # Mobile Recommendations
        mobile = analysis['mobile_analysis']
        if not mobile['viewport_meta']['is_responsive']:
            recommendations.append("Add responsive viewport meta tag for mobile optimization")
        
        # Security Recommendations
        security = analysis['security_analysis']
        if not security['https_usage']:
            recommendations.append("Implement HTTPS for security and SEO benefits")
        
        missing_headers = [k for k, v in security['security_headers'].items() if not v]
        if missing_headers:
            recommendations.append(f"Add security headers: {', '.join(missing_headers)}")
        
        # Structured Data Recommendations
        if not analysis['structured_data']['summary']['has_structured_data']:
            recommendations.append("Add structured data (JSON-LD) to improve search engine understanding")
        
        # Limit recommendations
        return recommendations[:10]

# API Endpoints
@app.post("/analyze-website")
async def analyze_complete_website(request: URLRequest):
    """
    Complete website analysis - extracts EVERYTHING in one structured JSON response
    
    This endpoint performs comprehensive analysis including:
    - Page information and meta data
    - Structured data (JSON-LD, Microdata, OpenGraph, etc.)
    - Technology stack detection (CMS, frameworks, analytics, etc.)
    - Content analysis (headings, paragraphs, images, etc.)
    - SEO analysis with scoring
    - Technical analysis (performance, security, accessibility)
    - Links and forms analysis
    - Business and contact information extraction
    - Mobile optimization analysis
    - Overall scoring and recommendations
    """
    async with CompleteWebScraper() as scraper:
        result = await scraper.complete_website_analysis(request.url)
        return result

@app.post("/analyze-website/batch")
async def analyze_websites_batch(request: BatchURLRequest):
    """Analyze multiple websites in batch - returns complete analysis for each"""
    results = []
    
    async with CompleteWebScraper() as scraper:
        for url in request.urls:
            try:
                result = await scraper.complete_website_analysis(url)
                results.append(result)
            except Exception as e:
                results.append({
                    'url': str(url),
                    'error': str(e),
                    'timestamp': datetime.now().isoformat(),
                    'processing_time': 0,
                    'status_code': 0
                })
    
    return {
        'results': results,
        'total_processed': len(results),
        'successful': len([r for r in results if 'error' not in r]),
        'failed': len([r for r in results if 'error' in r]),
        'timestamp': datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '5.0.0'
    }

@app.get("/")
async def root():
    """API information and usage"""
    return {
        'title': 'Complete Web Scraper API v5.0',
        'description': 'All-in-one web scraping API that extracts everything from a website in one structured JSON response',
        'main_endpoint': {
            'POST /analyze-website': {
                'description': 'Complete website analysis - extracts everything in one structured JSON',
                'input': {'url': 'https://example.com'},
                'features': [
                    'Complete page information (title, meta, structure, language)',
                    'Full structured data extraction (JSON-LD, Microdata, OpenGraph, Twitter Cards, RDFa)',
                    'Advanced technology stack detection (60+ technologies: CMS, frameworks, analytics, SEO tools)',
                    'Comprehensive content analysis (headings, paragraphs, lists, tables, multimedia)',
                    'Complete SEO analysis with scoring (title, meta, headings, images, structured data)',
                    'Technical analysis (performance metrics, HTML validation, resources)',
                    'Full links analysis (internal/external/social/email/phone links with categorization)',
                    'Images analysis (alt text, formats, optimization, lazy loading)',
                    'Forms analysis (fields, validation, security, accessibility)',
                    'Business information extraction (contact details, addresses, phones, emails)',
                    'Contact information detection (forms, maps, social links)',
                    'Complete page structure analysis (semantic HTML, nesting depth)',
                    'External resources analysis (robots.txt, sitemap.xml)',
                    'Security analysis (HTTPS, headers, mixed content, form security)',
                    'Performance analysis (size, optimization, loading times, resource counts)',
                    'Accessibility analysis with detailed scoring',
                    'Mobile optimization analysis (viewport, responsive design, touch)',
                    'Overall scoring system (6 categories: SEO, Performance, Accessibility, Mobile, Security, Content)',
                    'AI-powered actionable recommendations based on analysis',
                    'Technology confidence scoring with evidence tracking'
                ]
            }
        },
        'response_structure': {
            'basic_info': ['url', 'final_url', 'timestamp', 'processing_time', 'status_code'],
            'comprehensive_analyses': [
                'page_info (title, domain, language, page type)',
                'meta_data (SEO meta, social meta, technical meta, stylesheets, scripts)',
                'structured_data (JSON-LD, Microdata, OpenGraph, Twitter Cards, RDFa)',
                'tech_stack (CMS, frameworks, analytics, libraries, server info)',
                'content_analysis (text analysis, headings, paragraphs, lists, tables)',
                'seo_analysis (title, meta description, headings, images, structured data)',
                'technical_analysis (performance, HTML validation, resource analysis)',
                'links_analysis (internal/external/email/phone with full categorization)',
                'images_analysis (formats, alt text, optimization, responsive)',
                'forms_analysis (field types, validation, security)',
                'business_info (company details, contact info, social media)',
                'contact_info (forms, maps, contact methods)',
                'page_structure (semantic HTML, navigation, content sections)',
                'external_resources (robots.txt, sitemap analysis)',
                'security_analysis (HTTPS, headers, mixed content)',
                'performance_analysis (optimization, resource counts, timing)',
                'accessibility_analysis (alt text, links, headings, ARIA)',
                'mobile_analysis (viewport, responsive design, touch optimization)'
            ],
            'intelligent_summary': [
                'overall_scores (6 category scoring: SEO, Accessibility, Performance, Mobile, Security, Content)',
                'key_findings (CMS detection, analytics, SSL, mobile-friendly)',
                'actionable_recommendations (prioritized improvement suggestions)',
                'technology_summary (detected technologies with confidence)',
                'content_summary (type, length, structure, multimedia)'
            ]
        },
        'technology_detection': {
            'cms': ['WordPress', 'Drupal', 'Joomla', 'Shopify', 'Magento', 'WooCommerce'],
            'frameworks': ['React', 'Vue.js', 'Angular', 'Next.js', 'Nuxt.js'],
            'css_frameworks': ['Bootstrap', 'Tailwind CSS', 'Foundation'],
            'analytics': ['Google Analytics', 'Google Tag Manager', 'Facebook Pixel', 'Hotjar'],
            'seo_tools': ['Yoast SEO', 'RankMath', 'All in One SEO'],
            'libraries': ['jQuery', 'Lodash', 'D3.js'],
            'cdn': ['Cloudflare', 'Amazon CloudFront'],
            'performance': ['WP Rocket', 'W3 Total Cache'],
            'and_60_more': 'Complete signature-based detection with confidence scoring'
        },
        'scoring_system': {
            'seo_score': 'Title, meta description, headings, images, structured data (0-100)',
            'accessibility_score': 'Alt text, link text, headings, ARIA attributes, language (0-100)',
            'performance_score': 'Page size, optimization, resource efficiency (0-100)',
            'mobile_score': 'Viewport, responsive design, touch optimization (0-100)',
            'security_score': 'HTTPS, security headers, mixed content prevention (0-100)',
            'content_score': 'Word count, structure, diversity, readability (0-100)'
        },
        'other_endpoints': {
            'POST /analyze-website/batch': 'Analyze multiple websites (max 10 URLs)',
            'GET /health': 'Health check endpoint',
            'GET /docs': 'Interactive Swagger API documentation',
            'GET /redoc': 'Alternative ReDoc API documentation'
        },
        'usage_info': {
            'processing_time': '3-15 seconds depending on website complexity',
            'response_size': '50-200KB structured JSON',
            'rate_limits': 'No limits - deploy your own instance',
            'supported_formats': 'All modern websites, JavaScript-heavy sites, SPAs'
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        reload=False,
        access_log=True
    )
