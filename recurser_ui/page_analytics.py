# analytics.py
import streamlit as st
import os
import requests
import bs4

SEARCH_ENGINE = os.getenv('SEARCH_ENGINE', 'search-engine')
SEARCH_ENGINE_PORT = os.getenv('SEARCH_ENGINE_PORT', '5150')

def streamlit_page():
    st.title("📊 Analytics Dashboard")
    # Your analytics code here
    if st.button("Test web search"):
        with st.spinner("Searching..."):
            response = requests.post(f"http://{SEARCH_ENGINE}:{SEARCH_ENGINE_PORT}/query", timeout=60, json={"search_query": "What is the capital of France?"})
            st.write(response)
            print(response)
            data = response.json()
            if 'response' in data:
                st.write(data['response'])
            else:
                st.error(f"❌ Error: {'Unknown error'}")#
    if st.button("Test scraper"):
        with st.spinner("Searching..."):
            response = requests.post(f"http://{SEARCH_ENGINE}:{SEARCH_ENGINE_PORT}/query", timeout=60, json={"search_query": "What is the capital of France?"})
            st.write(response)
            print(response)
            data = response.json()
            if 'response' in data:
                results = data['response']
                if not results or not isinstance(results, list):
                    st.error("❌ No results or unexpected format from search engine.")
                else:
                    scraped_results = []
                    for idx, result in enumerate(results):
                        url = result.get('href') or result.get('url')
                        if not url:
                            continue
                        try:
                            page_resp = requests.get(url, timeout=10)
                            soup = bs4.BeautifulSoup(page_resp.text, 'html.parser')
                            # Get title and first 300 chars of text as summary
                            title = soup.title.string if soup.title else url
                            text = soup.get_text(separator=' ', strip=True)
                            summary = text[:300] + ('...' if len(text) > 300 else '')
                            scraped_results.append({
                                'url': url,
                                'title': title,
                                'summary': summary
                            })
                        except Exception as e:
                            scraped_results.append({
                                'url': url,
                                'title': 'Error',
                                'summary': f'Failed to scrape: {e}'
                            })
                    if scraped_results:
                        for item in scraped_results:
                            st.markdown(f"**[{item['title']}]({item['url']})**")
                            st.write(item['summary'])
                            st.write('---')
                    else:
                        st.error("❌ No URLs found in search results.")
            else:
                st.error(f"❌ Error: {'Unknown error'}")