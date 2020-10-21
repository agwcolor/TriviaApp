from flask import Flask, request, abort, jsonify
from flask.helpers import flash
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

# paginate helper method


def paginate_questions(request, selection):
    body = request.get_json()
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    formatted_questions = [question.format() for question in selection]
    return formatted_questions[start:end]


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    CORS(app)  # default for origins is '*'

    @app.after_request  # after request received run this method
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorizatoin')
        response.headers.add('Access-Control-Allow-Headers',
                             'GET,POST,PATCH,DELETE,OPTIONS')
        return response

    '''
  ENDPOINT: Handle GET requests for all available categories.
  Returns reshaped category dict.
  curl  http://127.0.0.1:5000/categories

  '''
    @app.route('/categories', methods=['GET', 'POST'])
    def get_categories():
        # reshape `categories` return value to {'1':'Science',...,'6':'Sports'}
        category_dict = {cat.id: cat.type for cat in Category.query.all()}
        print(category_dict)
        if len(category_dict) > 0:
            return jsonify({  # start by building out request body
                'success': True,
                'categories': category_dict  # formatted_categories
            })
        else:
            abort(404)

    '''
  ENDPOINT: Handles GET requests for questions, paginated(every 10 questions).
  Returns: a list of questions, number of total questions,
  current category, categories.

  TEST: Questions and categories are generated when app is started,
  paginated: 10 questions per page.
  Clicking page numbers shows a new set of questions.

  curl "http://127.0.0.1:5000/questions?page=2

  '''
    @app.route('/questions', methods=['GET'])
    def get_questions():
        questions = Question.query.all()
        page = request.args.get('page', 1, type=int)
        if page > (len(questions) // 10) + 1:
            abort(404)
        else:
            current_questions = paginate_questions(request, questions)
            # reshape `categories` to {id:type,...,'6':'Sports'}
            category_dict = {cat.id: cat.type for cat in Category.query.all()}
            return jsonify({  # start by building out request body
                'success': True,
                'questions': current_questions,
                'total_questions': len(Question.query.all()),
                'current_category': None,
                'categories': category_dict,
            })

    '''
  ENDPOINT : DELETE question using a question ID.
  TEST: Click the trash icon next to a question to remove the question.
  This should persist in the database & on page refresh.
  curl -X DELETE "http://127.0.0.1:5000/questions/24"

  '''
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_questions(question_id):
        question = Question.query.filter(
            Question.id == question_id).one_or_none()
        try:
            question.delete()
            return jsonify({
                'success': True,
                'deleted': question_id,
            })
        except BaseException:
            abort(422)

    '''
  Endpoint : POST a new question,
  Requires: question text, answer text, category, and difficulty score.
  TEST: "Add" question tab -- Add new trivia question form. After submitting,
  the form clears. The question will appear on the "List" tab)

  curl http://127.0.0.1:5000/questions/add
    -X POST
    -H "Content-Type: application/json"
    -d '{"answer":"My answer","category":"1", "difficulty":"5",
        "question":"my question"}'

  '''
    @app.route('/questions/add',
               methods=['POST'])  # plural collection endpoint
    def create_question():
        try:
            body = request.get_json()
            new_question = body.get('question', None)
            new_answer = body.get('answer', None)
            new_category = body.get('category', None)
            new_difficulty = body.get('difficulty', None)
            question = (
                Question(
                    question=new_question,
                    answer=new_answer,
                    category=new_category,
                    difficulty=new_difficulty))
            if all([new_question, new_answer, new_category, new_difficulty]):
                question.insert()
                return jsonify({
                    "success": True,
                    "created": question.id
                })
            else:
                abort(422)
        except BaseException:
            abort(422)  # unable to process question

    '''
  ENDPOINT: POST endpoint to submit search term.
  Returns any questions with a matching substring of the search term.

  TEST: Search by any phrase.
  Returns only questions that include that string in the question field.
  Try using the word "title" to start.

  curl http://127.0.0.1:5000/questions/search
    -X POST -H "Content-Type: application/json"
    -d '{"searchTerm":"title"}'

  '''

    @app.route('/questions/search', methods=['GET', 'POST'])
    def search_questions():
        body = request.get_json()

        search = body.get('searchTerm', 'None')
        print(search, " is the search term")
        if search:
            selection = (
                Question.query.order_by(
                    Question.id) .filter(
                    Question.question.ilike(
                        '%{}%'.format(search))))
            current_questions = paginate_questions(request, selection)
            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(selection.all())
            })
        else:
            abort(404)

    '''
  ENDPOINT: GET questions based on category.

  TEST: In the "List" tab, click a category in the left column
  to only see questions in that category.
  curl  http://127.0.0.1:5000/categories/1/questions
  '''
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_category_questions(category_id):
        category = Category.query.filter(
            category_id == Category.id).one_or_none()
        questions = Question.query.filter(
            category_id == Question.category).all()
        if not category:
            abort(422, "Unable to process : Category does not exist")
        elif len(questions) == 0:
            abort(404, "Sorry, There are no questions in this category")
        current_questions = paginate_questions(request, questions)
        return jsonify({  # start by building out request body
            'success': True,
            'questions': current_questions,
            'total_questions': len(current_questions),
            'current_category': category_id
        })

    '''
  POST endpoint: (Play tab) gets questions to play the quiz.
  Takes category (clicked) & previous_questions (from front end state) params,
  returns a random question within the given category or ALL.
  Question should not be one of the previous_questions.

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed. The user can answer
  and then see whether they are correct or not.
  '''
    @app.route("/play", methods=['POST'])
    def post_quizzes():
        '''
        Returns a single question from the database
        Filters the questions already sent to the client.
        curl -d '{"previous_questions": [2],
                "quiz_category": {"type":"Geography","id": "3"}}'
            -H 'Content-Type: application/json'
            -X POST http://127.0.0.1:5000/play
        '''
        try:
            body = request.get_json()
            category_id = body.get('quiz_category').get('id')
            category = Category.query.get(category_id)
            previous_questions = body.get("previous_questions", [])
            if int(category_id) > 0:
                if len(previous_questions) > 0:
                    questions = Question.query.filter(
                        Question.id.notin_(previous_questions),
                        Question.category == category.id
                    ).all()
                else:
                    questions = Question.query.filter(
                        Question. category == category.id).all()
            else:  # category = 0 or ALL
                if len(previous_questions) > 0:
                    questions = (
                        Question.query. filter(
                            Question.id.notin_(previous_questions)).all())
                else:
                    questions = Question.query.all()

            max = len(questions) - 1
            question = (questions[random.randint(0, max)]
                        .format() if max > 0 else False)
            # question {'id': 21, 'question': 'Who discovered penicillin?,
            #          'answer': 'Alexander Fleming', 'category': 1,
            #          'difficulty': 3}
            return jsonify({
                "success": True,
                "question": question
            })
        except BaseException:
            abort(422, "An error occured while trying to load \
                  the next question")

    '''
  Error Handlers
  '''
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "invalid syntax"
        }), 400

    @app.errorhandler(405)
    def not_allowed(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "method not allowed"
        }), 405

    @app.errorhandler(500)
    def not_allowed(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "server error"
        }), 405
    return app
