import traceback
from logging import *
from flask import *
from flask_socketio import SocketIO
from micrographer import run
from demandCurveGen import getDemandCurve

app = Flask(__name__)
socketio = SocketIO(app)
app.config['SECRET_KEY'] = 'jsdhjshjk837944789378923798$*(&#*&(#'

# architecture inspired from https://codeburst.io/building-your-first-chat-application-using-flask-in-7-minutes-f98de4adfa5d
# (thank you)

@app.route('/demandCurve/')
def render_static():
    return render_template('demandCurve.html')


@app.route('/') 
def session():
    return render_template('index.html')

def myCallback():
    print('client: acknowledged response')

@socketio.on('genGraphs')
def event_handler(json, methods=['GET', 'POST']):
    print("json:",json)
    print('server: received genGraphs request, responding...')
    if ('u' in json.keys()):
        json_r = None
        
        try:
            m = float(json['m'])
            u,px,px2,py = (str(json[k]) for k in ('u','px_1','px_2','py'))
            json_r = run(u,px,px2,py,m)
            
        except Exception as e:
            error(traceback.format_exc())

        if json_r is None:
            json_r = {'error':-1}
        elif json_r == 1:
            json_r = {'error':1}
            
        socketio.emit('displayGraphs', json_r, callback=myCallback)

@socketio.on('demandCurve')
def event_handler(json, methods=['GET','POST']):
    print("json: ",json)
    print('server: received demandCurve request, responding...')
    if ('f' in json.keys()):
        json_r = None

        try:
            json_r = getDemandCurve(json['f'],float(json['py']),float(json['m']))
        except Exception as e:
            error(traceback.format_exc())

        print('json:',json_r)
        socketio.emit('displayDemand', json_r, callback=myCallback)


if __name__=="__main__":
    print('starting server...')
    #socketio.run(app) #local host
    socketio.run(app, "0.0.0.0")
