import time
import threading
from nltk.tokenize import word_tokenize
from bs4 import BeautifulSoup

import json


from flask import Flask, request, jsonify
import requests
from flask_cors import CORS


user_log = []


def create_app():
    app = Flask(__name__)
    CORS(app)

    @app.route('/start/<cid>')
    def session_start(cid):
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        user_type = data.get('user_type')   # user_type: "s" or "i"
        request_data = {"email": email, "password": password}
        response_login = requests.post("http://lax.nonev.win:5500/users/login", json=request_data)
        if response_login.status_code == 401:
            return jsonify(message='Invalid credentials'), 401
        if response_login.status_code == 200:
            response_course = requests.get(f"http://lax.nonev.win:5500/users/{email}/courses/all")
            # print(response_course.json())
            if cid not in [entry["id"] for entry in response_course.json()]:
                return jsonify(message='Invalid Course ID'), 404
            # user_log.append({"email": email, "cid": cid, "type": user_type})
            embed(email, cid)
            user_log.append({"email": email, "cid": cid, "user_type": user_type})
            print(user_log)
            return jsonify(message=f"The bot for course {cid}, user {email} is up and running!"), 200

    @app.route('/stop/<cid>')
    def session_stop(cid):
        data = request.get_json()
        email = data.get('email')
        for course in user_log:
            if course["cid"] == cid and course["email"] == email:
                    request_data = {"email": email}
                    response_logout = requests.post("http://lax.nonev.win:5500/users/logout", json=request_data)
                    if response_logout.status_code == 401:
                        return jsonify(message='Invalid credentials'), 401
                    if response_logout.status_code == 200:
                        user_log.remove(course)
                        print(user_log)
                    return jsonify(message=f"The bot is terminated for course {cid}, user {email}!"), 200
        return jsonify(message='Invalid credentials'), 401

    return app


def preprocess_qa_pairs(data):
    preprocessed_data = {}
    for index, item in enumerate(data):
        # print(f"data id: {index}")
        if item is not None:
            detail = item.get('detail')  # Use get to avoid KeyError
            subject = detail.get('subject', '') if detail else 'no detail'
            content = detail.get('content', '') if detail else 'provided'
            combined_text = f'Questions: {subject} {content} Answer: '
            answers = item.get('answers')
            if answers:
                combined_text += ' '.join(answer['content'] for answer in answers)
            else:
                combined_text += 'no answer'
        else:
            combined_text = 'Questions: no item provided Answer: no answer'

        text = BeautifulSoup(combined_text, 'html.parser').get_text().lower()
        preprocessed_text = ' '.join(word_tokenize(text))

        preprocessed_data[str(index)] = preprocessed_text

    return preprocessed_data


def embed(email, cid):
    print("Start embedding!")
    print("Start getting posts...(might take some minutes)")

    response_posts = requests.get(f"http://lax.nonev.win:5500/users/{email}/courses/{cid}/posts/all")
    response_posts = response_posts.json()
    # with open("test_w.json", "r") as file:
    #     response_posts = json.load(file)

    print("Successfully get all posts!")
    # with open("test_w.json", "w") as file:
    #     json.dump(response_posts, file)

    preprocess = preprocess_qa_pairs(response_posts)
    request_body = {
        "courseID": cid,
        "fileID": "Piazza_API",
        "content": preprocess
    }
    print("Sending to embedding model")
    response_embed = requests.post(f"http://lax.nonev.win:5000/upload-json", json=request_body)
    if response_embed.status_code == 200:
        print("Embed successfully!")
    else:
        print("Failed to embed...")


def bot():
    print("Bot working!")
    for user in user_log:
        email = user["email"]
        cid = user["cid"]
        user_type = user["user_type"]
        response_unread = requests.get(f"http://lax.nonev.win:5500/users/{email}/courses/{cid}/posts/unread")
        print(cid, response_unread.json())
        for unread in response_unread.json():
            if unread["type"] == "question":
                question = unread["detail"]["subject"]+" "+unread["detail"]["content"]
                pid = unread["id_c"]
                print(pid, question)
                response_answer = requests.post("http://lax.nonev.win:5000/ask", json={"question": question, "courseID": cid}).json()
                answer1 = response_answer["answer"]
                answer2 = response_answer["llamaIndexAnswer"]
                answer = f"TA bot 1:\n{answer1}\n\nTA bot 2:\n{answer2}"
                # answer = f"Coursistant answer:\n{answer1}"
                request_data = {"content": answer, "revision": 0, "user_type": user_type}
                response_post = requests.post(f"http://lax.nonev.win:5500/users/{email}/courses/{cid}/posts/{pid}",json=request_data)
                print(response_post.status_code)
                if response_post.status_code == 200:
                    print("Answer posted!")
                if response_post.status_code == 401:
                    print("Invalid user or user type!")
    time.sleep(100)


if __name__ == '__main__':

    # Start Flask app in a separate thread
    flask_thread = threading.Thread(target=create_app().run, kwargs={'host': '0.0.0.0', 'port': 5505})
    flask_thread.start()

    while True:
        bot()
