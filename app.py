import os, boto3, random
from io import BytesIO
from flask import Flask, render_template, jsonify
from celery import Celery
from pyexcelerate import Workbook

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret-key'
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

S3_BUCKET_NAME = ''
ACCESS_KEY =  ''
SECRET_KEY = ''

s3_client = boto3.client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
file_urls = []

@celery.task
def generate_excel():
    data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    stream = BytesIO()
    wb = Workbook()
    wb.new_sheet("sheet name", data=data)
    wb.save(stream)
    stream.seek(0)

    key_name = 'small_excel-' + str(random.randint(1,1000)) + '.xlsx'

    s3_client.upload_fileobj(stream, S3_BUCKET_NAME, key_name)

    try:
        url = s3_client.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET_NAME, 'Key': key_name}, ExpiresIn=3600)
    except ClientError as e:
        print(' Error: file url could not be found ')
        return None

    print(' ---- ' + url + ' ----')
    file_urls.append(url)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', urls=file_urls)

@app.route('/generate_small', methods=['GET', 'POST'])
def generate_small():
    generate_excel()
    return jsonify('ok')


if __name__ == '__main__':
    app.run()