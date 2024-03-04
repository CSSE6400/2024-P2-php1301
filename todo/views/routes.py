from flask import Blueprint, jsonify, request
from todo.models import db
from todo.models.todo import Todo
from datetime import datetime, timedelta
 
api = Blueprint('api', __name__, url_prefix='/api/v1') 

TEST_ITEM = {
    "id": 1,
    "title": "Watch CSSE6400 Lecture",
    "description": "Watch the CSSE6400 lecture on ECHO360 for week 1",
    "completed": True,
    "deadline_at": "2023-02-27T00:00:00",
    "created_at": "2023-02-20T00:00:00",
    "updated_at": "2023-02-20T00:00:00"
}
 
@api.route('/health') 
def health():
    """Return a status of 'ok' if the server is running and listening to request"""
    return jsonify({"status": "ok"})


@api.route('/todos', methods=['GET'])
def get_todos():
    completed_param = request.args.get('completed')
    window = int(request.args.get('window')) if request.args.get('window') is not None else None

    todos = Todo.query.all()
    current_time = datetime.now()

    if window is not None:
        window_end_time = current_time + timedelta(days=window)

        todos = [todo for todo in todos if todo.deadline_at <= window_end_time]

    if completed_param is not None:
        completed = completed_param.lower() == 'true'
        todos = [todo for todo in todos if todo.completed == completed]

    result = [todo.to_dict() for todo in todos]

    return jsonify(result)

@api.route('/todos/<int:id>', methods=['GET'])
def get_todo(id):
    todo = Todo.query.get(id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    return jsonify(todo.to_dict())

@api.route('/todos', methods=['POST'])
def create_todo():
    # Define the expected fields
    expected_fields = ['title', 'description', 'completed', 'deadline_at']
    request_data = request.get_json()

    # Validate request body exists
    if not request_data:
        return jsonify({"error": "Request body is missing"}), 400

    # Check for unexpected fields
    extra_fields = [key for key in request_data if key not in expected_fields]
    if extra_fields:
        return jsonify({"error": "Unexpected fields {}".format(extra_fields)}), 400

    # Ensure mandatory fields 'title' and 'completed' are provided
    if 'title' not in request_data or request_data['title'].strip() == "":
        return jsonify({"error": "Title is required"}), 400
    if 'completed' not in request_data:
        request_data['completed'] = False

    # Prepare Todo instance
    todo = Todo(
        title=request_data['title'],
        description=request_data.get('description', ''),
        completed=request_data['completed'],
    )

    if 'deadline_at' in request_data:
        try:
            todo.deadline_at = datetime.fromisoformat(request_data['deadline_at'])
        except ValueError as e:
            return jsonify({"err": str(e)}), 400

    try:
        db.session.add(todo)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"err": str(e)}), 500

    # Successfully created the Todo
    return jsonify(todo.to_dict()), 201

@api.route('/todos/<int:id>', methods=['PUT'])
def update_todo(id):
    todo = Todo.query.get(id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404

    request_data = request.get_json()
    if not request_data:
        return jsonify({"error": "Request body is missing"}), 400

    expected_fields = ['title', 'description', 'completed', 'deadline_at']
    
    extra_fields = [key for key in request_data if key not in expected_fields]
    if extra_fields:
        return jsonify({"error": "Unexpected fields: {}".format(extra_fields)}), 400

    if 'title' in request_data and request_data['title'].strip() != "":
        todo.title = request_data['title']
    if 'description' in request_data:
        todo.description = request_data['description']
    if 'completed' in request_data:
        todo.completed = request_data['completed']
    
    if 'deadline_at' in request_data:
        try:
            todo.deadline_at = datetime.fromisoformat(request_data['deadline_at'])
        except ValueError:
            return jsonify({"error": "Invalid"}), 400

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error: {}".format(str(e))}), 500

    return jsonify(todo.to_dict()), 200

@api.route('/todos/<int:id>', methods=['DELETE'])
def delete_todo(id):
    todo = Todo.query.get(id)
    if todo is None:
        return jsonify({}), 200
    
    db.session.delete(todo)
    db.session.commit()
    return jsonify(todo.to_dict()), 200