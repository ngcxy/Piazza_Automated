import time
import threading
from nltk.tokenize import word_tokenize
from bs4 import BeautifulSoup
import json
import re


from flask import Flask, request, jsonify
import requests
from flask_cors import CORS

import nltk
nltk.download('punkt')

user_log = []


def create_app():
    app = Flask(__name__)
    CORS(app)

    @app.route('/start/<cid>', methods=['POST'])
    def session_start(cid):
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        embedding = data.get('embedding', False)
        user_type = data.get('user_type')   # user_type: "s" or "i"
        request_data = {"email": email, "password": password}
        response_login = requests.post("http://lax.nonev.win:5500/users/login", json=request_data)
        print(f"User {email} logged in for course {cid}!")
        if response_login.status_code == 401:
            return jsonify(message='Invalid credentials'), 401
        if response_login.status_code == 200:
            response_course = requests.get(f"http://lax.nonev.win:5500/users/{email}/courses/all")
            print(response_course.json())
            if cid not in [entry["id"] for entry in response_course.json()]:
                return jsonify(message='Invalid Course ID'), 404
            cname = ""
            for item in response_course.json():
                if item["id"] == cid:
                    cname = item["name"]
                    cname = cname.replace(" ", "")
                    cname = re.sub(r'[^\w.-]', '', cname)
            print(cname)
            if embedding is True:
                embed(email, cid, cname)
            user_log.append({"email": email, "cid": cid, "cname": cname, "user_type": user_type})
            print(user_log)
            return jsonify(message=f"The bot for course {cid}, {cname}, user {email} is up and running!"), 200

    @app.route('/stop/<cid>', methods=['POST'])
    def session_stop(cid):
        data = request.get_json()
        email = data.get('email')
        for i in user_log:
            if i["cid"] == cid and i["email"] == email:
                    request_data = {"email": email}
                    response_logout = requests.post("http://lax.nonev.win:5500/users/logout", json=request_data)
                    if response_logout.status_code == 401:
                        return jsonify(message='Invalid credentials'), 401
                    if response_logout.status_code == 200:
                        user_log.remove(i)
                        print(user_log)
                    return jsonify(message=f"The bot is terminated for course {cid}, user {email}!"), 200
        return jsonify(message='Invalid credentials'), 401

    @app.route('/search', methods=['POST'])
    def search_status():
        data = request.get_json()
        info_type = data.get('type')
        info = data.get('name')
        result = []
        if info_type == "user":
            for i in user_log:
                if i["email"] == info:
                    result.append({i["cid"]: i["cname"]})
        if info_type == "course":
            for i in user_log:
                if i["cid"] == info:
                    result.append(i["email"])
        return jsonify(result), 200

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


def embed(email, cid, cname):
    print("Start embedding!")
    print("Start getting posts...(might take some minutes)")

    # with open("test_w.json", "r") as file:
    #     response_posts = json.load(file)
    # if True:

    response_posts = requests.get(f"http://lax.nonev.win:5500/users/{email}/courses/{cid}/posts/all")

    if response_posts.status_code == 401:
        return jsonify(message='Getting all posts failed'), 401
    if response_posts.status_code == 200:
        print("Successfully get all posts!")
        # response_posts = response_posts.json()
        print(f"------{len(response_posts)}")

        preprocess = preprocess_qa_pairs(response_posts)
        request_body = {
            "courseID": cname,
            "fileID": "Piazza_API",
            "content": preprocess
        }
        print("Sending to embedding model")
        response_embed = requests.post(f"http://lax.nonev.win:5000/upload-json", json=request_body)
        if response_embed.status_code == 200:
            print("Embed successfully!")
        else:
            print("Failed to embed...")
            print(response_embed.text)

def embed_one(cname, question, answer):
    combined_text = f'Questions: {question} Answer: {answer}'
    text = BeautifulSoup(combined_text, 'html.parser').get_text().lower()
    preprocessed_text = ' '.join(word_tokenize(text))
    preprocessed_data = {"0": preprocessed_text}
    request_body = {
        "courseID": cname,
        "fileID": "Piazza_API",
        "content": preprocessed_data
    }
    response_embed = requests.post(f"http://lax.nonev.win:5000/upload-json", json=request_body)
    if response_embed.status_code == 200:
        print("Embed new posts successfully!")
    else:
        print("Failed to embed new post...")
        print(response_embed.text)

def bot():
    print("Bot Running!")
    for user in user_log:
        email = user["email"]
        cid = user["cid"]
        cname = user["cname"]
        user_type = user["user_type"]
        response_unread = requests.get(f"http://lax.nonev.win:5500/users/{email}/courses/{cid}/posts/unread")
        print(cid, response_unread.json())
        for unread in response_unread.json():
            if unread["type"] == "question":
                question = unread["detail"]["subject"]+" "+unread["detail"]["content"]
                pid = unread["id_c"]
                # print(pid, question)
                response_answer = requests.post("http://lax.nonev.win:5000/ask", json={"question": question, "courseID": cname}).json()
                print(response_answer)
                if response_answer["hasAnswer"] is True:
                    answer = response_answer["answer"]
                    answer = f"TA bot:\n{answer}\n"
                    request_data = {"content": answer, "revision": 0, "user_type": user_type}
                    response_post = requests.post(f"http://lax.nonev.win:5500/users/{email}/courses/{cid}/posts/{pid}", json=request_data)
                    print(response_post.status_code)
                    if response_post.status_code == 200:
                        embed_one(cname, question, response_answer["answer"])
                        print("Answer posted!")
                    if response_post.status_code == 401:
                        print("Invalid user or user type!")
    time.sleep(10)


if __name__ == '__main__':

    # Start Flask app in a separate thread
    flask_thread = threading.Thread(target=create_app().run, kwargs={'host': '0.0.0.0', 'port': 5505})
    flask_thread.start()

    while True:
        bot()