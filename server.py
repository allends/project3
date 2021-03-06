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
    print(users)
    print(secrets)


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
def get_secret(user_info):
    user, _ = headerparse(user_info)
    return secrets[user]

def headerparse(login_header):
    def extract(input):
        return input.split('=')[1]
    fields = login_header.split('&')
    key, value = map(extract, fields)
    return key, value

def authenticate(login_header):
    if login_header == '':
        return False
    key, value = headerparse(login_header)
    if key in users and users[key] == value:
        return True
    return False

### Loop to accept incoming HTTP connections and respond.
while True:
    data_initializer()
    client, addr = sock.accept()
    req = client.recv(1024)

    # Let's pick the headers and entity body apart
    header_body = req.split('\r\n\r\n')
    headers = header_body[0]
    body = '' if len(header_body) == 1 else header_body[1]
    print_value('headers', headers)
    print_value('entity body', body)
    login_info = ''
    if body != '':
        login_info = body
        if 'logout' in body:
            login_info = ''
    # TODO: Put your application logic here!
    # Parse headers and body and perform various actions

    # You need to set the variables:
    # (1) `html_content_to_send` => add the HTML content you'd
    # like to send to the client.
    # Right now, we just send the default login page.
    headers_to_send = ''
    if login_info == '':
        html_content_to_send = login_page
    elif authenticate(login_info):
        html_content_to_send = success_page + get_secret(login_info)
        username, _ = headerparse(login_info)
        if username not in cookies:
            rand_val = random.getrandbits(64)
            headers_to_send = 'Set-Cookie: token=' + str(rand_val) + '\r\n'
            cookies[username] = str(rand_val)
    else:
        html_content_to_send = bad_creds_page
    # But other possibilities exist, including
    # html_content_to_send = success_page + <secret>
    # html_content_to_send = bad_creds_page
    # html_content_to_send = logout_page

    # (2) `headers_to_send` => add any additional headers
    # you'd like to send the client?
    # Right now, we don't send any extra headers.
    print(cookies)

    # Construct and send the final response
    response = 'HTTP/1.1 200 OK\r\n'
    response += headers_to_send
    response += 'Content-Type: text/html\r\n\r\n'
    response += html_content_to_send
    print_value('response', response)
    client.send(response.encode('utf-8'))
    client.close()

    print("Served one request/connection!")
    print

# We will never actually get here.
# Close the listening socket
sock.close()
