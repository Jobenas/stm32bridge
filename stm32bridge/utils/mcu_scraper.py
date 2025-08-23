"""
MCU specification scraper for STM32 microcontrollers.
"""

import re
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from rich.console import Console
from ..exceptions import STM32MigrationError

console = Console()


@dataclass
class MCUSpecs:
    """STM32 MCU specifications extracted from web sources."""
    part_number: str
    family: str
    core: str
    max_frequency: str
    flash_size_kb: int
    ram_size_kb: int
    package: str
    pin_count: int
    operating_voltage_min: float
    operating_voltage_max: float
    temperature_min: int
    temperature_max: int
    peripherals: Dict[str, int]
    features: List[str]


class STM32Scraper:
    """Scrape STM32 specifications from ST Microelectronics website."""
    
    def __init__(self):
        self.session = requests.Session()
        # Enhanced headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        # Add retry configuration
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],  # Updated parameter name
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
    def scrape_from_url(self, url: str) -> Optional[MCUSpecs]:
        """
        Scrape MCU specifications from ST product page URL.
        
        Args:
            url: ST product page URL
            
        Returns:
            MCUSpecs object or None if scraping failed
        """
        import time
        
        try:
            console.print(f"[blue]Fetching MCU specifications from: {url}[/blue]")
            
            # Add delay to avoid being flagged as a bot
            time.sleep(2)
            
            # Try multiple timeouts and retries
            for attempt in range(3):
                try:
                    if attempt > 0:
                        console.print(f"[yellow]Retrying... (attempt {attempt + 1}/3)[/yellow]")
                        time.sleep(5)  # Longer delay between retries
                    
                    response = self.session.get(url, timeout=45)  # Increased timeout
                    response.raise_for_status()
                    break
                except requests.exceptions.Timeout:
                    if attempt == 2:  # Last attempt
                        raise STM32MigrationError(f"Timeout: ST website is not responding. This may be due to:\n"
                                                 f"  • Geographic restrictions or slow connection\n"
                                                 f"  • Bot detection blocking automated requests\n"
                                                 f"  • Website maintenance or high traffic\n"
                                                 f"Try again later or use --manual mode for interactive input.")
                    continue
                except requests.exceptions.RequestException as e:
                    if "403" in str(e) or "blocked" in str(e).lower():
                        raise STM32MigrationError(f"Access denied: ST website blocked the request. This may be due to:\n"
                                                 f"  • Bot detection or security measures\n"
                                                 f"  • Geographic restrictions\n"
                                                 f"  • Try using --manual mode instead.")
                    elif attempt == 2:
                        raise STM32MigrationError(f"Failed to fetch URL {url}: {e}")
                    continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Determine the page type and parse accordingly
            if 'mouser.com' in url.lower() or 'mouser.pe' in url.lower():
                specs = self._parse_mouser_page(soup, url)
            elif 'digikey.com' in url.lower() or 'digikey.' in url.lower():
                specs = self._parse_digikey_page(soup, url)
            elif 'st.com' in url.lower():
                # Validate this is an ST MCU page
                if not self._is_stm32_page(soup, url):
                    raise STM32MigrationError(f"URL does not appear to be a valid STM32 product page: {url}")
                specs = self._parse_st_page(soup, url)
            else:
                raise STM32MigrationError(f"Unsupported URL domain. Supported sites: st.com, mouser.com, digikey.com: {url}")
            
            if specs:
                console.print(f"[green]✅ Successfully extracted specs for {specs.part_number}[/green]")
                return specs
            else:
                # If parsing failed, try to extract part number and create basic specs
                part_number = self._extract_part_number_from_url(url)
                if part_number:
                    console.print(f"[yellow]⚠️  Scraping failed, falling back to basic specs for {part_number}[/yellow]")
                    return self.create_from_part_number(part_number)
                raise STM32MigrationError("Could not extract MCU specifications from the page")
                
        except requests.exceptions.RequestException as e:
            raise STM32MigrationError(f"Failed to fetch URL {url}: {e}")
        except Exception as e:
            raise STM32MigrationError(f"Error parsing MCU specifications: {e}")
    
    def _is_stm32_page(self, soup: BeautifulSoup, url: str) -> bool:
        """Validate that this is a valid STM32 product page."""
        # Check URL pattern
        if 'st.com' not in url.lower():
            return False
            
        # Check for STM32 indicators in the page
        page_text = soup.get_text().lower()
        stm32_indicators = ['stm32', 'microcontroller', 'arm cortex']
        
        return any(indicator in page_text for indicator in stm32_indicators)
    
    def _extract_part_number_from_url(self, url: str) -> Optional[str]:
        """Extract STM32 part number from URL when page scraping fails."""
        # Try to extract from URL path
        url_match = re.search(r'STM32[A-Z]\d+[A-Z]*\d*[A-Z]*\d*', url.upper())
        if url_match:
            return url_match.group(0)
        
        # Try different URL patterns for different sites
        if 'digikey.com' in url.lower():
            # Digikey URLs sometimes have part numbers in path
            digikey_match = re.search(r'/([^/]*STM32[A-Z0-9]+[^/]*)', url, re.IGNORECASE)
            if digikey_match:
                part_str = digikey_match.group(1)
                stm32_match = re.search(r'STM32[A-Z]\d+[A-Z]*\d*[A-Z]*\d*', part_str.upper())
                if stm32_match:
                    return stm32_match.group(0)
        
        elif 'mouser.com' in url.lower():
            # Mouser URLs sometimes have part numbers in query parameters
            mouser_match = re.search(r'ProductDetail/[^/]*/([^/?]+)', url)
            if mouser_match:
                part_str = mouser_match.group(1)
                stm32_match = re.search(r'STM32[A-Z]\d+[A-Z]*\d*[A-Z]*\d*', part_str.upper())
                if stm32_match:
                    return stm32_match.group(0)
        
        elif 'st.com' in url.lower():
            # ST URLs often have part numbers in the path
            st_match = re.search(r'/([^/]*stm32[a-z0-9]+[^/]*)', url, re.IGNORECASE)
            if st_match:
                part_str = st_match.group(1)
                stm32_match = re.search(r'STM32[A-Z]\d+[A-Z]*\d*[A-Z]*\d*', part_str.upper())
                if stm32_match:
                    return stm32_match.group(0)
        
        return None
    
    def _parse_st_page(self, soup: BeautifulSoup, url: str) -> Optional[MCUSpecs]:
        """Parse STM32 specifications from ST product page."""
        try:
            # Extract part number from title or URL
            part_number = self._extract_part_number(soup, url)
            if not part_number:
                return None
                
            # Extract specifications from various page sections
            specs_data = {
                'part_number': part_number,
                'family': self._extract_family(part_number),
                'core': self._extract_core(soup),
                'max_frequency': self._extract_frequency(soup),
                'flash_size_kb': self._extract_flash_size(soup),
                'ram_size_kb': self._extract_ram_size(soup),
                'package': self._extract_package(soup),
                'pin_count': self._extract_pin_count(soup),
                'operating_voltage_min': self._extract_voltage_min(soup),
                'operating_voltage_max': self._extract_voltage_max(soup),
                'temperature_min': self._extract_temp_min(soup),
                'temperature_max': self._extract_temp_max(soup),
                'peripherals': self._extract_peripherals(soup),
                'features': self._extract_features(soup)
            }
            
            return MCUSpecs(**specs_data)
            
        except Exception as e:
            console.print(f"[red]Error parsing specifications: {e}[/red]")
            return None
    
    def _extract_part_number(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract MCU part number from page title or URL."""
        # Try to get from page title
        title = soup.find('title')
        if title:
            title_text = title.get_text()
            # Look for STM32 pattern in title
            match = re.search(r'STM32[A-Z]\d+[A-Z]*\d*', title_text.upper())
            if match:
                return match.group(0)
        
        # Try to get from URL
        url_match = re.search(r'stm32([a-z]\d+[a-z]*\d*)', url.lower())
        if url_match:
            return f"STM32{url_match.group(1).upper()}"
            
        # Try to get from page content
        page_text = soup.get_text()
        match = re.search(r'STM32[A-Z]\d+[A-Z]*\d*', page_text.upper())
        if match:
            return match.group(0)
            
        return None
    
    def _extract_family(self, part_number: str) -> str:
        """Extract STM32 family from part number."""
        if not part_number:
            return "Unknown"
        
        # Extract family from part number (e.g., STM32L432KC -> L4, STM32WB55CG -> WB)
        # Handle both single letter families (L4, F1) and multi-letter families (WB, MP)
        match = re.search(r'STM32([A-Z]+)(\d+)', part_number.upper())
        if match:
            letters = match.group(1)
            first_digit = match.group(2)[0]
            
            # For single letter families like F, L, H, G - include first digit
            if len(letters) == 1:
                return f"STM32{letters}{first_digit}"
            # For multi-letter families like WB, MP - just use letters
            else:
                return f"STM32{letters}"
        return "STM32"
    
    def _extract_core(self, soup: BeautifulSoup) -> str:
        """Extract CPU core information."""
        page_text = soup.get_text().lower()
        
        # Common STM32 cores
        if 'cortex-m4' in page_text or 'cortex m4' in page_text:
            return 'cortex-m4'
        elif 'cortex-m3' in page_text or 'cortex m3' in page_text:
            return 'cortex-m3'
        elif 'cortex-m0+' in page_text or 'cortex m0+' in page_text:
            return 'cortex-m0plus'
        elif 'cortex-m0' in page_text or 'cortex m0' in page_text:
            return 'cortex-m0'
        elif 'cortex-m7' in page_text or 'cortex m7' in page_text:
            return 'cortex-m7'
        
        return 'cortex-m4'  # Default for most STM32s
    
    def _extract_frequency(self, soup: BeautifulSoup) -> str:
        """Extract maximum frequency."""
        page_text = soup.get_text()
        
        # Look for frequency patterns (MHz)
        freq_patterns = [
            r'(\d+)\s*MHz',
            r'(\d+)\s*mhz',
            r'up to (\d+)\s*MHz'
        ]
        
        for pattern in freq_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                # Get the highest frequency found
                freqs = [int(f) for f in matches if f.isdigit()]
                if freqs:
                    return f"{max(freqs)}000000L"
        
        return "80000000L"  # Default 80MHz
    
    def _extract_memory_size(self, soup: BeautifulSoup, memory_type: str) -> int:
        """Extract memory size (Flash or RAM) in KB."""
        page_text = soup.get_text()
        
        if memory_type.lower() == 'flash':
            patterns = [
                rf'(\d+)\s*KB?\s+Flash',
                rf'(\d+)\s*KB?\s+flash',
                rf'Flash.*?(\d+)\s*KB?',
                rf'(\d+)\s*KB?\s+of Flash'
            ]
        else:  # RAM
            patterns = [
                rf'(\d+)\s*KB?\s+RAM',
                rf'(\d+)\s*KB?\s+ram',
                rf'(\d+)\s*KB?\s+SRAM',
                rf'RAM.*?(\d+)\s*KB?',
                rf'SRAM.*?(\d+)\s*KB?'
            ]
        
        for pattern in patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                # Get the largest memory size found
                sizes = [int(m) for m in matches if m.isdigit()]
                if sizes:
                    return max(sizes)
        
        # Default values
        return 256 if memory_type.lower() == 'flash' else 64
    
    def _extract_flash_size(self, soup: BeautifulSoup) -> int:
        """Extract Flash memory size in KB."""
        return self._extract_memory_size(soup, 'flash')
    
    def _extract_ram_size(self, soup: BeautifulSoup) -> int:
        """Extract RAM size in KB."""
        return self._extract_memory_size(soup, 'ram')
    
    def _extract_package(self, soup: BeautifulSoup) -> str:
        """Extract package type."""
        page_text = soup.get_text().upper()
        
        packages = ['LQFP', 'BGA', 'QFN', 'TSSOP', 'UFQFPN', 'WLCSP', 'TQFP']
        for package in packages:
            if package in page_text:
                return package
        
        return 'LQFP'  # Default
    
    def _extract_pin_count(self, soup: BeautifulSoup) -> int:
        """Extract pin count."""
        page_text = soup.get_text()
        
        # Look for pin count patterns
        pin_patterns = [
            r'(\d+)[-\s]*pin',
            r'(\d+)[-\s]*pins',
            r'pin count.*?(\d+)',
        ]
        
        for pattern in pin_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                pins = [int(p) for p in matches if p.isdigit() and 10 <= int(p) <= 300]
                if pins:
                    return max(pins)
        
        return 64  # Default
    
    def _extract_voltage_range(self, soup: BeautifulSoup) -> Tuple[float, float]:
        """Extract operating voltage range."""
        page_text = soup.get_text()
        
        # Look for voltage patterns
        voltage_patterns = [
            r'(\d+\.?\d*)\s*V\s*to\s*(\d+\.?\d*)\s*V',
            r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*V',
        ]
        
        for pattern in voltage_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                try:
                    voltages = [(float(v1), float(v2)) for v1, v2 in matches]
                    if voltages:
                        return voltages[0]  # Take first match
                except ValueError:
                    continue
        
        return (1.71, 3.6)  # Default STM32 range
    
    def _extract_voltage_min(self, soup: BeautifulSoup) -> float:
        """Extract minimum operating voltage."""
        return self._extract_voltage_range(soup)[0]
    
    def _extract_voltage_max(self, soup: BeautifulSoup) -> float:
        """Extract maximum operating voltage."""
        return self._extract_voltage_range(soup)[1]
    
    def _extract_temp_range(self, soup: BeautifulSoup) -> Tuple[int, int]:
        """Extract temperature range."""
        page_text = soup.get_text()
        
        # Look for temperature patterns
        temp_patterns = [
            r'(-?\d+)°C\s*to\s*([+-]?\d+)°C',
            r'(-?\d+)\s*to\s*([+-]?\d+)\s*°C',
            r'(-?\d+)\s*-\s*([+-]?\d+)°C',
        ]
        
        for pattern in temp_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                try:
                    temps = [(int(t1), int(t2)) for t1, t2 in matches]
                    if temps:
                        return temps[0]  # Take first match
                except ValueError:
                    continue
        
        return (-40, 85)  # Default range
    
    def _extract_temp_min(self, soup: BeautifulSoup) -> int:
        """Extract minimum temperature."""
        return self._extract_temp_range(soup)[0]
    
    def _extract_temp_max(self, soup: BeautifulSoup) -> int:
        """Extract maximum temperature."""
        return self._extract_temp_range(soup)[1]
    
    def _extract_peripherals(self, soup: BeautifulSoup) -> Dict[str, int]:
        """Extract peripheral counts."""
        page_text = soup.get_text().upper()
        peripherals = {}
        
        # Common STM32 peripherals to look for
        peripheral_patterns = {
            'USART': r'(\d+)\s*x?\s*USARTS?',
            'SPI': r'(\d+)\s*x?\s*SPIS?',
            'I2C': r'(\d+)\s*x?\s*I2CS?',
            'ADC': r'(\d+)\s*x?\s*ADCS?',
            'DAC': r'(\d+)\s*x?\s*DACS?',
            'TIMER': r'(\d+)\s*x?\s*TIMERS?',
            'USB': r'(\d+)\s*x?\s*USB',
            'CAN': r'(\d+)\s*x?\s*CANS?',
        }
        
        for peripheral, pattern in peripheral_patterns.items():
            matches = re.findall(pattern, page_text)
            if matches:
                try:
                    count = max([int(m) for m in matches if m.isdigit()])
                    peripherals[peripheral] = count
                except ValueError:
                    continue
        
        return peripherals
    
    def _extract_features(self, soup: BeautifulSoup) -> List[str]:
        """Extract key features."""
        page_text = soup.get_text().lower()
        features = []
        
        # Look for common STM32 features
        feature_indicators = {
            'fpu': ['fpu', 'floating point', 'floating-point'],
            'dsp': ['dsp', 'digital signal'],
            'crypto': ['crypto', 'encryption', 'aes'],
            'usb': ['usb'],
            'ethernet': ['ethernet', 'eth'],
            'can': ['can bus', 'can'],
            'lcd': ['lcd', 'display'],
            'camera': ['camera', 'dcmi'],
        }
        
        for feature, indicators in feature_indicators.items():
            if any(indicator in page_text for indicator in indicators):
                features.append(feature)
        
        return features
    
    def create_from_part_number(self, part_number: str) -> Optional[MCUSpecs]:
        """
        Create basic MCU specs from part number using known STM32 patterns.
        This is a fallback when web scraping fails.
        
        Args:
            part_number: STM32 part number (e.g., STM32L432KC)
            
        Returns:
            Basic MCUSpecs object with estimated specifications
        """
        try:
            part_number = part_number.upper().strip()
            
            # Validate STM32 part number format
            if not re.match(r'^STM32[A-Z]\d+[A-Z]*\d*$', part_number):
                return None
            
            console.print(f"[yellow]⚠️  Creating basic specs from part number: {part_number}[/yellow]")
            console.print(f"[yellow]Note: These are estimated values. For accurate specs, try --manual mode.[/yellow]")
            
            # Extract family and series info
            family_match = re.search(r'STM32([A-Z])(\d)', part_number)
            if not family_match:
                return None
                
            family_letter = family_match.group(1)
            series_num = int(family_match.group(2))
            
            # Known STM32 family characteristics
            family_specs = {
                'F': {  # STM32F series
                    'core': 'cortex-m4' if series_num >= 4 else 'cortex-m3',
                    'frequency': '168000000L' if series_num >= 4 else '72000000L',
                    'voltage_range': (2.0, 3.6),
                    'typical_flash': 512 if series_num >= 4 else 256,
                    'typical_ram': 128 if series_num >= 4 else 64
                },
                'L': {  # STM32L series (Low power)
                    'core': 'cortex-m4' if series_num >= 4 else 'cortex-m3',
                    'frequency': '80000000L' if series_num >= 4 else '32000000L',
                    'voltage_range': (1.71, 3.6),
                    'typical_flash': 256,
                    'typical_ram': 64
                },
                'H': {  # STM32H series (High performance)
                    'core': 'cortex-m7',
                    'frequency': '480000000L',
                    'voltage_range': (1.62, 3.6),
                    'typical_flash': 1024,
                    'typical_ram': 512
                },
                'G': {  # STM32G series
                    'core': 'cortex-m4',
                    'frequency': '170000000L',
                    'voltage_range': (1.71, 3.6),
                    'typical_flash': 512,
                    'typical_ram': 128
                }
            }
            
            # Get family specifications or use defaults
            specs = family_specs.get(family_letter, {
                'core': 'cortex-m4',
                'frequency': '80000000L',
                'voltage_range': (1.8, 3.6),
                'typical_flash': 256,
                'typical_ram': 64
            })
            
            # Extract package info from part number suffix
            package = 'LQFP'  # Default
            pin_count = 64    # Default
            
            # Last character often indicates package
            if part_number.endswith('T'):
                package = 'LQFP'
                pin_count = 64
            elif part_number.endswith('C'):
                package = 'LQFP'
                pin_count = 48
            elif part_number.endswith('U'):
                package = 'UFQFPN'
                pin_count = 28
                
            return MCUSpecs(
                part_number=part_number,
                family=f"STM32{family_letter}{series_num}",
                core=specs['core'],
                max_frequency=specs['frequency'],
                flash_size_kb=specs['typical_flash'],
                ram_size_kb=specs['typical_ram'],
                package=package,
                pin_count=pin_count,
                operating_voltage_min=specs['voltage_range'][0],
                operating_voltage_max=specs['voltage_range'][1],
                temperature_min=-40,
                temperature_max=85,
                peripherals={},
                features=[]
            )
            
        except Exception as e:
            console.print(f"[red]Error creating specs from part number: {e}[/red]")
            return None

    def _parse_mouser_page(self, soup: BeautifulSoup, url: str) -> Optional[MCUSpecs]:
        """Parse STM32 specifications from Mouser product page."""
        try:
            # Extract part number from Mouser page
            part_number = self._extract_mouser_part_number(soup, url)
            if not part_number:
                return None
                
            # Extract specifications from Mouser page structure
            specs_data = {
                'part_number': part_number,
                'family': self._extract_family(part_number),
                'core': self._extract_mouser_core_from_part(part_number, soup),
                'max_frequency': self._extract_mouser_frequency(soup),
                'flash_size_kb': self._extract_mouser_flash_size(soup),
                'ram_size_kb': self._extract_mouser_ram_size(soup),
                'package': self._extract_mouser_package(soup),
                'pin_count': self._extract_mouser_pin_count(soup),
                'operating_voltage_min': self._extract_mouser_voltage_min(soup),
                'operating_voltage_max': self._extract_mouser_voltage_max(soup),
                'temperature_min': self._extract_mouser_temp_min(soup),
                'temperature_max': self._extract_mouser_temp_max(soup),
                'peripherals': {},  # Mouser doesn't usually have detailed peripheral info
                'features': []      # Mouser doesn't usually have detailed features
            }
            
            return MCUSpecs(**specs_data)
            
        except Exception as e:
            console.print(f"[red]Error parsing Mouser specifications: {e}[/red]")
            return None

    def _extract_mouser_part_number(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract MCU part number from Mouser page."""
        # Try to get from page title
        title = soup.find('title')
        if title:
            title_text = title.get_text()
            match = re.search(r'STM32[A-Z]\d+[A-Z]*\d*[A-Z]*\d*', title_text.upper())
            if match:
                return match.group(0)
        
        # Try to get from product name/header
        product_headers = soup.find_all(['h1', 'h2'], class_=re.compile(r'(product|part|title)', re.I))
        for header in product_headers:
            text = header.get_text()
            match = re.search(r'STM32[A-Z]\d+[A-Z]*\d*[A-Z]*\d*', text.upper())
            if match:
                return match.group(0)
        
        # Try to get from URL
        url_match = re.search(r'STM32[A-Z]\d+[A-Z]*\d*[A-Z]*\d*', url.upper())
        if url_match:
            return url_match.group(0)
            
        return None

    def _extract_mouser_core(self, soup: BeautifulSoup) -> str:
        """Extract ARM core from Mouser page."""
        # First, look for ARM core mentions in specifications table
        spec_text = soup.get_text().lower()
        if 'cortex-m7' in spec_text or 'cortex m7' in spec_text:
            return 'cortex-m7'
        elif 'cortex-m4' in spec_text or 'cortex m4' in spec_text:
            return 'cortex-m4'
        elif 'cortex-m3' in spec_text or 'cortex m3' in spec_text:
            return 'cortex-m3'
        elif 'cortex-m0+' in spec_text or 'cortex m0+' in spec_text:
            return 'cortex-m0plus'
        elif 'cortex-m0' in spec_text or 'cortex m0' in spec_text:
            return 'cortex-m0'
        elif 'cortex-m33' in spec_text or 'cortex m33' in spec_text:
            return 'cortex-m33'
        
        # If not found in spec text, try to infer from part number
        # Look for part number in the URL or page content
        full_text = soup.get_text().upper()
        
        # Check STM32F1 series (Cortex-M3)
        if re.search(r'STM32F1\d+', full_text) or 'STM32F103' in full_text or 'STM32F101' in full_text or 'STM32F105' in full_text or 'STM32F107' in full_text:
            return 'cortex-m3'
        
        # Check STM32F0 series (Cortex-M0)
        elif re.search(r'STM32F0\d+', full_text):
            return 'cortex-m0'
        
        # Check STM32L0 series (Cortex-M0+)
        elif re.search(r'STM32L0\d+', full_text):
            return 'cortex-m0plus'
        
        # Check STM32F7/H7 series (Cortex-M7)
        elif re.search(r'STM32[FH]7\d+', full_text):
            return 'cortex-m7'
        
        # Check STM32L5/U5 series (Cortex-M33)
        elif re.search(r'STM32[LU]5\d+', full_text):
            return 'cortex-m33'
        
        return 'cortex-m4'  # Default for most modern STM32 (F2, F3, F4, L1, L4, etc.)

    def _extract_mouser_core_from_part(self, part_number: str, soup: BeautifulSoup) -> str:
        """Extract ARM core based on part number and page content."""
        # First try to extract from page content
        spec_text = soup.get_text().lower()
        if 'cortex-m7' in spec_text or 'cortex m7' in spec_text:
            return 'cortex-m7'
        elif 'cortex-m4' in spec_text or 'cortex m4' in spec_text:
            return 'cortex-m4'
        elif 'cortex-m3' in spec_text or 'cortex m3' in spec_text:
            return 'cortex-m3'
        elif 'cortex-m0+' in spec_text or 'cortex m0+' in spec_text:
            return 'cortex-m0plus'
        elif 'cortex-m0' in spec_text or 'cortex m0' in spec_text:
            return 'cortex-m0'
        elif 'cortex-m33' in spec_text or 'cortex m33' in spec_text:
            return 'cortex-m33'
        
        # If not found in page content, infer from part number
        if not part_number:
            return 'cortex-m4'
            
        upper_part = part_number.upper()
        
        # STM32F1 series uses Cortex-M3
        if re.match(r'STM32F1\d+', upper_part):
            return 'cortex-m3'
        
        # STM32F0 series uses Cortex-M0
        elif re.match(r'STM32F0\d+', upper_part):
            return 'cortex-m0'
        
        # STM32L0 series uses Cortex-M0+
        elif re.match(r'STM32L0\d+', upper_part):
            return 'cortex-m0plus'
        
        # STM32F7/H7 series use Cortex-M7
        elif re.match(r'STM32[FH]7\d+', upper_part):
            return 'cortex-m7'
        
        # STM32L5/U5 series use Cortex-M33
        elif re.match(r'STM32[LU]5\d+', upper_part):
            return 'cortex-m33'
        
        # Default for most STM32 series (F2, F3, F4, L1, L4, etc.)
        return 'cortex-m4'

    def _extract_mouser_frequency(self, soup: BeautifulSoup) -> str:
        """Extract maximum frequency from Mouser page."""
        # Look for frequency specifications
        spec_text = soup.get_text()
        
        # Common patterns for frequency on Mouser
        patterns = [
            r'(\d+)\s*mhz.*max',
            r'max.*?(\d+)\s*mhz',
            r'frequency.*?(\d+)\s*mhz',
            r'clock.*?(\d+)\s*mhz',
            r'(\d+)\s*mhz.*frequency'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, spec_text.lower())
            if match:
                freq_mhz = int(match.group(1))
                return f"{freq_mhz * 1000000}L"  # Convert to Hz with L suffix
        
        return "80000000L"  # Default 80MHz

    def _extract_mouser_flash_size(self, soup: BeautifulSoup) -> int:
        """Extract flash memory size from Mouser page."""
        # Look for flash memory specifications
        spec_text = soup.get_text()
        
        patterns = [
            r'flash.*?(\d+)\s*kb',
            r'(\d+)\s*kb.*flash',
            r'program.*?(\d+)\s*kb',
            r'(\d+)\s*kb.*program'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, spec_text.lower())
            if match:
                return int(match.group(1))
        
        return 256  # Default

    def _extract_mouser_ram_size(self, soup: BeautifulSoup) -> int:
        """Extract RAM size from Mouser page."""
        # Look for RAM/SRAM specifications
        spec_text = soup.get_text()
        
        patterns = [
            r'sram.*?(\d+)\s*kb',
            r'(\d+)\s*kb.*sram',
            r'ram.*?(\d+)\s*kb',
            r'(\d+)\s*kb.*ram'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, spec_text.lower())
            if match:
                return int(match.group(1))
        
        return 64  # Default

    def _extract_mouser_package(self, soup: BeautifulSoup) -> str:
        """Extract package type from Mouser page."""
        spec_text = soup.get_text().lower()
        
        if 'lqfp' in spec_text:
            return 'LQFP'
        elif 'qfn' in spec_text or 'ufqfpn' in spec_text:
            return 'UFQFPN'
        elif 'bga' in spec_text:
            return 'BGA'
        elif 'tssop' in spec_text:
            return 'TSSOP'
        
        return 'LQFP'  # Default

    def _extract_mouser_pin_count(self, soup: BeautifulSoup) -> int:
        """Extract pin count from Mouser page."""
        spec_text = soup.get_text()
        
        # Look for pin count patterns
        patterns = [
            r'(\d+)\s*pin',
            r'pin.*?(\d+)',
            r'(\d+)\s*lead'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, spec_text.lower())
            if match:
                pin_count = int(match.group(1))
                if 20 <= pin_count <= 256:  # Reasonable range for MCU pins
                    return pin_count
        
        return 64  # Default

    def _extract_mouser_voltage_min(self, soup: BeautifulSoup) -> float:
        """Extract minimum operating voltage from Mouser page."""
        return 1.8  # Default minimum for most STM32

    def _extract_mouser_voltage_max(self, soup: BeautifulSoup) -> float:
        """Extract maximum operating voltage from Mouser page."""
        return 3.6  # Default maximum for most STM32

    def _extract_mouser_temp_min(self, soup: BeautifulSoup) -> int:
        """Extract minimum operating temperature from Mouser page."""
        return -40  # Default minimum temperature

    def _extract_mouser_temp_max(self, soup: BeautifulSoup) -> int:
        """Extract maximum operating temperature from Mouser page."""
        return 85  # Default maximum temperature

    def _parse_digikey_page(self, soup: BeautifulSoup, url: str) -> Optional[MCUSpecs]:
        """Parse STM32 specifications from Digikey product page."""
        try:
            # Extract part number from Digikey page
            part_number = self._extract_digikey_part_number(soup, url)
            if not part_number:
                return None
                
            # Extract specifications from Digikey page structure
            specs_data = {
                'part_number': part_number,
                'family': self._extract_family(part_number),
                'core': self._extract_digikey_core_from_part(part_number, soup),
                'max_frequency': self._extract_digikey_frequency(soup),
                'flash_size_kb': self._extract_digikey_flash_size(soup),
                'ram_size_kb': self._extract_digikey_ram_size(soup),
                'package': self._extract_digikey_package(soup),
                'pin_count': self._extract_digikey_pin_count(soup),
                'operating_voltage_min': self._extract_digikey_voltage_min(soup),
                'operating_voltage_max': self._extract_digikey_voltage_max(soup),
                'temperature_min': self._extract_digikey_temp_min(soup),
                'temperature_max': self._extract_digikey_temp_max(soup),
                'peripherals': {},  # Digikey doesn't usually have detailed peripheral info
                'features': []      # Digikey doesn't usually have detailed features
            }
            
            return MCUSpecs(**specs_data)
            
        except Exception as e:
            console.print(f"[red]Error parsing Digikey specifications: {e}[/red]")
            return None

    def _extract_digikey_part_number(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract MCU part number from Digikey page."""
        # Try to get from page title
        title = soup.find('title')
        if title:
            title_text = title.get_text()
            match = re.search(r'STM32[A-Z]\d+[A-Z]*\d*[A-Z]*\d*', title_text.upper())
            if match:
                return match.group(0)
        
        # Try to get from product name/header - Digikey specific selectors
        product_headers = soup.find_all(['h1', 'h2'], class_=re.compile(r'(product|part|title|name)', re.I))
        for header in product_headers:
            text = header.get_text()
            match = re.search(r'STM32[A-Z]\d+[A-Z]*\d*[A-Z]*\d*', text.upper())
            if match:
                return match.group(0)
        
        # Try manufacturer part number field (common in Digikey)
        mpn_fields = soup.find_all(['span', 'div'], string=re.compile(r'Manufacturer Part Number', re.I))
        for field in mpn_fields:
            parent = field.find_parent()
            if parent:
                text = parent.get_text()
                match = re.search(r'STM32[A-Z]\d+[A-Z]*\d*[A-Z]*\d*', text.upper())
                if match:
                    return match.group(0)
        
        # Try to get from URL
        url_match = re.search(r'STM32[A-Z]\d+[A-Z]*\d*[A-Z]*\d*', url.upper())
        if url_match:
            return url_match.group(0)
            
        return None

    def _extract_digikey_core_from_part(self, part_number: str, soup: BeautifulSoup) -> str:
        """Extract ARM core from Digikey page or infer from part number."""
        # First, look for ARM core mentions in specifications table
        spec_text = soup.get_text().lower()
        if 'cortex-m7' in spec_text or 'cortex m7' in spec_text:
            return 'cortex-m7'
        elif 'cortex-m4' in spec_text or 'cortex m4' in spec_text:
            return 'cortex-m4'
        elif 'cortex-m3' in spec_text or 'cortex m3' in spec_text:
            return 'cortex-m3'
        elif 'cortex-m0' in spec_text or 'cortex m0' in spec_text:
            return 'cortex-m0plus' if 'plus' in spec_text or '+' in spec_text else 'cortex-m0'
        elif 'cortex-m33' in spec_text or 'cortex m33' in spec_text:
            return 'cortex-m33'
            
        # Fall back to part number inference
        if not part_number:
            return 'cortex-m4'
            
        upper_part = part_number.upper()
        
        # STM32F1 series uses Cortex-M3
        if re.match(r'STM32F1\d+', upper_part):
            return 'cortex-m3'
        
        # STM32F0 series uses Cortex-M0
        elif re.match(r'STM32F0\d+', upper_part):
            return 'cortex-m0'
        
        # STM32L0 series uses Cortex-M0+
        elif re.match(r'STM32L0\d+', upper_part):
            return 'cortex-m0plus'
        
        # STM32F7/H7 series use Cortex-M7
        elif re.match(r'STM32[FH]7\d+', upper_part):
            return 'cortex-m7'
        
        # STM32L5/U5 series use Cortex-M33
        elif re.match(r'STM32[LU]5\d+', upper_part):
            return 'cortex-m33'
        
        # Default for most STM32 series (F2, F3, F4, L1, L4, etc.)
        return 'cortex-m4'

    def _extract_digikey_frequency(self, soup: BeautifulSoup) -> str:
        """Extract maximum frequency from Digikey page."""
        # Look for frequency in specifications tables
        freq_patterns = [
            r'(\d+)\s*MHz',
            r'(\d+)\s*mhz',
            r'frequency.*?(\d+)',
            r'clock.*?(\d+)',
            r'(\d+)\s*M\s*Hz'
        ]
        
        page_text = soup.get_text()
        for pattern in freq_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                # Find the highest frequency (likely the max)
                frequencies = [int(match) for match in matches if match.isdigit()]
                if frequencies:
                    max_freq = max(frequencies)
                    if 20 <= max_freq <= 500:  # Reasonable range for STM32
                        return f"{max_freq}000000L"
        
        return "80000000L"  # Default for most STM32L4

    def _extract_digikey_flash_size(self, soup: BeautifulSoup) -> int:
        """Extract flash memory size from Digikey page."""
        # Look for flash size in specifications
        flash_patterns = [
            r'(\d+)\s*KB.*?flash',
            r'(\d+)\s*kb.*?flash',
            r'flash.*?(\d+)\s*KB',
            r'flash.*?(\d+)\s*kb',
            r'program.*?memory.*?(\d+)',
            r'(\d+)\s*K.*?program'
        ]
        
        page_text = soup.get_text()
        for pattern in flash_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                sizes = [int(match) for match in matches if match.isdigit()]
                if sizes:
                    # Find reasonable flash size
                    for size in sorted(sizes, reverse=True):
                        if 16 <= size <= 2048:  # Reasonable range for STM32
                            return size
        
        return 256  # Default

    def _extract_digikey_ram_size(self, soup: BeautifulSoup) -> int:
        """Extract RAM size from Digikey page."""
        # Look for RAM size in specifications
        ram_patterns = [
            r'(\d+)\s*KB.*?RAM',
            r'(\d+)\s*kb.*?ram',
            r'RAM.*?(\d+)\s*KB',
            r'ram.*?(\d+)\s*kb',
            r'SRAM.*?(\d+)',
            r'(\d+)\s*K.*?SRAM'
        ]
        
        page_text = soup.get_text()
        for pattern in ram_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                sizes = [int(match) for match in matches if match.isdigit()]
                if sizes:
                    # Find reasonable RAM size
                    for size in sorted(sizes, reverse=True):
                        if 8 <= size <= 1024:  # Reasonable range for STM32
                            return size
        
        return 64  # Default

    def _extract_digikey_package(self, soup: BeautifulSoup) -> str:
        """Extract package type from Digikey page."""
        # Look for package information
        package_patterns = [
            r'package.*?(LQFP|BGA|TQFP|QFN|WLCSP|UFQFPN)',
            r'(LQFP|BGA|TQFP|QFN|WLCSP|UFQFPN)',
            r'mounting.*?(LQFP|BGA|TQFP|QFN|WLCSP|UFQFPN)'
        ]
        
        page_text = soup.get_text()
        for pattern in package_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        return "LQFP"  # Default

    def _extract_digikey_pin_count(self, soup: BeautifulSoup) -> int:
        """Extract pin count from Digikey page."""
        # Look for pin count information
        pin_patterns = [
            r'(\d+)[-\s]*pin',
            r'(\d+)[-\s]*pins',
            r'pin.*?count.*?(\d+)',
            r'(\d+)[-\s]*lead'
        ]
        
        page_text = soup.get_text()
        for pattern in pin_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                pins = [int(match) for match in matches if match.isdigit()]
                if pins:
                    # Find reasonable pin count
                    for pin_count in sorted(pins, reverse=True):
                        if 8 <= pin_count <= 256:  # Reasonable range for STM32
                            return pin_count
        
        return 32  # Default

    def _extract_digikey_voltage_min(self, soup: BeautifulSoup) -> float:
        """Extract minimum operating voltage from Digikey page."""
        return 1.8  # Default minimum for most STM32

    def _extract_digikey_voltage_max(self, soup: BeautifulSoup) -> float:
        """Extract maximum operating voltage from Digikey page."""
        return 3.6  # Default maximum for most STM32

    def _extract_digikey_temp_min(self, soup: BeautifulSoup) -> int:
        """Extract minimum operating temperature from Digikey page."""
        return -40  # Default minimum temperature

    def _extract_digikey_temp_max(self, soup: BeautifulSoup) -> int:
        """Extract maximum operating temperature from Digikey page."""
        return 85  # Default maximum temperature
