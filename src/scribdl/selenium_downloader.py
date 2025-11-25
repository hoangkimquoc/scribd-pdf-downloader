#!/usr/bin/env python
"""
Selenium-based downloader for Scribd documents.
Uses headless Chrome to handle JavaScript and lazy loading.
"""
import json
import logging
import time
from typing import Optional, Callable

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)


class ScribdSeleniumDownloader:
    """Download Scribd documents using Selenium with auto-scroll."""
    
    def __init__(self, headless: bool = True):
        """Initialize the Selenium downloader.
        
        Args:
            headless: Run Chrome in headless mode (no visible window)
        """
        self.headless = headless
        self.driver = None
        
    def _setup_driver(self):
        """Setup Chrome driver with appropriate options and retry logic."""
        try:
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
        except ImportError:
            logger.error("webdriver_manager not installed. Please run: pip install webdriver-manager")
            raise

        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        # Critical options for stability
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--remote-debugging-port=9222') # Fix for DevToolsActivePort file doesn't exist
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--log-level=3')
        
        # Eager loading strategy
        chrome_options.page_load_strategy = 'eager'
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Initializing Chrome driver (attempt {attempt + 1}/{max_retries})...")
                
                # Use webdriver_manager to automatically install/update driver
                service = Service(ChromeDriverManager().install())
                
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.set_page_load_timeout(60)  # Increased timeout
                logger.info("Chrome driver initialized successfully")
                return
            except Exception as e:
                logger.warning(f"Driver initialization failed (attempt {attempt + 1}): {e}")
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    raise Exception(f"Failed to initialize Chrome driver: {e}")
        
    def _get_page_height(self) -> int:
        """Get the current page height."""
        return self.driver.execute_script("return document.body.scrollHeight")
    
    def _get_scroll_position(self) -> int:
        """Get current scroll position."""
        return self.driver.execute_script("return window.pageYOffset")
    
    def _scroll_to(self, position: int):
        """Scroll to a specific position."""
        self.driver.execute_script(f"window.scrollTo(0, {position});")
        
    def _count_loaded_pages(self) -> int:
        """Count how many pages have been loaded."""
        try:
            pages = self.driver.find_elements(By.CLASS_NAME, "outer_page")
            return len(pages)
        except:
            return 0
    
    def _auto_scroll_and_load(self, 
                             check_stop: Optional[Callable[[], bool]] = None,
                             scroll_pause: float = 1.5) -> int:
        """Auto-scroll to trigger lazy loading of all pages.
        
        Args:
            check_stop: Callback to check if download should stop
            scroll_pause: Time to wait after each scroll (seconds)
            
        Returns:
            Number of pages loaded
        """
        logger.info("Starting auto-scroll to load all pages...")
        
        last_height = self._get_page_height()
        scroll_position = 0
        page_count = 0
        no_new_content_count = 0
        
        while True:
            if check_stop and check_stop():
                logger.info("Download stopped by user")
                break
                
            # Count pages before scroll
            pages_before = self._count_loaded_pages()
            
            # Scroll down by viewport height
            scroll_position += 800  # Scroll ~800px at a time
            self._scroll_to(scroll_position)
            
            # Wait for content to load
            time.sleep(scroll_pause)
            
            # Count pages after scroll
            pages_after = self._count_loaded_pages()
            
            if pages_after > pages_before:
                logger.info(f"Loaded {pages_after} pages (new: {pages_after - pages_before})")
                page_count = pages_after
                no_new_content_count = 0
            else:
                no_new_content_count += 1
            
            # Check if we've reached the bottom
            new_height = self._get_page_height()
            current_position = self._get_scroll_position()
            
            # Stop if:
            # 1. We're at the bottom AND no new content for 3 scrolls
            # 2. OR we've scrolled past the page height
            if (current_position + 1080 >= new_height and no_new_content_count >= 3) or \
               (scroll_position >= new_height):
                logger.info(f"Reached end of document. Total pages loaded: {page_count}")
                break
                
            last_height = new_height
            
        return page_count
    
    def _dismiss_cookie_banner(self):
        """Hide cookie consent banner and toolbar using JavaScript."""
        try:
            logger.info("Dismissing cookie banner and toolbars...")
            
            # JavaScript to click accept and hide elements
            hide_script = """
            // 1. Try to click 'Accept All' or 'Save' buttons first
            try {
                var acceptBtns = document.querySelectorAll('.osano-cm-accept-all, .osano-cm-accept, .osano-cm-save, button[class*="osano-cm-accept"]');
                acceptBtns.forEach(function(btn) {
                    console.log('Clicking accept button:', btn);
                    btn.click();
                });
            } catch(e) { console.log('Error clicking accept:', e); }

            // 2. Force hide elements with a small delay to ensure they don't reappear
            setTimeout(function() {
                var selectors = [
                    '.osano-cm-window__dialog', 
                    '.osano-cm-dialog', 
                    '.osano-cm-window',
                    '.osano-cm-info-dialog-header',
                    'div[id^="osano-cm-window"]'
                ];
                
                selectors.forEach(function(sel) {
                    var elements = document.querySelectorAll(sel);
                    elements.forEach(function(el) {
                        el.style.setProperty('display', 'none', 'important');
                        el.style.setProperty('visibility', 'hidden', 'important');
                        el.style.setProperty('opacity', '0', 'important');
                        el.style.setProperty('z-index', '-9999', 'important');
                    });
                });
                
                // Hide toolbars
                var toolbars = document.querySelectorAll('.toolbar_top, .toolbar_bottom');
                toolbars.forEach(function(el) {
                    el.style.setProperty('display', 'none', 'important');
                    el.style.setProperty('visibility', 'hidden', 'important');
                });
                
                console.log('Cookie banners and toolbars hidden');
            }, 500);
            """
            
            self.driver.execute_script(hide_script)
            time.sleep(1.0) # Wait a bit for the script to take effect
            logger.info("Cookie banner dismissal script executed")
            
        except Exception as e:
            logger.warning(f"Could not hide cookie banner/toolbar: {e}")
    
    def _get_page_elements(self):
        """Get all loaded page elements."""
        try:
            return self.driver.find_elements(By.CLASS_NAME, "outer_page")
        except:
            return []
    
    def _scroll_to_element(self, element):
        """Scroll to make an element visible in viewport."""
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'start', behavior: 'smooth'});", element)
        time.sleep(0.5)
    
    def _capture_as_image_pdf(self, element, output_path: str) -> bool:
        """Capture element as screenshot and convert to PDF."""
        try:
            from PIL import Image
            import io
            
            # Take screenshot of the element
            png_data = element.screenshot_as_png
            
            # Convert to PDF using Pillow
            image = Image.open(io.BytesIO(png_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
                
            image.save(output_path, "PDF", resolution=100.0)
            logger.info(f"Captured page as image PDF: {output_path}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to capture image PDF: {e}")
            return False

    def download_as_pdf(self, 
                       url: str, 
                       output_path: str,
                       check_stop: Optional[Callable[[], bool]] = None) -> bool:
        """Download Scribd document as PDF by capturing each page separately and merging.
        
        Args:
            url: Scribd document URL
            output_path: Path to save PDF file
            check_stop: Callback to check if download should stop
            
        Returns:
            True if successful, False otherwise
        """
        import os
        import base64
        temp_pdfs = []
        
        try:
            self._setup_driver()
            
            # Navigate to the embed URL
            doc_id = self._extract_doc_id(url)
            if not doc_id:
                logger.error("Could not extract document ID from URL")
                return False
                
            embed_url = f"https://www.scribd.com/embeds/{doc_id}/content"
            logger.info(f"Loading document: {embed_url}")
            
            self.driver.get(embed_url)
            
            # Wait for initial content to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "document_scroller"))
            )
            
            # Dismiss cookie banner
            self._dismiss_cookie_banner()
            
            # Auto-scroll to load all pages
            page_count = self._auto_scroll_and_load(check_stop)
            
            if check_stop and check_stop():
                return False
            
            # Get all page elements
            pages = self._get_page_elements()
            logger.info(f"Found {len(pages)} pages to capture")
            
            if not pages:
                logger.error("No pages found to capture")
                return False
            
            # Create temp directory for individual PDFs
            temp_dir = os.path.join(os.path.dirname(output_path), f"temp_{doc_id}")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Capture each page as separate PDF
            for i, page in enumerate(pages, 1):
                if check_stop and check_stop():
                    logger.info("Download stopped by user")
                    return False
                
                # Scroll to page
                self._scroll_to_element(page)
                time.sleep(0.5)
                
                # Capture this page as PDF with retry and fallback
                temp_pdf_path = os.path.join(temp_dir, f"page_{i:03d}.pdf")
                max_retries = 3
                captured = False
                
                for attempt in range(max_retries):
                    try:
                        logger.info(f"Capturing page {i}/{len(pages)} (attempt {attempt + 1}/{max_retries})...")
                        
                        # Try standard PDF print first
                        try:
                            result = self.driver.execute_cdp_cmd("Page.printToPDF", {
                                "printBackground": True,
                                "landscape": False,
                                "paperWidth": 8.5,
                                "paperHeight": 11,
                                "marginTop": 0,
                                "marginBottom": 0,
                                "marginLeft": 0,
                                "marginRight": 0,
                                "preferCSSPageSize": True,
                                "pageRanges": "1"
                            })
                            
                            with open(temp_pdf_path, 'wb') as f:
                                f.write(base64.b64decode(result['data']))
                            
                            captured = True
                            logger.info(f"✓ Page {i} captured successfully (PrintToPDF)")
                            break
                        except Exception as pdf_err:
                            logger.warning(f"PrintToPDF failed: {pdf_err}")
                            # Fallback to screenshot
                            if self._capture_as_image_pdf(page, temp_pdf_path):
                                captured = True
                                logger.info(f"✓ Page {i} captured successfully (Screenshot Fallback)")
                                break
                            else:
                                raise pdf_err # Re-raise to trigger retry logic
                        
                    except Exception as e:
                        logger.warning(f"Failed to capture page {i} (attempt {attempt + 1}): {e}")
                        if attempt < max_retries - 1:
                            time.sleep(1)
                        else:
                            logger.error(f"Failed to capture page {i} after {max_retries} attempts")
                
                if not captured:
                    # Create a blank PDF as placeholder if all else fails
                    self._create_blank_pdf(temp_pdf_path)
                
                temp_pdfs.append(temp_pdf_path)
            
            # Merge all PDFs
            logger.info("Merging PDFs...")
            self._merge_pdfs(temp_pdfs, output_path)
            
            # Cleanup temp files
            logger.info("Cleaning up temporary files...")
            for pdf in temp_pdfs:
                try:
                    os.remove(pdf)
                except:
                    pass
            try:
                os.rmdir(temp_dir)
            except:
                pass
                
            logger.info(f"PDF saved to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading PDF: {e}", exc_info=True)
            return False
        finally:
            if self.driver:
                self.driver.quit()
    
    def _create_blank_pdf(self, output_path: str):
        """Create a blank PDF as placeholder when capture fails."""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            c = canvas.Canvas(output_path, pagesize=letter)
            c.drawString(100, 750, "Page capture failed")
            c.save()
            logger.info(f"Created blank PDF placeholder: {output_path}")
        except ImportError:
            # If reportlab not available, create minimal PDF manually
            minimal_pdf = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000052 00000 n
0000000101 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
169
%%EOF"""
            with open(output_path, 'wb') as f:
                f.write(minimal_pdf)
            logger.info(f"Created minimal blank PDF: {output_path}")
        except Exception as e:
            logger.error(f"Failed to create blank PDF: {e}")
    
    def _merge_pdfs(self, pdf_files: list, output_path: str):
        """Merge multiple PDF files into one.
        
        Args:
            pdf_files: List of PDF file paths to merge
            output_path: Output path for merged PDF
        """
        try:
            from PyPDF2 import PdfMerger
            
            merger = PdfMerger()
            for pdf in pdf_files:
                merger.append(pdf)
            
            merger.write(output_path)
            merger.close()
            logger.info(f"Successfully merged {len(pdf_files)} PDFs")
            
        except ImportError:
            logger.error("PyPDF2 not installed. Installing...")
            import subprocess
            subprocess.check_call(["pip", "install", "PyPDF2"])
            # Retry
            self._merge_pdfs(pdf_files, output_path)
        except Exception as e:
            logger.error(f"Error merging PDFs: {e}", exc_info=True)
            raise
                
                
    def download_as_html(self,
                        url: str,
                        output_path: str,
                        check_stop: Optional[Callable[[], bool]] = None) -> bool:
        """Download Scribd document as HTML with all content loaded.
        
        Args:
            url: Scribd document URL
            output_path: Path to save HTML file
            check_stop: Callback to check if download should stop
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._setup_driver()
            
            # Navigate to the embed URL
            doc_id = self._extract_doc_id(url)
            if not doc_id:
                logger.error("Could not extract document ID from URL")
                return False
                
            embed_url = f"https://www.scribd.com/embeds/{doc_id}/content"
            logger.info(f"Loading document: {embed_url}")
            
            self.driver.get(embed_url)
            
            # Wait for initial content to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "document_scroller"))
            )
            
            # Auto-scroll to load all pages
            page_count = self._auto_scroll_and_load(check_stop)
            
            if check_stop and check_stop():
                return False
            
            # Get the full page source
            logger.info("Extracting HTML content...")
            html_content = self.driver.page_source
            
            # Save HTML
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            logger.info(f"HTML saved to: {output_path} ({page_count} pages)")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading HTML: {e}", exc_info=True)
            return False
        finally:
            if self.driver:
                self.driver.quit()
    
    @staticmethod
    def _extract_doc_id(url: str) -> Optional[str]:
        """Extract document ID from Scribd URL.
        
        Supports:
        - https://www.scribd.com/document/[id]/title
        - https://www.scribd.com/doc/[id]/title
        - https://www.scribd.com/embeds/[id]/content
        """
        import re
        
        # Try to match document/doc/embeds patterns
        match = re.search(r'(?:doc|document|embeds)/(\d+)', url)
        if match:
            doc_id = match.group(1)
            
            # Log if we're converting a document URL to embed URL
            if '/document/' in url or '/doc/' in url:
                logger.info(f"Extracted document ID: {doc_id}")
                logger.info(f"Will use embed URL: https://www.scribd.com/embeds/{doc_id}/content")
            elif '/embeds/' in url:
                logger.info(f"Using embed URL directly with ID: {doc_id}")
            
            return doc_id
        
        logger.error(f"Could not extract document ID from URL: {url}")
        return None


def download_with_selenium(url: str, 
                          mode: str,
                          output_dir: Optional[str] = None,
                          check_stop: Optional[Callable[[], bool]] = None) -> None:
    """Download Scribd document using Selenium.
    
    Args:
        url: Scribd document URL
        mode: Download mode ('pdf' or 'html')
        output_dir: Output directory
        check_stop: Callback to check if download should stop
    """
    downloader = ScribdSeleniumDownloader(headless=True)
    
    # Determine output path
    doc_id = ScribdSeleniumDownloader._extract_doc_id(url)
    if not doc_id:
        logger.error("Invalid Scribd URL")
        return
        
    if output_dir:
        import os
        os.makedirs(output_dir, exist_ok=True)
        if mode == 'pdf':
            output_path = os.path.join(output_dir, f"Scribd_{doc_id}.pdf")
        else:
            output_path = os.path.join(output_dir, f"Scribd_{doc_id}.html")
    else:
        output_path = f"Scribd_{doc_id}.{'pdf' if mode == 'pdf' else 'html'}"
    
    # Download
    if mode == 'pdf':
        downloader.download_as_pdf(url, output_path, check_stop)
    else:
        downloader.download_as_html(url, output_path, check_stop)
