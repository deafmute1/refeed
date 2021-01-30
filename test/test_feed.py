#!/usr/bin/env python
# -*- coding: utf-8 -*-

#refeed 
import refeed 

## Messages stolen from https://github.com/mjs/imapclient/blob/master/livetest.py
SIMPLE_MESSAGE = "Subject: something\r\n\r\nFoo\r\n"

MULTIPART_MESSAGE = """\
From: Bob Smith <bob@smith.com>
To: Some One <some@one.com>, foo@foo.com
Date: Tue, 16 Mar 2010 16:45:32 +0000
MIME-Version: 1.0
Subject: A multipart message
Content-Type: multipart/mixed; boundary="===============1534046211=="
--===============1534046211==
Content-Type: text/html; charset="us-ascii"
Content-Transfer-Encoding: quoted-printable
<html><body>
Here is the first part.
</body></html>
--===============1534046211==
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit
Here is the second part.
--===============1534046211==--
""".replace(
    "\n", "\r\n"
)

