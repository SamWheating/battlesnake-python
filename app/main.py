import bottle
import os
import random


# NOTES TO SAM:
# To run Game locally:
#
# sudo start_server.sh
# python app/main.py
# 
# Go to http://localhost:3000
# use local ip port 8080 (http://172.17.0.1:8080)

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

    y = int(data['you']['body']['data'][0]['y'])
    x = int(data['you']['body']['data'][0]['x'])

    target_x = int(data['food']['data'][0]['x'])
    target_y = int(data['food']['data'][0]['y'])

    print("at: ", x, y, "going to: ", target_x, target_y)

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

    if not validate_move(data, direction, 1):
        directions.remove(direction)
        direction = random.choice(directions)

    if not validate_move(data, direction, 2):
        directions.remove(direction)
        direction = random.choice(directions)

    if not validate_move(data, direction, 3):
        directions.remove(direction)
        direction = random.choice(directions)

    print(direction)

    # TODO: Do things with data
    return {
        'move': direction,
        'taunt': 'battlesnake-python!'
    }

def validate_move(data, direction, priority):

    # VALIDATE MOVE:
    # Check that the future position of the head isn't:
    #   a) on the snake's tail.
    #   b) outside the bounds of the game field.

    print("testing move", direction)

    # checking for hazards if snake is to make the chosen move.

    x = int(data['you']['body']['data'][0]['x'])
    y = int(data['you']['body']['data'][0]['y'])

    # DON'T HIT WALLS

    if x == 0:
        if direction == 'left':
            print("tried to run out left side")
            return False

    if y == 0:
        if direction == 'up':
            print("tried to run out top side")
            return False

    if x == (int(data['width'])-1):
        if direction == 'right':
            print("tried to run out right side")
            return False

    if y == (int(data['height'])-1):
        if direction == 'down':
            print("tried to run out bottom side")
            return False


    # DON'T HIT YOUR OWN TAIL OR OTHER SNAKES

    if direction == 'right':
        future_x = x + 1
        future_y = y

    elif direction == 'left':
        future_x = x - 1
        future_y = y

    elif direction == 'up':
        future_x = x
        future_y = y - 1

    elif direction == 'down':
        future_x = x
        future_y = y + 1

    future_pos = [future_x, future_y]

    tail = []   # this is the list of points to not enter
    heads = []  # for avoiding head areas

    for snake in data['snakes']['data']:
        for segment in snake['body']['data'][:-1]:
            tail.append([int(segment['x']), int(segment['y'])])

    
    for snake in data['snakes']['data'][:]:
        heads.append([int(snake['body']['data'][0]['x']), int(snake['body']['data'][0]['y'])])
    
    y = int(data['you']['body']['data'][0]['y'])
    x = int(data['you']['body']['data'][0]['x'])

    if [x,y] in heads:          # add list of heads of the other snakes (stay away!)
        heads.remove([x,y])

    # TO DO: DON't MOVE INTO CLOSED-OFF 1x1 AREAS.

    surrounding_points = [[future_x+1, future_y], [future_x-1, future_y], [future_x, future_y+1], [future_x, future_y-1]]

    count = 0

    for item in surrounding_points:
        if item in tail:
            count += 1

    if count == 4: 
        return False

    # DON'T MOVE WITHIN 1 SQUARE OF OPPONENTS HEADS

    if priority < 3:
        for item in heads:
            tail += [[item[0]-1, item[1]], [item[0]+1, item[1]], [item[0], item[1]-1], [item[0], item[1]+1]]

            # NOTES HERE:
            # urgency added as a prioritization, as this is a high-risk but not certain-death move.
            # i.e if all other examples are certain death, moving close to an opponents head is acceptable.





    print(tail)


    if future_pos in tail:
        print("future pos: ", future_pos, "in tail. Dodge!")
        return False


    # if there's no obstacles in da wae:
    return True



# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()
if __name__ == '__main__':
    bottle.run(application, host=os.getenv('IP', '0.0.0.0'), port=os.getenv('PORT', '8080'))
