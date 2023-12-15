from flask import Flask, jsonify
import pysolr

app = Flask(__name__)

SOLR_URL = "http://localhost:8983/solr/userCollection"  # Update with your Solr URL


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
    print(solr_query)

    # Execute the Solr query and return the documents
    results = solr.search(solr_query, rows=10)  # You can adjust the number of rows as needed
    for result in results.docs:
        # Assuming 'discount' is a field in your Solr schema
        categories = []
        if 'categories' in result:
            categories += result['categories']
        print(categories)
    return categories


def get_relevant_category_categories(user_id):
    categories = get_user_recommended_categories(user_id)
    SOLR_URL = "http://brs-solr-1.qa2-sg.cld:8983/solr/userProfileCollection"  # Update with your Solr URL
    solr = pysolr.Solr(SOLR_URL, timeout=10)

    # Construct the Solr query with the user_id
    category_codes = ''
    for category in categories:
        category_codes += category
    solr_query = f"salesCatalogCategoryIdsAll:{user_id}"
    print(solr_query)

    # Execute the Solr query and return the documents
    results = solr.search(solr_query, rows=10)  # You can adjust the number of rows as needed
    return results.docs


@app.route('/getUserBatchDetails/<user_id>', methods=['GET'])
def get_user(user_id):
    try:
        data = get_user_data(user_id)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/getUserSavings/<user_id>', methods=['GET'])
def get_user_savings(user_id):
    try:
        data = get_savings_data(user_id)

        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/getPrePreOrderProducts/<user_id>', methods=['GET'])
def get_pre_order_products(user_id):
    try:
        data = get_pre_order_products_data(user_id)

        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/getUserRecommendedCategories/<user_id>', methods=['GET'])
def get_user_recommended__categories(user_id):
    try:
        data = get_user_recommended_categories(user_id)

        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/getRelevantCategoryProducts/<user_id>', methods=['GET'])
def get_relevant_categories_data(user_id):
    try:
        data = get_user_recommended_categories(user_id)

        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
