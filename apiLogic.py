import pysolr
import requests

SOLR_URL = "http://localhost:8983/solr/userCollection"  # Update with your Solr URL
store_id = "10001"
channel_id = "10001"
client_id = "10001"
request_id = "bbiibhu"
username = "codiecon"


def get_user_data(user_id):
    solr = pysolr.Solr(SOLR_URL, timeout=10)

    # Construct the Solr query with the user_id
    solr_query = f"userId:{user_id}"

    # Execute the Solr query and return the documents
    results = solr.search(solr_query, rows=10)  # You can adjust the number of rows as needed
    return results.docs


def get_savings_data(user_id):
    SOLR_URL = "http://localhost:8983/solr/orderCollection"  # Update with your Solr URL
    solr = pysolr.Solr(SOLR_URL, timeout=10)
    date_range = f"[NOW-12YEAR TO NOW]"
    # Construct the Solr query with the user_id
    solr_query = f"userId:{user_id} AND orderDate:{date_range}"
    # Execute the Solr query and return the documents
    params = {
        'fl': 'discountAvailed',
        'stats': 'true',
        'stats.field': '{!sum=true}discountAvailed'
    }
    results = solr.search(solr_query, **params)  # You can adjust the number of rows as needed
    total_discount = results.stats['stats_fields']['discountAvailed']['sum']

    solr_query_last_month = f"userId:{user_id} AND orderDate:{date_range}"
    # Execute the Solr query and return the documents
    results_month = solr.search(solr_query_last_month, **params)
    total_discount_month = results.stats['stats_fields']['discountAvailed']['sum']

    return total_discount


def get_pre_order_products_data(user_id):
    SOLR_URL = "http://xsearch-solr-1.qa2-sg.cld:8983/solr/retailCollection"  # Update with your Solr URL
    solr = pysolr.Solr(SOLR_URL, timeout=10)

    # Construct the Solr query with the user_id
    true = "true"
    solr_query = f"*:* AND isPreorder:{true}"
    print(solr_query)

    # Execute the Solr query and return the documents
    results = solr.search(solr_query, rows=10)  # You can adjust the number of rows as needed
    return results.docs


def get_user_recommended_categories(user_id):
    SOLR_URL = "http://brs-solr-1.qa2-sg.cld:8983/solr/userProfileCollection"  # Update with your Solr URL
    solr = pysolr.Solr(SOLR_URL, timeout=10)

    # Construct the Solr query with the user_id
    solr_query = f"userId:{user_id}"
    # print(solr_query)

    # Execute the Solr query and return the documents
    results = solr.search(solr_query, rows=10)  # You can adjust the number of rows as needed
    for result in results.docs:
        # Assuming 'discount' is a field in your Solr schema
        categories = []
        if 'categories' in result:
            categories += result['categories']
        # print(categories)
    return categories


def get_user_recommended_categories_names(user_id):
    categories = get_user_recommended_categories(user_id)
    category_data_array = []

    for category_code in categories:
        category_data = fetch_category_data(category_code, store_id, channel_id, client_id, request_id, username)
        # print(category_data)
        if category_data:
            category_data_array.append(category_data)
    return category_data_array


def fetch_category_data(category_code, store_id, channel_id, client_id, request_id, username):
    base_url = "http://product-category-base.qa2-sg.cld/product-category-base/api/category/categoryCode/"
    api_url = f"{base_url}{category_code}?storeId={store_id}&channelId={channel_id}&clientId={client_id}&requestId={request_id}&username={username}"

    try:
        response = requests.get(api_url)
        # print(api_url)
        response.raise_for_status()
        category_data = response.json()
        # print(category_data)
        name = category_data.get("value", {}).get("nameEnglish")
        return name
        # Raise an exception for bad responses (4xx and 5xx status codes)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for category {category_code}: {e}")
        return None


def get_relevant_category_products(user_id):
    categories = get_user_recommended_categories(user_id)
    SOLR_URL = "http://xsearch-solr-1.qa2-sg.cld:8983/solr/retailCollection"  # Update with your Solr URL
    solr = pysolr.Solr(SOLR_URL, timeout=10)

    # Construct the Solr query with the user_id
    category_codes = " OR ".join(categories)
    solr_query = f"salesCatalogCategoryIds:{category_codes}"
    print(solr_query)

    # Execute the Solr query and return the documents
    results = solr.search(solr_query, rows=10)  # You can adjust the number of rows as needed
    return results.docs


def get_relevant_category_products_sort_by_price(user_id):
    categories = get_user_recommended_categories(user_id)
    SOLR_URL = "http://xsearch-solr-1.qa2-sg.cld:8983/solr/retailCollection"  # Update with your Solr URL
    solr = pysolr.Solr(SOLR_URL, timeout=10)

    # Construct the Solr query with the user_id
    category_codes = " OR ".join(categories)
    solr_query = f"salesCatalogCategoryIds:{category_codes}"
    print(solr_query)
    sort_field = "salePrice"
    sort_order = "asc"
    # Execute the Solr query and return the documents
    results = solr.search(solr_query, sort=f"{sort_field} {sort_order}", rows=10)  # You can adjust the number of rows as needed
    return results.docs