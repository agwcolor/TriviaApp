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
        self.database_path = "postgresql://{}/{}".format('localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        #new question object
        self.new_question = {
            'question': 'What color is the sky?',
            'answer': 'Blue',
            'category': 1,
            'difficulty': 1
        }

        #new quiz ojbect
        self.play = {
            'previous_questions': [2],
            'quiz_category': {'type':'Geography','id':'3'}
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
    Write at least one test for each test for successful operation and for expected errors.
    """

    def test_get_all_categories(self):
        #number of total questions, current category, categories
        res = self.client().get('/categories') #is client geting endpoint
        data = json.loads(res.data) #load data w/ json.loads as string
        #check these things:
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['categories']['1'],"Science")
        self.assertEqual(len(data['categories']),6)

    def test_get_paginated_questions_categories_current_category(self):
        #number of total questions, current category, categories
        res = self.client().get('/questions') #is client geting endpoint
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['categories'])
        self.assertTrue(data['total_questions'])
        #print(data['total_questions'], len(data['questions']), data['categories'])
        self.assertEqual(len(data['questions']),10) #pagination-first page has 10 questions

    ''' You can only run this test once or change the question id ea time
    def test_delete_question(self):
        #click trash to delete, persist in db
        res = self.client().delete('/questions/2') #is client geting endpoint
        data = json.loads(res.data)
        question = Question.query.filter(Question.id == 2).one_or_none()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['deleted'],2)
        print(data['deleted'], " was deleted")
        self.assertEqual(question, None) #make sure it no longer exists
        '''

    def test_add_new_question(self):
        res = self.client().post('/questions/add', json=self.new_question)  #correct endpoint
        data = json.loads(res.data)
        question = Question.query.filter(Question.id == data['created']).one_or_none()
        self.assertEqual(res.status_code, 200) #status code
        self.assertEqual(data['success'], True)
        #self.assertTrue(data['created']) #is question created
        self.assertEqual(data['created'], question.id) #is question created
        print("created question", question.id, question.question)


    def test_get_question_search_with_results(self):
        res = self.client().post('/questions/search', json={'searchTerm':'bird'}) #endpoint expects argument (search) with a value
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        #print(data, " is the search data")
        self.assertEqual(data['success'], True)
        self.assertTrue(data['questions'])
        self.assertEqual(len(data['questions']), 1)

    def test_404_no_search_results(self):
        res = self.client().post('/questions/search', json={'searchTerm':''}) 
        data = json.loads(res.data) 
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    def test_get_category_questions(self):
        #number of total questions, current category, categories
        res = self.client().get('/categories/1/questions') #endpoint for science category
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['questions'])
        self.assertTrue(data['total_questions'])
        self.assertEqual(data['current_category'],1)
        print(data['total_questions'], len(data['questions']), data['current_category'])
        self.assertTrue(0 <= len(data['questions']) <=10) #pagination-first page has 10 questions

    def test_422_if_category_does_not_exist(self):
        res = self.client().get('/categories/1000/questions')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'unprocessable')

    def test_422_if_play_fails_to_load_questions(self):
        res = self.client().post('/play', json={'question':{}})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'unprocessable')

    def test_play_all_or_by_category(self):
        res = self.client().post('/play', json=self.play) #sample data
        data = json.loads(res.data)
        print(data['question'])
        print(data['success'])
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['question'])


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()