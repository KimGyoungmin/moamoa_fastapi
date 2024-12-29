from rest_framework_simplejwt.authentication import JWTAuthentication


class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # 쿠키에서 access_token을 가져옴
        access_token = request.COOKIES.get('access_token')
        if access_token is None:
            return None  # 쿠키에 토큰이 없으면 인증하지 않음

        # 기본 JWT 인증 로직 (SimpleJWT의 토큰 검증)
        validated_token = self.get_validated_token(access_token)
        user = self.get_user(validated_token)
        return (user, validated_token)
