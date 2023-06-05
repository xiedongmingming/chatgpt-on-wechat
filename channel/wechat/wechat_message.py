import re

from bridge.context import ContextType
from channel.chat_message import ChatMessage
from common.log import logger
from common.tmp_dir import TmpDir
from lib import itchat
from lib.itchat.content import *


class WeChatMessage(ChatMessage):

    def __init__(self, itchat_msg, is_group=False):

        super().__init__(itchat_msg)
        # {
        #   'MsgId': '8868215959353617342',
        #   'FromUserName': '@b6aa2c9f63e79afbd594c6e0c5a98cc9d229e06c181bb868852397bf6aea6423',
        #   'ToUserName': '@b6aa2c9f63e79afbd594c6e0c5a98cc9d229e06c181bb868852397bf6aea6423',
        #   'MsgType': 1,
        #   'Content': '你好',
        #   'Status': 3,
        #   'ImgStatus': 1,
        #   'CreateTime': 1682498422,
        #   'VoiceLength': 0,
        #   'PlayLength': 0,
        #   'FileName': '',
        #   'FileSize': '',
        #   'MediaId': '',
        #   'Url': '',
        #   'AppMsgType': 0,
        #   'StatusNotifyCode': 0,
        #   'StatusNotifyUserName': '',
        #   'RecommendInfo': {
        #       'UserName': '',
        #       'NickName': '',
        #       'QQNum': 0,
        #       'Province': '',
        #       'City': '',
        #       'Content': '',
        #       'Signature': '',
        #       'Alias': '',
        #       'Scene': 0,
        #       'VerifyFlag': 0,
        #       'AttrStatus': 0,
        #       'Sex': 0,
        #       'Ticket': '',
        #       'OpCode': 0
        #    },
        #    'ForwardFlag': 0,
        #    'AppInfo': {
        #       'AppID': '',
        #       'Type': 0
        #    },
        #    'HasProductId': 0,
        #    'Ticket': '',
        #    'ImgHeight': 0,
        #    'ImgWidth': 0,
        #    'SubMsgType': 0,
        #    'NewMsgId': 8868215959353617342,
        #    'OriContent': '',
        #    'EncryFileName': '',
        #    'User': <User: {
        #       'MemberList': <ContactList: []>,
        #       'UserName': '@b6aa2c9f63e79afbd594c6e0c5a98cc9d229e06c181bb868852397bf6aea6423',
        #       'City': '',
        #       'DisplayName': '',
        #       'PYQuanPin': '',
        #       'RemarkPYInitial': '',
        #       'Province': '',
        #       'KeyWord': '',
        #       'RemarkName': '',
        #       'PYInitial': '',
        #       'EncryChatRoomId': '',
        #       'Alias': '',
        #       'Signature': '明天会更好',
        #       'NickName': '东明16619786407',
        #       'RemarkPYQuanPin': '',
        #       'HeadImgUrl': '/cgi-bin/mmwebwx-bin/webwxgeticon?seq=1780322439&username=@b6aa2c9f63e79afbd594c6e0c5a98cc9d229e06c181bb868852397bf6aea6423&skey=@crypt_6817bf66_7233bf2ca20460c1c5597cbb491bc447',
        #       'UniFriend': 0,
        #       'Sex': 1,
        #       'AppAccountFlag': 0,
        #       'VerifyFlag': 0,
        #       'ChatRoomId': 0,
        #       'HideInputBarFlag': 0,
        #       'AttrStatus': 0,
        #       'SnsFlag': 273,
        #       'MemberCount': 0,
        #       'OwnerUin': 0,
        #       'ContactFlag': 0,
        #       'Uin': 1231084328,
        #       'StarFriend': 0,
        #       'Statues': 0,
        #       'WebWxPluginSwitch': 0,
        #       'HeadImgFlag': 1
        #    }>,
        #    'Type': 'Text',
        #    'Text': '你好'
        #  }

        self.msg_id = itchat_msg["MsgId"]
        self.create_time = itchat_msg["CreateTime"]
        self.is_group = is_group

        if itchat_msg["Type"] == TEXT:

            self.ctype = ContextType.TEXT

            self.content = itchat_msg["Text"]

        elif itchat_msg["Type"] == VOICE:

            self.ctype = ContextType.VOICE

            self.content = TmpDir().path() + itchat_msg["FileName"]  # CONTENT直接存临时目录路径

            self._prepare_fn = lambda: itchat_msg.download(self.content)

        elif itchat_msg["Type"] == PICTURE and itchat_msg["MsgType"] == 3:

            self.ctype = ContextType.IMAGE

            self.content = TmpDir().path() + itchat_msg["FileName"]  # CONTENT直接存临时目录路径

            self._prepare_fn = lambda: itchat_msg.download(self.content)

        elif itchat_msg["Type"] == NOTE and itchat_msg["MsgType"] == 10000:

            if is_group and ("加入群聊" in itchat_msg["Content"] or "加入了群聊" in itchat_msg["Content"]):

                self.ctype = ContextType.JOIN_GROUP

                self.content = itchat_msg["Content"]

                if "加入了群聊" in itchat_msg["Content"]:  # 这里只能得到NICKNAME，ACTUAL_USER_ID还是机器人的ID
                    self.actual_user_nickname = re.findall(r"\"(.*?)\"", itchat_msg["Content"])[-1]
                elif "加入群聊" in itchat_msg["Content"]:
                    self.actual_user_nickname = re.findall(r"\"(.*?)\"", itchat_msg["Content"])[0]

            elif "拍了拍我" in itchat_msg["Content"]:

                self.ctype = ContextType.PATPAT

                self.content = itchat_msg["Content"]

                if is_group:
                    #
                    self.actual_user_nickname = re.findall(r"\"(.*?)\"", itchat_msg["Content"])[0]

            else:

                raise NotImplementedError("Unsupported note message: " + itchat_msg["Content"])

        else:

            raise NotImplementedError("Unsupported message type: Type:{} MsgType:{}".format(
                itchat_msg["Type"],
                itchat_msg["MsgType"])
            )

        self.from_user_id = itchat_msg["FromUserName"]
        self.to_user_id = itchat_msg["ToUserName"]

        user_id = itchat.instance.storageClass.userName
        nickname = itchat.instance.storageClass.nickName

        if self.from_user_id == user_id:  # 虽然FROM_USER_ID和TO_USER_ID用的少，但是为了保持一致性，还是要填充一下 以下很繁琐，一句话总结：能填的都填了。
            self.from_user_nickname = nickname
        if self.to_user_id == user_id:
            self.to_user_nickname = nickname

        try:  # 陌生人时候, 'USER'字段可能不存在

            self.other_user_id = itchat_msg["User"]["UserName"]
            self.other_user_nickname = itchat_msg["User"]["NickName"]

            if self.other_user_id == self.from_user_id:
                self.from_user_nickname = self.other_user_nickname
            if self.other_user_id == self.to_user_id:
                self.to_user_nickname = self.other_user_nickname

        except KeyError as e:  # 处理偶尔没有对方信息的情况

            logger.warn("[WX]get other_user_id failed: " + str(e))

            if self.from_user_id == user_id:
                self.other_user_id = self.to_user_id
            else:
                self.other_user_id = self.from_user_id

        if self.is_group:
            #
            self.is_at = itchat_msg["IsAt"]
            self.actual_user_id = itchat_msg["ActualUserName"]

            if self.ctype not in [ContextType.JOIN_GROUP, ContextType.PATPAT]:
                #
                self.actual_user_nickname = itchat_msg["ActualNickName"]
