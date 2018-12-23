slack-qrcoder
=============

Generate QR code with Slack command.

Author
======

[Shingo Imota](https://github.com/simota/)

Setup
=====

**setup heroku app**

```
$ heroku create appname
$ heroku addons:add heroku-postgresql
$ heroku config:set VERIFICATION_TOKEN=<slack app Verification Token>
$ heroku config:set BASE_URL=<heroku app url>
```

**setup slack app**

Command: `/qrcoder`
Request URL: `<heroku app url>/command`

Usage
=====

```
/qrcoder text or url
```

License
=======

Copyright © 2018 [Shingo Imota](https://github.com/simota/). All rights reserved.
