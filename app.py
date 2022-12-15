from flask import Flask, render_template,request,Response
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
      #try:
      processed_values = data_process(secfilename)
      os.remove(secfilename)
      return render_template('speed_result.html',
                               testID=processed_values['testID'],
                               speed_kmh=processed_values['speed_kmh'],
                               imgdata=processed_values['imgdata'],
                               outputfilename=processed_values['outputfilename']
                               )
      #except:
       #   os.remove(secfilename)
        #  return 'failed'   
   else:
       return 'no file'
   
    
@app.route("/getCSV/<outputfilename>")
def getCSV(outputfilename):
    with open(f'{outputfilename}.csv') as fp:
        csv = fp.read()
    #csv = '1,2,3\n4,5,6\n'
    
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition":
                  f"attachment; filename={outputfilename}.csv"})



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


@app.route('/example')
def example():
    return render_template('result_example.html')


if __name__ == '__main__':
    app.run(debug=True)
    