import boto3, random, time
from io import BytesIO
from flask import Flask, render_template, jsonify, url_for, request
from celery import Celery
from pyexcelerate import Workbook

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret-key'
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# S3_BUCKET_NAME = ''
# ACCESS_KEY =  ''
# SECRET_KEY = ''

s3_client = boto3.client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

@celery.task(bind=True)
def generate_excel(self, size=5):
    '''
    Generates Excel file and uploads to S3 bucket. Updates task state as it generates.
    '''
    data = []
    for i in range(size):
        row = []
        row.append(i)
        data.append(row)
        self.update_state(state='PROGRESS', meta={'current': i, 'total': size})
        time.sleep(1)

    stream = BytesIO()
    wb = Workbook()
    wb.new_sheet("sheet name", data=data)
    wb.save(stream)
    stream.seek(0)

    key_name = 'small_excel_' + str(random.randint(1,10000)) + '.xlsx'

    s3_client.upload_fileobj(stream, S3_BUCKET_NAME, key_name)
    url = s3_client.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET_NAME, 'Key': key_name}, ExpiresIn=3600)

    return {'current': size, 'total': size, 'status': 'COMPLETED', 'result': 42, 'url': url}

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/generate_report', methods=['GET'])
def generate_report():
    size = int(request.args.get('size'))
    task = generate_excel.apply_async(args=[size])
    return jsonify({}), 202, {'Location': url_for('taskstatus', task_id=task.id)}

@app.route('/taskstatus/<task_id>')
def taskstatus(task_id):
    task = generate_excel.AsyncResult(task_id)

    if task.state == 'PENDING':
        # job did not start yet
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
            response['url'] = task.info['url']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)


if __name__ == '__main__':
    app.run()