# 🚀 Advanced FastAPI Web Scraper

Een complete FastAPI-gebaseerde web scraping API die gespecialiseerd is in **structured data extractie** en **technology stack detectie** zonder gebruik van commerciële APIs.

## 🎯 Functionaliteiten

### 📊 Structured Data Extractie
- **JSON-LD** parsing en extractie
- **Microdata** (Schema.org) detectie  
- **OpenGraph** meta tags
- **Twitter Cards** extractie
- **RDFa** structured data
- **Meta tags** analyse
- Schema type classificatie
- Data kwaliteit scoring

### 🔧 Technology Stack Detectie
- **CMS detectie**: WordPress, Drupal, Joomla, Shopify, Magento, WooCommerce
- **JavaScript frameworks**: React, Vue.js, Angular, Next.js, Nuxt.js
- **CSS frameworks**: Bootstrap, Tailwind CSS, Foundation
- **Analytics tools**: Google Analytics, GTM, Facebook Pixel, Hotjar
- **SEO tools**: Yoast SEO, RankMath, All in One SEO
- **Libraries**: jQuery, Lodash, D3.js
- **CDN & Hosting**: Cloudflare, Amazon CloudFront
- **Security tools**: Wordfence, security headers
- **Performance tools**: WP Rocket, W3 Total Cache
- **Server informatie**: van HTTP headers

## 🏗️ Architectuur

```
FastAPI + Playwright + BeautifulSoup + Pydantic
├── Async/await support voor hoge performance
├── Comprehensive tech signature database
├── Advanced pattern matching algoritmes
├── Confidence scoring systeem
├── Batch processing capabilities
└── Production-ready deployment
```

## 📚 API Endpoints

### 1. Structured Data Extractie

```http
POST /extract-structured-data
```

**Request:**
```json
{
  "url": "https://example.com"
}
```

**Response:**
```json
{
  "url": "https://example.com",
  "timestamp": "2024-01-01T12:00:00",
  "json_ld": [...],
  "microdata": [...],
  "opengraph": {...},
  "twitter_cards": {...},
  "rdfa": [...],
  "schema_types": ["Organization", "WebPage"],
  "meta_tags": {...},
  "summary": {
    "total_json_ld_items": 2,
    "total_microdata_items": 1,
    "total_opengraph_tags": 8,
    "total_twitter_cards": 4,
    "structured_data_score": 85,
    "has_structured_data": true
  }
}
```

### 2. Technology Stack Detectie

```http
POST /detect-tech-stack
```

**Request:**
```json
{
  "url": "https://example.com"
}
```

**Response:**
```json
{
  "url": "https://example.com",
  "timestamp": "2024-01-01T12:00:00",
  "cms": {
    "WordPress": {
      "category": "cms",
      "confidence": 95,
      "version": "6.4.2",
      "evidence": ["wp-content", "wp-includes", "wp-json API"]
    }
  },
  "frameworks": {
    "React": {
      "category": "framework", 
      "confidence": 90,
      "version": "18.2.0",
      "evidence": ["React global", "data-reactroot"]
    }
  },
  "analytics": {...},
  "seo_tools": {...},
  "libraries": {...},
  "server_info": {
    "server": "nginx/1.18.0",
    "cdn": "Cloudflare",
    "security_headers": {...}
  },
  "summary": {
    "total_technologies": 12,
    "cms_detected": ["WordPress"],
    "frameworks_detected": ["React"],
    "main_server": "nginx",
    "technology_score": 12
  }
}
```

### 3. Batch Processing

```http
POST /extract-structured-data/batch
POST /detect-tech-stack/batch
```

**Request:**
```json
{
  "urls": [
    "https://example1.com",
    "https://example2.com",
    "https://example3.com"
  ]
}
```

### 4. Overige Endpoints

```http
GET /health          # Health check
GET /                # API informatie
GET /docs            # Interactive Swagger docs
GET /redoc           # Alternative documentation
```

## 🚀 Installation & Deployment

### Lokale Development

```bash
# Clone repository
git clone <repository-url>
cd fastapi-web-scraper

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment

```bash
# Build image
docker build -t fastapi-scraper .

# Run container
docker run -p 8000:8000 fastapi-scraper
```

### Render Deployment

1. Connect je GitHub repository
2. Zorg dat `render.yaml` in je root staat
3. Deploy automatisch via Render dashboard

**Render configuratie:**
- Plan: Standard (voor Playwright performance)
- Docker runtime
- Health check: `/health`
- Auto-deploy enabled

## 🧪 Testing

```bash
# Run test suite
python test_api.py

# Test specific URL interactively
python test_api.py
# → Follow prompts for interactive testing
```

**Test coverage:**
- ✅ Health checks
- ✅ Basic API endpoints
- ✅ Structured data extraction
- ✅ Tech stack detection  
- ✅ Batch processing
- ✅ Error handling
- ✅ Performance metrics

## 🔧 Configuratie

### Environment Variables

```bash
# Playwright configuratie
PLAYWRIGHT_BROWSERS_PATH=/app/pw-browsers
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0

# FastAPI configuratie  
FASTAPI_ENV=production
UVICORN_WORKERS=1
TIMEOUT_KEEP_ALIVE=120

# Python optimizations
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
```

### Performance Tuning

**Single worker configuratie** (aanbevolen voor Playwright):
```bash
uvicorn main:app --workers 1 --timeout-keep-alive 120
```

**Browser resource management:**
- Hergebruik van browser context
- Automatic page cleanup
- Memory optimization
- Request/response caching

## 📈 Advanced Features

### Technology Detection Engine

**Signature-based detectie:**
```python
TechSignature(
    name="WordPress",
    category="cms", 
    patterns=[r'/wp-content/', r'/wp-includes/'],
    confidence_indicators=['generator.*wordpress'],
    version_patterns=[r'WordPress (\d+\.\d+\.\d+)']
)
```

**Multi-layer analysis:**
1. HTML content pattern matching
2. HTTP header analysis
3. JavaScript global variable detection
4. CSS class/ID pattern recognition
5. File path analysis

### Structured Data Processing

**JSON-LD advanced parsing:**
- Comment removal
- Format normalization  
- Nested object handling
- Type extraction
- Validation scoring

**Microdata extraction:**
- Element-specific content detection
- Property aggregation
- Hierarchical data mapping
- Schema.org compliance checking

## 🔒 Security & Best Practices

### Security Headers Detection
- Strict-Transport-Security
- Content-Security-Policy  
- X-Frame-Options
- X-Content-Type-Options
- Referrer-Policy

### Rate Limiting & Resource Management
- Request timeout configuration
- Memory usage monitoring
- Browser process management
- Graceful error handling

### Data Privacy
- No data storage/caching
- Request-response isolation
- Minimal data collection
- GDPR compliant processing

## 📊 Performance Metrics

**Typical response times:**
- Single URL structured data: 3-8 seconds
- Single URL tech detection: 2-6 seconds  
- Batch processing (3 URLs): 15-30 seconds

**Resource usage:**
- Memory: ~200-500MB per request
- CPU: Moderate (browser rendering)
- Disk: Minimal (temp files only)

## 🐛 Troubleshooting

### Common Issues

**1. Playwright browser not found:**
```bash
playwright install chromium
export PLAYWRIGHT_BROWSERS_PATH=/app/pw-browsers
```

**2. Memory issues on small servers:**
```bash
# Reduce concurrent requests
# Monitor memory usage
# Consider upgrading server plan
```

**3. Timeout errors:**
```bash
# Increase timeout settings
# Check network connectivity
# Verify target site accessibility
```

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Add comprehensive tests
4. Update documentation
5. Submit pull request

### Development Guidelines
- Follow FastAPI/Pydantic patterns
- Add type hints everywhere
- Include error handling
- Write comprehensive tests
- Update tech signatures database

## 📄 License

MIT License - zie LICENSE file voor details.

## 🔗 Links

- **Live API:** [Your Render URL]/docs
- **Documentation:** [Your Render URL]/redoc  
- **Health Check:** [Your Render URL]/health
- **GitHub:** [Repository URL]

## 💡 Roadmap

- [ ] GraphQL API support
- [ ] WebSocket real-time updates
- [ ] Enhanced caching layer
- [ ] Machine learning tech detection
- [ ] Custom signature management
- [ ] Enterprise authentication
- [ ] Webhook notifications
- [ ] Export formats (PDF, CSV, Excel)

---

**Gebouwd met ❤️ voor de Nederlandse development community**
