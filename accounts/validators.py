from .models import User
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

# 회원가입 시, validator
def validate_signup(user, user_data):
    err_msg = []

    # validate_username
    if username := user_data.get("username"):
        if User.objects.filter(username=username).exists():
            err_msg.append({"username": ['이미 존재하는 아이디입니다.']})

    # validate_password
    password = user_data.get("password")
    password2 = user_data.get("password2")
    if not password == password2:
        err_msg.append({"password": ['비밀번호가 일치하지 않습니다.']})
    else:
        # settings에 있는 validator 사용한 유효성 검사 (비밀번호 자체에 대한 유효성 검사)
        try:
            validate_password(password, user)
        except  ValidationError as e:
            err_msg.append({"password": e.messages})  # ValidationError는 리스트 형태로 반환

    # validate_email
    if email := user_data.get("email"):
        if User.objects.filter(email=email).exists():
            err_msg.append({"email": '이미 존재하는 이메일입니다.'})
        else:
            # email 형식 유효성 검사
            try:
                validate_email(email)
            except:
                err_msg.append({"email": '이메일 형식이 올바르지 않습니다.'})

    if err_msg:
        return False, err_msg
    return True, err_msg

# 수정했을때 비밀번호 유효성 검사
def custom_validate_password(password):
    # 새로운 비밀번호에 대한 유효성 검사 진행
    new_password = password
    if len(new_password) < 8:
        return False, "비밀번호는 8자 이상이어야 합니다."
    
    has_letter = any(c.isalpha() for c in new_password)
    has_number = any(c.isdigit() for c in new_password)
    
    if not (has_letter and has_number):
        return False, "비밀번호는 문자와 숫자를 모두 포함해야 합니다."
    
    for i in range(len(new_password) - 3):
        if new_password[i] == new_password[i+1] == new_password[i+2] == new_password[i+3]:
            return False, "동일한 문자를 4번 이상 연속해서 사용할 수 없습니다."
    
    return True, None