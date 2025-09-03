from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import boto3
import hashlib
import json
from datetime import datetime
import threading
import time
import os
import sys
from decimal import Decimal
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'trivia_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
app.logger.setLevel(logging.DEBUG)

# DynamoDB setup
region = os.getenv('AWS_REGION', 'us-west-2')
print(f"Using DynamoDB region: {region}", flush=True)
dynamodb = boto3.resource('dynamodb', region_name=region)

# Game state
games = {}
game_timers = {}

def init_dynamodb():
    """Initialize DynamoDB tables"""
    print(f"Creating DynamoDB tables in region: {region}", flush=True)
    try:
        # Create admins table
        admins_table = dynamodb.create_table(
            TableName='trivia_admins',
            KeySchema=[{'AttributeName': 'username', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'username', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        admins_table.wait_until_exists()
        
        # Create questions table
        questions_table = dynamodb.create_table(
            TableName='trivia_questions',
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        questions_table.wait_until_exists()
        
        # Create games table
        games_table = dynamodb.create_table(
            TableName='trivia_games',
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        games_table.wait_until_exists()
        
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print("Tables already exist", flush=True)
        pass  # Tables already exist
    except Exception as e:
        print(f"Error creating tables: {e}", flush=True)
        print(f"Region being used: {dynamodb.meta.client.meta.region_name}", flush=True)
    
    # Insert default admin
    admins_table = dynamodb.Table('trivia_admins')
    try:
        admins_table.put_item(
            Item={'username': 'admin', 'password': hashlib.sha256('admin123'.encode()).hexdigest()},
            ConditionExpression='attribute_not_exists(username)'
        )
    except:
        pass
    
    # Insert sample questions
    questions_table = dynamodb.Table('trivia_questions')
    sample_questions = [
        ("What is the capital of France?", "London", "Berlin", "Paris", "Madrid", "c"),
        ("Which planet is closest to the Sun?", "Venus", "Mercury", "Earth", "Mars", "b"),
        ("What is 2 + 2?", "3", "4", "5", "6", "b"),
        ("Who painted the Mona Lisa?", "Van Gogh", "Picasso", "Da Vinci", "Monet", "c"),
        ("What is the largest ocean?", "Atlantic", "Indian", "Arctic", "Pacific", "d")
    ] * 9
    
    for i, q in enumerate(sample_questions):
        try:
            questions_table.put_item(
                Item={
                    'id': str(i+1),
                    'question': q[0],
                    'option_a': q[1],
                    'option_b': q[2],
                    'option_c': q[3],
                    'option_d': q[4],
                    'correct_answer': q[5]
                },
                ConditionExpression='attribute_not_exists(id)'
            )
        except:
            pass

class GameState:
    def __init__(self, game_id, name, password):
        self.game_id = game_id
        self.name = name
        self.password = password
        self.players = {}
        self.admin_sid = None
        self.status = 'waiting'
        self.current_round = 0
        self.current_question = 0
        self.questions = []
        self.question_start_time = None
        self.answers = {}
        self.scores = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin_login():
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    print(f"=== ADMIN DASHBOARD ACCESSED ===", flush=True)
    print(f"Session contents: {dict(session)}", flush=True)
    
    if 'admin' not in session:
        print("Admin not in session, redirecting to login", flush=True)
        return redirect(url_for('admin_login'))
    
    print("Admin authenticated, loading dashboard", flush=True)
    
    try:
        print("=== LOADING ADMIN DASHBOARD ===", flush=True)
        games_table = dynamodb.Table('trivia_games')
        print(f"Table name: {games_table.table_name}", flush=True)
        print(f"Table region: {games_table.meta.client.meta.region_name}", flush=True)
        
        response = games_table.scan()
        print(f"DynamoDB scan response: {response}", flush=True)
        
        game_configs = response['Items']
        print(f"Dashboard - Found {len(game_configs)} games in DB", flush=True)
        print(f"Dashboard - Games data: {game_configs}", flush=True)
        print(f"Dashboard - Active games in memory: {list(games.keys())}", flush=True)
        
        print(f"Rendering template with {len(game_configs)} games", flush=True)
        
    except Exception as e:
        print(f"ERROR loading dashboard: {e}", flush=True)
        import traceback
        traceback.print_exc()
        game_configs = []
    
    return render_template('admin_dashboard.html', games=game_configs, active_games=games)

@app.route('/game/<game_id>')
def game_lobby(game_id):
    if game_id not in games:
        return "Game not found", 404
    return render_template('game_lobby.html', game_id=game_id)

@app.route('/game/<game_id>/play')
def game_play(game_id):
    if game_id not in games:
        return "Game not found", 404
    return render_template('game_play.html', game_id=game_id)

@app.route('/game/<game_id>/admin')
def game_admin(game_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    # Check if game exists in memory or database
    if game_id not in games:
        # Try to load from database
        try:
            games_table = dynamodb.Table('trivia_games')
            response = games_table.get_item(Key={'id': game_id})
            if 'Item' not in response:
                return "Game not found", 404
            
            # Create game state if it doesn't exist in memory
            game_data = response['Item']
            games[game_id] = GameState(game_id, game_data['name'], game_data['password'])
        except Exception as e:
            return f"Error loading game: {e}", 500
    
    return render_template('admin_game.html', game_id=game_id)

@app.route('/api/admin/login', methods=['POST'])
def admin_login_api():
    username = request.json['username']
    password = hashlib.sha256(request.json['password'].encode()).hexdigest()
    
    admins_table = dynamodb.Table('trivia_admins')
    response = admins_table.get_item(Key={'username': username})
    
    if 'Item' in response and response['Item']['password'] == password:
        session['admin'] = username
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/admin/create_game', methods=['POST'])
def create_game():
    print(f"=== CREATE GAME REQUEST ===")
    print(f"Session: {session}")
    print(f"Request data: {request.get_json()}")
    
    if 'admin' not in session:
        print("ERROR: Admin not in session")
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    try:
        request_data = request.get_json()
        if not request_data:
            print("ERROR: No JSON data received")
            return jsonify({'success': False, 'error': 'No data received'})
            
        name = request_data.get('name')
        password = request_data.get('password')
        
        if not name or not password:
            print(f"ERROR: Missing name or password. Name: {name}, Password: {password}")
            return jsonify({'success': False, 'error': 'Name and password required'})
        
        game_id = str(int(time.time()))
        
        print(f"Creating game: {name} with ID: {game_id}")
        
        # Test DynamoDB connection
        try:
            games_table = dynamodb.Table('trivia_games')
            print(f"DynamoDB region: {games_table.meta.client.meta.region_name}", flush=True)
            print(f"Table ARN: {games_table.table_arn}", flush=True)
            print(f"Table status: {games_table.table_status}", flush=True)
        except Exception as table_error:
            print(f"ERROR accessing table: {table_error}", flush=True)
            return jsonify({'success': False, 'error': f'Table access error: {str(table_error)}'})
        
        # Write to DynamoDB
        item = {
            'id': game_id,
            'name': name,
            'password': password,
            'created_at': datetime.now().isoformat()
        }
        print(f"Writing item: {item}", flush=True)
        
        response = games_table.put_item(Item=item)
        print(f"DynamoDB response: {response}", flush=True)
        
        # Verify write by reading back
        verify_response = games_table.get_item(Key={'id': game_id})
        print(f"Verification read: {verify_response}", flush=True)
        
        games[game_id] = GameState(game_id, name, password)
        print(f"In-memory games: {list(games.keys())}", flush=True)
        
        return jsonify({'success': True, 'game_id': game_id})
        
    except Exception as e:
        print(f"ERROR creating game: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@socketio.on('join_game')
def handle_join_game(data):
    game_id = data['game_id']
    password = data['password']
    player_name = data['player_name']
    
    print(f"Player {player_name} trying to join game {game_id} with password {password}", flush=True)
    
    if game_id not in games:
        print(f"Game {game_id} not found in memory", flush=True)
        emit('error', {'message': 'Game not found'})
        return
    
    game = games[game_id]
    print(f"Game password: {game.password}, provided password: {password}", flush=True)
    
    if game.password != password:
        print(f"Invalid password for game {game_id}", flush=True)
        emit('error', {'message': 'Invalid password'})
        return
    
    if len(game.players) >= 100:
        print(f"Game {game_id} is full", flush=True)
        emit('error', {'message': 'Game is full'})
        return
    
    print(f"Player {player_name} joining room {game_id}", flush=True)
    join_room(game_id)
    game.players[request.sid] = {
        'name': player_name,
        'score': 0,
        'eliminated': False,
        'readonly': False
    }
    
    print(f"Player {player_name} successfully joined. Total players: {len(game.players)}", flush=True)
    emit('joined_game', {'player_name': player_name})
    socketio.emit('player_joined', {'players': list(game.players.values())}, room=game_id)

@socketio.on('admin_join')
def handle_admin_join(data):
    game_id = data['game_id']
    print(f"Admin joining game: {game_id}", flush=True)
    if game_id in games:
        games[game_id].admin_sid = request.sid
        join_room(game_id)
        emit('admin_joined')
        
        # Send current player list to admin
        game = games[game_id]
        player_list = list(game.players.values())
        print(f"Sending {len(player_list)} players to admin", flush=True)
        emit('player_joined', {'players': player_list})
    else:
        print(f"Game {game_id} not found in memory", flush=True)
        emit('error', {'message': 'Game not found'})

@socketio.on('get_players')
def handle_get_players(data):
    game_id = data['game_id']
    if game_id in games:
        game = games[game_id]
        player_list = list(game.players.values())
        emit('player_joined', {'players': player_list})

@socketio.on('start_game')
def handle_start_game(data):
    game_id = data['game_id']
    print(f"Starting game {game_id}", flush=True)
    
    if game_id not in games:
        print(f"Game {game_id} not found", flush=True)
        return
    
    game = games[game_id]
    if game.admin_sid != request.sid:
        print(f"Unauthorized start game request", flush=True)
        return
    
    # Load questions from DynamoDB
    print(f"Loading questions from DynamoDB", flush=True)
    questions_table = dynamodb.Table('trivia_questions')
    response = questions_table.scan()
    all_questions = response['Items']
    print(f"Found {len(all_questions)} questions in database", flush=True)
    
    import random
    game.questions = random.sample(all_questions, min(45, len(all_questions)))
    print(f"Selected {len(game.questions)} questions for game", flush=True)
    
    game.status = 'playing'
    game.current_round = 1
    game.current_question = 0
    
    print(f"Emitting game_started to room {game_id}", flush=True)
    print(f"Players in room: {[p['name'] for p in game.players.values()]}", flush=True)
    socketio.emit('game_started', room=game_id)
    
    # Start first question after a short delay
    threading.Timer(2.0, start_question, [game_id]).start()
    print(f"First question will start in 2 seconds", flush=True)

def start_question(game_id):
    if game_id not in games:
        print(f"Game {game_id} not found in start_question", flush=True)
        return
    
    game = games[game_id]
    print(f"Starting question for game {game_id}, round {game.current_round}, question {game.current_question}", flush=True)
    
    if game.current_question >= 15:
        print(f"Round {game.current_round} complete, ending round", flush=True)
        end_round(game_id)
        return
    
    question_idx = (game.current_round - 1) * 15 + game.current_question
    if question_idx >= len(game.questions):
        print(f"No more questions, ending game", flush=True)
        end_game(game_id)
        return
    
    question = game.questions[question_idx]
    print(f"Question data: {question}", flush=True)
    
    game.question_start_time = time.time()
    game.answers = {}
    
    question_data = {
        'round': game.current_round,
        'question_num': game.current_question + 1,
        'question': question['question'],
        'options': {
            'a': question['option_a'],
            'b': question['option_b'],
            'c': question['option_c'],
            'd': question['option_d']
        }
    }
    
    print(f"Sending question data: {question_data}", flush=True)
    socketio.emit('new_question', question_data, room=game_id)
    
    # Start 30-second timer
    timer = threading.Timer(30.0, question_timeout, [game_id])
    game_timers[game_id] = timer
    timer.start()
    print(f"Question timer started for 30 seconds", flush=True)

@socketio.on('submit_answer')
def handle_submit_answer(data):
    game_id = data['game_id']
    answer = data['answer']
    
    if game_id not in games:
        return
    
    game = games[game_id]
    player = game.players.get(request.sid)
    
    if not player or player['eliminated'] or player['readonly']:
        return
    
    game.answers[request.sid] = answer
    
    # Check if all active players answered
    active_players = [p for p in game.players.values() if not p['eliminated'] and not p['readonly']]
    if len(game.answers) >= len(active_players):
        if game_id in game_timers:
            game_timers[game_id].cancel()
        question_timeout(game_id)

def question_timeout(game_id):
    if game_id not in games:
        return
    
    game = games[game_id]
    question_idx = (game.current_round - 1) * 15 + game.current_question
    correct_answer = game.questions[question_idx]['correct_answer']
    
    correct_players = []
    incorrect_players = []
    
    for sid, answer in game.answers.items():
        player = game.players[sid]
        if answer == correct_answer:
            correct_players.append({'sid': sid, 'name': player['name']})
        else:
            incorrect_players.append({'sid': sid, 'name': player['name']})
    
    socketio.emit('question_result', {
        'correct_answer': correct_answer,
        'correct_players': correct_players,
        'incorrect_players': incorrect_players
    }, room=game_id)
    
    # Allow voting phase
    if correct_players and incorrect_players:
        socketio.emit('voting_phase', {'incorrect_players': incorrect_players}, room=game_id)
        
        # Start voting timer
        timer = threading.Timer(15.0, end_voting, [game_id])
        game_timers[game_id] = timer
        timer.start()
    else:
        next_question(game_id)

@socketio.on('vote_player')
def handle_vote_player(data):
    game_id = data['game_id']
    target_sid = data['target_sid']
    
    if game_id not in games:
        return
    
    game = games[game_id]
    voter = game.players.get(request.sid)
    target = game.players.get(target_sid)
    
    if not voter or not target:
        return
    
    # Award points based on round
    points = game.current_round * (2 if game.current_round <= 2 else 4)
    
    # Check 4-point limit per round
    if target['score'] + points > (game.current_round * 4):
        return
    
    target['score'] += points
    
    # Eliminate if 10+ points
    if target['score'] >= 10:
        target['eliminated'] = True
        target['readonly'] = True
    
    emit('vote_recorded', {'target': target['name'], 'points': points})

def end_voting(game_id):
    next_question(game_id)

def next_question(game_id):
    if game_id not in games:
        return
    
    game = games[game_id]
    game.current_question += 1
    
    threading.Timer(3.0, start_question, [game_id]).start()

def end_round(game_id):
    if game_id not in games:
        return
    
    game = games[game_id]
    
    if game.current_round >= 3:
        end_game(game_id)
        return
    
    game.current_round += 1
    game.current_question = 0
    
    socketio.emit('round_ended', {'next_round': game.current_round}, room=game_id)
    threading.Timer(5.0, start_question, [game_id]).start()

def end_game(game_id):
    if game_id not in games:
        return
    
    game = games[game_id]
    final_scores = [(p['name'], p['score']) for p in game.players.values()]
    final_scores.sort(key=lambda x: x[1])
    
    socketio.emit('game_ended', {'final_scores': final_scores}, room=game_id)

if __name__ == '__main__':
    print("Initializing DynamoDB...", flush=True)
    try:
        init_dynamodb()
        print("DynamoDB initialized successfully", flush=True)
    except Exception as e:
        print(f"ERROR initializing DynamoDB: {e}", flush=True)
    
    print("Starting Flask application...", flush=True)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)