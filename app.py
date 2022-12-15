from flask import Flask, render_template,request
from werkzeug.utils import secure_filename
from data_process import data_process
app = Flask(__name__)

@app.route('/')
def homepage():
    return render_template('index.html')


@app.route('/speed_result', methods = ['GET', 'POST'])
def upload_file():
   if request.method == 'POST':
      f = request.files['file']
      secfilename = secure_filename(f.filename)
      f.save(secure_filename(secfilename))
      processed_values = data_process(secfilename)
      return f'Test ID: {processed_values["testID"]}      speed:  {processed_values["speed_kmh"]} km/h'
  
    


if __name__ == '__main__':
    app.run(debug=False)
    