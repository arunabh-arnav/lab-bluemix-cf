# Copyright 2016, 2017 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import logging
from threading import Lock
from flask import Flask, Response, jsonify, request, make_response, json, url_for

#List of functions foudn in auxiliary files
#from customer_utilities import next_index, reply, is_valid, write_to_file
#from create_customers import create_cust
#from get_customers import get_cust
#from list_customers import list_all
#from delete_customers import delete_cust
#from update_customers import update_cust

# Create Flask application
app = Flask(__name__)
app.config['LOGGING_LEVEL'] = logging.INFO

# Status Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
HTTP_400_BAD_REQUEST = 400
HTTP_404_NOT_FOUND = 404
HTTP_409_CONFLICT = 409
HTTP_500_INTERNAL_ERROR = 500

#Lock for thread-safe counter increment
lock = Lock()

#Initial id initialization
current_customer_id = 0
with open('customers.json') as json_file:
    customers = json.load(json_file)

#In order to fetch the latest/highest customer id ever created
for customer in customers:
    if current_customer_id < customer['id']:
        current_customer_id = customer['id']

######################################################################
# GET INDEX
######################################################################
@app.route('/')
def index():
    customers_url = request.base_url + "customers"
    return make_response(jsonify(name='REST API Service for Customers in sample e-commerce website',
        version='1.0',
        url=customers_url
        ), HTTP_200_OK)

######################################################################
# LIST ALL CUSTOMERS
######################################################################
#return list_all(customers)
@app.route('/customers', methods=['GET'])
def list_customers():
    results = []
    gender = request.args.get('gender')
    if gender:
        results = [customer for customer in customers if customer['gender'] == gender]
    else:
        results = customers
    return make_response(jsonify(results), HTTP_200_OK)

######################################################################
# RETRIEVE A CUSTOMER
######################################################################
#return get_cust(customers)
@app.route('/customers/<int:id>', methods=['GET'])
def get_customers(id):
    index = [i for i, customer in enumerate(customers) if customer['id'] == id]
    if len(index) > 0:
        message = customers[index[0]]
        rc = HTTP_200_OK
    else:
        message = { 'error' : 'Customer with id: %s was not found' % str(id) }
        rc = HTTP_404_NOT_FOUND

    return make_response(jsonify(message), rc)

######################################################################
# ADD A NEW CUSTOMER
######################################################################
#return create_cust(customers)
@app.route('/customers', methods=['POST'])
def create_customers():
    payload = request.get_json()
    if is_valid(payload):
        id = next_index()#id = next_index(current_customer_id) <-------------------------X.x.x.x.x.x.x.x.x.x
        customer = {'id': id, 'first-name': payload['first-name'],
		'last-name': payload['last-name'],'gender': payload['gender'], 
		'age': payload['age'],'email':payload['email'], 
		'address-line1': payload['address-line1'], 'address-line2':payload['address-line2'], 
		'phonenumber': payload['phonenumber']}
        customers.append(customer)
        if write_to_file(customers):
            message = customer
	    rc = HTTP_201_CREATED
	else:
	    message = { 'error' : 'Failed to write data in the file'}
	    rc = HTTP_500_INTERNAL_ERROR
    else:
        message = { 'error' : 'Data is not valid' }
        rc = HTTP_400_BAD_REQUEST

    response = make_response(jsonify(message), rc)

    if rc == HTTP_201_CREATED:
        response.headers['Lofion'] = url_for('get_customers', id=id)
    return response

######################################################################
# UPDATE AN EXISTING CUSTOMER
######################################################################
#return update_cust(customers)
@app.route('/customers/<int:id>', methods=['PUT'])
def update_customers(id):
    index = [i for i, customer in enumerate(customers) if customer['id'] == id]
    if len(index) > 0:
        payload = request.get_json()
        if is_valid(payload):
            customers[index[0]] = {'id': id, 'first-name': payload['first-name'], 
		'last-name': payload['last-name'], 'gender': payload['gender'], 
		'age': payload['age'],'email':payload['email'], 
		'address-line1': payload['address-line1'], 'address-line2': payload['address-line2'],
		'phonenumber': payload['phonenumber']}
            if write_to_file(customers):
		message = customer
		rc = HTTP_201_CREATED
	    else:
		message = { 'error' : 'Failed to write data in the file'}
		rc = HTTP_500_INTERNAL_ERROR
        else:
            message = { 'error' : 'Customer data was not valid' }
            rc = HTTP_400_BAD_REQUEST
    else:
        message = { 'error' : 'customer %s was not found' % id }
        rc = HTTP_404_NOT_FOUND

    return make_response(jsonify(message), rc)

######################################################################
# DELETE A CUSTOMER
######################################################################
#delete_cust(id,customers)
@app.route('/customers/<int:id>', methods=['DELETE'])
def delete_customers(id):
    index = [i for i, customer in enumerate(customers) if customer['id'] == id]
    if len(index) > 0:
        del customers[index[0]]
	if write_to_file(customers):
	    message = ''
	    rc = HTTP_204_NO_CONTENT
	else:
	    message = { 'error' : 'Failed to write data in the file'}
	    rc = HTTP_500_INTERNAL_ERROR
    return make_response(jsonify(message))
	
######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################
def next_index():
    global current_pet_id
    with lock:
        current_pet_id += 1
    return current_pet_id

def is_valid(data):
    valid = False
    try:
        name = data['name']
        kind = data['kind']
        valid = True
    except KeyError as err:
        app.logger.warn('Missing parameter error: %s', err)
    except TypeError as err:
        app.logger.warn('Invalid Content Type error: %s', err)

    return valid

@app.before_first_request
def setup_logging():
    if not app.debug:
        # In production mode, add log handler to sys.stderr.
        handler = logging.StreamHandler()
        handler.setLevel(app.config['LOGGING_LEVEL'])
        # formatter = logging.Formatter(app.config['LOGGING_FORMAT'])
        #'%Y-%m-%d %H:%M:%S'
        formatter = logging.Formatter('[%(asctime)s] - %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
		
write_to_file(customers):
    with open('customers.json', 'w') as fp:
        json.dump(customers, fp)
	return true

######################################################################
#   M A I N
######################################################################
if __name__ == "__main__":
    # Pull options from environment
    debug = (os.getenv('DEBUG', 'False') == 'True')
    port = os.getenv('PORT', '5000')
    app.run(host='0.0.0.0', port=int(port), debug=debug)
