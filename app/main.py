import json
import os
import random
import bottle
import math
import astar
import time

from api import ping_response, start_response, move_response, end_response

DIRECTIONS = {'right': [1,0], 'left':[-1,0], 'up':[0,-1], 'down':[0,1]}
TAUNTS = ['UVIC Satellite Design Team is #1', 'ESKETTIT']

# State Storage and Management:
#
# Stores the state like:
#     {
#         SnakeID : {
#             ObjectivePoint: (1, 1),
#             Updated: 29821.2324
#         }
#     }
#
# remove record if not updated for 10s.

STATES = {}

@bottle.route('/')
def index():
    return '''
    Battlesnake documentation can be found at
       <a href="https://docs.battlesnake.io">https://docs.battlesnake.io</a>.
    '''

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

    color = "#5F7BFF"
    head = "beluga"
    tail = "round-bum"

    return start_response(color, head, tail)


def get_state(data):

    # Grabs the state from a global variable and makes the required updates

    global STATES

    if data['you']['id'] in STATES:
        STATES[data['you']['id']]['moves'] += 1
        STATES[data['you']['id']]['target'] = update_target(data, STATES[data['you']['id']])
    else:
        STATES[data['you']['id']] = {
            'moves': 0,
            'updated': time.time(),
            'target': (1 , 1),
            'next_point': (1, 1),
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

    closest = min(food_distances)

    STATES[data['you']['id']]['nearest_food'] = (food_locs[food_distances.index(int(closest))][0], food_locs[food_distances.index(int(closest))][1])

    return  STATES[data['you']['id']]

def update_target(data, state):

    global STATES
    position = (int(data['you']['body'][0]['x']), int(data['you']['body'][0]['y']))

    # if it's time to eat, find the nearest food
    if int(data['you']['health']) < 40:
        return state['nearest_food']

    # If we've reached a waypoint, go to the next one
    elif (position == state['target'] == state['next_point']):
        
        targets = [
            (1, 1),
            (1, int(data['board']['height'])-2),
            (int(data['board']['width'])-2, int(data['board']['height'])-2),
            (int(data['board']['width'])-2, 1)
        ]

        current_index = targets.index(state['target'])
        next_index = (current_index + 1) % 4
        STATES[data['you']['id']]['next_point'] = targets[next_index]
        return targets[next_index]

    # Otherwise, just stay the course
    return state['next_point']

@bottle.post('/move')
def move():

    # MOVE function:
    # Finds food and directs the snake there in an x-y search pattern
    # validates move 3x to ensure that the snake isn't gonna hit anything

    data = bottle.request.json
    state = get_state(data)

    # print state

    # # DETERMINE WHETHER TO GO FOR FOOD OR STAY SAFE

    # sizeofboard = int(data['board']['width']) * int(data['board']['height'])
    # sizeofboard = float(sizeofboard)

    # y = int(data['you']['body'][0]['y'])
    # x = int(data['you']['body'][0]['x'])   

    # numberofsnakes = 0.0

    # for snake in data['board']['snakes']:
    #     for segment in snake['body']:
    #         numberofsnakes += 1.0

    # coverage = numberofsnakes / sizeofboard

    # THRESHOLD = int(data['board']['width']) + int(data['board']['height']) + 15 + int(55*coverage)

    # health = int(data['you']['health'])

    # food_locs = []
    # for i in range(len(data['board']['food'])):
    #     food_locs.append([data['board']['food'][i]['x'], data['board']['food'][i]['y']])

    # food_distances = []
    # for i in range(len(data['board']['food'])):
    #     food_distances.append(int(math.fabs(food_locs[i][0] - x) + math.fabs(food_locs[i][1] - y)))

    # closest = min(food_distances)

    # # find head coordinates 

    # if health > THRESHOLD and  closest > 1:                                     # ONLY chase food if actually hungry

    #         target_x = int(data['you']['body'][-1]['x'])
    #         target_y = int(data['you']['body'][-1]['y'])
    #         taunt = "perfectly content"

    # else:           # move to the closest available food (inefficient af but w/e)

    #     target_x = food_locs[food_distances.index(int(closest))][0]
    #     target_y = food_locs[food_distances.index(int(closest))][1]
    #     taunt = "...just gonna ssnake past ya there...."

    # direction = astar_move(data, (x, y), (target_x, target_y))

    print state

    y = int(data['you']['body'][0]['y'])
    x = int(data['you']['body'][0]['x'])  

    target_x, target_y = state['target']

    direction = quick_move(data, (x, y), (target_x, target_y))

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
    # print(json.dumps(data))

    return end_response()

def quick_move(data, location, target):
    """ 
    Quick move towards the target in an x-y pattern.
    """

    x = location[0]
    y = location[1]
    target_x = target[0]
    target_y = target[1]

    directions = ['up', 'left', 'right', 'down']

    if x < target_x:
        direction = 'right'

    elif x > target_x:
        direction = 'left'

    elif y < target_y:
        direction = 'down'

    elif y > target_y:
        direction = 'up'

    else: direction = random.choice(directions)

    first_move = direction

    if not validate_move(data, direction, 1, [x, y]):
        directions.remove(direction)

    # if the initial move is invalid, try switching the search order:

        if y < target_y and direction != 'down':
            direction = 'down'

        elif y > target_y and direction != 'up':
            direction = 'up'

        elif x < target_x and direction != 'right':
            direction = 'right'

        elif x > target_x and direction != 'left':
            direction = 'left'

        else: direction = random.choice(directions)

    if not validate_move(data, direction, 2, [x, y]):
        directions.remove(direction)
        direction = random.choice(directions)

    if not validate_move(data, direction, 3, [x, y]):
        directions.remove(direction)
        direction = random.choice(directions)

    return direction

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

def validate_move(data, direction, priority, position):

    # VALIDATE MOVE:
    # Check that the future position of the head isn't:
    #   a) on the snake's tail.
    #   b) outside the bounds of the game field.
    #   c) in a 1x1 space.

    # checking for hazards if snake is to make the chosen move.

    # DON'T HIT WALL

    x = position[0]
    y = position[1]

    if x == 0:
        if direction == 'left':
            #print("tried to run out left side")
            return False

    if y == 0:
        if direction == 'up':
            #print("tried to run out top side")
            return False

    if x == (int(data['board']['width'])-1):
        if direction == 'right':
            #print("tried to run out right side")
            return False

    if y == (int(data['board']['height'])-1):
        if direction == 'down':
            #print("tried to run out bottom side")
            return False

    # DON'T HIT YOUR OWN TAIL OR OTHER SNAKES

    future_pos = [future_x, future_y] = [sum(q) for q in zip(position, DIRECTIONS[direction])]


    tail = []   # this is the list of points to not enter
    heads = []  # for avoiding head areas

    # add all snakes to the list of points to not enter (including oneself)

    for snake in data['board']['snakes']:
        for segment in snake['body'][:-1]:
            tail.append([int(segment['x']), int(segment['y'])])

    
    for snake in data['board']['snakes'][:]:
        heads.append([int(snake['body'][0]['x']), int(snake['body'][0]['y'])])

   # don't worry about your own head.
    try:
        heads.remove([x,y])
    except:
        pass    

    # check that it isn't a 1x1 space:    

    surrounding_points = [[future_x+1, future_y], [future_x-1, future_y], [future_x, future_y+1], [future_x, future_y-1]]

    count = 0

    for item in surrounding_points:
        if item in tail: count += 1
        elif item[0] < 0: count += 1
        elif item[0] >  (int(data['board']['width'])-1): count += 1
        elif item[1] < 0: count += 1
        elif item[1] >  (int(data['board']['height'])-1): count += 1

    if count == 4:              # if the space is confirmed to be a dead-end
        return False

    # DON'T MOVE WITHIN 1 SQUARE OF OPPONENTS HEADS
    # This is brokend uhhh 

    if priority < 3:
        for item in heads:
            tail += [[item[0]-1, item[1]], [item[0]+1, item[1]], [item[0], item[1]-1], [item[0], item[1]+1]]

            # NOTES HERE:
            # urgency added as a prioritization, as this is a high-risk but not certain-death move.
            # i.e if all other examples are certain death, moving close to an opponents head is acceptable.

    if future_pos in tail:
        return False    


    # if there's no obstacles in da wae:
    return True


# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()

if __name__ == '__main__':
    bottle.run(
        application,
        host=os.getenv('IP', '0.0.0.0'),
        port=os.getenv('PORT', '8080'),
        debug=os.getenv('DEBUG', True)
    )
