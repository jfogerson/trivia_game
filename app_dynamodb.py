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
            Item={'username': 'james', 'password': hashlib.sha256('pango123'.encode()).hexdigest()},
            ConditionExpression='attribute_not_exists(username)'
        )
    except:
        pass
    
    # Copy questions from source table if it exists
    try:
        source_table = dynamodb.Table('trivia_questions_source')
        questions_table = dynamodb.Table('trivia_questions')
        
        # Check if source table has questions
        source_response = source_table.scan(Limit=1)
        if source_response['Items']:
            print("Copying questions from source table", flush=True)
            
            # Get all questions from source
            response = source_table.scan()
            source_questions = response['Items']
            
            # Copy to game table (only if game table is empty)
            game_response = questions_table.scan(Limit=1)
            if not game_response['Items']:
                for question in source_questions:
                    questions_table.put_item(Item=question)
                print(f"Copied {len(source_questions)} questions to game table", flush=True)
            else:
                print("Game table already has questions", flush=True)
        else:
            print("Source table is empty, using default questions", flush=True)
            # Fallback to basic questions if source is empty
            basic_questions = [
                ("What is the capital of France?", "London", "Berlin", "Paris", "Madrid", "c"),
                ("Which planet is closest to the Sun?", "Venus", "Mercury", "Earth", "Mars", "b"),
                ("What is 2 + 2?", "3", "4", "5", "6", "b")
            ] * 15
            
            for i, q in enumerate(basic_questions):
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
                    
    except Exception as e:
        print(f"Error copying questions: {e}", flush=True)
        print("Using fallback questions", flush=True)

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

@app.route('/api/join_game', methods=['POST'])
def join_game_api():
    data = request.json
    game_id = data.get('game_id')
    password = data.get('password')
    player_name = data.get('player_name')
    
    if not all([game_id, password, player_name]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Verify game exists and password is correct
    if game_id not in games:
        return jsonify({'success': False, 'message': 'Game not found'}), 404
    
    game = games[game_id]
    if game.password != password:
        return jsonify({'success': False, 'message': 'Invalid password'}), 401
    
    # Store game session
    session[f'game_{game_id}'] = {
        'player_name': player_name,
        'authenticated': True
    }
    
    return jsonify({'success': True, 'redirect': f'/game/{game_id}'})

@app.route('/api/get_session_info', methods=['POST'])
def get_session_info():
    data = request.json
    game_id = data.get('game_id')
    
    if not game_id:
        return jsonify({'success': False, 'message': 'Game ID required'}), 400
    
    session_key = f'game_{game_id}'
    if session_key not in session or not session[session_key].get('authenticated'):
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    return jsonify({
        'success': True,
        'player_name': session[session_key]['player_name']
    })

@app.route('/game/<game_id>')
def game_lobby(game_id):
    if game_id not in games:
        return "Game not found", 404
    
    # Check if user is authenticated for this game
    if f'game_{game_id}' not in session or not session[f'game_{game_id}'].get('authenticated'):
        return redirect(url_for('index'))
    
    return render_template('game_lobby.html', game_id=game_id)

@app.route('/game/<game_id>/play')
def game_play(game_id):
    if game_id not in games:
        return "Game not found", 404
    
    # Check if user is authenticated for this game
    if f'game_{game_id}' not in session or not session[f'game_{game_id}'].get('authenticated'):
        return redirect(url_for('index'))
    
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

@app.route('/game/<game_id>/round/<int:round_number>')
def round_start(game_id, round_number):
    if game_id not in games:
        return "Game not found", 404
    if round_number not in [1, 2, 3]:
        return "Invalid round number", 400
    return render_template('round_start.html', round_number=round_number)

@app.route('/api/admin/login', methods=['POST'])
def admin_login_api():
    username = request.json['username']
    password = hashlib.sha256(request.json['password'].encode()).hexdigest()
    
    admins_table = dynamodb.Table('trivia_admins')
    response = admins_table.get_item(Key={'username': username})
    
    if 'Item' in response and response['Item']['password'] == password:
        session['admin'] = username
        return jsonify({'success': True, 'redirect': '/admin/dashboard'})
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401


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

@app.route('/api/admin/delete_game', methods=['POST'])
def delete_game():
    if 'admin' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    try:
        game_id = request.json['game_id']
        print(f"Deleting game {game_id}", flush=True)
        
        # Remove from DynamoDB
        games_table = dynamodb.Table('trivia_games')
        games_table.delete_item(Key={'id': game_id})
        print(f"Game {game_id} deleted from database", flush=True)
        
        # Notify players and remove from memory
        if game_id in games:
            game = games[game_id]
            print(f"Notifying {len(game.players)} players that game is cancelled", flush=True)
            
            # Notify all players that game is cancelled
            socketio.emit('game_cancelled', {'message': 'Game has been cancelled by administrator'}, room=game_id)
            
            # Remove all players from the room
            for player_sid in list(game.players.keys()):
                socketio.server.leave_room(player_sid, game_id)
            
            # Cancel any active timers
            if game_id in game_timers:
                game_timers[game_id].cancel()
                del game_timers[game_id]
            
            # Remove from memory
            del games[game_id]
            print(f"Game {game_id} removed from memory", flush=True)
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"ERROR deleting game: {str(e)}", flush=True)
        return jsonify({'success': False, 'error': str(e)})

@socketio.on('join_game')
def handle_join_game(data):
    game_id = data['game_id']
    player_name = data['player_name']
    
    print(f"Player {player_name} trying to join game {game_id}", flush=True)
    
    if game_id not in games:
        print(f"Game {game_id} not found in memory", flush=True)
        emit('error', {'message': 'Game not found'})
        return
    
    game = games[game_id]
    
    # Only clean up players that have been disconnected for a while
    # Don't clean up during active join process
    
    if len(game.players) >= 100:
        print(f"Game {game_id} is full", flush=True)
        emit('error', {'message': 'Game is full'})
        return
    
    # Check if this exact player (by sid) already exists
    player_exists = request.sid in game.players
    
    if not player_exists:
        # Temporarily disabled duplicate name check for debugging
        print(f"Current players in game: {[(sid, p.get('name', 'NO_NAME')) for sid, p in game.players.items()]}", flush=True)
        print(f"New player {player_name} with sid {request.sid} joining", flush=True)
        
        print(f"Player {player_name} joining room {game_id}", flush=True)
        join_room(game_id)
        game.players[request.sid] = {
            'name': player_name,
            'score': 0,
            'eliminated': False,
            'readonly': False,
            'eliminated_at': None
        }
    else:
        print(f"Player {player_name} already in game, updating info", flush=True)
        game.players[request.sid]['name'] = player_name
    
    print(f"Player {player_name} successfully joined. Total players: {len(game.players)}", flush=True)
    emit('joined_game', {'player_name': player_name})
    
    # If game is already playing, send current state to new player
    if game.status == 'playing':
        print(f"Game already playing, sending current state to {player_name}", flush=True)
        emit('game_started')
        # Show round start if we're at the beginning of a round
        if game.current_question == 0:
            print(f"Sending round start to new player: Round {game.current_round}", flush=True)
            emit('show_round_start', {'round_number': game.current_round})
    
    # Only emit player list update if this is a new player and game hasn't started
    if not player_exists and game.status == 'waiting':
        socketio.emit('player_joined', {'players': list(game.players.values())}, room=game_id)

@socketio.on('admin_join')
def handle_admin_join(data):
    game_id = data['game_id']
    print(f"Admin joining game: {game_id}", flush=True)
    if game_id in games:
        games[game_id].admin_sid = request.sid
        join_room(game_id)
        emit('admin_joined')
        
        # Send current player list to admin only
        game = games[game_id]
        player_list = list(game.players.values())
        print(f"Sending {len(player_list)} players to admin", flush=True)
        emit('admin_player_list', {'players': player_list})
    else:
        print(f"Game {game_id} not found in memory", flush=True)
        emit('error', {'message': 'Game not found'})

@socketio.on('get_players')
def handle_get_players(data):
    game_id = data['game_id']
    if game_id in games:
        game = games[game_id]
        player_list = list(game.players.values())
        emit('admin_player_list', {'players': player_list})

@socketio.on('stop_game')
def handle_stop_game(data):
    game_id = data['game_id']
    print(f"Stopping game {game_id}", flush=True)
    
    if game_id not in games:
        return
    
    game = games[game_id]
    if game.admin_sid != request.sid:
        return
    
    # Cancel any active timers
    if game_id in game_timers:
        game_timers[game_id].cancel()
        del game_timers[game_id]
    
    # Close all player tabs
    socketio.emit('close_tab', {'message': 'Game has been stopped by administrator'}, room=game_id)
    
    # Remove all players from the room
    for player_sid in list(game.players.keys()):
        socketio.server.leave_room(player_sid, game_id)
    
    # Reset game state
    game.status = 'waiting'
    game.current_round = 0
    game.current_question = 0
    game.questions = []
    game.players = {}
    
    print(f"Game {game_id} stopped and reset", flush=True)

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
    socketio.emit('game_started', room=game_id)
    
    # Show round 1 start screen before first question
    print(f"Showing round 1 start screen to room {game_id}", flush=True)
    socketio.emit('show_round_start', {'round_number': 1}, room=game_id)
    print(f"Round start event emitted, waiting 8 seconds before first question", flush=True)
    
    # Wait longer to ensure round start screen is seen
    threading.Timer(8.0, start_question, [game_id]).start()

def validate_question(question):
    """Validate question has required fields"""
    required_fields = ['question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer']
    
    for field in required_fields:
        if field not in question:
            return False
    
    # Check if correct_answer is valid (a, b, c, or d)
    if question['correct_answer'] not in ['a', 'b', 'c', 'd']:
        return False
        
    return True

def find_correct_answer_fallback(question, correct_text):
    """Try to find correct answer by matching text"""
    for option in ['a', 'b', 'c', 'd']:
        option_key = f'option_{option}'
        if option_key in question and question[option_key] == correct_text:
            question['correct_answer'] = option  # Fix the correct_answer field
            return correct_text
    return None

def skip_to_next_question(game_id):
    """Skip current question and move to next"""
    try:
        game = games[game_id]
        game.current_question += 1
        
        socketio.emit('question_skipped', {
            'message': 'Question had errors and was skipped'
        }, room=game_id)
        
        # Start next question after short delay
        threading.Timer(2.0, start_question, [game_id]).start()
        
    except Exception as e:
        print(f"Error skipping question: {e}", flush=True)
        end_game(game_id)

def start_question(game_id):
    try:
        if game_id not in games:
            print(f"Game {game_id} not found in start_question", flush=True)
            return
        
        game = games[game_id]
        print(f"Total players in game: {len(game.players)}", flush=True)
        
        # Check if only one player remains active before starting question
        active_players = [p for p in game.players.values() if not p['eliminated']]
        print(f"Active players: {len(active_players)}", flush=True)
        
        if len(active_players) <= 1:
            print(f"Not enough active players ({len(active_players)}), ending game", flush=True)
            end_game(game_id)
            return
        
        print(f"Starting question for game {game_id}, round {game.current_round}, question {game.current_question}", flush=True)
        
        if game.current_question >= 15:
            print(f"Round {game.current_round} complete, ending round", flush=True)
            end_round(game_id)
            return
        
        # Use modulo to cycle through questions if we run out
        question_idx = ((game.current_round - 1) * 15 + game.current_question) % len(game.questions)
        question = game.questions[question_idx]
        print(f"Question data: {question}", flush=True)
        
        # Validate question structure
        if not validate_question(question):
            print(f"Invalid question structure: {question}", flush=True)
            skip_to_next_question(game_id)
            return
        
        # Reset question state completely
        game.question_start_time = time.time()
        game.answers = {}
        game.voting_active = False
        game.votes_cast = {}
        game.points_awarded = {}
        game.question_expired = False
        
        # Cancel any existing timers
        if game_id in game_timers:
            game_timers[game_id].cancel()
            del game_timers[game_id]
        
        # Randomize correct answer position
        import random
        positions = ['a', 'b', 'c', 'd']
        new_correct_position = random.choice(positions)
        
        # Get the correct answer text with error handling
        original_correct = question['correct_answer']
        try:
            correct_text = question[f'option_{original_correct}']
        except KeyError:
            print(f"Error: Invalid correct_answer '{original_correct}' for question {question.get('id', 'unknown')}", flush=True)
            # Try to find the correct answer by matching text
            correct_text = find_correct_answer_fallback(question, original_correct)
            if not correct_text:
                skip_to_next_question(game_id)
                return
            original_correct = question['correct_answer']  # Use the fixed value
        
        # Create list of all answer texts
        all_options = [
            question['option_a'],
            question['option_b'],
            question['option_c'],
            question['option_d']
        ]
        
        # Remove correct answer and shuffle remaining
        other_options = [opt for opt in all_options if opt != correct_text]
        random.shuffle(other_options)
        
        # Place correct answer in random position, fill others
        final_options = [''] * 4
        correct_index = positions.index(new_correct_position)
        final_options[correct_index] = correct_text
        
        other_index = 0
        for i in range(4):
            if i != correct_index:
                final_options[i] = other_options[other_index]
                other_index += 1
        
        # Store the randomized correct answer
        game.current_correct_answer = new_correct_position
        
        question_data = {
            'round': game.current_round,
            'question_num': game.current_question + 1,
            'question': question['question'],
            'options': {
                'a': final_options[0],
                'b': final_options[1],
                'c': final_options[2],
                'd': final_options[3]
            },
            'correct_answer': new_correct_position
        }
        
        print(f"Sending question data to room {game_id}: {question_data}", flush=True)
        print(f"Active players: {[p['name'] for p in game.players.values() if not p['eliminated']]}", flush=True)
        
        # Send to all players individually to ensure delivery
        for player_sid in game.players.keys():
            socketio.emit('new_question', question_data, room=player_sid)
        
        # Also send to room as backup
        socketio.emit('new_question', question_data, room=game_id)
        
        # Send question data to admin
        if game.admin_sid:
            socketio.emit('new_question', question_data, room=game.admin_sid)
        
        # Start 30-second timer
        timer = threading.Timer(30.0, question_timeout, [game_id])
        game_timers[game_id] = timer
        timer.start()
        print(f"Question timer started for 30 seconds", flush=True)
        
    except Exception as e:
        print(f"Error in start_question: {e}", flush=True)
        import traceback
        traceback.print_exc()
        skip_to_next_question(game_id)

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
    
    # Check if question time has expired
    if hasattr(game, 'question_expired') and game.question_expired:
        emit('answer_rejected', {'message': 'Time expired, answer not accepted'})
        return
    
    # Prevent duplicate answers
    if request.sid in game.answers:
        return
    
    game.answers[request.sid] = answer
    print(f"Player {player['name']} submitted answer. Total answers: {len(game.answers)}", flush=True)
    
    # Check if ALL active players have answered
    active_players = [sid for sid, p in game.players.items() if not p['eliminated']]
    print(f"Active players: {len(active_players)}, Answers received: {len(game.answers)}", flush=True)
    
    if len(game.answers) >= len(active_players):
        print(f"All active players answered, stopping timer", flush=True)
        if game_id in game_timers:
            game_timers[game_id].cancel()
            del game_timers[game_id]
        socketio.emit('timer_stop', room=game_id)
        # Send timer stop to admin
        if game.admin_sid:
            socketio.emit('timer_stop', room=game.admin_sid)
        question_timeout(game_id)

def question_timeout(game_id):
    if game_id not in games:
        return
    
    game = games[game_id]
    # Mark question as expired to prevent late answers
    game.question_expired = True
    
    # Add incorrect answers for players who didn't answer
    active_players = [sid for sid, p in game.players.items() if not p['eliminated']]
    for player_sid in active_players:
        if player_sid not in game.answers:
            game.answers[player_sid] = 'no_answer'  # Mark as incorrect
    
    # Get correct answer from the last question data sent
    correct_answer = getattr(game, 'current_correct_answer', 'a')
    
    correct_players = []
    incorrect_players = []
    
    for sid, answer in game.answers.items():
        if sid in game.players:  # Safety check
            player = game.players[sid]
            if answer == correct_answer:
                correct_players.append({'sid': sid, 'name': player['name']})
            else:
                incorrect_players.append({'sid': sid, 'name': player['name']})
    
    # Initialize voting state
    game.voting_active = True
    game.votes_cast = {}
    game.points_awarded = {}
    game.correct_players = correct_players
    game.incorrect_players = incorrect_players
    
    socketio.emit('question_result', {
        'correct_answer': correct_answer,
        'correct_players': correct_players,
        'incorrect_players': incorrect_players
    }, room=game_id)
    
    # Start voting phase if there are correct and incorrect players
    if correct_players and incorrect_players:
        start_voting_phase(game_id)
    else:
        # No voting needed, proceed to next question
        end_voting_phase(game_id)

def start_voting_phase(game_id):
    if game_id not in games:
        return
    
    game = games[game_id]
    
    # Send voting options to correct players
    available_targets = [p for p in game.incorrect_players 
                        if game.players[p['sid']]['score'] < 10]
    
    for correct_player in game.correct_players:
        socketio.emit('voting_phase', {
            'incorrect_players': available_targets,
            'time_limit': 30
        }, room=correct_player['sid'])
    
    # Start 30-second voting timer
    timer = threading.Timer(30.0, voting_timeout, [game_id])
    game_timers[game_id] = timer
    timer.start()
    print(f"Voting phase started for 30 seconds", flush=True)

def voting_timeout(game_id):
    if game_id not in games:
        return
    
    game = games[game_id]
    print(f"Voting timeout - assigning random votes", flush=True)
    
    # Assign random votes for players who haven't voted
    import random
    
    for correct_player in game.correct_players:
        voter_sid = correct_player['sid']
        if voter_sid not in game.votes_cast:
            # Find available targets for this voter
            available_targets = []
            for incorrect_player in game.incorrect_players:
                target_sid = incorrect_player['sid']
                current_round_points = game.points_awarded.get(target_sid, 0)
                total_score = game.players[target_sid]['score']
                points_per_vote = game.current_round if game.current_round <= 3 else 1
                points_would_award = min(points_per_vote, 10 - total_score)
                
                if current_round_points + points_would_award <= 4 and total_score < 10 and points_would_award > 0:
                    available_targets.append(target_sid)
            
            if available_targets:
                # Randomly select a target
                target_sid = random.choice(available_targets)
                points_per_vote = game.current_round if game.current_round <= 3 else 1
                points_to_award = min(points_per_vote, 10 - game.players[target_sid]['score'])
                
                # Record the vote
                game.votes_cast[voter_sid] = target_sid
                game.points_awarded[target_sid] = game.points_awarded.get(target_sid, 0) + points_to_award
                game.players[target_sid]['score'] += points_to_award
                
                # Send updated player list to admin with new scores
                if game.admin_sid:
                    player_list = list(game.players.values())
                    socketio.emit('admin_player_list', {'players': player_list}, room=game.admin_sid)
                
                # Send score updates to all players
                player_list = list(game.players.values())
                socketio.emit('score_update', {'players': player_list}, room=game_id)
                
                # Check for elimination
                if game.players[target_sid]['score'] >= 10:
                    game.players[target_sid]['eliminated'] = True
                    game.players[target_sid]['readonly'] = True
                    game.players[target_sid]['eliminated_at'] = time.time()
                    socketio.emit('player_eliminated', {'name': game.players[target_sid]['name']}, room=game_id)
                    
                    # Send updated player list to admin after elimination
                    if game.admin_sid:
                        player_list = list(game.players.values())
                        socketio.emit('admin_player_list', {'players': player_list}, room=game.admin_sid)
                    
                    # Send score updates to all players after elimination
                    player_list = list(game.players.values())
                    socketio.emit('score_update', {'players': player_list}, room=game_id)
                
                # Notify the voter
                socketio.emit('vote_recorded', {
                    'target': game.players[target_sid]['name'], 
                    'points': points_to_award,
                    'auto_selected': True
                }, room=voter_sid)
                
                print(f"Auto-voted: {game.players[voter_sid]['name']} -> {game.players[target_sid]['name']} (+{points_to_award})", flush=True)
    
    # End voting phase
    end_voting_phase(game_id)

def end_voting_phase(game_id):
    if game_id not in games:
        return
    
    game = games[game_id]
    game.voting_active = False
    
    # Send points received to incorrect players with voter names
    for incorrect_player in game.incorrect_players:
        target_sid = incorrect_player['sid']
        points_this_round = game.points_awarded.get(target_sid, 0)
        
        # Find who voted for this player
        voters = []
        for voter_sid, voted_for_sid in game.votes_cast.items():
            if voted_for_sid == target_sid:
                voter_name = game.players[voter_sid]['name']
                voters.append(voter_name)
        
        if points_this_round > 0:
            if len(voters) == 1:
                message = f"You received {points_this_round} point from {voters[0]}!"
            else:
                voter_list = ', '.join(voters[:-1]) + f" and {voters[-1]}"
                message = f"You received {points_this_round} points from {voter_list}!"
        else:
            message = "You received no points this round."
        
        socketio.emit('points_received', {
            'points': points_this_round,
            'message': message,
            'voters': voters
        }, room=target_sid)
    
    # Check if only one player remains active
    active_players = [p for p in game.players.values() if not p['eliminated']]
    if len(active_players) <= 1:
        end_game(game_id)
        return
    
    # Send final admin summary
    if game.admin_sid:
        # Create points awarded with player names
        points_with_names = {}
        for sid, points in game.points_awarded.items():
            player_name = game.players[sid]['name']
            points_with_names[player_name] = points
        
        admin_summary = {
            'correct_players': game.correct_players,
            'incorrect_players': game.incorrect_players,
            'points_awarded': points_with_names,
            'all_scores': {p['name']: p['score'] for p in game.players.values()}
        }
        socketio.emit('admin_question_summary', admin_summary, room=game.admin_sid)
    
    print(f"Voting phase ended for game {game_id}", flush=True)

@socketio.on('vote_player')
def handle_vote_player(data):
    game_id = data['game_id']
    target_sid = data['target_sid']
    
    if game_id not in games:
        return
    
    game = games[game_id]
    voter = game.players.get(request.sid)
    target = game.players.get(target_sid)
    
    if not voter or not target or not hasattr(game, 'voting_active') or not game.voting_active:
        return
    
    # Check if voter already voted
    if request.sid in game.votes_cast:
        emit('vote_failed', {'message': 'You have already voted'})
        return
    
    # Check limits: max 4 points per round, max 10 total points
    points_per_vote = game.current_round if game.current_round <= 3 else 1
    round_points = game.points_awarded.get(target_sid, 0)
    points_would_award = min(points_per_vote, 10 - target['score'])
    if round_points + points_would_award > 4 or target['score'] >= 10 or points_would_award <= 0:
        # Send updated list without this player
        available_targets = []
        for incorrect_player in game.incorrect_players:
            sid = incorrect_player['sid']
            if (game.points_awarded.get(sid, 0) < 4 and 
                game.players[sid]['score'] < 10):
                available_targets.append(incorrect_player)
        
        emit('vote_failed', {
            'message': f"{target['name']} cannot receive more points",
            'available_targets': available_targets
        })
        return
    
    # Record vote and award points based on round, but cap at 10 total
    points_per_vote = game.current_round if game.current_round <= 3 else 1
    points_to_award = min(points_per_vote, 10 - target['score'])
    
    game.votes_cast[request.sid] = target_sid
    game.points_awarded[target_sid] = game.points_awarded.get(target_sid, 0) + points_to_award
    target['score'] += points_to_award
    
    # Send updated player list to admin with new scores
    if game.admin_sid:
        player_list = list(game.players.values())
        socketio.emit('admin_player_list', {'players': player_list}, room=game.admin_sid)
    
    # Send score updates to all players
    player_list = list(game.players.values())
    socketio.emit('score_update', {'players': player_list}, room=game_id)
    
    # Check if target now has 4 points this round - notify other voters to choose again
    if game.points_awarded[target_sid] == 4:
        for voter_sid in game.correct_players:
            if (voter_sid['sid'] not in game.votes_cast and 
                voter_sid['sid'] != request.sid):
                # Send updated voting options without the maxed-out player
                available_targets = []
                for incorrect_player in game.incorrect_players:
                    sid = incorrect_player['sid']
                    if (game.points_awarded.get(sid, 0) < 4 and 
                        game.players[sid]['score'] < 10):
                        available_targets.append(incorrect_player)
                
                socketio.emit('voting_phase', {
                    'incorrect_players': available_targets,
                    'time_limit': 30,
                    'message': f"{target['name']} has reached maximum points. Please choose another player."
                }, room=voter_sid['sid'])
    
    # Check for elimination
    if target['score'] >= 10:
        target['eliminated'] = True
        target['readonly'] = True
        target['eliminated_at'] = time.time()
        socketio.emit('player_eliminated', {'name': target['name']}, room=game_id)
        
        # Send updated player list to admin after elimination
        if game.admin_sid:
            player_list = list(game.players.values())
            socketio.emit('admin_player_list', {'players': player_list}, room=game.admin_sid)
        
        # Send score updates to all players after elimination
        player_list = list(game.players.values())
        socketio.emit('score_update', {'players': player_list}, room=game_id)
    
    emit('vote_recorded', {'target': target['name'], 'points': points_to_award})
    print(f"Vote recorded: {voter['name']} -> {target['name']}", flush=True)
    
    # Check if all correct players have voted
    if len(game.votes_cast) >= len(game.correct_players):
        print(f"All votes cast, ending voting phase", flush=True)
        if game_id in game_timers:
            game_timers[game_id].cancel()
            del game_timers[game_id]
        end_voting_phase(game_id)
    else:
        # Update admin with current voting status
        if game.admin_sid:
            voting_summary = {
                'votes_cast': len(game.votes_cast),
                'total_voters': len(game.correct_players),
                'points_awarded': game.points_awarded
            }
            socketio.emit('voting_update', voting_summary, room=game.admin_sid)

def end_voting(game_id):
    next_question(game_id)

@socketio.on('next_question')
def handle_next_question(data):
    try:
        game_id = data['game_id']
        print(f"Admin requesting next question for game {game_id}", flush=True)
        
        if game_id not in games:
            print(f"Game {game_id} not found", flush=True)
            return
        
        game = games[game_id]
        if game.admin_sid != request.sid:
            print(f"Unauthorized next question request", flush=True)
            return
        
        # Reset voting state
        game.voting_active = False
        game.votes_cast = {}
        game.points_awarded = {}
        
        # Clear previous answers
        game.answers = {}
        
        game.current_question += 1
        print(f"Moving to question {game.current_question} in round {game.current_round}", flush=True)
        
        # Check if round is complete
        if game.current_question >= 15:
            end_round(game_id)
        else:
            start_question(game_id)
            
    except Exception as e:
        print(f"Error in handle_next_question: {e}", flush=True)
        if 'game_id' in data and data['game_id'] in games:
            skip_to_next_question(data['game_id'])

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
    
    # Check if only one player remains active
    active_players = [p for p in game.players.values() if not p['eliminated']]
    if len(active_players) <= 1:
        end_game(game_id)
        return
    
    # Continue to next round if more than one player remains
    game.current_round += 1
    game.current_question = 0
    
    # Show round start page before continuing
    socketio.emit('show_round_start', {'round_number': game.current_round}, room=game_id)
    threading.Timer(8.0, start_question, [game_id]).start()

def end_game(game_id):
    if game_id not in games:
        return
    
    game = games[game_id]
    
    # Find the winner (last remaining active player)
    active_players = [p for p in game.players.values() if not p['eliminated']]
    winner = active_players[0] if active_players else None
    
    final_scores = [(p['name'], p['score']) for p in game.players.values()]
    final_scores.sort(key=lambda x: x[1])
    
    socketio.emit('game_ended', {
        'final_scores': final_scores,
        'winner': winner['name'] if winner else 'No winner'
    }, room=game_id)
    
    print(f"Game {game_id} ended. Winner: {winner['name'] if winner else 'No winner'}", flush=True)

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Player disconnected: {request.sid}", flush=True)
    
    try:
        # Remove player from all games
        for game_id, game in games.items():
            if request.sid in game.players:
                player_name = game.players[request.sid]['name']
                print(f"Removing {player_name} from game {game_id}", flush=True)
                del game.players[request.sid]
                
                # If this was during a question and all remaining connected players have answered, end the question
                if hasattr(game, 'answers') and game.status == 'playing':
                    connected_active_sids = [sid for sid, p in game.players.items() if not p['eliminated'] and sid in socketio.server.manager.rooms.get('/', {}).get(game_id, set())]
                    if len(game.answers) >= len(connected_active_sids) and len(connected_active_sids) > 0:
                        if game_id in game_timers:
                            game_timers[game_id].cancel()
                            del game_timers[game_id]
                        socketio.emit('timer_stop', room=game_id)
                        question_timeout(game_id)
                break
    except Exception as e:
        print(f"disconnect handler error", flush=True)
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("Initializing DynamoDB...", flush=True)
    try:
        init_dynamodb()
        print("DynamoDB initialized successfully", flush=True)
    except Exception as e:
        print(f"ERROR initializing DynamoDB: {e}", flush=True)
    
    print("Starting Flask application...", flush=True)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)