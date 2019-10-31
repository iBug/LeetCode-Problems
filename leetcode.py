import sys
import os
import json
import sqlite3
import getpass

import requests


class LeetCodeDatabase:
    def __init__(self, filename):
        self.db = sqlite3.connect(filename)

    def __del__(self):
        self.db.close()

    def create_all(self):
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS
            `questions` (
                id              INTEGER PRIMARY KEY,
                titleSlug       TEXT UNIQUE,
                title           TEXT,
                content         TEXT,
                difficulty      TEXT CHECK (difficulty IN ('Easy', 'Medium', 'Hard')),
                likes           INTEGER,
                dislikes        INTEGER,
                totalAccepted   INTEGER,
                totalSubmission INTEGER
            )""")
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS
            `topicTags` (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                questionId INTEGER NOT NULL,
                tag        TEXT
            )""")
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS
            `codeSnippets` (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                questionId INTEGER NOT NULL,
                lang       TEXT,
                code       TEXT
            )""")
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS
            `solutions` (
                id            INTEGER PRIMARY KEY,
                questionId    INTEGER NOT NULL,
                content       TEXT,
                averageRating REAL,
                votes         INTEGER
            )""")
        self.db.commit()

    def add_question(self, i):
        # Try looking it up first
        result = self.db.execute("SELECT COUNT(*) FROM `questions` WHERE id = ?", (i['questionId'],)).fetchone()
        if result[0]:  # The question already exists in DB
            return
        s = json.loads(i['stats'])

        # Save question into DB
        self.db.execute(
            """INSERT INTO `questions` VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (i['questionId'], i['titleSlug'], i['title'], i['content'], i['difficulty'], i['likes'], i['dislikes'], s['totalAcceptedRaw'], s['totalSubmissionRaw']))

        # Save tags into DB
        self.db.executemany(
            """INSERT INTO `topicTags` (questionId, tag) VALUES (?, ?)""",
            [(i['questionId'], s['name']) for s in i['topicTags']])

        # Save code templates into DB
        if i['codeSnippets']:
            # The GraphQL endpoint returns NULL if no code snippets available
            self.db.executemany(
                """INSERT INTO `codeSnippets` (questionId, lang, code) VALUES (?, ?, ?)""",
                [(i['questionId'], s['lang'], s['code']) for s in i['codeSnippets']])

        # Solutions are stored separately
        self.db.commit()

    def add_solution(self, i):
        s = i['solution']
        if not s:
            # Some problems don't have solutions yet
            return
        result = self.db.execute("SELECT COUNT(*) FROM `solutions` WHERE id = ?", (s['id'],)).fetchone()
        if result[0]:
            # The question already exists in DB
            return

        r = s['rating']
        if not r:
            r = {'average': None, 'count': 0}
        self.db.execute(
            """INSERT INTO `solutions` VALUES (?, ?, ?, ?, ?)""",
            (s['id'], i['questionId'], s['content'], r['average'], r['count']))
        self.db.commit()

    def get_all_question_ids(self):
        r = self.db.execute("SELECT id FROM `questions`").fetchall()
        return [item[0] for item in r]

    def get_question(self, id):
        r = self.db.execute("SELECT * FROM `questions` WHERE id = ?", (id,)).fetchone()
        result = {
            'questionId': r[0],
            'titleSlug': r[1],
            'title': r[2],
            'content': r[3],
            'difficulty': r[4],
            'likes': r[5],
            'dislikes': r[6],
            'totalAccepted': r[7],
            'totalSubmission': r[8],
        }
        r = self.db.execute("SELECT t.tag FROM `topicTags` AS t INNER JOIN `questions` AS q ON q.id = t.questionId WHERE q.id = ?", (id,)).fetchall()
        result['topicTags'] = [item[0] for item in r]
        r = self.db.execute("SELECT c.lang, c.code FROM `codeSnippets` AS c INNER JOIN `questions` AS q ON q.id = c.questionId WHERE q.id = ?", (id,)).fetchall()
        result['codeSnippets'] = [{'lang': item[0], 'code': item[1]} for item in r]
        r = self.db.execute("SELECT s.id, s.content, s.averageRating, s.votes FROM `solutions` AS s INNER JOIN `questions` AS q ON q.id = s.questionId WHERE q.id = ?", (id,)).fetchall()
        if r:
            r = r[0]
            result['solution'] = {
                'id': str(r[0]),
                'content': r[1],
                'averageRating': r[2],
                'votes': r[3],
            }
        else:
            result['solution'] = {}
        return result


class LeetCodeClient:
    def __init__(self):
        self.client = requests.Session()
        self.data_dir = os.path.join(os.path.dirname(sys.argv[0]), "data")
        self.questions_dir = os.path.join(self.data_dir, "problems")
        self.solutions_dir = os.path.join(self.data_dir, "articles")

        self.questions_file = os.path.join(self.data_dir, "problems.json")

        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.questions_dir, exist_ok=True)
        os.makedirs(self.solutions_dir, exist_ok=True)

        self.db = LeetCodeDatabase(os.path.join(self.data_dir, "data.db"))
        self.db.create_all()

    def login(self, username, password):
        login_url = 'https://leetcode.com/accounts/login/'
        self.client.get(login_url)
        data = {'login': username, 'password': password, 'csrfmiddlewaretoken': self.client.cookies['csrftoken']}
        headers = {
            'Referer': login_url,
            'X-CSRFToken': self.client.cookies['csrftoken'],
        }
        response = self.client.post(login_url, json=data, headers=headers)
        if response.status_code != 200:
            raise Exception("Login failed")

    def fetch_all_questions(self):
        if os.path.isfile(self.questions_file):
            try:
                with open(self.questions_file, "r") as f:
                    questions = json.load(f)
                return questions
            except Exception:  # Consider file corrupt
                pass
        response = self.client.get("https://leetcode.com/api/problems/all/")
        if response.status_code != 200:
            raise Exception("Unable to fetch problem list")
        questions = response.json()
        with open(self.questions_file, "w") as f:
            json.dump(questions, f, indent=2)
        return questions

    def fetch_question(self, slug: str):
        question_file = os.path.join(self.questions_dir, slug + ".json")
        try:
            with open(question_file, "r") as f:
                return json.load(f)
        except Exception:
            pass

        # Fetch from GraphQL endpoint
        query = "query questionData($titleSlug: String!) { question(titleSlug: $titleSlug) { questionId title titleSlug content difficulty likes dislikes topicTags { name slug } codeSnippets { lang langSlug code __typename } stats hints solution { id canSeeDetail __typename } status } }"
        headers = {
            'Accept-Encoding': "deflate, gzip",
            'X-CSRFToken': self.client.cookies['csrftoken']
        }
        payload = {
            'operationName': "questionData",
            'variables': {'titleSlug': slug},
            'query': query,
        }
        response = self.client.post("https://leetcode.com/graphql", headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch problem \"{slug}\" (Code {response.status_code})")
        data = response.json()['data']['question']
        self.db.add_question(data)

        with open(question_file, "w") as f:
            json.dump(data, f)
        return data

    def fetch_solution(self, slug: str):
        solution_file = os.path.join(self.solutions_dir, slug + ".json")
        try:
            with open(solution_file, "r") as f:
                return json.load(f)
        except Exception:
            pass

        # Fetch from GraphQL endpoint
        query = "query QuestionNote($titleSlug: String!) { question(titleSlug: $titleSlug) { questionId article solution { id url content contentTypeId canSeeDetail rating { id count average } } } }"
        headers = {
            'Accept-Encoding': "deflate, gzip",
            'X-CSRFToken': self.client.cookies['csrftoken']
        }
        payload = {
            'operationName': "QuestionNote",
            'variables': {'titleSlug': slug},
            'query': query,
        }
        response = self.client.post("https://leetcode.com/graphql", headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch solution for \"{slug}\" (Code: {response.status_code})")
        data = response.json()['data']['question']
        self.db.add_solution(data)

        with open(solution_file, "w") as f:
            json.dump(data, f)
        return data

    def get_question(self, id):
        # Fetch from DB
        return self.db.get_question(id)


def main():
    username = os.environ.get('LEETCODE_USERNAME')
    password = os.environ.get('LEETCODE_PASSWORD')
    if not username:
        username = input("Enter your LeetCode username: ")
    if not password:
        password = getpass.getpass("Enter your LeetCode password: ")

    spider = LeetCodeClient()
    spider.login(username, password)

    total_count = 0
    success_count = 0
    all_questions = spider.fetch_all_questions()['stat_status_pairs']
    all_questions_count = len(all_questions)
    for question in all_questions:
        total_count += 1
        print(f"""\x1B[2K Fetching "{question['stat']['question__title_slug']}" ({total_count} / {all_questions_count})""", end="\r", file=sys.stderr)
        try:
            spider.fetch_question(question['stat']['question__title_slug'])
            spider.fetch_solution(question['stat']['question__title_slug'])
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print(f"\x1B[2K{exc_type} when fetching {question['stat']['question__title_slug']}: {exc_obj}", file=sys.stderr)
        except KeyboardInterrupt:
            print("")
            break
        else:
            success_count += 1
    print(f"{success_count} out of {total_count} LeetCode questions are fetched successfully.")

    output_data = []
    for question_id in sorted(spider.db.get_all_question_ids()):
        output_data.append(spider.get_question(question_id))

    with open("output.json", "w") as f:
        json.dump(output_data, f, indent=2)


if __name__ == '__main__':
    main()
