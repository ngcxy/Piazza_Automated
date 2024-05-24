## How to run Automated Piazza server

### Step 1:
**POST** `http://lax.nonev.win:5500/users/login`

Request Body: {"email": "test@usc.edu", "password": "12345678"}

### Step 2:
**GET** `http://lax.nonev.win:5500/users/<email>/courses/all`

This will return a list of courses and their IDs. Choose the course from the list.

### Step 3: (Notice that the port number is Different!)
**POST** `http://lax.nonev.win:5505/start/<cid>`

Request Body: {"email": "test@usc.edu", "password": "12345678", "user_type": "i"}

For "user_type", if you're an instructor, use "i", otherwise use "s".

**This step will get all the history posts and pass to the database, so it will take up to 5-10 minutes**
