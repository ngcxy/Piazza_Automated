## How to run Automated Piazza server

### Step 1: User log in

**POST** `http://lax.nonev.win:5500/users/login`

Request Body: {"email": "test@usc.edu", "password": "12345678"}

For email and password, please enter the ones for the Piazza account.

### Step 2: Get available courses

**GET** `http://lax.nonev.win:5500/users/<email>/courses/all`

This will return a list of courses and their IDs. Choose the course from the list.

### Step 3: Start the bot

**POST** `http://lax.nonev.win:5505/start/<cid>`

Request Body: {"email": "test@usc.edu", "password": "12345678", "embedding": true, "user_type": "i"}

For "embedding", select _True_ for learning before starting, select _False_ for direct starting the bot. Default as False.

For "user_type", if you're an instructor, use "i", otherwise use "s".

**If choose to embed before launching, the application will get all the history posts and pass to the database, so it will take up to 5-10 minutes**

### Get user/course status

**POST** `http://lax.nonev.win:5505/search`

Request Body: {"type": xxx, "name": xxx}

Option 1: "info_type": "user", "info": "test@usc.edu" // return all courses(cid&name) running under this user

Option 2: "info_type": "course, "info": "courseCid" // return all users(email) owning bot for this course

### Stop the bot

**POST** `http://lax.nonev.win:5505/stop/<cid>`

Request Body: {"email": "test@usc.edu"}
