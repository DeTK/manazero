class Module:
    def text_reg(self, str):  # 폴더와 파일이름에서 쓸수없는문자들을 제거해주고 앞뒤 공백도 제거해준다.
        import re
        tempstr = re.sub('[\/:*?"<>|]', '', str).strip()
        return tempstr