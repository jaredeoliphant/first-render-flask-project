from flask import Flask, render_template, request, Response, session, redirect, flash, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, FileField
from wtforms.validators import Length, DataRequired, NumberRange
from werkzeug.utils import secure_filename
from data_process import data_process
import os, time


app = Flask(__name__)

app.config['SECRET_KEY'] = 'secretkey'
app.config['UPLOAD_FOLDER'] = 'static\\files'


class DataForm(FlaskForm):

    file = FileField('CSV File  ', validators=[DataRequired()])
    start = FloatField('Start time for sampling bias calculation:  ',
                       default=7.0, validators=[DataRequired(), NumberRange(min=0, max=10)])
    end = FloatField('End time for sampling bias calculation:  ',
                     default=9.8, validators=[DataRequired(), NumberRange(min=0, max=10)])
    submit = SubmitField('Submit')


@app.route('/', methods=['GET', 'POST'])
def index():
    form = DataForm()

    if form.validate_on_submit():
        f = form.file.data

        filename = secure_filename(f.filename)
        filepath = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'], filename)

        # delete all existing files in the upload folder to keep it clean
        path = os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'])
        for ff in os.listdir(path):
            fff = os.path.join(path, ff)
            os.remove(fff)

        # save the new file in the upload folder
        f.save(filepath)

        session['filename'] = filename.split('.csv')[0]
        session['filepath'] = filepath
        session['start'] = form.start.data
        session['end'] = form.end.data

        return redirect(url_for('speed_result'))

    return render_template('index.html', form=form)


@app.route("/speed_result", methods=['GET', 'POST'])
def speed_result():
    if request.method == 'GET':
        filepath = session['filepath']
        start = session['start']
        end = session['end']

        processed_values = data_process(filepath, start, end)
        os.remove(filepath)

        session['outputfilename'] = processed_values['outputfilename']

        return render_template('speed_result.html',
                               testID=processed_values['testID'],
                               speed_kmh=processed_values['speed_kmh'],
                               imgdata=processed_values['imgdata'],
                               outputfilename=processed_values['outputfilename'],
                               speed_falling=processed_values['speed_falling'],
                               rollbias=processed_values['rollbias'],
                               pitchbias=processed_values['pitchbias'],
                               yawbias=processed_values['yawbias'],
                               starttime=start,
                               endtime=end
                               )
    else:
        return 'did not work'
   
    
@app.route("/getCSV")
def getCSV():
    fullfilepath = f'{session["outputfilename"]}.csv'
    with open(fullfilepath) as fp:
        csv = fp.read()
    
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition":
                  f"attachment; filename={session['filename']}_OFFSET.csv"})


@app.route('/ip_notebook',methods=['GET'])
def ip_notebook():
    return render_template('ip_notebook.html')


@app.route('/result_example',methods=['GET'])
def result_example():
    return render_template('result_example.html')


@app.route('/algorithm',methods=['GET'])
def algorithm():
    return render_template('algorithm.html')


if __name__ == '__main__':
    app.run(debug=True)
    