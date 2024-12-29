import requests
import hashlib

from django.contrib.auth import authenticate
from django.conf import settings
from django.contrib.auth import login
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model


from rest_framework import status
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .validators import validate_signup, custom_validate_password
from .serializers import UserSerializer
from .models import User

from django.shortcuts import redirect
from django.conf import settings

from django.core.files.base import ContentFile

from rest_framework.parsers import MultiPartParser, FormParser

User = get_user_model()


# 유저 토큰 확인
class CheckTokenView(APIView):
    def get(self, request):
        if not request.auth:
            return Response({}, status=401)
        return Response({}, status=200)

# 부모 회원가입
class KakaoCallbackView(APIView):
    # 카카오 OAuth를 통한 로그인 프로세스를 처리하는 뷰
    def get(self, request, *args, **kwargs):

        # 요청에서 'code' 파라미터
        code = request.GET.get("code")

        # 인증 코드가 없는 경우 오류 메시지와 함께 요청
        if not code:
            return Response({"error": "인증 코드가 없습니다"}, status=status.HTTP_400_BAD_REQUEST)

        # 자동 로그인
        token_req = requests.get(
            f"https://kauth.kakao.com/oauth/token?grant_type=authorization_code&client_id={settings.REST_API_KEY}&client_secret={settings.CLIENT_SECRET}&redirect_uri={settings.KAKAO_CALLBACK_URI}&code={code}"
        )
        token_req_json = token_req.json()
        error = token_req_json.get("error")

        # 토큰 요청에 실패했을 경우 오류를 반환
        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        # 액세스 토큰을 추출
        access_token = token_req_json.get("access_token")

        # 액세스 토큰을 사용하여 카카오에서 사용자 프로필을 요청
        profile_request = requests.get("https://kapi.kakao.com/v2/user/me",
                                       headers={"Authorization": f"Bearer {access_token}"})
        profile_data = profile_request.json()

        # 사용자 계정 정보를 추출
        kakao_account = profile_data.get("kakao_account")
        if not kakao_account or not kakao_account.get("email"):
            return Response({"error": "등록하려면 이메일이 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 카카오 ID와 이메일을 추출
        kakao_id = str(profile_data.get("id"))
        email = kakao_account.get("email")
        nickname = kakao_account["profile"]["nickname"]
        profile_image_url = kakao_account["profile"].get("profile_image_url")

        # 카카오 ID로부터 비밀번호를 생성하기 위한 해시를 생성
        hash_object = hashlib.sha256(kakao_id.encode())
        password_hash = hash_object.hexdigest()

        # 시스템 내 사용자를 생성하거나 기존 사용자를 가져옴
        try:
            user, created = User.objects.get_or_create(username=kakao_id,
                                                       defaults={'email': email, 'first_name': nickname,
                                                                 'password': password_hash})

            # 새로운 사용자가 생성되었다면 비밀번호를 설정 저장
            if created:
                user.set_password(password_hash)

            # 프로필 이미지 저장 (이미지 URL이 있으면 다운로드 후 저장)
            if profile_image_url:
                response = requests.get(profile_image_url)

                if response.status_code == 200:
                    # 이미지 파일을 저장 (파일명은 kakao_id로 설정)
                    image_name = f"{kakao_id}_profile_image.jpg"
                    user.images.save(image_name, ContentFile(response.content))

            # 정보 저장
            user.save()

            # 사용자를 로그인 시킵니다. settings.py 추가
            login(request, user)

            # JWT 토큰을 발급합니다.
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # 프론트엔드로 리다이렉트할 URL (프론트엔드 도메인)
            frontend_url = settings.FRONTEND_URL + '/profile/'  # 프로필 페이지로 리다이렉트

            # 리다이렉트 시, JWT 토큰을 쿠키에 설정 (HTTP-Only 쿠키로 저장)
            response = redirect(frontend_url)  # 프론트엔드 도메인으로 리다이렉트

            # 쿠키에 토큰 설정 (HTTPOnly=True로 보안을 강화)
            response.set_cookie('access_token', access_token,
                                httponly=True, samesite='Lax', secure=False)
            response.set_cookie('refresh_token', refresh_token,
                                httponly=True, samesite='Lax', secure=True)

            return response

        # 사용자 이름 충돌 시 오류를 반환합니다.
        except IntegrityError:
            return Response({"error": "해당 사용자 이름을 가진 사용자가 이미 있습니다."}, status=status.HTTP_400_BAD_REQUEST)


# 아이들 로그인
class LoginView(APIView):
    def post(self, request):

        # 요청 데이터에서 'username'과 'password'를 추출
        username = request.data.get("username")
        password = request.data.get("password")

        # Django의 인증 시스템을 사용하여 사용자를 인증
        user = authenticate(username=username, password=password)

        # 사용자명이 데이터베이스에 존재하는지 확인
        if not User.objects.filter(username=username).exists():
            # 사용자명이 데이터베이스에 없다면 오류 메시지와 함께 응답 반환
            return Response({"error": "존재하지 않는 아이디입니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 인증된 사용자가 없고, 즉 비밀번호가 틀렸다면 오류 메시지 반환
        if not user:
            return Response({"error": "패스워드가 틀렸습니다."}, status=status.HTTP_400_BAD_REQUEST)
                
        # 사용자를 세션에 로그인 처리
        login(request, user)

        # 인증된 사용자에 대한 정보를 시리얼라이즈하여 응답 데이터에 포함
        serializer = UserSerializer(user)
        res_data = serializer.data

        # 사용자를 위한 JWT 리프레시 토큰과 액세스 토큰을 발행
        refresh = RefreshToken.for_user(user)

        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # 쿠키에 토큰 설정 (HTTP-Only 쿠키로 저장)
        response = Response(res_data, status=status.HTTP_200_OK)
        response.set_cookie('access_token', access_token, httponly=True, samesite='Lax', secure=False)
        response.set_cookie('refresh_token', refresh_token, httponly=True, samesite='Lax', secure=False)

        return response


# 아이들 회원가입
class ChildrenPRCreate(APIView):
    # API 뷰에서 인증된 사용자만 접근을 허용
    permission_classes = [IsAuthenticated]

    def check_parent_logged_in(self, user):

        # 사용자의 인증 상태를 확인하여 로그인되지 않았을 경우 None을 반환하고 에러 메시지
        if not user.is_authenticated:
            return None, "로그인이 필요합니다."

        # 사용자가 부모인지 확인합니다. 부모의 'parents_id'가 None이면 부모
        if user.parents_id is None:
            return user, None  # 부모로 확인된 사용자 객체와 None을 반환
        else:
            return None, "부모님만 등록할 수 있습니다."  # 부모가 아닐 경우 None과 에러 메시지를 반환

    def post(self, request):

        # 요청을 보낸 사용자의 부모 로그인 상태를 확인
        parent_user, error_msg = self.check_parent_logged_in(request.user)
        if error_msg:
            # 부모 로그인 상태가 아니라면 에러 메시지와 함께 403 Forbidden 응답을 반환
            return Response({"error": error_msg}, status=status.HTTP_403_FORBIDDEN)

        # 회원가입의 유효성을 검사합니다. 유효하지 않을 경우 에러 메시지를 반환
        is_valid, err_msg = validate_signup(request.user, request.data)
        if not is_valid:
            return Response({"error": err_msg}, status=status.HTTP_400_BAD_REQUEST)

        # 요청 데이터에서 first_name, birthday를 가져옴
        first_name = request.data.get("first_name")
        birthday = request.data.get("birthday")

        if not first_name or not birthday:
            return Response({"error": "first_name 및 birthday 필드는 필수입니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 유효성 검사를 통과한 데이터로 새로운 사용자(자녀)를 생성 parents=parent_user 부모 사용자를 외래키로 설정
        user = User.objects.create_user(username=request.data.get("username"), password=request.data.get("password"),
                                        email=request.data.get("email"), parents=parent_user, first_name=first_name,
                                        birthday=birthday)
        
        # 프로필 이미지 파일이 있는지 확인하고 저장
        if 'profile_image' in request.FILES:
            user.images = request.FILES['profile_image']  # 이미지 파일을 user의 images 필드에 저장

        # 생성된 사용자를 저장
        user.save()

        # 생성된 사용자의 정보를 시리얼라이즈
        serializer = UserSerializer(user)
        res_data = serializer.data

        # 사용자를 위한 리프레시 토큰과 액세스 토큰 발행
        refresh = RefreshToken.for_user(user)
        res_data["tokens"] = {"access_token": str(
            refresh.access_token), "refresh_token": str(refresh)}

        # 성공적으로 생성된 사용자 정보와 토큰을 포함하여 응답 반환
        return Response(res_data, status=status.HTTP_201_CREATED)


# 아이들 조회, 수정, 삭제
class ChildrenPRView(APIView):
    # API 뷰에서 인증된 사용자만 접근을 허용
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # 파일과 데이터를 함께 처리

    # 특정 자녀의 정보를 조회 (자식의 토큰으로도 조회 가능)
    def get(self, request, pk):

        try:
            # 부모인 경우, 해당 자녀를 조회
            if request.user.parents_id is None:
                # 요청된 pk(자녀의 ID)와 부모 사용자를 기준으로 자녀 객체를 조회
                child = User.objects.get(pk=pk, parents=request.user)
            else:
                # 자식의 토큰으로 자신의 정보를 조회할 수 있게 처리
                if request.user.pk != pk:
                    return Response({"error": "자신의 정보만 조회할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)

                child = request.user
            
            # child 객체에서 부모 ID가 있는지 확인
            if child.parents_id:
                parent = child.parents  # 부모 객체를 가져옴
            else:
                parent = None  # 부모 객체가 없으면 None으로 설정

            child_serializer = UserSerializer(child)  # 자녀 객체를 시리얼라이즈
            
            # parent 객체가 존재하는지 확인
            if parent:
                parent_serializer = UserSerializer(parent)  # 부모 객체 직렬화
            else:
                parent_serializer = None  # 부모 객체가 없으면 None으로 설정

            # 부모와 자녀 정보를 함께 반환
            response_data = {"child": child_serializer.data, "parent": parent_serializer.data}

            # serializer = UserSerializer(child)  조회된 자녀 객체를 시리얼라이즈
            return Response(response_data)  # 시리얼라이즈된 데이터 응답 반환

        except User.DoesNotExist:

            return Response({"error": "아이들을 찾을수가 없습니다."},
                            status=status.HTTP_404_NOT_FOUND)  # 자녀 객체가 존재하지 않을 경우 오류 메시지를 반환


    # 자녀의 정보를 수정
    def put(self, request, pk):
        try:
            child = User.objects.get(pk=pk, parents=request.user)
            serializer = UserSerializer(child, data=request.data, partial=True)
            if serializer.is_valid():
                if 'password' in request.data:
                    is_valid, error_msg = custom_validate_password(request.data['password'])
                    if not is_valid:
                        return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)
                    
                # 요청 데이터에 비밀번호가 포함되어 있으면, 비밀번호를 업데이트
                if 'password' in request.data:
                    child.set_password(request.data['password'])
                    
                # 파일 업로드 처리
                profile_image = request.FILES.get('profile_image')
                if profile_image:
                    child.images.save(profile_image.name, profile_image)

                # serializer.save()  # 자녀 정보 저장
                #1015 s
                if 'firstname' in request.data:
                    # 요청 데이터에 first_name이 있는 경우, first_name 수정
                    child.first_name = request.data['firstname']
                #1015 e


                if 'birthday' in request.data:
                    child.birthday = request.data['birthday']

                # 격려 메시지가 포함되어 있으면 자녀의 encouragement 필드를 업데이트
                if 'encouragement' in request.data:
                    child.encouragement = request.data['encouragement']

                # 자녀 정보 저장
                child.save()

                return Response(serializer.data)  # 수정된 자녀 정보 반환

            # 시리얼라이즈 데이터가 유효하지 않을 경우, 오류 메시지
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({"error": "아이들을 찾을수가 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    # 특정 자녀의 정보 삭제
    def delete(self, request, pk):
        try:
            child = User.objects.get(pk=pk, parents=request.user)
            child.delete()
            return Response({"success": "자녀가 성공적으로 삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response({"error": "아이들을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)


# 부모 수정, 조회
class AccountsView(APIView):
    permission_classes = [IsAuthenticated]

    # 프로필 조회:
    def get(self, request):

        username = request.user.username

        try:
            # username을 가진 사용자(부모)를 찾기
            parent = User.objects.get(username=username)
            if parent.parents_id is not None:
                # 부모의 parents_id가 None이 아니면 오류 응답 반환
                return Response({"error": "접근 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

            # 요청자가 조회하려는 사용자와 동일 체크
            if request.user != parent:
                return Response({"error": "접근 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

            # 부모의 정보를 시리얼라이즈
            parent_serializer = UserSerializer(parent)

            # 부모 사용자에 연결된 자녀들 목록을 조회 시리얼라이즈
            children = User.objects.filter(parents=parent)
            children_serializer = UserSerializer(children, many=True)

            # 부모와 자녀들의 정보를 함께 반환
            response_data = {
                "parent": parent_serializer.data,
                "children": children_serializer.data
            }
            return Response(response_data)

        except User.DoesNotExist:
            # 사용자가 데이터베이스에 없으면 오류 메시지 반환
            return Response({"error": "부모님을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)


# 아이들 로그아웃
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # 쿠키로 refreshtoken 가져오기
            refresh_token = request.COOKIES.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                # 블랙리스트 추가
                token.blacklist()

            response = Response({"message": "로그아웃 되었습니다."}, status = status.HTTP_200_OK)
            # 쿠키에 저장된 토큰들 삭제
            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')
            response.delete_cookie('sessionid')
            return response
        except TokenError:
            return Response({"error": "유효하지 않은 토큰입니다."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"로그아웃 중 오류가 발생했습니다. {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
