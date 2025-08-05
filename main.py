from fastapi import FastAPI, HTTPException, BackgroundTasks
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
import hashlib
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Advanced Web Scraper API",
    description="Complete web scraping API with structured data extraction and tech stack detection",
    version="3.0.0",
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

class StructuredDataResponse(BaseModel):
    url: str
    timestamp: str
    json_ld: List[Dict[str, Any]]
    microdata: List[Dict[str, Any]]
    opengraph: Dict[str, str]
    twitter_cards: Dict[str, str]
    schema_types: List[str]
    rdfa: List[Dict[str, Any]]
    meta_tags: Dict[str, str]
    summary: Dict[str, Any]

class TechStackResponse(BaseModel):
    url: str
    timestamp: str
    cms: Dict[str, Any]
    frameworks: Dict[str, Any]
    analytics: Dict[str, Any]
    seo_tools: Dict[str, Any]
    libraries: Dict[str, Any]
    hosting: Dict[str, Any]
    security: Dict[str, Any]
    performance_tools: Dict[str, Any]
    cdn: Dict[str, Any]
    server_info: Dict[str, Any]
    summary: Dict[str, Any]

@dataclass
class TechSignature:
    name: str
    category: str
    patterns: List[str]
    confidence_indicators: List[str]
    version_patterns: List[str] = None

class AdvancedWebScraper:
    def __init__(self):
        self.browser = None
        self.context = None
        self.playwright = None
        
        # Initialize tech stack signatures
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
                patterns=[
                    r'/wp-content/',
                    r'/wp-includes/',
                    r'/wp-admin/',
                    r'wp-json',
                    r'wordpress'
                ],
                confidence_indicators=[
                    'generator.*wordpress',
                    'wp-content',
                    'wp-includes',
                    'rest_route',
                    'wlwmanifest'
                ],
                version_patterns=[r'WordPress (\d+\.\d+(?:\.\d+)?)']
            ),
            TechSignature(
                name="Drupal",
                category="cms",
                patterns=[
                    r'/sites/default/',
                    r'/modules/',
                    r'/themes/',
                    r'drupal',
                    r'Drupal.settings'
                ],
                confidence_indicators=[
                    'generator.*drupal',
                    'sites/default',
                    'Drupal.settings',
                    'drupal.js'
                ],
                version_patterns=[r'Drupal (\d+\.\d+(?:\.\d+)?)']
            ),
            TechSignature(
                name="Joomla",
                category="cms",
                patterns=[
                    r'/components/',
                    r'/modules/',
                    r'/templates/',
                    r'joomla',
                    r'option=com_'
                ],
                confidence_indicators=[
                    'generator.*joomla',
                    'option=com_',
                    'components/',
                    'joomla.js'
                ],
                version_patterns=[r'Joomla! (\d+\.\d+(?:\.\d+)?)']
            ),
            TechSignature(
                name="Shopify",
                category="cms",
                patterns=[
                    r'shopify',
                    r'myshopify.com',
                    r'cdn.shopify.com',
                    r'Shopify.theme'
                ],
                confidence_indicators=[
                    'Shopify.theme',
                    'shopify-analytics',
                    'myshopify.com',
                    'cdn.shopify.com'
                ]
            ),
            TechSignature(
                name="Magento",
                category="cms",
                patterns=[
                    r'magento',
                    r'/skin/frontend/',
                    r'/js/mage/',
                    r'Mage.Cookies'
                ],
                confidence_indicators=[
                    'Mage.Cookies',
                    'skin/frontend',
                    'js/mage',
                    'magento'
                ]
            ),
            TechSignature(
                name="WooCommerce",
                category="cms",
                patterns=[
                    r'woocommerce',
                    r'wc-',
                    r'wp-content/plugins/woocommerce'
                ],
                confidence_indicators=[
                    'woocommerce',
                    'wc-ajax',
                    'plugins/woocommerce'
                ]
            ),
            
            # JavaScript Frameworks
            TechSignature(
                name="React",
                category="framework",
                patterns=[
                    r'react',
                    r'_react',
                    r'React\.',
                    r'__REACT_DEVTOOLS_'
                ],
                confidence_indicators=[
                    'data-reactroot',
                    '__REACT_DEVTOOLS_',
                    'React.',
                    '_react'
                ]
            ),
            TechSignature(
                name="Vue.js",
                category="framework",
                patterns=[
                    r'vue',
                    r'Vue\.',
                    r'__VUE__',
                    r'v-'
                ],
                confidence_indicators=[
                    '__VUE__',
                    'Vue.',
                    'data-v-',
                    'vue.js'
                ],
                version_patterns=[r'Vue\.js v(\d+\.\d+\.\d+)']
            ),
            TechSignature(
                name="Angular",
                category="framework",
                patterns=[
                    r'angular',
                    r'ng-',
                    r'Angular\.',
                    r'__ng'
                ],
                confidence_indicators=[
                    'ng-version',
                    'ng-app',
                    'angular.js',
                    '_angular'
                ]
            ),
            TechSignature(
                name="Next.js",
                category="framework",
                patterns=[
                    r'next\.js',
                    r'_next/',
                    r'__NEXT_DATA__',
                    r'next-route'
                ],
                confidence_indicators=[
                    '__NEXT_DATA__',
                    '_next/',
                    'next-route'
                ]
            ),
            TechSignature(
                name="Nuxt.js",
                category="framework",
                patterns=[
                    r'nuxt',
                    r'_nuxt/',
                    r'__NUXT__'
                ],
                confidence_indicators=[
                    '__NUXT__',
                    '_nuxt/',
                    'nuxt.js'
                ]
            ),
            
            # CSS Frameworks
            TechSignature(
                name="Bootstrap",
                category="css_framework",
                patterns=[
                    r'bootstrap',
                    r'btn-',
                    r'col-',
                    r'container-'
                ],
                confidence_indicators=[
                    'bootstrap.css',
                    'bootstrap.min.css',
                    'btn-primary',
                    'container-fluid'
                ],
                version_patterns=[r'Bootstrap v(\d+\.\d+\.\d+)']
            ),
            TechSignature(
                name="Tailwind CSS",
                category="css_framework",
                patterns=[
                    r'tailwind',
                    r'tw-',
                    r'bg-\w+-\d+',
                    r'text-\w+-\d+'
                ],
                confidence_indicators=[
                    'tailwindcss',
                    'bg-blue-500',
                    'text-gray-900',
                    'flex-col'
                ]
            ),
            TechSignature(
                name="Foundation",
                category="css_framework",
                patterns=[
                    r'foundation',
                    r'grid-x',
                    r'cell-'
                ],
                confidence_indicators=[
                    'foundation.css',
                    'grid-x',
                    'foundation.js'
                ]
            ),
            
            # Analytics & Tracking
            TechSignature(
                name="Google Analytics",
                category="analytics",
                patterns=[
                    r'google-analytics',
                    r'gtag\(',
                    r'ga\(',
                    r'GoogleAnalyticsObject',
                    r'UA-\d+-\d+',
                    r'G-[A-Z0-9]+',
                    r'gtm\.js'
                ],
                confidence_indicators=[
                    'gtag(',
                    'GoogleAnalyticsObject',
                    'google-analytics.com',
                    'googletagmanager.com'
                ]
            ),
            TechSignature(
                name="Google Tag Manager",
                category="analytics",
                patterns=[
                    r'gtm\.js',
                    r'googletagmanager',
                    r'GTM-[A-Z0-9]+',
                    r'dataLayer'
                ],
                confidence_indicators=[
                    'googletagmanager.com',
                    'GTM-',
                    'dataLayer',
                    'gtm.js'
                ]
            ),
            TechSignature(
                name="Facebook Pixel",
                category="analytics",
                patterns=[
                    r'fbevents\.js',
                    r'facebook\.net',
                    r'connect\.facebook\.net',
                    r'fbq\('
                ],
                confidence_indicators=[
                    'fbevents.js',
                    'connect.facebook.net',
                    'fbq('
                ]
            ),
            TechSignature(
                name="Hotjar",
                category="analytics",
                patterns=[
                    r'hotjar',
                    r'static\.hotjar\.com',
                    r'hj\('
                ],
                confidence_indicators=[
                    'static.hotjar.com',
                    'hj(',
                    'hotjar'
                ]
            ),
            
            # SEO Tools
            TechSignature(
                name="Yoast SEO",
                category="seo",
                patterns=[
                    r'yoast',
                    r'wp-seo',
                    r'wpseo'
                ],
                confidence_indicators=[
                    'Yoast SEO',
                    'wp-seo',
                    'wpseo'
                ]
            ),
            TechSignature(
                name="RankMath",
                category="seo",
                patterns=[
                    r'rank-math',
                    r'rankmath'
                ],
                confidence_indicators=[
                    'rank-math',
                    'rankmath'
                ]
            ),
            TechSignature(
                name="All in One SEO",
                category="seo",
                patterns=[
                    r'aioseop',
                    r'all-in-one-seo'
                ],
                confidence_indicators=[
                    'aioseop',
                    'all-in-one-seo'
                ]
            ),
            
            # CDN & Hosting Technologies
            TechSignature(
                name="Cloudflare",
                category="cdn",
                patterns=[
                    r'cloudflare',
                    r'cf-ray',
                    r'__cfduid'
                ],
                confidence_indicators=[
                    'cf-ray',
                    'cloudflare',
                    '__cfduid'
                ]
            ),
            TechSignature(
                name="Amazon CloudFront",
                category="cdn",
                patterns=[
                    r'cloudfront',
                    r'amazonaws\.com'
                ],
                confidence_indicators=[
                    'cloudfront.net',
                    'amazonaws.com'
                ]
            ),
            
            # Security Tools
            TechSignature(
                name="Wordfence",
                category="security",
                patterns=[
                    r'wordfence',
                    r'wfwaf'
                ],
                confidence_indicators=[
                    'wordfence',
                    'wfwaf'
                ]
            ),
            
            # Performance Tools
            TechSignature(
                name="WP Rocket",
                category="performance",
                patterns=[
                    r'wp-rocket',
                    r'wpr_'
                ],
                confidence_indicators=[
                    'wp-rocket',
                    'wpr_'
                ]
            ),
            TechSignature(
                name="W3 Total Cache",
                category="performance",
                patterns=[
                    r'w3tc',
                    r'w3-total-cache'
                ],
                confidence_indicators=[
                    'w3tc',
                    'w3-total-cache'
                ]
            ),
            
            # Libraries
            TechSignature(
                name="jQuery",
                category="library",
                patterns=[
                    r'jquery',
                    r'jQuery',
                    r'\$\.'
                ],
                confidence_indicators=[
                    'jquery.js',
                    'jQuery',
                    'jquery.min.js'
                ],
                version_patterns=[r'jQuery v(\d+\.\d+\.\d+)']
            ),
            TechSignature(
                name="Lodash",
                category="library",
                patterns=[
                    r'lodash',
                    r'_\.'
                ],
                confidence_indicators=[
                    'lodash.js',
                    'lodash.min.js'
                ]
            ),
            TechSignature(
                name="D3.js",
                category="library",
                patterns=[
                    r'd3\.js',
                    r'd3\.min\.js',
                    r'd3\.'
                ],
                confidence_indicators=[
                    'd3.js',
                    'd3.min.js'
                ]
            )
        ]

    async def extract_structured_data(self, url: str) -> Dict[str, Any]:
        """Extract comprehensive structured data from a website"""
        try:
            page = await self.context.new_page()
            
            # Navigate to page
            response = await page.goto(str(url), wait_until='networkidle', timeout=30000)
            if not response:
                raise HTTPException(status_code=400, detail="Failed to load page")
            
            # Get page content
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract structured data
            structured_data = {
                'url': str(url),
                'timestamp': datetime.now().isoformat(),
                'json_ld': self._extract_json_ld(soup),
                'microdata': self._extract_microdata(soup),
                'opengraph': self._extract_opengraph(soup),
                'twitter_cards': self._extract_twitter_cards(soup),
                'rdfa': self._extract_rdfa(soup),
                'meta_tags': self._extract_meta_tags(soup),
                'schema_types': [],
                'summary': {}
            }
            
            # Collect all schema types
            schema_types = set()
            
            # From JSON-LD
            for json_data in structured_data['json_ld']:
                if isinstance(json_data, dict) and '@type' in json_data:
                    if isinstance(json_data['@type'], list):
                        schema_types.update(json_data['@type'])
                    else:
                        schema_types.add(json_data['@type'])
                elif isinstance(json_data, list):
                    for item in json_data:
                        if isinstance(item, dict) and '@type' in item:
                            if isinstance(item['@type'], list):
                                schema_types.update(item['@type'])
                            else:
                                schema_types.add(item['@type'])
            
            # From Microdata
            for micro_item in structured_data['microdata']:
                if micro_item.get('type'):
                    # Extract schema.org type name
                    schema_type = micro_item['type'].split('/')[-1] if '/' in micro_item['type'] else micro_item['type']
                    schema_types.add(schema_type)
            
            # From RDFa
            for rdfa_item in structured_data['rdfa']:
                if rdfa_item.get('typeof'):
                    schema_types.add(rdfa_item['typeof'])
            
            structured_data['schema_types'] = list(schema_types)
            
            # Create summary
            structured_data['summary'] = {
                'total_json_ld_items': len(structured_data['json_ld']),
                'total_microdata_items': len(structured_data['microdata']),
                'total_opengraph_tags': len(structured_data['opengraph']),
                'total_twitter_cards': len(structured_data['twitter_cards']),
                'total_rdfa_items': len(structured_data['rdfa']),
                'total_schema_types': len(structured_data['schema_types']),
                'has_structured_data': bool(structured_data['json_ld'] or structured_data['microdata'] or structured_data['rdfa']),
                'has_social_meta': bool(structured_data['opengraph'] or structured_data['twitter_cards']),
                'structured_data_score': self._calculate_structured_data_score(structured_data)
            }
            
            await page.close()
            return structured_data
            
        except Exception as e:
            logger.error(f"Error extracting structured data from {url}: {str(e)}")
            if 'page' in locals():
                await page.close()
            raise HTTPException(status_code=500, detail=f"Failed to extract structured data: {str(e)}")

    async def detect_tech_stack(self, url: str) -> Dict[str, Any]:
        """Detect comprehensive tech stack of a website"""
        try:
            page = await self.context.new_page()
            
            # Track response headers
            response_headers = {}
            def handle_response(response):
                if response.url == str(url):
                    response_headers.update(dict(response.headers))
            
            page.on('response', handle_response)
            
            # Navigate to page
            response = await page.goto(str(url), wait_until='networkidle', timeout=30000)
            if not response:
                raise HTTPException(status_code=400, detail="Failed to load page")
            
            # Get page content and additional data
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Get JavaScript context data
            js_data = await page.evaluate("""
                () => {
                    const data = {
                        window_vars: Object.keys(window).filter(key => 
                            !['chrome', 'webkit', 'moz'].some(prefix => key.toLowerCase().includes(prefix))
                        ).slice(0, 100),
                        frameworks: {},
                        libraries: {}
                    };
                    
                    // Check for common framework globals
                    if (window.React) data.frameworks.React = typeof window.React;
                    if (window.Vue) data.frameworks.Vue = window.Vue.version || 'detected';
                    if (window.angular) data.frameworks.Angular = window.angular.version || 'detected';
                    if (window.jQuery) data.libraries.jQuery = window.jQuery.fn.jquery || 'detected';
                    if (window._) data.libraries.Lodash = 'detected';
                    if (window.d3) data.libraries.D3 = window.d3.version || 'detected';
                    
                    return data;
                }
            """)
            
            # Analyze tech stack
            tech_stack = {
                'url': str(url),
                'timestamp': datetime.now().isoformat(),
                'cms': {},
                'frameworks': {},
                'analytics': {},
                'seo_tools': {},
                'libraries': {},
                'hosting': {},
                'security': {},
                'performance_tools': {},
                'cdn': {},
                'server_info': {},
                'summary': {}
            }
            
            # Detect technologies
            detected_techs = self._detect_technologies(html_content, response_headers, js_data)
            
            # Categorize detected technologies
            for tech_name, tech_info in detected_techs.items():
                category = tech_info['category']
                
                if category == 'cms':
                    tech_stack['cms'][tech_name] = tech_info
                elif category == 'framework':
                    tech_stack['frameworks'][tech_name] = tech_info
                elif category == 'analytics':
                    tech_stack['analytics'][tech_name] = tech_info
                elif category == 'seo':
                    tech_stack['seo_tools'][tech_name] = tech_info
                elif category == 'library':
                    tech_stack['libraries'][tech_name] = tech_info
                elif category == 'cdn':
                    tech_stack['cdn'][tech_name] = tech_info
                elif category == 'security':
                    tech_stack['security'][tech_name] = tech_info
                elif category == 'performance':
                    tech_stack['performance_tools'][tech_name] = tech_info
                elif category == 'css_framework':
                    if 'css_frameworks' not in tech_stack:
                        tech_stack['css_frameworks'] = {}
                    tech_stack['css_frameworks'][tech_name] = tech_info
            
            # Server information from headers
            tech_stack['server_info'] = self._extract_server_info(response_headers)
            
            # Create summary
            tech_stack['summary'] = {
                'total_technologies': len(detected_techs),
                'cms_detected': list(tech_stack['cms'].keys()),
                'frameworks_detected': list(tech_stack['frameworks'].keys()),
                'analytics_tools': list(tech_stack['analytics'].keys()),
                'seo_tools': list(tech_stack['seo_tools'].keys()),
                'main_server': tech_stack['server_info'].get('server', 'Unknown'),
                'has_cms': bool(tech_stack['cms']),
                'has_analytics': bool(tech_stack['analytics']),
                'technology_score': len(detected_techs)
            }
            
            await page.close()
            return tech_stack
            
        except Exception as e:
            logger.error(f"Error detecting tech stack for {url}: {str(e)}")
            if 'page' in locals():
                await page.close()
            raise HTTPException(status_code=500, detail=f"Failed to detect tech stack: {str(e)}")

    def _extract_json_ld(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract and parse JSON-LD structured data"""
        json_ld_data = []
        
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                if script.string:
                    json_str = script.string.strip()
                    # Handle common JSON-LD formatting issues
                    json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)  # Remove comments
                    json_str = re.sub(r'//.*$', '', json_str, flags=re.MULTILINE)  # Remove line comments
                    
                    data = json.loads(json_str)
                    if isinstance(data, list):
                        json_ld_data.extend(data)
                    else:
                        json_ld_data.append(data)
            except (json.JSONDecodeError, ValueError) as e:
                logger.debug(f"Failed to parse JSON-LD: {e}")
                continue
        
        return json_ld_data

    def _extract_microdata(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract microdata structured data"""
        microdata_items = []
        
        for elem in soup.find_all(attrs={'itemscope': True}):
            item = {
                'type': elem.get('itemtype', ''),
                'id': elem.get('itemid', ''),
                'properties': {}
            }
            
            # Extract properties
            for prop_elem in elem.find_all(attrs={'itemprop': True}):
                prop_name = prop_elem.get('itemprop')
                
                # Determine content based on element type
                if prop_elem.name == 'meta':
                    content = prop_elem.get('content', '')
                elif prop_elem.name in ['img', 'audio', 'video', 'source']:
                    content = prop_elem.get('src', '')
                elif prop_elem.name == 'a':
                    content = prop_elem.get('href', '')
                elif prop_elem.name == 'time':
                    content = prop_elem.get('datetime', '') or prop_elem.get_text(strip=True)
                elif prop_elem.name == 'data':
                    content = prop_elem.get('value', '') or prop_elem.get_text(strip=True)
                else:
                    content = prop_elem.get_text(strip=True)
                
                if content:
                    if prop_name in item['properties']:
                        if not isinstance(item['properties'][prop_name], list):
                            item['properties'][prop_name] = [item['properties'][prop_name]]
                        item['properties'][prop_name].append(content)
                    else:
                        item['properties'][prop_name] = content
            
            if item['properties']:
                microdata_items.append(item)
        
        return microdata_items

    def _extract_opengraph(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract Open Graph meta tags"""
        og_data = {}
        
        for meta in soup.find_all('meta'):
            property_attr = meta.get('property', '')
            content = meta.get('content', '')
            
            if property_attr.startswith('og:') and content:
                og_data[property_attr] = content.strip()
        
        return og_data

    def _extract_twitter_cards(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract Twitter Card meta tags"""
        twitter_data = {}
        
        for meta in soup.find_all('meta'):
            name_attr = meta.get('name', '')
            content = meta.get('content', '')
            
            if name_attr.startswith('twitter:') and content:
                twitter_data[name_attr] = content.strip()
        
        return twitter_data

    def _extract_rdfa(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract RDFa structured data"""
        rdfa_items = []
        
        for elem in soup.find_all(attrs={'typeof': True}):
            rdfa_item = {
                'typeof': elem.get('typeof', ''),
                'resource': elem.get('resource', ''),
                'about': elem.get('about', ''),
                'properties': {}
            }
            
            # Get properties from this element and children
            for prop_elem in elem.find_all(attrs={'property': True}):
                prop = prop_elem.get('property')
                content = (prop_elem.get('content') or 
                          prop_elem.get('href') or 
                          prop_elem.get_text(strip=True))
                
                if content:
                    rdfa_item['properties'][prop] = content
            
            if rdfa_item['properties']:
                rdfa_items.append(rdfa_item)
        
        return rdfa_items

    def _extract_meta_tags(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract all meta tags"""
        meta_tags = {}
        
        for meta in soup.find_all('meta'):
            name_attr = meta.get('name') or meta.get('property') or meta.get('http-equiv')
            content = meta.get('content', '')
            
            if name_attr and content:
                meta_tags[name_attr.lower()] = content.strip()
        
        return meta_tags

    def _detect_technologies(self, html_content: str, headers: Dict[str, str], js_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Detect technologies using signatures and patterns"""
        detected = {}
        
        # Combine all text for pattern matching
        all_text = html_content.lower()
        header_text = ' '.join(f"{k}: {v}" for k, v in headers.items()).lower()
        combined_text = all_text + ' ' + header_text
        
        for signature in self.tech_signatures:
            confidence = 0
            version = None
            evidence = []
            
            # Check main patterns
            pattern_matches = 0
            for pattern in signature.patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    pattern_matches += 1
                    evidence.append(f"Pattern: {pattern}")
            
            if pattern_matches > 0:
                confidence += pattern_matches * 20
            
            # Check confidence indicators
            indicator_matches = 0
            for indicator in signature.confidence_indicators:
                if re.search(indicator, combined_text, re.IGNORECASE):
                    indicator_matches += 1
                    evidence.append(f"Indicator: {indicator}")
            
            confidence += indicator_matches * 30
            
            # Check JavaScript globals
            if signature.name in js_data.get('frameworks', {}):
                confidence += 40
                version = js_data['frameworks'][signature.name]
                evidence.append("JavaScript global detected")
            elif signature.name in js_data.get('libraries', {}):
                confidence += 40
                version = js_data['libraries'][signature.name]
                evidence.append("JavaScript global detected")
            
            # Extract version if patterns provided
            if signature.version_patterns and not version:
                for version_pattern in signature.version_patterns:
                    version_match = re.search(version_pattern, html_content, re.IGNORECASE)
                    if version_match:
                        version = version_match.group(1)
                        evidence.append(f"Version found: {version}")
                        break
            
            # Only include if confidence is high enough
            if confidence >= 40:
                detected[signature.name] = {
                    'category': signature.category,
                    'confidence': min(confidence, 100),
                    'version': version,
                    'evidence': evidence[:5]  # Limit evidence
                }
        
        return detected

    def _extract_server_info(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Extract server information from HTTP headers"""
        server_info = {
            'server': headers.get('server', 'Unknown'),
            'powered_by': headers.get('x-powered-by', ''),
            'cdn': '',
            'cache_control': headers.get('cache-control', ''),
            'content_encoding': headers.get('content-encoding', ''),
            'security_headers': {}
        }
        
        # Detect CDN from headers
        if 'cloudflare' in str(headers).lower():
            server_info['cdn'] = 'Cloudflare'
        elif 'amazonaws' in str(headers).lower():
            server_info['cdn'] = 'Amazon CloudFront'
        elif 'fastly' in str(headers).lower():
            server_info['cdn'] = 'Fastly'
        
        # Security headers
        security_headers = [
            'strict-transport-security',
            'content-security-policy',
            'x-frame-options',
            'x-content-type-options',
            'referrer-policy',
            'x-xss-protection'
        ]
        
        for header in security_headers:
            if header in headers:
                server_info['security_headers'][header] = headers[header]
        
        return server_info

    def _calculate_structured_data_score(self, data: Dict[str, Any]) -> int:
        """Calculate a structured data quality score (0-100)"""
        score = 0
        
        # JSON-LD presence and quality
        if data['json_ld']:
            score += 30
            if len(data['json_ld']) > 1:
                score += 10
        
        # Microdata presence
        if data['microdata']:
            score += 20
        
        # Open Graph tags
        if data['opengraph']:
            score += 15
            required_og = ['og:title', 'og:description', 'og:image']
            if all(tag in data['opengraph'] for tag in required_og):
                score += 10
        
        # Twitter Cards
        if data['twitter_cards']:
            score += 10
        
        # Schema diversity
        if len(data['schema_types']) > 2:
            score += 15
        
        return min(score, 100)

# API Endpoints
@app.post("/extract-structured-data", response_model=StructuredDataResponse)
async def extract_structured_data(request: URLRequest):
    """Extract structured data from a website"""
    async with AdvancedWebScraper() as scraper:
        result = await scraper.extract_structured_data(request.url)
        return StructuredDataResponse(**result)

@app.post("/detect-tech-stack", response_model=TechStackResponse)  
async def detect_tech_stack(request: URLRequest):
    """Detect the technology stack of a website"""
    async with AdvancedWebScraper() as scraper:
        result = await scraper.detect_tech_stack(request.url)
        return TechStackResponse(**result)

@app.post("/extract-structured-data/batch")
async def extract_structured_data_batch(request: BatchURLRequest):
    """Extract structured data from multiple websites"""
    results = []
    
    async with AdvancedWebScraper() as scraper:
        for url in request.urls:
            try:
                result = await scraper.extract_structured_data(url)
                results.append(result)
            except Exception as e:
                results.append({
                    'url': str(url),
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
    
    return {
        'results': results,
        'total_processed': len(results),
        'timestamp': datetime.now().isoformat()
    }

@app.post("/detect-tech-stack/batch")
async def detect_tech_stack_batch(request: BatchURLRequest):
    """Detect tech stack for multiple websites"""
    results = []
    
    async with AdvancedWebScraper() as scraper:
        for url in request.urls:
            try:
                result = await scraper.detect_tech_stack(url)
                results.append(result)
            except Exception as e:
                results.append({
                    'url': str(url),
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
    
    return {
        'results': results,
        'total_processed': len(results),
        'timestamp': datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '3.0.0'
    }

@app.get("/")
async def root():
    """API information and usage"""
    return {
        'title': 'Advanced Web Scraper API',
        'version': '3.0.0',
        'description': 'FastAPI-based web scraper with structured data extraction and tech stack detection',
        'endpoints': {
            'POST /extract-structured-data': 'Extract structured data (JSON-LD, Microdata, OpenGraph) from a website',
            'POST /detect-tech-stack': 'Detect technology stack (CMS, frameworks, analytics, etc.) of a website',
            'POST /extract-structured-data/batch': 'Extract structured data from multiple websites',
            'POST /detect-tech-stack/batch': 'Detect tech stack for multiple websites',
            'GET /health': 'Health check endpoint',
            'GET /docs': 'Interactive API documentation',
            'GET /redoc': 'Alternative API documentation'
        },
        'features': [
            'Comprehensive JSON-LD extraction and parsing',
            'Microdata structured data extraction',
            'Open Graph and Twitter Cards meta tag extraction',
            'RDFa structured data support',
            'Advanced technology stack detection',
            'CMS detection (WordPress, Drupal, Joomla, Shopify, etc.)',
            'JavaScript framework detection (React, Vue, Angular, etc.)',
            'CSS framework detection (Bootstrap, Tailwind, Foundation)',
            'Analytics tools detection (Google Analytics, GTM, Facebook Pixel)',
            'SEO tools detection (Yoast, RankMath, etc.)',
            'CDN and hosting technology detection',
            'Security and performance tools detection',
            'Server information extraction from headers',
            'Batch processing support',
            'High confidence scoring system',
            'Version detection where possible'
        ],
        'usage_examples': {
            'structured_data': {
                'url': 'https://api.example.com/extract-structured-data',
                'method': 'POST',
                'body': {'url': 'https://example.com'}
            },
            'tech_stack': {
                'url': 'https://api.example.com/detect-tech-stack',
                'method': 'POST', 
                'body': {'url': 'https://example.com'}
            }
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
