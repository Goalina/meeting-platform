#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2025/8/1 16:20
# @Author  : Tom_zc
# @FileName: custom_worker.py
# @Software: PyCharm
import ssl
import errno
import traceback

from gunicorn.workers.sync import SyncWorker
from gunicorn import http
from gunicorn import util
from django.conf import settings


def ssl_context(conf):
    def default_ssl_context_factory():
        context = settings.TLS_CONTEXT
        context.verify_mode = conf.cert_reqs
        if conf.ciphers:
            context.set_ciphers(conf.ciphers)
        return context

    return conf.ssl_context(conf, default_ssl_context_factory)


def ssl_wrap_socket(sock, conf):
    return ssl_context(conf).wrap_socket(sock,
                                         server_side=True,
                                         suppress_ragged_eofs=conf.suppress_ragged_eofs,
                                         do_handshake_on_connect=conf.do_handshake_on_connect)


class SSLCachedWorker(SyncWorker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ssl_context = None

    def handle(self, listener, client, addr):
        req = None
        try:
            if self.cfg.is_ssl:
                client = ssl_wrap_socket(client, self.cfg)
            parser = http.RequestParser(self.cfg, client, addr)
            req = next(parser)
            self.handle_request(listener, req, client, addr)
        except http.errors.NoMoreData as e:
            self.log.debug("Ignored premature client disconnection. %s", e)
        except StopIteration as e:
            self.log.debug("Closing connection. %s", e)
        except ssl.SSLError as e:
            if e.args[0] == ssl.SSL_ERROR_EOF:
                self.log.debug("ssl connection closed")
                client.close()
            else:
                self.log.debug("Error processing SSL request.")
                self.handle_error(req, client, addr, e)
        except OSError as e:
            if e.errno not in (errno.EPIPE, errno.ECONNRESET, errno.ENOTCONN):
                self.log.exception("Socket error processing request.")
            else:
                if e.errno == errno.ECONNRESET:
                    self.log.debug("Ignoring connection reset")
                elif e.errno == errno.ENOTCONN:
                    self.log.debug("Ignoring socket not connected")
                else:
                    self.log.debug("Ignoring EPIPE")
        except BaseException as e:
            self.log.debug("error e:{}".format(traceback.format_exc()))
            self.handle_error(req, client, addr, e)
        finally:
            util.close(client)
