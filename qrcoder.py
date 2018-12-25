import hashlib
import json
import os
import tempfile
import uuid

import qrcode
import requests
from gino.ext.sanic import Gino
from sanic import Sanic, response
from sanic.request import Request

BASE_URL = os.environ.get('BASE_URL')
VERIFICATION_TOKEN = os.environ.get('VERIFICATION_TOKEN')
PORT = int(os.environ.get('PORT', '8000'))
DATABASE_URL = os.environ.get('DATABASE_URL')

app = Sanic()
app.config.DB_DSN = DATABASE_URL
db = Gino()
db.init_app(app)


class QRCode(db.Model):
    __tablename__ = 'qr_codes'

    key = db.Column(db.String(40), primary_key=True)
    value = db.Column(db.Text())

    @classmethod
    async def generate(cls, value: str) -> 'QRCode':
        key = hashlib.sha1(str(uuid.uuid4()).encode()).hexdigest()[0:7]
        return await cls.create(key=key, value=value)

    @property
    def url(self) -> str:
        return '{}/{}'.format(BASE_URL, self.key)

    async def create_image_url(self) -> str:
        filename = '{}/{}.png'.format(tempfile.gettempdir(), self.key)
        if not os.path.exists(filename):
            img = qrcode.make(self.value)
            img.save(filename)
        return filename


async def post_to_slack(text: str, response_url: str) -> None:
    code = await QRCode.generate(text)
    data = {
        'response_type': 'in_channel',
        'text': code.url,
        'unfurl_links': True
    }
    requests.post(response_url, data=json.dumps(data))


@app.listener('before_server_start')
async def before_server_start(_, loop):
    await db.gino.create_all()


@app.post('/command')
async def command(request: Request):
    token = request.form['token'][0]
    if token != VERIFICATION_TOKEN:
        return response.text('401 Unauthorized', status=401)

    text = request.form['text'][0]
    response_url = request.form['response_url'][0]
    app.add_task(post_to_slack(text, response_url))
    return response.text('')


@app.get('/<key>')
async def show(request: Request, key: str):
    code = await QRCode.get_or_404(key)
    return await response.file(
        await code.create_image_url()
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
