import pysolr
import requests
import json
import re
import os

from flask import jsonify
import psycopg2
from psycopg2 import sql

# Connection parameters
host = "postgres13-02.qa2-sg.cld"
username = "pbpuser"
password = "HiPlTlsHryGgV"
database = "pbp"

# Specify the SKU you want to query
gdn_sku_to_query = "your_sku_here"

# import savingForecastModel

SOLR_URL = "http://localhost:8983/solr/userCollection"  # Update with your Solr URL
store_id = "10001"
channel_id = "10001"
client_id = "10001"
request_id = "bbiibhu"
username = "pbpuser"


def get_user_data(user_id):
    global progress, current_batch, profilePhoto
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
        profilePhoto = document.get('url')

    # Create a list of URLs by replacing the placeholder with multivalued field values
    badge_urls = {
        f"{value}": f"https://raw.githubusercontent.com/akhilesh-k/temp-static-image-hosting/main/{value}.png"
        for i, value in enumerate(multivalued_field_values)
    }
    response_data = {
        "user_id": user_id,
        "achieved_badges": multivalued_field_values,
        "progress": progress,
        "currentBatch": current_batch,
        "profilePhoto": profilePhoto
    }
    json_response = json.dumps(response_data)
    return response_data


def process_uploaded_image(user_id, filename):
    solr = pysolr.Solr(SOLR_URL, timeout=10)
    result = solr.search(f"userId:{user_id}")
    user_document = result.docs[0] if result.docs else None
    solr_id = user_document.get('id', [])
    updated_fields = {'set': {'url': filename}}
    solr.add([
        {
            "id": solr_id,
            "userId": user_document.get('userId'),
            "achieved": user_document.get('achieved'),
            "progress": user_document.get('progress'),
            "url": filename,
        }
    ])
    solr.commit()


def get_savings_data(user_id):
    global average_saving_percentage
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
        'stats.field': '{!sum=true}savingPercentage',
        'rows': 0
    }
    results_saving_percentage = solr.search(solr_query, **params1)
    # response_data = results_saving_percentage.get('response', {})
    # if response_data and 'numFound' in response_data:
    #     num_docs_used_for_sum = response_data['numFound']
    # total_discount_saving_percentage = (
    #         results_saving_percentage.stats['stats_fields']['savingPercentage']['sum']
    #         / num_docs_used_for_sum
    # )

    # print("Raw Solr Response:")
    # print(results_saving_percentage.raw_response)

    if 'stats' in results_saving_percentage.raw_response:
        stats_data = results_saving_percentage.raw_response['stats']

        # print("Stats Data:")
        # print(stats_data)

        if 'numFound' in results_saving_percentage.raw_response['response']:
            num_docs_used_for_sum = results_saving_percentage.raw_response['response']['numFound']

            print(f"Number of Docs Found: {num_docs_used_for_sum}")

            if num_docs_used_for_sum > 0:
                if 'stats_fields' in stats_data:
                    saving_percentage_stats = stats_data['stats_fields'].get('savingPercentage', {})

                    print("Saving Percentage Stats:")
                    print(saving_percentage_stats)

                    if 'sum' in saving_percentage_stats:
                        total_sum_saving_percentage = saving_percentage_stats['sum']
                        average_saving_percentage = total_sum_saving_percentage / num_docs_used_for_sum
                        print(f"Average Saving Percentage: {average_saving_percentage}")
                    else:
                        print("No 'sum' field in savingPercentage stats.")
                else:
                    print("No 'stats_fields' in savingPercentage stats.")
            else:
                print("No documents found for calculating average savingPercentage.")
        else:
            print("No 'numFound' field in the main response.")
    else:
        print("No 'stats' field in the response.")

    api_response = {
        "total_discount_saving_percentage": average_saving_percentage,
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


def get_pre_order_products_data_for_category(category_id):
    # categories = get_user_recommended_categories(user_id)
    SOLR_URL = "http://xsearch-solr-1.qa2-sg.cld:8983/solr/retailCollection"  # Update with your Solr URL
    solr = pysolr.Solr(SOLR_URL, timeout=10)

    # Construct the Solr query with the user_id
    # category_codes = " OR ".join(categories)
    params1 = {
        'fq': '{!collapse field = sku}',
        'fl': 'mediumImage,name,merchantName,discount,salePrice,listPrice,sku,itemSku,pickupPointCode'
    }
    true = "true"
    solr_query = f"salesCatalogCategoryIds:{category_id} AND isPreorder:{true}"
    # Construct the Solr query with the user_id
    # solr_query = f"*:* AND isPreorder:{true}"
    print(solr_query)

    # Execute the Solr query and return the documents
    results = solr.search(solr_query, **params1, rows=10)  # You can adjust the number of rows as needed
    add_url_to_response(results)
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
    category_data_dict = {}

    for category_code in categories:
        category_data = fetch_category_data(category_code, store_id, channel_id, client_id, request_id, username)
        if category_data:
            category_data_dict[category_code] = category_data

    return category_data_dict


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
    category_codes = "(" + " OR ".join(categories) + ")"
    params1 = {
        'fq': '{!collapse field = sku}',
        'fl': 'mediumImage,name,merchantName,discount,salePrice,listPrice,sku,itemSku,pickupPointCode',
        'rows': 10
    }
    fqValue = '{!collapse field=sku}'
    solr_query = f"salesCatalogCategoryIds:{category_codes}"
    print(solr_query)

    # Execute the Solr query and return the documents
    results = solr.search(solr_query, **params1)  # You can adjust the number of rows as needed
    add_url_to_response(results)
    return results.docs


def get_relevant_category_products_by_category(category_id):
    SOLR_URL = "http://xsearch-solr-1.qa2-sg.cld:8983/solr/retailCollection"  # Update with your Solr URL
    solr = pysolr.Solr(SOLR_URL, timeout=10)

    # Construct the Solr query with the user_id
    params1 = {
        'fq': '{!collapse field = sku}',
        'fl': 'mediumImage,name,merchantName,discount,salePrice,listPrice,sku,itemSku,pickupPointCode',
        'rows': 10
    }
    solr_query = f"salesCatalogCategoryIds:{category_id}"
    print(solr_query)

    # Execute the Solr query and return the documents
    results = solr.search(solr_query, **params1)  # You can adjust the number of rows as needed
    add_url_to_response(results)
    return results.docs


def get_relevant_category_products_sort_by_price(user_id):
    categories = get_user_recommended_categories(user_id)
    SOLR_URL = "http://xsearch-solr-1.qa2-sg.cld:8983/solr/retailCollection"  # Update with your Solr URL
    solr = pysolr.Solr(SOLR_URL, timeout=10)

    # Construct the Solr query with the user_id
    category_codes = "(" + " OR ".join(categories) + ")"
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
            "detail": "Purchasing more than 10 products at once",
            "url": "https://raw.githubusercontent.com/akhilesh-k/temp-static-image-hosting/main/perfect-cart.png",
            "id": "perfect-cart"
        },
        {
            "name": "Event Voyager",
            "detail": "Buying tickets for more than 5 events",
            "url": "https://raw.githubusercontent.com/akhilesh-k/temp-static-image-hosting/main/event-voyager.png",
            "id": "event-voyager"
        },
        # {
        #     "name": "Show Savvy",
        #     "detail": "Bought tickets for more than 10 events",
        #     "url": "https://raw.githubusercontent.com/akhilesh-k/temp-static-image-hosting/main/show-savvy.png",
        #     "id": "show-savvy"
        # },
        {
            "name": "Style Sculptor",
            "detail": "Purchasing a fashion product which was worth 5k",
            "url": "https://raw.githubusercontent.com/akhilesh-k/temp-static-image-hosting/main/style-sculptor.png",
            "id": "style-sculptor"
        },
        {
            "name": "Glamour Guru",
            "detail": "Purchasing a fashion product which was worth 10k",
            "url": "https://raw.githubusercontent.com/akhilesh-k/temp-static-image-hosting/main/glamour-guru.png",
            "id": "glamour-guru"
        },
        {
            "name": "Bundle Binge",
            "detail": "Purchasing more than 5 products at once",
            "url": "https://raw.githubusercontent.com/akhilesh-k/temp-static-image-hosting/main/bundle-binge.png",
            "id": "bundle-binge"
        },
        {
            "name": "Mega Saver",
            "detail": "Purchasing a product with more than 80% savings",
            "url": "https://raw.githubusercontent.com/akhilesh-k/temp-static-image-hosting/main/mega-saver.png",
            "id": "mega-saver"
        },
        {
            "name": "Ultra Saver",
            "detail": "Purchasing a product with more than 90% savings",
            "url": "https://raw.githubusercontent.com/akhilesh-k/temp-static-image-hosting/main/ultra-saver.png",
            "id": "ultra-saver"
        },
        {
            "name": "Rush Gizmo",
            "detail": "Purchasing any tech product on 1st day",
            "url": "https://raw.githubusercontent.com/akhilesh-k/temp-static-image-hosting/main/gizmo-rush.png",
            "id": "gizmo-rush"
        },
        {
            "name": "Mobile Maestro",
            "detail": "Buying mobile in 1st hour of launch",
            "url": "https://raw.githubusercontent.com/akhilesh-k/temp-static-image-hosting/main/mobile-maestro.png",
            "id": "mobile-maestro"
        },
    ]
    return all_badge_details


def search_pickup_points_agp(lat, lon):
    # Get latitude and longitude from request parameters
    print(lat, lon)
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
                            "distance": 2000.0,
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
    try:
        response_data = response.json()
    except json.JSONDecodeError:
        # Handle the case where the response is not in JSON format
        return []
    parsed_data = []

    for hit in response_data.get('hits', {}).get('hits', []):
        source = hit.get('_source', {})
        geo_point = source.get('geoPoint', {})
        full_pickup_point_address = source.get('fullPickupPointAddress', '')

        data = {
            'name': source.get('name', ''),
            'businessPartnerName': source.get('businessPartnerName', ''),
            'code': source.get('code', ''),
            'geoPoint': {
                'lat': geo_point.get('lat', 0.0),
                'lon': geo_point.get('lon', 0.0),
            },
            'fullPickupPointAddress': full_pickup_point_address,
        }

        parsed_data.append(data)

    result = response.json()

    return parsed_data


def get_near_by_store_products(lat, lon):
    # parsed_data = search_pickup_points_agp(lat, lon)
    SOLR_URL = "http://xsearch-solr-1.qa2-sg.cld:8983/solr/retailCollection"  # Update with your Solr URL
    solr = pysolr.Solr(SOLR_URL, timeout=10)
    code_list = [entry["code"] for entry in search_pickup_points_agp(lat, lon)]
    pp_codes = "(" + " OR ".join(code_list) + ")"
    print(pp_codes)
    # Construct the Solr query with the user_id
    solr_query = f"pickupPointCode:{pp_codes} AND cnc:true"
    print(solr_query)
    params = {
        'fq': '{!collapse field = sku}',
        'fl': 'mediumImage,name,merchantName,discount,salePrice,listPrice,sku,itemSku,pickupPointCode'
    }
    # Execute the Solr query and return the documents
    results = solr.search(solr_query, **params, rows=10)  # You can adjust the number of rows as needed
    add_url_to_response(results)
    return jsonify(results.docs)


def get_near_by_store_recommended_products(lat, lon, user_id):
    # parsed_data = search_pickup_points_agp(lat, lon)
    SOLR_URL = "http://xsearch-solr-1.qa2-sg.cld:8983/solr/retailCollection"  # Update with your Solr URL
    solr = pysolr.Solr(SOLR_URL, timeout=10)
    code_list = [entry["code"] for entry in search_pickup_points_agp(lat, lon)]
    pp_codes = "(" + " OR ".join(code_list) + ")"
    print(pp_codes)
    categories = get_user_recommended_categories(user_id)
    category_codes = "(" + " OR ".join(categories) + ")"
    # Construct the Solr query with the user_id
    solr_query = f"pickupPointCode:{pp_codes} AND salesCatalogCategoryIds:{category_codes}"
    print(solr_query)
    params = {
        'fq': [
            '{!collapse field = sku}',
            'cnc:true'],
        'fl': 'mediumImage,name,merchantName,discount,salePrice,listPrice,sku,itemSku,pickupPointCode'
    }
    # Execute the Solr query and return the documents
    results = solr.search(solr_query, **params, rows=10)  # You can adjust the number of rows as needed
    add_url_to_response(results)
    return jsonify(results.docs)


def get_near_by_store_recommended_products_by_pp_code(lat, lon, user_id, pickup_point_code):
    # parsed_data = search_pickup_points_agp(lat, lon)
    SOLR_URL = "http://xsearch-solr-1.qa2-sg.cld:8983/solr/retailCollection"  # Update with your Solr URL
    solr = pysolr.Solr(SOLR_URL, timeout=10)
    code_list = [entry["code"] for entry in search_pickup_points_agp(lat, lon)]
    pp_codes = " OR ".join(code_list)
    print(pp_codes)
    categories = get_user_recommended_categories(user_id)
    category_codes = "(" + " OR ".join(categories) + ")"
    # Construct the Solr query with the user_id
    solr_query = f"pickupPointCode:{pickup_point_code} AND salesCatalogCategoryIds:{category_codes}"
    print(solr_query)
    params = {
        'fq': [
            '{!collapse field = sku}',
            'cnc:true'],
        'fl': 'mediumImage,name,merchantName,discount,salePrice,listPrice,sku,itemSku,pickupPointCode'
    }
    # Execute the Solr query and return the documents
    results = solr.search(solr_query, **params, rows=10)  # You can adjust the number of rows as needed
    add_url_to_response(results)
    return jsonify(results.docs)


def get_near_by_store_recommended_products_by_item_sku(lat, lon, user_id, item_sku):
    # parsed_data = search_pickup_points_agp(lat, lon)
    SOLR_URL = "http://xsearch-solr-1.qa2-sg.cld:8983/solr/retailCollection"  # Update with your Solr URL
    solr = pysolr.Solr(SOLR_URL, timeout=10)
    code_list = [entry["code"] for entry in search_pickup_points_agp(lat, lon)]
    pp_codes = " OR ".join(code_list)
    print(pp_codes)
    categories = get_user_recommended_categories(user_id)
    category_codes = " OR ".join(categories)
    # Construct the Solr query with the user_id
    solr_query = f"itemSku:{item_sku} AND salesCatalogCategoryIds:{category_codes}"
    print(solr_query)
    params = {
        'fq': [
            '{!collapse field = sku}',
            'cnc:true'],
        'fl': 'pickupPointCode,latLong,merchantCode,merchantName'
    }
    # params = {
    #     'fl': 'pickupPointCode,latLong,merchantCode,merchantName'
    # }
    # Execute the Solr query and return the documents
    results = solr.search(solr_query, **params, rows=10)  # You can adjust the number of rows as needed
    # add_url_to_response(results)
    return jsonify(results.docs)


def get_product_by_pp_code(pp_code):
    SOLR_URL = "http://xsearch-solr-1.qa2-sg.cld:8983/solr/retailCollection"  # Update with your Solr URL
    solr = pysolr.Solr(SOLR_URL, timeout=10)
    # Construct the Solr query with the user_id
    solr_query = f"pickupPointCode:{pp_code} AND cnc:true"
    print(solr_query)
    params = {
        'fq': '{!collapse field = sku}',
        'fl': 'mediumImage,name,merchantName,discount,salePrice,listPrice,sku,itemSku,pickupPointCode'
    }
    # Execute the Solr query and return the documents
    results = solr.search(solr_query, **params, rows=10)  # You can adjust the number of rows as needed
    add_url_to_response(results)
    return results.docs


def get_pp_codes_by_product(item_sku):
    SOLR_URL = "http://xsearch-solr-1.qa2-sg.cld:8983/solr/retailCollection"  # Update with your Solr URL
    solr = pysolr.Solr(SOLR_URL, timeout=10)
    params = {
        'fl': 'pickupPointCode,latLong,merchantCode,merchantName'
    }
    # Construct the Solr query with the user_id
    solr_query = f"itemSku:{item_sku}"
    print(solr_query)

    # Execute the Solr query and return the documents
    results = solr.search(solr_query, **params, rows=10)  # You can adjust the number of rows as needed

    return results.docs


def get_new_arrival_products_by_category(category_id):
    SOLR_URL = "http://xsearch-solr-1.qa2-sg.cld:8983/solr/retailCollection"  # Update with your Solr URL
    solr = pysolr.Solr(SOLR_URL, timeout=10)
    date_range_month = f"[NOW-1YEAR TO NOW]"
    params = {
        'fq': [
            '{!collapse field = sku}',
            'createdDate:[NOW-1YEAR TO NOW]'],
        'fl': 'mediumImage,name,merchantName,discount,salePrice,listPrice,sku,itemSku,pickupPointCode'
    }
    # Construct the Solr query with the user_id
    solr_query = f"salesCatalogCategoryIds:{category_id}"
    print(solr_query)

    # Execute the Solr query and return the documents
    results = solr.search(solr_query, **params, rows=10)  # You can adjust the number of rows as needed
    add_url_to_response(results)

    return results.docs


def get_top_discounted_by_category(category_id):
    SOLR_URL = "http://xsearch-solr-1.qa2-sg.cld:8983/solr/retailCollection"  # Update with your Solr URL
    solr = pysolr.Solr(SOLR_URL, timeout=10)
    params = {
        'fq': '{!collapse field = sku}',
        'sort': 'discount desc',
        'fl': 'mediumImage,name,merchantName,discount,salePrice,listPrice,sku,itemSku,pickupPointCode'
    }
    # Construct the Solr query with the user_id
    solr_query = f"salesCatalogCategoryIds:{category_id}"
    print(solr_query)

    # Execute the Solr query and return the documents
    results = solr.search(solr_query, **params, rows=10)  # You can adjust the number of rows as needed
    print(add_url_to_response(results))
    return results.docs


def add_url_to_response(response):
    base_url = "https://wwwuatb.gdn-app.com/p/{name}/ps--{sku}?ds={itemSku}&source=SEARCH&cnc=true&pickupPointCode={pickupPointCode}&pid1={sku}"
    base_url1 = "https://static-uatb.gdn-app.com/wcsstore/Indraprastha/images/catalog/full{mu}"

    # Iterate through each document in the response
    for document in response:
        # Create the URL using document values
        url = base_url.format(
            name=create_url_friendly_string(document["name"]),
            sku=document["sku"],
            itemSku=document["itemSku"],
            pickupPointCode=document["pickupPointCode"]
        )

        # Append the URL to the document
        document["url"] = url

    for document in response:
        if document["sku"] == 'LAY-70007-34922':
            document["mediumImage"] = '/catalog-image/96/MTA-49427313/oem_samsung_galaxy_s23_ultra_full01_r407bq0q.jpg'
        if document["sku"] == 'DUT-70015-00007':
            document["mediumImage"] = '/catalog-image/95/MTA-49416304/puma_apiautomation_full0493.jpg'
        # Create the URL using document values
        url = base_url1.format(
            mu=document["mediumImage"]
        )
        # Append the URL to the document
        document["mediumImage"] = url

    return response


def create_url_friendly_string(s):
    if not s:
        return ""

    # Convert to lowercase and replace non-alphanumeric characters with "-"
    url_friendly = re.sub(r'[^a-zA-Z0-9]+', '-', s.lower())

    # Remove leading and trailing "-"
    url_friendly = url_friendly.strip('-')

    return url_friendly


def get_price_drop_products(category_id):
    sku_list = get_relevant_category_products_by_category_skus(category_id)
    return query_postgres(sku_list)


def query_postgres(gdn_skus):
    global connection, cursor
    try:
        connection = psycopg2.connect(
            host=host,
            user=username,
            password=password,
            database=database
        )

        # Create a cursor object to execute SQL queries
        cursor = connection.cursor()
        # query = sql.SQL('SELECT * FROM prd_updated_product_history WHERE gdn_sku IN ({})').format(
        #     sql.SQL(', ').join(map(sql.Placeholder, range(len(gdn_skus))))
        # )
        query = sql.SQL('SELECT * FROM prd_updated_product_history WHERE gdn_sku IN ({})').format(
            sql.SQL(', ').join(map(sql.Identifier, gdn_skus))
        )
        # Example: Execute a query to fetch data for a specific SKU
        cursor.execute(query, (gdn_sku_to_query,))

        # Fetch the results
        rows = cursor.fetchall()

        for row in rows:
            print(row)

    except psycopg2.Error as e:
        print("Error connecting to PostgreSQL:", e)

    finally:
        # Close the cursor and connection
        if connection:
            cursor.close()
            connection.close()
            print("Connection closed.")


def get_relevant_category_products_by_category_skus(category_id):
    SOLR_URL = "http://xsearch-solr-1.qa2-sg.cld:8983/solr/retailCollection"  # Update with your Solr URL
    solr = pysolr.Solr(SOLR_URL, timeout=10)

    # Construct the Solr query with the user_id
    params1 = {
        'fq': '{!collapse field = sku}',
        'fl': 'mediumImage,name,merchantName,discount,salePrice,listPrice,sku,itemSku,pickupPointCode',
        'rows': 10
    }
    solr_query = f"salesCatalogCategoryIds:{category_id}"
    print(solr_query)

    # Execute the Solr query and return the documents
    results = solr.search(solr_query, **params1)  # You can adjust the number of rows as needed
    # add_url_to_response(results)
    sku_list = [doc['sku'] for doc in results.docs]
    return sku_list
