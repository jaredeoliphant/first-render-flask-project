from flask import Flask, render_template, request, Response, session, redirect, flash, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, FileField, MultipleFileField, BooleanField
from wtforms.validators import Length, DataRequired, NumberRange
from werkzeug.utils import secure_filename
from data_process import data_process
import os


app = Flask(__name__)

app.config['SECRET_KEY'] = 'secretkey'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'files')
if not os.path.exists(os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'])):
    os.makedirs(os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER']))


class DataForm(FlaskForm):

    file = FileField('CSV File  ', validators=[DataRequired()])
    start = FloatField('Start time for sampling bias calculation:  ',
                       default=7.0, validators=[DataRequired(), NumberRange(min=0, max=10)])
    end = FloatField('End time for sampling bias calculation:  ',
                     default=9.8, validators=[DataRequired(), NumberRange(min=0, max=10)])
    submit = SubmitField('Submit')


class ImageForm(FlaskForm):

    xfile = FileField('X accel file  ')#, validators=[DataRequired()])
    yfile = FileField('Y accel file  ')#, validators=[DataRequired()])
    zfile = FileField('Z accel file  ')#, validators=[DataRequired()])
    rpyfile = FileField('RPY angles file  ')#, validators=[DataRequired()])
    asifile = FileField('ASI file  ')

    oiv = FloatField('Input OIV time here:  ',
                       default=0.160124)#, validators=[DataRequired(), NumberRange(min=0, max=10)])
    final = FloatField('Input final time here:  ',
                     default=0.5)#, validators=[DataRequired(), NumberRange(min=0, max=10)])
    datarate = FloatField('Input data sample rate here:  ',
                     default=30008)#, validators=[DataRequired(), NumberRange(min=0, max=100000)])
    camerarate = FloatField('Input camera sample rate here:  ',
                          default=1000)#, validators=[DataRequired(), NumberRange(min=0, max=10000)])
    en1317 = BooleanField('EN 1317 test')
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


@app.route('/image_generator', methods=['GET', 'POST'])
def image_generator():
    form = ImageForm()

    if form.validate_on_submit():
        fx = form.xfile.data
        fy = form.yfile.data
        fz = form.zfile.data
        frpy = form.rpyfile.data


        filenamex = secure_filename(fx.filename)
        filepathx = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'], filenamex)
        filenamey = secure_filename(fy.filename)
        filepathy = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'], filenamey)
        filenamez = secure_filename(fz.filename)
        filepathz = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'], filenamez)
        filenamerpy = secure_filename(frpy.filename)
        filepathrpy = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'], filenamerpy)


        # delete all existing files in the upload folder to keep it clean
        path = os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'])
        for ff in os.listdir(path):
            fff = os.path.join(path, ff)
            os.remove(fff)

        # save the new files in the upload folder
        fx.save(filepathx)
        fy.save(filepathy)
        fz.save(filepathz)
        frpy.save(filepathrpy)

        # asi file is optional. only save it if it exists
        fasi = form.asifile.data
        if fasi:
            filenameasi = secure_filename(fasi.filename)
            filepathasi = os.path.join(
                os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'], filenameasi)
            fasi.save(filepathasi)
            session['filenameasi'] = filenameasi.split('.csv')[0]
            session['filepathasi'] = filepathasi


        print('validated')
        session['filenamex'] = filenamex.split('.csv')[0]
        session['filepathx'] = filepathx
        session['filenamey'] = filenamey.split('.csv')[0]
        session['filepathy'] = filepathy
        session['filenamez'] = filenamez.split('.csv')[0]
        session['filepathz'] = filepathz
        session['filenamerpy'] = filenamerpy.split('.csv')[0]
        session['filepathrpy'] = filepathrpy
        session['oiv'] = form.oiv.data
        session['final'] = form.final.data
        session['datarate'] = form.datarate.data
        session['camerarate'] = form.camerarate.data
        session['en1317'] = form.en1317.data

        return redirect(url_for('image_response'))

    return render_template('image_generator.html', form=form)


@app.route('/image_response', methods=['GET', 'POST'])
def image_response():
    if request.method == 'GET':

        return render_template('image_response.html')


if __name__ == '__main__':
    app.run(debug=True)
    