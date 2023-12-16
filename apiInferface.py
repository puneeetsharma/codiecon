from flask import Flask, jsonify
import apiLogic

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


if __name__ == '__main__':
    app.run(debug=True)
