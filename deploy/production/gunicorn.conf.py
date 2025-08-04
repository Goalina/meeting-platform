# gunicorn.conf.py
bind = "{{ip}}:8080"
workers = 8
threads = 4
worker_class = "custom_worker.SSLCachedWorker"
certfile = "/vault/secrets/server.crt"
keyfile = "/vault/secrets/server.key"

# TLS 版本和加密算法配置
# 允许 TLS 1.2 和 1.3 (Gunicorn 会自动协商最高版本)
ssl_version = "TLSv1_2 TLSv1_3"

# 推荐的加密套件 (优先使用前向保密算法)
ciphers = (
    "ECDHE-ECDSA-AES256-GCM-SHA384:"
    "ECDHE-RSA-AES256-GCM-SHA384:"
    "ECDHE-ECDSA-CHACHA20-POLY1305:"
    "ECDHE-RSA-CHACHA20-POLY1305:"
    "ECDHE-ECDSA-AES128-GCM-SHA256:"
    "ECDHE-RSA-AES128-GCM-SHA256:"
    "DHE-RSA-AES256-GCM-SHA384:"
    "DHE-RSA-AES128-GCM-SHA256"
)

# 其他安全相关设置
preload_app = True
keepalive = 5
timeout = 30
max_requests = 1000
max_requests_jitter = 50


# 服务启动成功回调函数
def when_ready(server):
    import os
    from django.conf import settings
    for config_path in settings.ALL_CONFIG_PATH_LIST:
        if not config_path:
            continue
        if os.path.exists(config_path):
            os.remove(config_path)
            print("delete config {} success".format(config_path))
        else:
            print("config {} is not exist".format(config_path))
    print("start to run server successfully...")
