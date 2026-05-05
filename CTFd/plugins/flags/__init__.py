import re
import json
from CTFd.plugins import register_plugin_assets_directory


class FlagException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class BaseFlag(object):
    name = None
    templates = {}

    @staticmethod
    def compare(self, saved, provided):
        return True


class CTFdStaticFlag(BaseFlag):
    name = "static"
    templates = {  # Nunjucks templates used for key editing & viewing
        "create": "/plugins/flags/assets/static/create.html",
        "update": "/plugins/flags/assets/static/edit.html",
    }

    @staticmethod
    def compare(chal_key_obj, provided):
        saved = chal_key_obj.content
        data = chal_key_obj.data

        if len(saved) != len(provided):
            return False
        result = 0

        if data == "case_insensitive":
            for x, y in zip(saved.lower(), provided.lower()):
                result |= ord(x) ^ ord(y)
        else:
            for x, y in zip(saved, provided):
                result |= ord(x) ^ ord(y)
        return result == 0


class CTFdRegexFlag(BaseFlag):
    name = "regex"
    templates = {  # Nunjucks templates used for key editing & viewing
        "create": "/plugins/flags/assets/regex/create.html",
        "update": "/plugins/flags/assets/regex/edit.html",
    }

    @staticmethod
    def compare(chal_key_obj, provided):
        saved = chal_key_obj.content
        data = chal_key_obj.data

        try:
            if data == "case_insensitive":
                res = re.match(saved, provided, re.IGNORECASE)
            else:
                res = re.match(saved, provided)
        # TODO: this needs plugin improvements. See #1425.
        except re.error as e:
            raise FlagException("Regex parse error occured") from e

        return res and res.group() == provided

# New Flag Type: Time
def time_to_seconds(time_str):
    """Converts HH:MM:SS to total seconds."""
    if not time_str:
        return None
    try:
        parts = time_str.strip().split(':')
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return int(parts[0])
    except (ValueError, IndexError):
        return None

class CTFdTimeFlag(BaseFlag):
    name = "time"
    templates = {
        "create": "/plugins/flags/assets/time/create.html",
        "update": "/plugins/flags/assets/time/edit.html",
    }
    
    @staticmethod
    def compare(chal_key_obj, provided):
        # 1. Convert what the user typed (provided)
        user_seconds = time_to_seconds(provided)
        if user_seconds is None:
            return False

        try:
            # 2. Parse the saved settings from the database
            saved_data = json.loads(chal_key_obj.data)
            mode = saved_data.get("mode", "specific")

            if mode == "range":
                # CALLING THE TOP-LEVEL FUNCTION HERE
                start = time_to_seconds(saved_data.get('start'))
                end = time_to_seconds(saved_data.get('end'))
                
                if start is not None and end is not None:
                    return start <= user_seconds <= end
            
            elif mode == "specific":
                target = time_to_seconds(saved_data.get('target'))
                return user_seconds == target

        except Exception:
            # If JSON fails, check the content field as a backup
            # (Matches what shows in your "Flag" column screenshot)
            if "-" in chal_key_obj.content:
                p = chal_key_obj.content.split('-')
                return time_to_seconds(p[0]) <= user_seconds <= time_to_seconds(p[1])
            return False
        return False

# New Flag Type: Numerical Range 
class CTFNumericalRange(BaseFlag):
     name = "range"
     templates = {  # Nunjucks templates used for key editing & viewing
        "create": "/plugins/flags/assets/range/create.html",
        "update": "/plugins/flags/assets/range/edit.html",
    }
     @staticmethod
     def compare(chal_key_obj, provided):
        try:
            # provided is user's answer
            val = float(provided.strip())

            # chal_key_obj.content is the finalcontent.value from range folder(create.html)
            minimum, maximum = map(float, chal_key_obj.content.split('-'))

            return minimum <= val <= maximum
        except:
            return False
       

FLAG_CLASSES = {"static": CTFdStaticFlag, 
                "regex": CTFdRegexFlag, 
                "range": CTFNumericalRange,
                "time": CTFdTimeFlag}


def get_flag_class(class_id):
    cls = FLAG_CLASSES.get(class_id)
    if cls is None:
        raise KeyError
    return cls


def load(app):
    register_plugin_assets_directory(app, base_path="/plugins/flags/assets/")
