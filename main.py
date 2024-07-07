import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from collections import defaultdict, Counter
from time import sleep
def extract_components(soup):
    components = {
        'buttons': len(soup.find_all('button')),
        'links': len(soup.find_all('a')),
        'images': len(soup.find_all('img')),
        'forms': len(soup.find_all('form')),
        'galleries': len(soup.find_all(class_=re.compile(r'.*gallery.*'))),
        'feeds': len(soup.find_all(class_=re.compile(r'.*feed.*'))),
        'cta_buttons': len(soup.find_all(class_=re.compile(r'.*cta.*'))),
    }
    return components
def get_html_structure(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return BeautifulSoup(response.text, 'html.parser')
        else:
            st.error(f"Failed to retrieve {url} (Status code: {response.status_code})")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while fetching {url}: {e}")
        return None
def get_internal_links(soup, base_url):
    internal_links = set()
    for link in soup.find_all('a', href=True):
        href = link['href']
        full_url = urljoin(base_url, href)
        if urlparse(full_url).netloc == urlparse(base_url).netloc:
            internal_links.add(full_url)
    return internal_links
def scan_website(base_url, max_pages=10):
    visited = set()
    to_visit = set([base_url])
    unique_layouts = set()
    components_count = defaultdict(Counter)
    
    while to_visit and len(visited) < max_pages:
        url = to_visit.pop()
        if url in visited:
            continue
        visited.add(url)
        
        soup = get_html_structure(url)
        if not soup:
            continue
        page_layout = str(soup.body)
        unique_layouts.add(page_layout)
    
        page_components = extract_components(soup)
        for component, count in page_components.items():
            components_count[component][url] += count
        internal_links = get_internal_links(soup, base_url)
        to_visit.update(internal_links - visited)
        
        progress.progress(len(visited) / max_pages)
        sleep(0.1)  
    return unique_layouts, components_count, visited
def display_results(unique_layouts, components_count, visited_urls):
    st.write(f"Scanned {len(visited_urls)} pages")
    st.write(f"Found {len(unique_layouts)} unique page layouts")
    
    st.write("### Component Summary:")
    for component, counts in components_count.items():
        total_count = sum(counts.values())
        st.write(f"- **{component.capitalize()}:** {total_count} instances across {len(counts)} pages")

    st.write("### Detailed Breakdown:")
    for component, counts in components_count.items():
        st.write(f"#### {component.capitalize()}:")
        for url, count in counts.items():
            st.write(f"- {url}: {count} instances")
st.title("Website Structure Scanner")
url = st.text_input("Enter the URL of the website to scan:")
max_pages = st.slider("Maximum number of pages to scan", 1, 100, 10)
progress = st.progress(0)

if url:
    st.write(f"Scanning {url} up to {max_pages} pages...")
    unique_layouts, components_count, visited_urls = scan_website(url, max_pages)
    display_results(unique_layouts, components_count, visited_urls)
    progress.progress(100)
