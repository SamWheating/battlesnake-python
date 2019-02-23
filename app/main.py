import json
import os
import random
import bottle
import math
import astar
import time

from api import ping_response, start_response, move_response, end_response

# State Storage and Management:
#
# Stores the state like:
#     {
#         SnakeID : {
#             moves: 123
#             ObjectivePoint: (1, 1),
#             Updated: 29821.2324
#         }
#     }
#
# remove record if not updated for 10s.

DIRECTIONS = {'right': [1,0], 'left':[-1,0], 'up':[0,-1], 'down':[0,1]}
STATES = {}

@bottle.route('/')
def index():
    return bottle.static_file('landing.html', root='static/')
    #return bottle.redirect('../http://www.samwheating.com')   
"""     return '''
    Battlesnake documentation can be found at
       <a href="https://docs.battlesnake.io">https://docs.battlesnake.io</a>.
    ''' """

@bottle.route('/static/<path:path>')
def static(path):
    """
    Given a path, return the static file located relative
    to the static folder.

    This can be used to return the snake head URL in an API response.
    """
    return bottle.static_file(path, root='static/')

@bottle.post('/ping')
def ping():
    """
    A keep-alive endpoint used to prevent cloud application platforms,
    such as Heroku, from sleeping the application instance.
    """
    return ping_response()

@bottle.post('/start')
def start():
    data = bottle.request.json

    """
    TODO: If you intend to have a stateful snake AI,
            initialize your snake state here using the
            request's data if necessary.
    """

    # color = "#efefef"
    color = "#30db4c"
    head = "bendr"
    tail = "fat-rattle"

    return start_response(color, head, tail)

def closest_waypoint(data, waypoints): 

    y = int(data['you']['body'][0]['y'])
    x = int(data['you']['body'][0]['x'])

    waypoint_distances = []
    for i in range(len(waypoints)):
        waypoint_distances.append(int(math.fabs(waypoints[i][0] - x) + math.fabs(waypoints[i][1] - y)))

    closest = min(waypoint_distances)
    
    return (waypoints[waypoint_distances.index(int(closest))][0], waypoints[waypoint_distances.index(int(closest))][1])


def get_state(data):

    # Grabs the state from a global variable and makes the required updates

    global STATES

    try:
        margin = 1 if int(data['board']['height']) <= 9 else 2
    except e:
        print(e)
        margin = 2


    # Defines the pattern to follow:

    # Square CCW
    waypoints = [
        (margin, margin),
        (margin, int(data['board']['height'])-(1+margin)),
        (int(data['board']['width'])-(1+margin), int(data['board']['height'])-(1+margin)),
        (int(data['board']['width'])-(1+margin), margin)
    ]

    middle = (int(int(data['board']['width'])/2), int(int(data['board']['width'])/2))
    other_middle = (middle[0]+1, middle[1])

    # waypoints = [
    #     (margin, margin), # Top left
    #     (margin, int(data['board']['height'])-(1+margin)), # bottom left
    #     middle,# middle
    #     (int(data['board']['width'])-(1+margin), margin), #top right
    #     (int(data['board']['width'])-(1+margin), int(data['board']['height'])-(1+margin)), # bottom right 
    #     other_middle # middle
    # ]

    if data['you']['id'] in STATES:
        STATES[data['you']['id']]['moves'] += 1
        STATES[data['you']['id']]['target'] = update_target(data, STATES[data['you']['id']], waypoints)
        STATES[data['you']['id']]['updated'] = time.time()
    else:
        STATES[data['you']['id']] = {
            'moves': 0,
            'updated': time.time(),
            'target': (1 , 1),
            'next_point': closest_waypoint(data, waypoints),
            'nearest_food': (0,0),
        }

    # Drop expired records (10s TTL)

    for state in STATES.keys():
        if time.time() - STATES[state]['updated'] > 10:
            STATES.pop(state)

    # Update the nearest food:

    y = int(data['you']['body'][0]['y'])
    x = int(data['you']['body'][0]['x']) 
    
    food_locs = []
    for i in range(len(data['board']['food'])):
        food_locs.append([data['board']['food'][i]['x'], data['board']['food'][i]['y']])

    food_distances = []
    for i in range(len(data['board']['food'])):
        food_distances.append(int(math.fabs(food_locs[i][0] - x) + math.fabs(food_locs[i][1] - y)))

    # Prevent weird edge case when there is no food on the board
    if len(food_distances) > 0:
        closest = min(food_distances)
        STATES[data['you']['id']]['nearest_food'] = (food_locs[food_distances.index(int(closest))][0], food_locs[food_distances.index(int(closest))][1])
    else:
        STATES[data['you']['id']]['nearest_food'] = (margin, margin)

    return  STATES[data['you']['id']]


def update_target(data, state, waypoints):

    global STATE
    position = (int(data['you']['body'][0]['x']), int(data['you']['body'][0]['y']))

    # if it's time to eat, find the nearest food
    if int(data['you']['health']) < 30:
        return state['nearest_food']

    # If we've reached a waypoint, go to the next one
    elif (position == state['target'] == state['next_point']):
    
        current_index = waypoints.index(state['target'])
        next_index = (current_index + 1) % len(waypoints)
        STATES[data['you']['id']]['next_point'] = waypoints[next_index]
        return waypoints[next_index]

    # Otherwise, just stay the course
    return state['next_point']

@bottle.post('/move')
def move():
    
    global STATES
    # MOVE function:
    # Finds food and directs the snake there in an x-y search pattern
    # validates move 3x to ensure that the snake isn't gonna hit anything

    data = bottle.request.json
    state = get_state(data)

    y = int(data['you']['body'][0]['y'])
    x = int(data['you']['body'][0]['x'])  

    target_x, target_y = state['target']

    direction = insightful_move(data, (x, y), (target_x, target_y))
    # direction = quick_move(data, (x, y), (target_x, target_y))

    return {
        'move': direction,
    }


@bottle.post('/end')
def end():
    data = bottle.request.json

    """
    TODO: If your snake AI was stateful,
        clean up any stateful objects here.
    """
    # dangerous(json.dumps(data))

    return end_response()

def insightful_move(data, location, target):

    directions = ['up', 'left', 'right', 'down']
    dangerous = []
    fatal = []

    for direction in directions:
        if is_fatal(data, direction): 
            fatal.append(direction)

    for direction in [i for i in directions if i not in fatal]:
        if is_dangerous(data, direction):
            dangerous.append(direction)

    safe = [i for i in directions if (i not in fatal and i not in dangerous)]

    x = location[0]
    y = location[1]
    target_x = target[0]
    target_y = target[1]

    if x < target_x and 'right' in safe:
        return 'right'

    elif x > target_x and 'left' in safe:
        return 'left'

    elif y < target_y and 'down' in safe:
        return 'down'

    elif y > target_y and 'up' in safe:
        return 'up'

    elif len(fatal) == 4:
        return random.choice(directions)

    elif len(fatal) + len(dangerous) != 4:
        return random.choice(safe)

    else:
        return random.choice(dangerous)

def off_board(x, y, data):

    if x not in range(int(data['board']['width'])):
        return True

    if y not in range(int(data['board']['height'])):
        return True

    return False

def is_fatal(data, direction):
    
    x = int(data['you']['body'][0]['x'])  
    y = int(data['you']['body'][0]['y'])
    position = (x, y)

    future_pos = (future_x, future_y) = tuple(sum(q) for q in zip(position, DIRECTIONS[direction]))

    if off_board(future_x, future_y, data):
        return True

    snakes = []
    for snake in data['board']['snakes']:
        for segment in snake['body'][:-1]:
            if future_pos == (int(segment['x']), int(segment['y'])):
                return True

    return False


def is_dangerous(data, direction):

    x = int(data['you']['body'][0]['x'])  
    y = int(data['you']['body'][0]['y'])
    position = (x, y)
    future_pos = (future_x, future_y) = tuple(sum(q) for q in zip(position, DIRECTIONS[direction]))

    heads = []  # for avoiding head areas
    snakes = []

    for snake in data['board']['snakes'][:]:
        if len(snake['body' ]) >= (len(data['you']['body']) - 1):
            heads.append([int(snake['body'][0]['x']), int(snake['body'][0]['y'])])
            for segment in snake['body'][:-1]:
                snakes.append((int(segment['x']), int(segment['y'])))

    try:
        heads.remove([x,y])
    except:
        pass

    spots_near_heads = []

    for item in heads:
        spots_near_heads += [(item[0]-1, item[1]), (item[0]+1, item[1]), (item[0], item[1]-1), (item[0], item[1]+1)]
    
    if future_pos in spots_near_heads:  
        return True

    # Check for 1x1 spaces:

    surrounding_points = [(future_x+1, future_y), (future_x-1, future_y), (future_x, future_y+1), (future_x, future_y-1)]
    count = 0

    for item in surrounding_points:
        if item in snakes: count += 1
        if off_board(item[0], item[1], data): count += 1

    if count == 4:
        return True

    return False

def astar_move(data, location, target):

    # Make maze before sending to a-star pathing function
    maze = [[0 for _ in range(data['board']['width'])] for _ in range(data['board']['height'])]

    # add all of the other snakes
    for snake in data['board']['snakes']:
        for seg in snake['body'][:-1]:
            maze[seg['x']][seg['y']] = 1

    # add self
    for seg in data['you']['body'][:-2]:
        maze[seg['x']][seg['y']] = 1

    path = astar.astar(maze, location, target)

    print location
    print target

    maze[location[0]][location[1]] = "S"
    maze[target[0]][target[1]] = "T"

    for row in maze:
        print row

    print "\n\n\n"

    print path

    return 'down'

# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()

if __name__ == '__main__':

    bottle.run(
        application,
        host=os.getenv('IP', '0.0.0.0'),
        port=os.getenv('PORT', '8080'),
        debug=os.getenv('DEBUG', True)
    )
