import socket
import signal
import sys
import random

# Read a command line argument for the port where the server
# must run.
port = 8080
if len(sys.argv) > 1:
    port = int(sys.argv[1])
else:
    print("Using default port 8080")

# Start a listening server socket on the port
sock = socket.socket()
sock.bind(('', port))
sock.listen(2)

### Contents of pages we will serve.
# Login form
login_form = """
   <form action = "http://localhost:%d" method = "post">
   Name: <input type = "text" name = "username">  <br/>
   Password: <input type = "text" name = "password" /> <br/>
   <input type = "submit" value = "Submit" />
   </form>
""" % port
# Default: Login page.
login_page = "<h1>Please login</h1>" + login_form
# Error page for bad credentials
bad_creds_page = "<h1>Bad user/pass! Try again</h1>" + login_form
# Successful logout
logout_page = "<h1>Logged out successfully</h1>" + login_form
# A part of the page that will be displayed after successful
# login or the presentation of a valid cookie
success_page = """
   <h1>Welcome!</h1>
   <form action="http://localhost:%d" method = "post">
   <input type = "hidden" name = "action" value = "logout" />
   <input type = "submit" value = "Click here to logout" />
   </form>
   <br/><br/>
   <h1>Your secret data is here:</h1>
""" % port

# Important Data Structures We'll Need Globally
# Define as objects or lists? 
users = {}
secrets = {}
cookies = {}

#### Helper functions
# Initialize the server and the values
def data_initializer():
    with open('passwords.txt') as f:
        res = f.read().splitlines()
        for line in res:
            creds = line.split(' ')
            users[creds[0]] = creds[1]
    with open('secrets.txt') as f:
        res = f.read().splitlines()
        for line in res:
            secret_data = line.split(' ')
            secrets[secret_data[0]] = secret_data[1]


# Printing.
def print_value(tag, value):
    print("Here is the", tag)
    print("\"\"\"")
    print(value)
    print("\"\"\"")
    print()


# Signal handler for graceful exit
def sigint_handler(sig, frame):
    print('Finishing up by closing listening socket...')
    sock.close()
    sys.exit(0)


# Register the signal handler
signal.signal(signal.SIGINT, sigint_handler)

# TODO: put your application logic here!
# Read login credentials for all the users
# Read secret data of all the users
# Parse through the response for both headers and body
def request_parse(req):
    req_lines = req.split('\r\n\r\n')
    headers = req_lines[0]
    body = '' if len(req_lines) == 1 else req_lines[1]
    return headers, body

# What type of HTTP request was received
def get_request_type(header):
    type = header.split(' ')[0]
    return type 

# Get the secret for user 
def get_secret(user_info):
    if user_info == None:
        return ''
    user = user_info
    if '=' in user_info:
        user, _ = login_parse(user_info)
    return secrets[user]

# Get username and password from body
def login_parse(login_header):
    if 'username' not in login_header:
        return None, None
    def extract(input):
        return input.split('=')[1]
    fields = login_header.split('&')
    key, value = map(extract, fields)
    return key, value

# Authenticate with username and password
def authenticate(login_header):
    if login_header == '':
        return False
    key, value = login_parse(login_header)
    if key in users and users[key] == value:
        return True
    return False

# Check if the cookie is valid
def cookie_auth(body):
    user = body.split('=')[1]
    for key, value in cookies.items():
        if user == value:
            return True, key 
    return False, None 

# Add a cookie entry for user and send them the Set-Cookie
def cookie_update(user):
    if user not in cookies:
        rand_val = random.getrandbits(64)
        headers_to_send = 'Set-Cookie: token=' + str(rand_val) + '\r\n'
        cookies[user] = str(rand_val)
        return headers_to_send
    return '' 

# Remove the cookie==value
def cookie_remove(value):
    print("looking for " + value)
    for key, cookie in cookies.items():
        if value == cookie:
            print('removing ' + key)
            del cookies[key]
            return

# Given the headers and HTML, construct a response
def build_response(headers, html):
    response = 'HTTP/1.1 200 OK\r\n'
    response += headers 
    response += 'Content-Type: text/html\r\n\r\n'
    response += html 
    return response

def get_response(request_type, headers, body):
    if request_type == 'GET':
        return build_response('', login_page)
    username, password = login_parse(body) 
    
    # check for the logout
    if 'logout' in body:
        remove_cookie = 'Set-Cookie: token=; expires=Thu, 01 Jan 1970 00:00:00 GMT\r\n'
        for header in headers.splitlines():
            if 'token' in header:
                token = header.split(' ')[1].split('=')[1]
                cookie_remove(token)
        return build_response(remove_cookie, login_page)

    # check for cookie login
    for header in headers.splitlines():
        if 'token' in header:
            token = header.split(' ')[1]
            cookie_result, user = cookie_auth(token)
            if cookie_result:
                content = success_page + get_secret(user)
                return build_response('', content) 
            else:
                return build_response('', bad_creds_page)

    # default login page
    if body == '':
        return build_response('', login_page)

    # regular authentication
    if authenticate(body):
        headers = cookie_update(username)
        content = success_page + get_secret(username)
        return build_response(headers, content) 
    return build_response('', bad_creds_page)
    
### Loop to accept incoming HTTP connections and respond.
while True:
    # Set up the data structures with the file data.
    data_initializer()

    # Accept new clinets
    client, addr = sock.accept()
    req = client.recv(1024)

    # Separate the headers and the body
    headers, body = request_parse(req)

    # Get the request type "GET" or "POST"
    request_type = get_request_type(headers)

    # Generate response based on the request, headers, and body
    response = get_response(request_type, headers, body)

    # Send the response and close the client socket
    client.send(response.encode('utf-8'))
    client.close()

# We will never actually get here.
# Close the listening socket
sock.close()
