import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgresql://{}/{}".format(
            'localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        # new question object
        self.new_question = {
            'question': 'What color is the sky?',
            'answer': 'Blue',
            'category': 1,
            'difficulty': 1
        }

        # new quiz ojbect
        self.play = {
            'previous_questions': [2],
            'quiz_category': {'type': 'Geography', 'id': '3'}
        }

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    Test for successful operation and for expected errors.
    """

    def test_add_new_question(self):
        res = self.client().post('/questions/add', json=self.new_question)
        data = json.loads(res.data)
        question = (Question.query
                    .filter(Question.id == data['created']).one_or_none())
        self.assertEqual(res.status_code, 200)  # status code
        self.assertEqual(data['success'], True)
        self.assertEqual(data['created'], question.id)  # is question created
        # print("created question", question.id, question.question)

    def test_422_invalid_add_question_data(self):
        res = self.client().post('/questions/add',
                                 json={"question": "", "answer": "",
                                       "category": "1", "difficulty": "1"})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'unprocessable')

    def test_get_all_categories(self):
        res = self.client().get('/categories')  # is client geting endpoint
        data = json.loads(res.data)  # load data w/ json.loads as string
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['categories']['1'], "Science")
        self.assertEqual(len(data['categories']), 6)

    def test_get_paginated_questions_categories_current_category(self):
        res = self.client().get('/questions')  # is client geting endpoint
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['categories'])
        self.assertTrue(data['total_questions'])
        self.assertEqual(len(data['questions']), 10)  # paginate 10 questions

    def test_404_request_beyond_valid_page(self):
        res = self.client().get('/questions?page=1000')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    def test_get_category_questions(self):
        res = self.client().get('/categories/1/questions')  # science category
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['questions'])
        self.assertTrue(data['total_questions'])
        self.assertEqual(data['current_category'], 1)
        self.assertTrue(0 <= len(data['questions']) <= 10)  # pagination check

    def test_422_if_category_does_not_exist(self):
        res = self.client().get('/categories/1000/questions')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'unprocessable')

    def test_get_question_search_with_results(self):
        res = self.client().post('/questions/search',
                                 json={'searchTerm': 'title'})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['questions'])
        self.assertEqual(len(data['questions']), 2)

    def test_404_no_search_results(self):
        res = self.client().post('/questions/search', json={'searchTerm': ''})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    def test_422_if_play_fails_to_load_questions(self):
        res = self.client().post('/play', json={'question': {}})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'unprocessable')

    def test_play_all_or_by_category(self):
        res = self.client().post('/play', json=self.play)    # sample data
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['question'])

    def test_delete_question(self):
        # this delete test can now be run repeatedly because it deletes
        # a question that was added in test_add_new_question test
        added_question = (Question.query.filter
                          (Question.question == self.new_question['question'])
                          .one_or_none())
        print(added_question.id, " is the question id")
        res = self.client().delete('/questions/' + str(added_question.id))
        data = json.loads(res.data)
        # now get question after deleting it
        question = Question.query.filter(Question.id
                                         == added_question.id).one_or_none()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['deleted'], added_question.id)
        self.assertEqual(question, None)  # make sure it no longer exists

    def test_422_delete_fail(self):
        res = self.client().delete('/questions/1000')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'unprocessable')


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
