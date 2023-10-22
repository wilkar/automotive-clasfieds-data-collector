OTOMOTO_BRANDS: list = ["abarth"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/118.0",
    "Accept": "application/graphql+json, application/json",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://www.otomoto.pl/osobowe",
    "content-type": "application/json",
    "newrelic": "eyJ2IjpbMCwxXSwiZCI6eyJ0eSI6IkJyb3dzZXIiLCJhYyI6IjE2OTUzNjYiLCJhcCI6IjE4MzQ3OTM5MjAiLCJpZCI6Ijk1NmRjMzc0ZGIyNTk3NGEiLCJ0ciI6ImM2YzdkN2ZhM2E4MjExMmMyMzA4NGI2MjExZGE4YjAwIiwidGkiOjE2OTc3NDgzMTg1NDQsInRrIjoiMTcwNTIyMiJ9fQ==",
    "sitecode": "otomotopl",
    "traceparent": "00-c6c7d7fa3a82112c23084b6211da8b00-956dc374db25974a-01",
    "tracestate": "1705222@nr=0-0-1695366-1834793920-956dc374db25974a-c6c7d7fa3a82112c23084b6211da8b00-1-1697748318.54457-1661865785.3325",
    "Origin": "https://www.otomoto.pl",
    "Connection": "keep-alive",
    "TE": "Trailers",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}

OTOMOTO_PAGINATION_LIMIT = 500
OTOMOTO_MAIN_PAGE = "https://www.otomoto.pl/"
