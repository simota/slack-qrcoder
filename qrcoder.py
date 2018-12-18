import os
import base64
import hashlib
import qrcode
import requests
import json

from sanic import Sanic, response

app = Sanic()

IMAGE_BASE_URL = os.environ.get('IMAGE_BASE_URL')
SLACK_VERIFICATION_TOKEN = os.environ.get('SLACK_VERIFICATION_TOKEN')
PORT = int(os.environ.get('PORT', '8000'))


def encode_text(text):
    return base64.b64encode(text.encode()).decode()


def decode_text(text):
    return base64.b64decode(text.encode()).decode()


def make_qrcode_url(text):
    return '{}/qrcode/{}'.format(IMAGE_BASE_URL, encode_text(text))


async def post_to_slack(text, url):
    qrcode_url = make_qrcode_url(text)
    data = {
        'response_type': 'in_channel',
        'text': qrcode_url,
        'unfurl_links': True
    }
    requests.post(url, data=json.dumps(data))


async def make_qrcode(content):
    md5 = hashlib.md5(content.encode()).hexdigest()
    name = '/tmp/' + md5 + '.png'
    if not os.path.exists(name):
        img = qrcode.make(content)
        img.save(name)
    return name


@app.route('/command', methods=['POST'])
async def command(request):
    token = request.form['token'][0]
    if token != SLACK_VERIFICATION_TOKEN:
        return response.text('401 Unauthorized', status=401)

    text = request.form['text'][0]
    response_url = request.form['response_url'][0]
    app.add_task(post_to_slack(text, response_url))
    return response.text('')


@app.route('qrcode/<key>', methods=['GET'])
async def show(request, key):
    return await response.file(
        await make_qrcode(decode_text(key))
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
