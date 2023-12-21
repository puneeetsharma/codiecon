from flask import Flask, jsonify, request
from flask_uploads import UploadSet, configure_uploads, IMAGES
import apiLogic
import os
from flask_cors import CORS
import cloudinary.uploader

app = Flask(__name__)
CORS(app)

upload_folder = 'uploads'
app.config['UPLOADS_DEFAULT_DEST'] = os.path.join(os.getcwd(), upload_folder)
app.config['UPLOADED_IMAGES_DEST'] = os.path.join(
    app.config['UPLOADS_DEFAULT_DEST'], 'images')
app.config['UPLOADED_IMAGES_ALLOW'] = IMAGES

images = UploadSet('images', IMAGES)
configure_uploads(app, images)

cloudinary.config(
    cloud_name='akhi',
    api_key='378827219998729',
    api_secret='fgqnwSlJ0bcIk422g0UHMKTcOqY'
)


@app.route("/upload/<user_id>", methods=['POST'])
def upload_file(user_id):
    app.logger.info('in upload route')
    upload_result = None
    if request.method == 'POST':
        file_to_upload = request.files['image']
        app.logger.info('%s file_to_upload', file_to_upload)
        if file_to_upload:
            upload_result = cloudinary.uploader.upload(file_to_upload)
            app.logger.info(upload_result)
            apiLogic.process_uploaded_image(user_id, upload_result.get("url"))
            return jsonify({"profilePhoto": upload_result["url"],"userId": user_id})


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


@app.route('/getPreOrderProductsByCategory/<category_id>', methods=['GET'])
def get_pre_order_products_by_category(category_id):
    try:
        data = apiLogic.get_pre_order_products_data_for_category(category_id)

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


@app.route('/getRelevantCategoryProductsByCategory/<category_id>', methods=['GET'])
def get_relevant_categories_products_data_by_category(category_id):
    try:
        data = apiLogic.get_relevant_category_products_by_category_skus(
            category_id)

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
        return jsonify(apiLogic.search_pickup_points_agp(lat, lon))

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/getNearByStoresProducts', methods=['GET'])
def get_near_by_stores_products():
    try:
        lat = float(request.args.get('lat', 0.0))
        lon = float(request.args.get('lon', 0.0))
        return apiLogic.get_near_by_store_products(lat, lon)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/getNearByStoresRecommendedProducts', methods=['GET'])
def get_near_by_recommended_products():
    try:
        lat = float(request.args.get('lat', 0.0))
        lon = float(request.args.get('lon', 0.0))
        user_id = request.args.get('user_id')
        return apiLogic.get_near_by_store_recommended_products(lat, lon, user_id)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/getNearByStoresRecommendedProductsByPickUpPointCode', methods=['GET'])
def get_near_by_recommended_products_by_pickup_point_code():
    try:
        lat = float(request.args.get('lat', 0.0))
        lon = float(request.args.get('lon', 0.0))
        user_id = request.args.get('user_id')
        pickup_point_code = request.args.get('pickup_point_code')
        return apiLogic.get_near_by_store_recommended_products_by_pp_code(lat, lon, user_id, pickup_point_code)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/getNearByStoresRecommendedProductsByItemSku', methods=['GET'])
def get_near_by_recommended_products_by_item_sku():
    try:
        lat = float(request.args.get('lat', 0.0))
        lon = float(request.args.get('lon', 0.0))
        user_id = request.args.get('user_id')
        item_sku = request.args.get('item_sku')
        return apiLogic.get_near_by_store_recommended_products_by_item_sku(lat, lon, user_id, item_sku)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/getProductByPickUpPointCode/<pp_code>', methods=['GET'])
def search_product_by_pp_code(pp_code):
    try:
        return apiLogic.get_product_by_pp_code(pp_code)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/getPickUpPointCodesByItemSku/<item_sku>', methods=['GET'])
def search_pp_code_by_item_sku(item_sku):
    try:
        return jsonify(apiLogic.get_pp_codes_by_product(item_sku))

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/getNewArrivalProductsByCategory/<category_id>', methods=['GET'])
def get_new_arrival_products(category_id):
    try:
        return jsonify(apiLogic.get_new_arrival_products_by_category(category_id))

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/getTopDiscountedProductsByCategory/<category_id>', methods=['GET'])
def get_top_discounted_products(category_id):
    try:
        return jsonify(apiLogic.get_top_discounted_by_category(category_id))

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/getPriceDropProductsByCategory/<category_id>', methods=['GET'])
def get_price_drop_products(category_id):
    try:
        return jsonify(apiLogic.get_price_drop_products(category_id))

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/uploadImage', methods=['POST'])
def upload_image():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        user_id = request.args.get('userId', "")
        if not user_id:
            return jsonify({'error': 'UserId not provided'}), 400

        uploaded_file = request.files['image']
        if uploaded_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        filename = images.save(uploaded_file)
        apiLogic.process_uploaded_image(user_id, filename, app)

        return jsonify({'success': 'Image uploaded successfully', 'filename': filename})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/")
def test():
    return "hi"


if __name__ == '__main__':
    app.run(host="10.20.2.180", debug=True)
