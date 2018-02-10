import bottle
import os
import random


@bottle.route('/static/<path:path>')
def static(path):
    return bottle.static_file(path, root='static/')


@bottle.post('/start')
def start():
    data = bottle.request.json
    game_id = data['game_id']
    board_width = data['width']
    board_height = data['height']

    head_url = '%s://%s/static/head.png' % (
        bottle.request.urlparts.scheme,
        bottle.request.urlparts.netloc
    )

    head_type = "bendr"
    tail_type = "small_rattle"

    # TODO: Do things with data

    return {
        'color': '#21205E',
        'taunt': '{} ({}x{})'.format(game_id, board_width, board_height),
        'head_url': head_url,
        'name': 'Perogie Joe'
    }


@bottle.post('/move')
def move():
    data = bottle.request.json

    y = int(data['snakes']['data'][0]['body']['data'][0]['y'])
    x = int(data['snakes']['data'][0]['body']['data'][0]['x'])

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

    if not validate_move(data, direction):
        directions.remove(direction)
        direction = random.choice(directions)

    if not validate_move(data, direction):
        directions.remove(direction)
        direction = random.choice(directions)

    if not validate_move(data, direction):
        directions.remove(direction)
        direction = random.choice(directions)

    print(direction)

    # TODO: Do things with data
    return {
        'move': direction,
        'taunt': 'battlesnake-python!'
    }

def validate_move(data, direction):

    print("testing move", direction)

    # checking for hazards if snake is to make the chosen move.
    x = int(data['snakes']['data'][0]['body']['data'][0]['x'])
    y = int(data['snakes']['data'][0]['body']['data'][0]['y'])

    if x == 0:
        if direction == 'left':
            print("tried to run out left side")
            return False

    if y == 0:
        if direction == 'up':
            print("tried to run out top side")
            return False

    if x == int(data['width']):
        if direction == 'right':
            print("tried to run out right side")
            return False

    if y == int(data['height']):
        if direction == 'down':
            print("tried to run out bottom side")
            return False


    # check that move will not put snake on its own tail
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

    tail = []

    for segment in data['snakes']['data'][0]['body']['data'][1:-1]:
        tail.append([int(segment['x']), int(segment['y'])])

    print(future_pos)
    print(tail)

    if future_pos in tail:
        print("future pos: ", future_pos, "in tail. Dodge!")
        return False

    return True



# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()
if __name__ == '__main__':
    bottle.run(application, host=os.getenv('IP', '0.0.0.0'), port=os.getenv('PORT', '8080'))
