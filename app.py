import requests
from bs4 import BeautifulSoup
import sqlite3


DB_FILE = "scrapes.db"


def init_db():
    conn = None
    
    try:
        conn = sqlite3.connect(DB_FILE)    
        cursor = conn.cursor()
        
        query = '''
            CREATE TABLE IF NOT EXISTS scrapes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote TEXT NOT NULL,
                author TEXT NOT NULL,
                tags TEXT NOT NULL,
                page INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''
        
        cursor.execute(query)
        
        conn.commit()
    except sqlite3.Error as e:
        print(f"❌ ERROR: Database error occurred: {e}")        
    finally:
        if conn:
            conn.close()


def save_current_page_to_db(data, current_page):
    conn = None
    
    try: 
        conn = sqlite3.connect(DB_FILE)    
        cursor = conn.cursor()
        
        query = '''
            INSERT INTO scrapes (
                quote,
                author,
                tags,
                page
            ) VALUES (?, ?, ?, ?)
        '''
        
        for quote in data:
            tags_str = ", ".join(quote['tags'])
            
            cursor.execute(query, (quote['quote'], quote['author'], tags_str, current_page))
        
        conn.commit()
        
        print(f"✅ Scraped data added successfully!")
    except sqlite3.Error as e:
        print(f"❌ ERROR: Database error occurred: {e}")    
    finally:
        if conn:
            conn.close()


def save_to_file(soup):
    with open("index.html", "w", encoding="utf-8") as file:
        file.write(str(soup, ))


def find_maximum_page(url):
    print("Finding max pages, please wait...")
    max_page = 1
    current_page = 1
    
    while True:
        retries = 0
        while True:
            soup = scrape(url, current_page)
            retries += 1
            
            if soup or retries == 10:
                break
            
        data = extract_data(soup)
        
        print(max_page, end=" -> ")
        
        if not data:
            print("Found!")
            return max_page
        
        max_page = current_page
        current_page += 1
        

def extract_data(soup):
    data = []
    
    divs = soup.find_all('div', class_='quote')
    
    for div in divs:
        quote = div.find('span', class_='text').text
        author = div.find('small', class_='author').text
        tags = {tag.text for tag in div.find_all('a', class_="tag")}
        
        data.append({
            'quote': quote,
            'author': author,
            'tags': tags
        })
    
    return data
        

def require_soup(soup):
    if not soup:
        print("\n🚨 Please scrape website first (option 1)\n")
        return False
    return True


def print_quotes(data):
    for quote in data: 
        print(f"Quote: {quote['quote']}\n")
    

def print_authors(data):        
    for quote in data:
        print(f"Author: {quote['author']}\n")


def print_tags(data):
    tags = set()
    
    for quote in data:
        for tag in quote['tags']:
            tags.add(tag)
    
    for tag in tags: 
        print(f"Tag: {tag}\n")


def print_quotes_authors_tags(data):        
    for quote in data: 
        print("-" * 100)
            
        print(f"Quote: {quote['quote']}")
        
        print(f"By: {quote['author']}\n")
            
        print("Tags: ", end = "")
        print(*quote['tags'], sep=", ")
            
        print("-" * 100 + "\n")


def scrape(url, page_to_scrape):
    try:
        if page_to_scrape != 1:
            url = url + f"page/{page_to_scrape}/"
            
        response = requests.get(url, timeout=10)
        response.raise_for_status() 
        
        return BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.HTTPError as errh:
        print(f"❌ ERROR: HTTP Error: {errh}")
    except requests.exceptions.ConnectionError as errc:
        print(f"❌ ERROR: Error Connecting: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"❌ ERROR: Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"❌ ERROR: An unexpected error occurred: {err}")
        
    return None


def main():
    init_db()
    url = "http://quotes.toscrape.com/"
    current_page = 0
    max_page = None
    soup = None
    data = []
    
    while True:
        print("\n" + "-" * 66)
        print(">>>================ WELCOME TO THE WEB SCRAPER ================<<<")
        print("-" * 66 + "\n")

        print("1. Scrape the website \"quotes.toscrape.com\" (restarts from page 1)")
        print("2. Scrape the next page")
        print("3. Print Just Quotes")
        print("4. Print Just Authors")
        print("5. Print Just Tags")
        print("6. Print Quotes with their Authors and Tags")
        print("7. Save to DB")
        print("8. Exit")
        
        choice = input("\n-> Please type your input: ").strip().lower()
        
        match choice:
            case "1":
                current_page = 1
                soup = scrape(url, current_page)
                if soup:
                    data = extract_data(soup)
                    print(f"\n✅ Scraped {len(data)} quotes from page {current_page}\n")
            case "2":
                next_page = current_page + 1
                
                if not max_page:
                    max_page = find_maximum_page(url)
                
                if next_page > max_page:
                    print(f"\n🚨 Already at last page ({max_page})\n")
                    continue
                
                soup = scrape(url, next_page)

                if soup:
                    current_page += 1
                    data = extract_data(soup)
                    print(f"\n✅ Scraped {len(data)} quotes from page {next_page}\n")
                else:
                    print(f"\n❌ Failed to scrape page {next_page}. Still on page {current_page}\n")
            case "3":
                if require_soup(soup):
                    print_quotes(data)
            case "4":
                if require_soup(soup):
                    print_authors(data)
            case "5":
                if require_soup(soup):
                    print_tags(data)
            case "6":
                if require_soup(soup):
                    print_quotes_authors_tags(data)
            case "7":
                if require_soup(soup):
                    save_current_page_to_db(data, current_page)
            case "8" | "exit":
                print("\nBye!\n")
                break
            case _:
                print("\n🚨 Please only enter from the given options.\n")
    
    
if __name__ == "__main__":
    main()