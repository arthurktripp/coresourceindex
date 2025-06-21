import csv
import filetype
from flask import Flask, request, jsonify
from google.cloud import datastore, storage
import io
from jinja2 import Environment, PackageLoader, select_autoescape
import json

app = Flask(__name__)
env = Environment(
    loader=PackageLoader("main"),
    autoescape=select_autoescape()
)
client = datastore.Client(project="central-oregon-action-network")

SERVICES = "services"
CITIES = "cities"
CATEGORIES = "categories"
ERROR_MISSING_INPUT_400 = {
    "Error": "The body is missing at least one of the required attributes"}
ERROR_401 = {"Error": "Unauthorized"}
ERROR_403 = {"Error": "You don't have permission on this resource"}
ERROR_404 = {"Error": "Not found"}
ERROR_409 = {"Error": "Enrollment data is invalid"}
PHOTO_BUCKET = 'central-oregon-action-network.appspot.com'

# ####### #
# HELPERS #
# ####### #

def create_cities(cities: list):
    cities_query = client.query(kind=CITIES)
    datastore_cities = list(cities_query.fetch())
    ds_city_names = [city['name'] for city in datastore_cities]
    for city in cities:
        if city not in ds_city_names:
            new_city = datastore.Entity(client.key(CITIES))
            new_city.update({"name": city})
            client.put(new_city)
            
def create_categories(categories: list):
    categories_query = client.query(kind=CATEGORIES)
    datastore_categories = list(categories_query.fetch())
    ds_cat_names = [category['name'] for category in datastore_categories]
    for category in categories:
        if category not in ds_cat_names:
            new_category = datastore.Entity(client.key(CATEGORIES))
            new_category.update({'name': category})
            client.put(new_category)
            
            
def _contains_reqs(content: dict, *argv: str) -> bool:
    """ 
    Check that a dictionary contains specified keys

    Args:
        content (dict): the dictionary that we are checking for completeness
        argv (str): keys required in content

    Returns: Bool
    """
    for each in argv:
        if each not in content:
            return False
    return True


# ###### #
# ROUTES #
# ###### #

@app.route(f'/{SERVICES}', methods=['POST'])
def add_service():
    content = request.get_json()
    if not _contains_reqs(content, "name", "cities", "categories"):
        return ERROR_MISSING_INPUT_400, 400

    cities_query = client.query(kind=CITIES)
    datastore_cities = list(cities_query.fetch())
    city_names = [city['name'] for city in datastore_cities]
    for city in content['cities']:
        if city not in city_names:
            new_city = datastore.Entity(client.key(CITIES))
            new_city.update({"name": city})
            client.put(new_city)

    categories_query = client.query(kind=CATEGORIES)
    datastore_categories = list(categories_query.fetch())
    ds_cat_names = [category['name'] for category in datastore_categories]
    for category in content['categories']:
        if category not in ds_cat_names:
            new_category = datastore.Entity(client.key(CATEGORIES))
            new_category.update({'name': category})
            client.put(new_category)
    
    new_service = datastore.Entity(client.key(SERVICES))
    new_service.update({
        "name": content["name"],
        "description": content["description"],
        "url_website": content["url_website"],
        "url_donate": content["url_donate"],
        "url_find_services": content["url_find_services"],
        "volunteer": content["volunteer"],
        "cities": content["cities"],
        "categories": content["categories"],
        "icon_filename": 'default-blank.png'
    })

    client.put(new_service)
    new_service['id'] = new_service.key.id
    
    return (new_service, 201)


@app.route(f'/api/{SERVICES}', methods=['GET'])
@app.route(f'/api/{SERVICES}/<int:id>', methods=['GET'])
def get_service(id=0):
    if id:
        service_key = client.key(SERVICES, id)
        service = client.get(service_key)
        if not service:
            return "Service not found", 404
        service['id'] = service.key.id
        service['self'] = f'{request.base_url}'
        return service, 200
    else:
        services_query = client.query(kind=SERVICES)
        services = list(services_query.fetch())
        for service in services:
            service["id"] = service.key.id
            service['self'] = f'{request.base_url}/{service['id']}'
        return services, 200


@app.route(f'/{SERVICES}/bulk-upload', methods=['POST'])
def sevices_bulk_upload():
    if 'file' not in request.files:
        return (ERROR_MISSING_INPUT_400, 400)

    file_obj = request.files['file']
    csv_file = io.TextIOWrapper(file_obj, encoding='utf-8')
    
    upload_dict = csv.DictReader(csv_file, quotechar='"')
    
    combined_cities = []
    combined_cats = []
    upload_list = []
    for entry in upload_dict:
        cities = entry['cities'].split(', ')
        for each in cities:
            if each not in combined_cities:
                combined_cities.append(each)
        cats = entry['categories'].split(', ')
        for each in cats:
            if each not in combined_cats:
                combined_cats.append(each)
        upload_list.append(entry)
    create_cities(combined_cities)
    create_categories(combined_cats)
  
    for service in upload_list:
        new_service = datastore.Entity(client.key(SERVICES))
        new_service.update({
            "name": service["name"],
            "description": service["description"],
            "url_website": service["url_website"],
            "url_donate": service["url_donate"],
            "url_find_services": service["url_find_services"],
            "volunteer": service["volunteer"],
            "cities": service["cities"].split(', '),
            "categories": service["categories"].split(', '),
            "icon_filename": 'default-blank.png'
        })
        client.put(new_service)
        new_service['id'] = new_service.key.id

    return ("Upload Successful", 201)
        

@app.route(f'/{SERVICES}/<int:service_id>/image', methods=['POST'])
def add_image(service_id):
    if 'file' not in request.files:
        return (ERROR_MISSING_INPUT_400, 400)
    
    service_key = client.key(SERVICES, service_id)
    service = client.get(key=service_key)
    if not service:
        return (ERROR_403, 403)
    
    file_obj = request.files['file']
    kind = filetype.guess(file_obj)
    
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(PHOTO_BUCKET)
    blob = bucket.blob(file_obj.filename)
    file_obj.seek(0)
    blob.upload_from_file(file_obj, content_type=f'{kind}')
    
    service['icon_filename'] = file_obj.filename
    client.put(service)
    
    return(service, 200)
    


if __name__ == "__main__":
    app.run('127.0.0.1', 8081, True)
