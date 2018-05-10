import json

from bson import json_util
from flask import Flask, request, Response, session, jsonify
from flask_bcrypt import Bcrypt
from flask_pymongo import PyMongo
from pymongo.errors import DuplicateKeyError
from werkzeug.exceptions import BadRequest, NotFound, UnsupportedMediaType, Unauthorized
from exceptions import JSONExceptionHandler


from bson.json_util import dumps


# This defines a Flask application
app = Flask(__name__)

# This code here converts Flask's default (HTML) errors to Json errors.
# This is helpful because HTML breaks clients that are expecting JSON
JSONExceptionHandler(app)

# We configure the app object

app.config['MONGO_DBNAME'] = 'laundry_app'                         
app.config['MONGO_HOST'] = 'ds251588.mlab.com:51588'
app.config['MONGO_USERNAME'] = 'cameron'
app.config['MONGO_PASSWORD'] = 'laundryapp'



app.secret_key = 'A0Zr98j/3yX R~XHH!!!jmN]LWX/,?RT'


# This initializes PyMongo and makes `mongo` available
mongo = PyMongo(app)
bcrypt = Bcrypt(app)


@app.route('/laundry/<location>/', methods= ['GET'])
def get_location_info(location):
    '''
    Return all of the records pertaining to this location
    '''
    result = jsonify(dumps(list(mongo.db.laundry.find({'location':location}))))
    return result

@app.route('/washer/<location>/', methods= ['GET'])
def get_location_info_washer(location):
    '''
    Return all of the washer records pertaining to this location
    '''
    result = jsonify(dumps(list(mongo.db.washer.find({'location':location}))))
    return result

@app.route('/dryer/<location>/', methods= ['GET'])
def get_location_info_dryer(location):
    '''
    Return all of the washer records pertaining to this location
    '''
    result = jsonify(dumps(list(mongo.db.dryer.find({'location':location}))))
    return result



@app.route('/laundry/<location>/<laundry_number>', methods =['GET'])
def get_particular_machine_info(location, laundry_number):
    '''
    Return the laundry_status of the particular laundry machine corresponding to this location and laundry number
    '''

    laundry_number = int(laundry_number) 
    result = jsonify(dumps(list(mongo.db.laundry.find({'laundry_number':laundry_number,'location':location}))))
    return result



@app.route('/laundry',methods = ['POST'])
def update_laundry_info():
    '''
    JSON format: {'laundry_number: {1...n}',location: 'name', laundry_status: {1,0} } //laundry_status = 1 means laundry machine being used
    '''
    print ("HELLO")
    body = request.get_json()
    post_laundry_num = body.get('laundry_number')
    post_location = body.get('location')
    post_laundry_status = body.get('laundry_status')
    
    mongo.db.laundry.update({'laundry_number':post_laundry_num, 'location':post_location}, {"$set": {"laundry_status":post_laundry_status}}, upsert=True)

    return Response(status=201)



@app.route('/washer',methods = ['POST'])
def update_washer_info():
    '''
    JSON format: {'laundry_number: {1...n}',location: 'name', laundry_status: {1,0} } //laundry_status = 1 means laundry machine being used
    '''
    body = request.get_json()
    post_washer_num = body.get('washer_num')
    post_location = body.get('location')
    post_washer_status = body.get('washer_status')
    
    mongo.db.washer.update({'location':post_location, 'washer_num':post_washer_num}, {"$set": {"washer_status":post_washer_status}}, upsert=True)

    return Response(status=201)

@app.route('/dryer',methods = ['POST'])
def update_dryer_info():
    '''
    JSON format: {'laundry_number: {1...n}',location: 'name', laundry_status: {1,0} } //laundry_status = 1 means laundry machine being used
    '''
    body = request.get_json()
    post_dryer_num = body.get('dryer_num')
    post_location = body.get('location')
    post_dryer_status = body.get('dryer_status')
    
    mongo.db.dryer.update({'location':post_location, 'dryer_num':post_dryer_num}, {"$set": {"dryer_status":post_dryer_status}}, upsert=True)

    return Response(status=201)




@app.route('/user', methods=['POST'])
def add_new_user():
    """
    This method is used to register a new user.
    """
    # Bounce any requests that are not JSON type requests
    if not request.is_json:
        raise UnsupportedMediaType()

    # Check that the request body has required properties
    body = request.get_json()
    if body.get('name') is None:
        raise BadRequest('missing name property')
    if body.get('password') is None:
        raise BadRequest('missing password property')
    if body.get('email') is None:
        raise BadRequest('missing email property')
    if body.get('phone_number') is None:
        raise BadRequest('missing phone_number property')

    password_hash = bcrypt.generate_password_hash(body.get('password'))
    try:
        mongo.db.users.insert_one({'_id': body.get('email'), 'password_hash': password_hash, 'name': body.get('name'), 'phone_number': body.get('phone_number')})
    except DuplicateKeyError:
        raise NotFound('User already exists')

    # check that mongo didn't fail
    return Response(status=201)


@app.route('/user', methods=['PUT'])
def login():
    """
    This method logs the user in by checking username + password
    against the mongo database
    :return:
    """
    # Bounce any requests that are not JSON type requests
    if not request.is_json:
        raise UnsupportedMediaType()

    # Check that the request body has `email` and `password` properties
    body = request.get_json()
    if body.get('email') is None:
        raise BadRequest('missing email property')
    if body.get('password') is None:
        raise BadRequest('missing password property')

    user = mongo.db.users.find_one({'_id': body.get('email')})
    if user is None:
        session.clear()
        raise BadRequest('User not found')
    if not bcrypt.check_password_hash(user['password_hash'], body.get('password')):
        session.clear()
        raise BadRequest('Password does not match')

    # this little trick is necessary because MongoDb sends back objects that are
    # CLOSE to json, but not actually JSON (principally the ObjectId is not JSON serializable)
    # so we just convert to json and use `loads` to get a dict
    serializable_user_obj = json.loads(json_util.dumps(user))
    session['user'] = serializable_user_obj
    return Response(status=200)

# This allows you to run locally.
# When run in GCP, Gunicorn is used instead (see entrypoint in app.yaml) to
# Access the Flack app via WSGI
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
