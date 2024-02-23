import feedparser
import re
import threading
import time
# from url_list import urls

urls=[
    "https://en.setopati.com/feed",
    "https://thehimalayantimes.com/feed/",
    "https://english.onlinekhabar.com/feed",
    "http://www.huffingtonpost.com/feeds/verticals/technology/news.xml",
    "http://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "http://www.theverge.com/rss/group/features/index.xml",

]


# Function to scrape articles from an RSS feed
def scrape_rss_feed(feed_url):
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries:
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "summary": entry.summary,
            "published": entry.published
        })
    return articles

# Function to remove HTML tags from a string
def remove_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

# Function to scrape and print articles from an RSS feed
def scrape_and_print_rss(feed_url, feed_name):
    print(f"Starting the RSS feed scraping job for {feed_name}...")
    start_time = time.time()
    articles = scrape_rss_feed(feed_url)
    for article in articles:
        summary_without_html = remove_html_tags(article['summary'])
        print(f"Title: {article['title']}")
        print(f"Link: {article['link']}")
        print(f"Summary: {summary_without_html}")
        print(f"Published: {article['published']}\n")
    end_time = time.time()
    print(f"Finished scraping {feed_name}. Time taken: {end_time - start_time} seconds\n")
    return articles

if __name__ == "__main__":
    # Create threads for scraping each RSS feed
    threads = []
    for url in urls:
        thread = threading.Thread(target=scrape_and_print_rss, args=(url, url))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    print("Both RSS feed scraping jobs have completed.")
