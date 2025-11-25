#!/usr/bin/env python
import argparse
import base64
import json
import logging
import os
import re
import shutil
import sys
from typing import Optional, Callable
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def get_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="A Scribd-Downloader that actually works"
    )

    parser.add_argument(
        "doc", metavar="DOC", type=str, nargs="?", help="scribd document to download"
    )
    parser.add_argument(
        "-i",
        "--images",
        help="download document made up of images",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--html",
        help="download document as HTML",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--gui",
        help="launch the graphical user interface",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-o",
        "--output",
        help="output directory",
        type=str,
        default=None,
    )

    return parser.parse_args()


def fix_encoding(query: str) -> str:
    """Fix encoding for Python 2 compatibility (kept for legacy reasons)."""
    if sys.version_info > (3, 0):
        return query
    else:
        return query.encode("utf-8")  # type: ignore


def extract_jsonp_content(response: str) -> Optional[str]:
    """Extract content from JSONP response safely."""
    # Pattern to match: window.page123_callback(["content"]);
    # We want to extract ["content"] part and parse it as JSON
    match = re.search(r'window\.page\d+_callback\((.*)\);', response, re.DOTALL)
    if match:
        json_str = match.group(1)
        try:
            data = json.loads(json_str)
            if isinstance(data, list) and len(data) > 0:
                return data[0]
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON from JSONP response")
    return None


def get_base64_image(img_url: str) -> str:
    """Download image and convert to Base64."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(img_url, headers=headers, timeout=30)
        if r.status_code == 200:
            b64 = base64.b64encode(r.content).decode('utf-8')
            mime_type = r.headers.get('Content-Type', 'image/jpeg')
            return f"data:{mime_type};base64,{b64}"
    except Exception as e:
        logger.warning(f"Failed to convert image {img_url} to base64: {e}")
    return img_url


def extract_css(soup: BeautifulSoup, base_url: str) -> str:
    """Extract and combine CSS from link tags and style tags."""
    combined_css = ""
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # Link tags
    for link in soup.find_all("link", rel="stylesheet"):
        href = link.get('href')
        if href:
            css_url = urljoin(base_url, href)
            try:
                r = requests.get(css_url, headers=headers, timeout=30)
                if r.status_code == 200:
                    combined_css += f"\n/* Source: {css_url} */\n{r.text}"
            except Exception as e:
                logger.warning(f"Failed to fetch CSS {css_url}: {e}")

    # Style tags
    for style in soup.find_all("style"):
        if style.string:
            combined_css += f"\n{style.string}"
            
    return combined_css


def save_image(jsonp: str, imagename: str) -> None:
    """Download and save an image from a JSONP URL."""
    try:
        replacement = jsonp.replace("/pages/", "/images/").replace("jsonp", "jpg")
        logger.info(f"Downloading image: {imagename}")
        response = requests.get(replacement, stream=True, timeout=30)
        response.raise_for_status()

        with open(imagename, "wb") as out_file:
            shutil.copyfileobj(response.raw, out_file)
    except requests.RequestException as e:
        logger.error(f"Failed to download image {imagename}: {e}")


def save_text(jsonp: str, filename: str) -> None:
    """Extract and save text from a JSONP URL."""
    try:
        response = requests.get(url=jsonp, timeout=30).text
        content = extract_jsonp_content(response)
        
        if not content:
            logger.warning(f"Could not extract content from {jsonp}")
            return

        soup_content = BeautifulSoup(content, "html.parser")

        with open(filename, "a", encoding="utf-8") as feed:
            for x in soup_content.find_all("span", {"class": "a"}):
                xtext = fix_encoding(x.get_text())
                logger.debug(f"Extracted text: {xtext[:50]}...")
                extraction = xtext + "\n"
                feed.write(extraction)
    except requests.RequestException as e:
        logger.error(f"Failed to fetch text content: {e}")
    except Exception as e:
        logger.error(f"Error processing text content: {e}")


def save_html(jsonp: str, filename: str, page_no: int, base_url: str) -> None:
    """Extract and save HTML content from a JSONP URL with offline support."""
    try:
        response = requests.get(url=jsonp, timeout=30).text
        content = extract_jsonp_content(response)
        
        if not content:
            logger.warning(f"Could not extract content from {jsonp}")
            return

        # Parse content to process images
        soup = BeautifulSoup(content, "html.parser")
        
        # Convert images to Base64
        for img in soup.find_all("img"):
            src = img.get("src")
            if src:
                abs_url = urljoin(base_url, src)
                img["src"] = get_base64_image(abs_url)
                # Remove orig attribute to prevent conflicts
                if img.has_attr("orig"):
                    del img["orig"]

        # Wrap content in the structure requested by user
        html_fragment = f'''
        <div class="outer_page" id="outer_page_{page_no}" style="margin-bottom: 10px; border: 1px solid #ccc;">
            {str(soup)}
        </div>
        '''
        
        with open(filename, "a", encoding="utf-8") as f:
            f.write(html_fragment)
            
    except requests.RequestException as e:
        logger.error(f"Failed to fetch HTML content: {e}")
    except Exception as e:
        logger.error(f"Error processing HTML content: {e}")


def save_content(jsonp: str, mode: str, train: int, title: str, output_dir: Optional[str] = None, base_url: str = "") -> int:
    """Decide whether to save image, text, or HTML based on mode."""
    if not jsonp:
        return train

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        base_path = os.path.join(output_dir, title)
    else:
        base_path = title

    if mode == "images":
        imagename = f"{base_path}_{train}.jpg"
        save_image(jsonp, imagename)
    elif mode == "html":
        filename = f"{base_path}.html"
        save_html(jsonp, filename, train, base_url)
    else: # text
        filename = f"{base_path}.txt"
        save_text(jsonp, filename)
    
    return train + 1


def sanitize_title(title: str) -> str:
    """Remove forbidden characters from title."""
    forbidden_chars = " *\"/\\<>:|?"
    replace_char = "_"

    for ch in forbidden_chars:
        title = title.replace(ch, replace_char)

    return title


def get_doc_id(url: str) -> Optional[str]:
    """Extract document ID from Scribd URL.
    
    Supports:
    - https://www.scribd.com/document/[id]/title
    - https://www.scribd.com/doc/[id]/title
    - https://www.scribd.com/embeds/[id]/content
    """
    match = re.search(r'(?:doc|document|embeds)/(\d+)', url)
    if match:
        doc_id = match.group(1)
        
        # Log if we're converting a document URL to embed URL
        if '/document/' in url or '/doc/' in url:
            logger.info(f"Extracted document ID: {doc_id}")
            logger.info(f"Converting to embed URL for better compatibility")
        elif '/embeds/' in url:
            logger.info(f"Using embed URL directly with ID: {doc_id}")
        
        return doc_id
    
    logger.error(f"Could not extract document ID from URL: {url}")
    return None

def get_scribd_document(url: str, mode: str, output_dir: Optional[str] = None, check_stop: Optional[Callable[[], bool]] = None) -> None:
    """Main logic to fetch document and download content."""
    try:
        doc_id = get_doc_id(url)
        if not doc_id:
            logger.error("Could not extract document ID from URL.")
            return

        # For HTML mode, use the embed URL for better rendering
        if mode == "html":
            target_url = f"https://www.scribd.com/embeds/{doc_id}/content"
            logger.info(f"Using embed URL for HTML mode: {target_url}")
        else:
            target_url = url

        logger.info(f"Fetching document: {target_url}")
        response = requests.get(url=target_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")

        title_tag = soup.find("title")
        if not title_tag:
            # Fallback title if not found (embed page might have different title structure)
            title = f"Scribd_Document_{doc_id}"
        else:
            title = title_tag.get_text()
        
        title = sanitize_title(title)

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Saving to directory: {output_dir}")

        logger.info(f"Downloading {title} in {mode} mode")
        
        # Initialize HTML file if in HTML mode
        if mode == "html":
            if output_dir:
                html_path = os.path.join(output_dir, f"{title}.html")
            else:
                html_path = f"{title}.html"
            
            logger.info("Extracting CSS for offline viewing...")
            css_content = extract_css(soup, target_url)
            
            # Add custom CSS to center the document_scroller
            custom_css = """
            body { background-color: #f4f4f4; display: flex; justify-content: center; }
            .document_scroller { background-color: white; box-shadow: 0 0 10px rgba(0,0,0,0.1); padding: 20px; }
            .outer_page { margin-bottom: 10px; }
            """
            
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(f'<!DOCTYPE html>\n<html>\n<head><meta charset="utf-8"><title>{title}</title>\n<style>{css_content}\n{custom_css}</style>\n</head>\n<body>\n<div class="document_scroller">\n')

            # Extract inline pages from embed view
            inline_pages = soup.find_all("div", class_="outer_page")
            for page in inline_pages:
                # Process images to Base64
                for img in page.find_all("img"):
                    src = img.get("src")
                    if src:
                        abs_url = urljoin(target_url, src)
                        img["src"] = get_base64_image(abs_url)
                        # Remove orig attribute to prevent conflicts
                        if img.has_attr("orig"):
                            del img["orig"]
                
                # Write inline page to file
                with open(html_path, "a", encoding="utf-8") as f:
                    f.write(str(page))

        # Logic to find JSONP URLs in Embed Mode
        # Embed mode uses scripts with "contentUrl": "..."
        scripts = soup.find_all("script")
        train = 1
        
        # First, check for standard window.pageXX_callback (legacy/non-embed)
        has_legacy_callback = False
        for s in scripts:
            if s.string and "window.page" in s.string and "_callback" in s.string:
                has_legacy_callback = True
                break
        
        if has_legacy_callback:
             for opening in scripts:
                if check_stop and check_stop():
                    logger.info("Download stopped by user.")
                    break
                
                if not opening.string: continue
                
                # We need to handle the script content directly if it's not a list of strings
                inner_opening = opening.string
                
                portion1 = inner_opening.find("https://")
                if portion1 != -1:
                    portion2 = inner_opening.find(".jsonp")
                    if portion2 != -1:
                        jsonp = inner_opening[portion1 : portion2 + 6]
                        train = save_content(jsonp, mode, train, title, output_dir, base_url=target_url)

        # If no legacy callback, look for contentUrl in scripts (Embed Mode)
        else:
            logger.info("Parsing scripts for contentUrl...")
            for s in scripts:
                if check_stop and check_stop():
                    break
                
                if not s.string: continue
                
                # Find all occurrences of contentUrl: "..."
                # Regex to match JavaScript object notation: contentUrl: "url"
                matches = re.findall(r'contentUrl:\s*"(https://[^"]+\.jsonp)"', s.string)
                
                for jsonp in matches:
                    # Replace \u002F with / if needed (JSON escaping)
                    jsonp = jsonp.replace("\\u002F", "/")
                    
                    if check_stop and check_stop():
                        break
                        
                    train = save_content(jsonp, mode, train, title, output_dir, base_url=target_url)

        
        # Close HTML file
        if mode == "html":
             if output_dir:
                html_path = os.path.join(output_dir, f"{title}.html")
             else:
                html_path = f"{title}.html"
             with open(html_path, "a", encoding="utf-8") as f:
                f.write('\n</div>\n</body>\n</html>')

    except requests.RequestException as e:
        logger.error(f"Network error accessing document: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)


def command_line() -> None:
    args = get_arguments()
    
    if args.gui:
        from scribdl.gui import main
        main()
    else:
        if not args.doc:
            print("Error: Document URL is required unless using --gui")
            sys.exit(1)
        
        mode = "text"
        if args.images:
            mode = "images"
        elif args.html:
            mode = "html"
            
        get_scribd_document(args.doc, mode, args.output)


if __name__ == "__main__":
    command_line()
