from flask import request
import logging
from flask import Flask, request, redirect, render_template, send_from_directory, url_for
from flask_wtf import FlaskForm
from google.cloud import datastore
from markupsafe import escape
from wtforms import StringField, SubmitField, EmailField, TextAreaField
from wtforms.validators import DataRequired
import zoho_integration as zi
from utilities import access_secrets

SERVICES = "services"
CITIES = "cities"
CATEGORIES = "categories"
ERROR_MISSING_INPUT_400 = {
    "Error": "The body is missing at least one of the required attributes"}
ERROR_401 = {"Error": "Unauthorized"}
ERROR_403 = {"Error": "You don't have permission on this resource"}
ERROR_404 = {"Error": "Not found"}
ERROR_405 = {"Error": "Request method not allowed"}
PHOTO_BUCKET = "central-oregon-action-network.appspot.com"
PROJECT_ID = "central-oregon-action-network"
FORM_SUBMIT_EMAIL = "contact@coresourceindex.org"

app = Flask(__name__)
client = datastore.Client(project=PROJECT_ID)

app.debug = False

# logs form submission metadata, for spam analysis
logger = logging.getLogger("contact_logger")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()  # stdout -> Cloud Logging
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


app.config.update(
    SECRET_KEY=access_secrets("APP_SECRET_KEY"),
    MAIL_PASSWORD=access_secrets("ZOHO_CONTACT_FORM"),
    MAIL_BACKEND='smtp',
    MAIL_HOST='smtppro.zoho.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USE_TLS=False,
    MAIL_USERNAME='arthur@coresourceindex.org',
    MAIL_DEFAULT_FROM='contact@coresourceindex.org'
)


@app.route('/', methods=['GET'])
def service_list():
    # default request values:
    cit = []
    cat = 0
    limit = 10
    offset = 0
    splash = False
    services = []
    total_count = 0

    # Check and validate request parameters:
    try:
        if 'limit' in request.values and 'offset' in request.values:
            limit = int(request.values['limit'])
            if not 1 <= limit <= 100:
                raise ValueError("Limit out of range")
            offset = int(request.values['offset'])
            if offset < 0:
                raise ValueError("Offset must be non-negative")
        if 'cit' in request.values:
            cit = request.values.getlist('cit')
            cit = [int(val) for val in cit]
        if 'cat' in request.values:
            cat = int(request.values['cat'])
        if 'cit' not in request.values and 'cat' not in request.values:
            splash = True

    except (ValueError, TypeError):
        print(f"Invalid query string: {request.url}")
        return redirect(url_for('service_list'), code=302)

    # Load list of cities:
    cities_query = client.query(kind=CITIES)
    cities_query.order = ["name"]
    cities = list(cities_query.fetch())
    for city in cities:
        city['id'] = city.key.id
    id_to_city = {entity['id']: entity['name'] for entity in cities}
    city_names = []
    if cit and cit != [1]:
        for city in cit:
            if city == 0:
                continue
            try:
                city_names.append(id_to_city[city])
            except KeyError:
                print("Invalid city ID")
                return redirect(url_for('service_list'), 302)

    # Load list of categories:
    categories_query = client.query(kind=CATEGORIES)
    categories_query.order = ["name"]
    categories = list(categories_query.fetch())
    for category in categories:
        category['id'] = category.key.id
    id_to_category = {entity['id']: entity['name'] for entity in categories}

    if not splash:
        # Load filtered, paginated list of services:
        services_query = client.query(kind=SERVICES)
        if cat:
            try:
                services_query.add_filter(filter=datastore.query.PropertyFilter(
                    'categories', '=', id_to_category[cat]))
            except KeyError:
                print("Invalid category ID")
                return redirect(url_for('service_list'), 302)
        if city_names:
            services_query.add_filter(filter=datastore.query.PropertyFilter(
                'cities', 'IN', city_names))
        services_query.order = ["name"]
        services = list(services_query.fetch(limit=limit, offset=offset))
        for service in services:
            service["id"] = service.key.id

        # Get total count of filtered services:
        services_count_query = client.query(
            kind=SERVICES, projection=["__key__"])
        if cat:
            services_count_query.add_filter(filter=datastore.query.PropertyFilter(
                'categories', '=', id_to_category[cat]))
        if city_names:
            services_count_query.add_filter(filter=datastore.query.PropertyFilter(
                'cities', 'IN', city_names))
        keys_only = list(services_count_query.fetch())
        total_count = len(keys_only)

    # Render Page:
    title = "CORI | Home"
    return render_template('index.html',
                           splash=splash,
                           cat=cat,
                           cit=cit,
                           title=title,
                           categories=categories,
                           cities=cities,
                           services=services,
                           limit=limit,
                           offset=offset,
                           total_count=total_count)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/about', methods=['GET'])
def about():
    # Render Page:
    title = "CORI | About"
    return render_template('about.html',
                           title=title)


class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired()])
    website = StringField("Website")
    message = TextAreaField("Message", validators=[DataRequired()])
    submit = SubmitField("Submit")


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    title = "CORI | Contact"
    name = None
    form = ContactForm()

    if request.method == 'POST' and form.validate_on_submit():
        name = escape(form.name.data)
        email = escape(form.email.data)
        message = escape(form.message.data)
        website = escape(form.website.data)  # honeypot field

        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent')
        honeypot_triggered = bool(website)

        email_body = f'''<p><strong>New website form submission</strong></p>
            <strong>Name:</strong> {name}<br>
            <strong>Email:</strong> {email}
            </p>
            <p><strong>Message: </strong>{message}</p>'''

        if honeypot_triggered:
            logger.info(
                f'Contact Form Submission | IP: {ip} | User Agent: {user_agent} | Honeypot: {honeypot_triggered} | Name: {name} | Email: {email} | Message: {message}')
        else:
            zi.form_submit(PROJECT_ID, email_body)

        # Clear form after send
        form.name.data = ''
        form.email.data = ''
        form.message.data = ''

    # elif request.method == 'GET':
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ''

    # Render Page:
    return render_template('contact.html',
                           title=title,
                           name=name,
                           form=form)


@app.route('/privacy', methods=['GET'])
def privacy():
    # Render Page:
    title = "CORI | Privacy"

    return render_template('privacy.html',
                           title=title)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
