import bottle
import os
import random
import math


# NOTES TO SAM:
# To run Game locally:
#
# sudo start_server.sh
# python app/main.py
# 
# Go to http://localhost:3000
#
# use local http://{local IP}:8080
# 
# Find local IP with "hostname -I"

DIRECTIONS = {'right': [1,0], 'left':[-1,0], 'up':[0,-1], 'down':[0,1]}

TAUNTS = ['lil pump!', 'eskettit!', 'little pump!']

@bottle.route('/static/<path:path>')
def static(path):
    return bottle.static_file(path, root='static/')


@bottle.post('/start')
def start():
    data = bottle.request.json
    game_id = data['game_id']
    board_width = data['width']
    board_height = data['height']


    # Using shrek as the snek avatar for now
    head_url = 'https://orig00.deviantart.net/04d8/f/2017/095/f/9/shrek_head_png_by_darkwoodsx-db4reoe.png'

    return {
        'color': '#21205E',
        'taunt': '{} ({}x{})'.format(game_id, board_width, board_height),
        'head_url': head_url,
        'name': 'Perogie Joe',
        "head_type": "pixel",       # For some reason these don't work.
        "tail_type": "pixel"        # This one too
    }


@bottle.post('/move')
def move():

    # MOVE function:
    # Finds food and directs the snake there in an x-y search pattern
    # validates move 3x to ensure that the snake isn't gonna hit anything

    data = bottle.request.json

    health = int(data['you']['health'])

    y = int(data['you']['body']['data'][0]['y'])
    x = int(data['you']['body']['data'][0]['x'])    

    if health > 50:                                                 # ONLY chase food if actually hungrye

        target_x = int(data['you']['body']['data'][-1]['x'])
        target_y = int(data['you']['body']['data'][-1]['y'])

    else:           # move to the closest available food (inefficient af but w/e)

        food_locs = []
        for i in range(len(data['food']['data'])):
            food_locs.append([data['food']['data'][i]['x'], data['food']['data'][i]['y']])

        food_distances = []
        for i in range(len(data['food']['data'])):
            food_distances.append(int(math.fabs(food_locs[i][0] - x) + math.fabs(food_locs[i][1] - y)))

        closest = min(food_distances)

        target_x = food_locs[food_distances.index(int(closest))][0]
        target_y = food_locs[food_distances.index(int(closest))][1]

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

    return {
        'move': direction,
        'taunt': random.choice(TAUNTS)
    }

def validate_move(data, direction, priority, position):

    # VALIDATE MOVE:
    # Check that the future position of the head isn't:
    #   a) on the snake's tail.
    #   b) outside the bounds of the game field.
    #   c) in a 1x1 space.

    # checking for hazards if snake is to make the chosen move.

    # DON'T HIT WALLS

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

    if x == (int(data['width'])-1):
        if direction == 'right':
            #print("tried to run out right side")
            return False

    if y == (int(data['height'])-1):
        if direction == 'down':
            #print("tried to run out bottom side")
            return False

    # DON'T HIT YOUR OWN TAIL OR OTHER SNAKES

    future_pos = [future_x, future_y] = [sum(q) for q in zip(position, DIRECTIONS[direction])]


    tail = []   # this is the list of points to not enter
    heads = []  # for avoiding head areas

    # add all snakes to the list of points to not enter (including oneself)

    for snake in data['snakes']['data']:
        for segment in snake['body']['data'][:-1]:
            tail.append([int(segment['x']), int(segment['y'])])

    
    for snake in data['snakes']['data'][:]:
        heads.append([int(snake['body']['data'][0]['x']), int(snake['body']['data'][0]['y'])])

   # don't worry about your own head.
    try:
        heads.remove([x,y])
    except:
        pass    

    # check that it isn't a 1x1 space:    

    surrounding_points = [[future_x+1, future_y], [future_x-1, future_y], [future_x, future_y+1], [future_x, future_y-1]]

    count = 0

    for item in surrounding_points:
        if item in tail:
            count += 1

    if count == 4:              # if the space is confirmed to be a dead-end
        return False

    # DON'T MOVE WITHIN 1 SQUARE OF OPPONENTS HEADS

    if priority < 3:
        for item in heads:
            tail += [[item[0]-1, item[1]], [item[0]+1, item[1]], [item[0], item[1]-1], [item[0], item[1]+1]]

            # NOTES HERE:
            # urgency added as a prioritization, as this is a high-risk but not certain-death move.
            # i.e if all other examples are certain death, moving close to an opponents head is acceptable.

    if future_pos in tail:
        print future_pos
        return False


    # if there's no obstacles in da wae:
    return True


def heuristic_function(data, direction, position):

    future_pos = [future_x, future_y] = [sum(q) for q in zip(position, DIRECTIONS[direction])]  # gives future position as [x,y]

    # recursively find the size of the space to be moved into

    bad_list = []
    for snake in data['snakes']['data']:
        for segment in snake['body']['data'][:-1]:
            tail.append([int(segment['x']), int(segment['y'])])




    # To Do: calculate an effective score for each possible move.
    # return a single number. Highest number will be taken.

    pass

def expand(point, bad_list, bounds):
    pass

# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()
if __name__ == '__main__':
    bottle.run(application, host=os.getenv('IP', '0.0.0.0'), port=os.getenv('PORT', '8080'))
