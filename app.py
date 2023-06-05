# encoding:utf-8

import os
import signal
import sys

from channel import channel_factory

from common.log import logger

from config import conf, load_config

from plugins import *


def sigterm_handler_wrap(_signo):
    #
    old_handler = signal.getsignal(_signo)  # 默认的处理函数

    def func(_signo, _stack_frame):
        #
        logger.info("signal {} received, exiting...".format(_signo))

        conf().save_user_datas()  # 保存用户数据--在默认构造函数之前调用

        if callable(old_handler):  # check old_handler：调用默认处理函数
            #
            return old_handler(_signo, _stack_frame)

        sys.exit(0)

    signal.signal(_signo, func)  # 构造新的处理函数


def run():
    #
    try:

        # load config
        load_config()

        # ctrl + c
        sigterm_handler_wrap(signal.SIGINT)
        # kill signal
        sigterm_handler_wrap(signal.SIGTERM)

        # create channel
        channel_name = conf().get("channel_type", "wx")  # 默认是微信

        if "--cmd" in sys.argv:
            #
            channel_name = "terminal"

        if channel_name == "wxy":
            #
            os.environ["WECHATY_LOG"] = "warn"

            # os.environ['WECHATY_PUPPET_SERVICE_ENDPOINT'] = '127.0.0.1:9001'

        channel = channel_factory.create_channel(channel_name)

        if channel_name in ["wx", "wxy", "terminal", "wechatmp", "wechatmp_service", "wechatcom_app"]:
            #
            PluginManager().load_plugins()

        # startup channel
        channel.startup()

    except Exception as e:

        logger.error("App startup failed!")

        logger.exception(e)


if __name__ == "__main__":
    #
    run()
