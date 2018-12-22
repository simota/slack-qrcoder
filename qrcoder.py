import hashlib
import os
import uuid
import requests
import json

import qrcode
from gino.ext.sanic import Gino
from sanic import Sanic, response

BASE_URL = os.environ.get('BASE_URL')
VERIFICATION_TOKEN = os.environ.get('VERIFICATION_TOKEN')
PORT = int(os.environ.get('PORT', '8000'))

app = Sanic()
app.config.DB_HOST = os.environ.get('DB_HOST')
app.config.DB_USER = os.environ.get('DB_USER')
app.config.DB_DATABASE = os.environ.get('DB_DATABASE')
app.config.DB_PASSWORD = os.environ.get('DB_PASSWORD')

db = Gino()
db.init_app(app)


class QRCode(db.Model):
    __tablename__ = 'qr_codes'

    key = db.Column(db.String(40), primary_key=True)
    value = db.Column(db.Text())

    @classmethod
    async def generate(cls, value: str):
        key = hashlib.sha1(str(uuid.uuid4()).encode()).hexdigest()[0:7]
        return await cls.create(key=key, value=value)

    @property
    def url(self) -> str:
        return '{}/{}'.format(BASE_URL, self.key)

    async def create_image_url(self) -> str:
        filename = '/tmp/' + self.key + '.png'
        if not os.path.exists(filename):
            img = qrcode.make(self.value)
            img.save(filename)
        return filename


async def post_to_slack(text, url):
    code = await QRCode.generate(text)
    data = {
        'response_type': 'in_channel',
        'text': code.url,
        'unfurl_links': True
    }
    requests.post(url, data=json.dumps(data))


@app.listener('before_server_start')
async def before_server_start(_, loop):
    await db.gino.create_all()


@app.route('/command', methods=['POST'])
async def command(request):
    token = request.form['token'][0]
    if token != VERIFICATION_TOKEN:
        return response.text('401 Unauthorized', status=401)

    text = request.form['text'][0]
    response_url = request.form['response_url'][0]
    app.add_task(post_to_slack(text, response_url))
    return response.text('')


@app.route('/<key>', methods=['GET'])
async def show(request, key):
    code = await QRCode.get_or_404(key)
    return await response.file(
        await code.create_image_url()
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
