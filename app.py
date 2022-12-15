from flask import Flask, render_template,request
from werkzeug.utils import secure_filename
from data_process import data_process
import os
from matplotlib.figure import Figure
from io import BytesIO
import base64

app = Flask(__name__)

@app.route('/')
def homepage():
    return render_template('index.html')


@app.route('/speed_result', methods = ['GET', 'POST'])
def upload_file():
   if request.method == 'POST':
      f = request.files['file']
      secfilename = secure_filename(f.filename)
      f.save(secfilename)
      try:
          processed_values = data_process(secfilename)
          os.remove(secfilename)
          return f'Test ID: {processed_values["testID"]}      speed:  {processed_values["speed_kmh"]} km/h <br> <img src="data:image/png;base64,{processed_values["imgdata"]}"/>'

      except:
          os.remove(secfilename)
          return 'failed'
   
      
   else:
       return 'no file'

@app.route("/plot")
def hello():
    # Generate the figure **without using pyplot**.
    fig = Figure()
    ax = fig.subplots()
    ax.plot([1, 2])
    # Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format="png")
    # Embed the result in the html output.
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    #print(data)
    return f"<img src='data:image/png;base64,{data}'/>"



@app.route('/for_fun')
def ip_notebook():
    return render_template('notebook.html')


if __name__ == '__main__':
    app.run(debug=True)
    