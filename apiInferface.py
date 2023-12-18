from flask import Flask, jsonify, request
import apiLogic
import requests

app = Flask(__name__)


@app.route('/getUserBatchDetails/<user_id>', methods=['GET'])
def get_user(user_id):
    try:
        data = apiLogic.get_user_data(user_id)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/getUserSavings/<user_id>', methods=['GET'])
def get_user_savings(user_id):
    try:
        data = apiLogic.get_savings_data(user_id)

        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/getPreOrderProducts/<user_id>', methods=['GET'])
def get_pre_order_products(user_id):
    try:
        data = apiLogic.get_pre_order_products_data(user_id)

        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/getPreOrderProductsByCategory/<user_id>', methods=['GET'])
def get_pre_order_products_by_category(user_id):
    try:
        data = apiLogic.get_pre_order_products_data_for_category(user_id)

        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/getUserRecommendedCategories/<user_id>', methods=['GET'])
def get_user_recommended__categories(user_id):
    try:
        data = apiLogic.get_user_recommended_categories_names(user_id)

        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/getRelevantCategoryProducts/<user_id>', methods=['GET'])
def get_relevant_categories_products_data(user_id):
    try:
        data = apiLogic.get_relevant_category_products(user_id)

        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/getRelevantCategoryProductsSorted/<user_id>', methods=['GET'])
def get_relevant_categories_products_data_sorted(user_id):
    try:
        data = apiLogic.get_relevant_category_products_sort_by_price(user_id)

        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/getAllBadgeDetails', methods=['GET'])
def get_all_badge_details():
    try:
        return jsonify({"badges": apiLogic.get_all_badge_details()})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/getNearByStores', methods=['GET'])
def search_pickup_points():
    try:
        lat = float(request.args.get('lat', 0.0))
        lon = float(request.args.get('lon', 0.0))
        return apiLogic.search_pickup_points_agp(lat, lon)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/")
def test():
    return "hi"


if __name__ == '__main__':
    app.run(host="10.20.2.180", debug=True)
