import pysolr
import requests
import json

from flask import jsonify

# import savingForecastModel

SOLR_URL = "http://localhost:8983/solr/userCollection"  # Update with your Solr URL
store_id = "10001"
channel_id = "10001"
client_id = "10001"
request_id = "bbiibhu"
username = "codiecon"


def get_user_data(user_id):
    global progress, current_batch
    solr = pysolr.Solr(SOLR_URL, timeout=10)

    # Construct the Solr query with the user_id
    solr_query = f"userId:{user_id}"

    results = solr.search(solr_query, rows=10)
    # Extract multivalued field from the Solr response
    multivalued_field_values = []
    for document in results.docs:
        if 'achieved' in document:
            multivalued_field_values.extend(document['achieved'])
        progress = document.get('progress')
        current_batch = document.get('currentBatch')

    # Create a list of URLs by replacing the placeholder with multivalued field values
    badge_urls = {
        f"{value}": f"https://raw.githubusercontent.com/akhilesh-k/temp-static-image-hosting/main/{value}.png"
        for i, value in enumerate(multivalued_field_values)
    }
    response_data = {
        "user_id": user_id,
        "achieved_badges": badge_urls,
        "progress": progress,
        "currentBatch": current_batch,
    }
    json_response = json.dumps(response_data)
    return response_data


def get_savings_data(user_id):
    SOLR_URL = "http://localhost:8983/solr/orderCollection"  # Update with your Solr URL
    solr = pysolr.Solr(SOLR_URL, timeout=10)
    date_range = f"[NOW-1YEAR TO NOW]"
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
    date_range_month = f"[NOW-1MONTH TO NOW]"
    solr_query_last_month = f"userId:{user_id} AND orderDate:{date_range_month}"
    # Execute the Solr query and return the documents
    results_month = solr.search(solr_query_last_month, **params)
    total_discount_month = results_month.stats['stats_fields']['discountAvailed']['sum']
    params1 = {
        'fl': 'savingPercentage',
        'stats': 'true',
        'stats.field': '{!sum=true}savingPercentage'
    }
    results_saving_percentage = solr.search(solr_query, **params1)
    total_discount_saving_percentage = results_saving_percentage.stats['stats_fields']['savingPercentage']['sum']

    api_response = {
        "total_discount_saving_percentage": total_discount_saving_percentage,
        "year_discount": total_discount,
        "month_discount": total_discount_month,
        # "saving_forecast": savingForecastModel.savings_forecast(total_discount)
    }
    return api_response


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


def get_pre_order_products_data_for_category(user_id):
    categories = get_user_recommended_categories(user_id)
    SOLR_URL = "http://xsearch-solr-1.qa2-sg.cld:8983/solr/retailCollection"  # Update with your Solr URL
    solr = pysolr.Solr(SOLR_URL, timeout=10)

    # Construct the Solr query with the user_id
    category_codes = " OR ".join(categories)
    true = "true"
    solr_query = f"salesCatalogCategoryIds:{category_codes} AND isPreorder:{true}"
    # Construct the Solr query with the user_id
    # solr_query = f"*:* AND isPreorder:{true}"
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
    results = solr.search(solr_query, sort=f"{sort_field} {sort_order}",
                          rows=10)  # You can adjust the number of rows as needed
    return results.docs


def get_all_badge_details():
    all_badge_details = [
        {
            "name": "Perfect Cart",
            "detail": "Bought more than 10+ products at once 10",
            "url": "https://raw.githubusercontent.com/akhilesh-k/temp-static-image-hosting/main/perfect-cart.png"
        },
        {
            "name": "Event Voyager",
            "detail": "Bought tickets for more than 5 events",
            "url": "https://raw.githubusercontent.com/akhilesh-k/temp-static-image-hosting/main/event-voyager.png"
        },
        {
            "name": "Show Savvy",
            "detail": "Bought tickets for more than 10 events",
            "url": "https://raw.githubusercontent.com/akhilesh-k/temp-static-image-hosting/main/show-savvy.png"
        },
        {
            "name": "Style Sculptor",
            "detail": "Bought a fashion product which was worth  5k",
            "url": "https://raw.githubusercontent.com/akhilesh-k/temp-static-image-hosting/main/style-sculptor.png"
        },
        {
            "name": "Glamour Guru",
            "detail": "Bought a fashion product which was worth  10k",
            "url": "https://raw.githubusercontent.com/akhilesh-k/temp-static-image-hosting/main/glamour-guru.png"
        },
        {
            "name": "Bundle Binge",
            "detail": "Bought more than 10+ products at once 10",
            "url": "https://raw.githubusercontent.com/akhilesh-k/temp-static-image-hosting/main/bundle-binge.png"
        },
        {
            "name": "Mega Saver",
            "detail": "Buying a product with more than  80%",
            "url": "https://raw.githubusercontent.com/akhilesh-k/temp-static-image-hosting/main/mega-saver.png"
        },
        {
            "name": "Ultra Saver",
            "detail": "Buying a product with more than 90%",
            "url": "https://raw.githubusercontent.com/akhilesh-k/temp-static-image-hosting/main/ultra-saver.png"
        },
        {
            "name": "Rush Gizmo",
            "detail": "Any tech product on 1st day",
            "url": "https://raw.githubusercontent.com/akhilesh-k/temp-static-image-hosting/main/gizmo-rush.png"
        },
        {
            "name": "Mobile Maestro",
            "detail": "Buying mobile in 1st hour of launch",
            "url": "https://raw.githubusercontent.com/akhilesh-k/temp-static-image-hosting/main/mobile-maestro.png"
        },
    ]
    return all_badge_details


def search_pickup_points_agp(lat, lon):
    # Get latitude and longitude from request parameters

    # Define the search query
    search_url = 'http://aggregate-platform-query.qa2-sg.cld/api-native/business_partner_pickup_points/_search'
    headers = {
        'Content-Type': 'application/json',
        'X-Service-Id': 'pyeongyang-search'
    }

    query = {
        "size": 10,
        "query": {
            "bool": {
                "must": [
                    {
                        "exists": {
                            "field": "displayName",
                            "boost": 1.0
                        }
                    }
                ],
                "filter": [
                    {
                        "term": {
                            "archived": {
                                "value": False,
                                "boost": 1.0
                            }
                        }
                    },
                    {
                        "range": {
                            "productCount": {
                                "from": 0,
                                "to": None,
                                "include_lower": False,
                                "include_upper": True,
                                "boost": 1.0
                            }
                        }
                    },
                    {
                        "geo_distance": {
                            "geoPoint": [lon, lat],
                            "distance": 20000.0,
                            "distance_type": "plane",
                            "validation_method": "STRICT",
                            "ignore_unmapped": False,
                            "boost": 1.0
                        }
                    }
                ],
                "adjust_pure_negative": True,
                "boost": 1.0
            }
        },
        "stored_fields": "_source",
        "script_fields": {
            "distance": {
                "script": {
                    "source": "doc['geoPoint'].arcDistance(params.lat, params.lon) * 0.001",
                    "lang": "painless",
                    "params": {
                        "lon": lon,
                        "lat": lat
                    }
                },
                "ignore_failure": False
            }
        },
        "sort": [
            {
                "productCount": {
                    "order": "desc"
                }
            },
            {
                "_geo_distance": {
                    "geoPoint": [{"lat": lat, "lon": lon}],
                    "unit": "km",
                    "distance_type": "plane",
                    "order": "asc",
                    "mode": "min",
                    "validation_method": "STRICT",
                    "ignore_unmapped": True
                }
            },
            {
                "displayName": {
                    "order": "asc"
                }
            }
        ]
    }

    # Make the search request
    response = requests.post(search_url, headers=headers, json=query)
    result = response.json()

    return jsonify(result)
