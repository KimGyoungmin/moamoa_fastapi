from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user
from accounts.models import User
from django.contrib.auth import get_user



# index
def Index(request):
    return render(request, 'webs/index.html')

# 키즈 로그인 페이지
def Children_view(request):
    return render(request, 'webs/children.html')


# 부모 프로필
def Profile_view(request):
    return render(request, 'webs/profile.html')

def Create_view(request):
    # GET 요청일 때만 로그인 여부를 확인합니다.
    if request.method == 'GET':
        # 사용자가 로그인하지 않은 경우
        if not request.user.is_authenticated:
            # 로그인 페이지로 리다이렉트
            return redirect('/')
    
    # 로그인된 사용자는 페이지를 볼 수 있습니다.
    return render(request, 'webs/children_create.html')

# 키즈 프로필
def ChildrenProfile_view(request, child_pk):
    # 키즈 정보 가져오기
    child = get_object_or_404(User, pk=child_pk)
    # 템플릿으로 child 객체 전달
    return render(request, 'webs/children_profile.html', {
        'child': child,
        })

# AI 채팅
def Chatbot_view(request, child_pk):
    user = get_object_or_404(User, pk=child_pk)
    current_user = get_user(request)
    
    user_image = request.build_absolute_uri(
                        user.images.url)
    
    context = {
        'user': user,
        'user_image': user_image,
        'child_pk': child_pk,
    }
    return render(request, 'webs/chatbot.html', context)

# 부모 프로필
def ProfileDetail_view(request, pk):
    return render(request, 'webs/profile_detail.html')

# Access-error 페이지
def access_error_view(request):
    # 현재 세션에 로그인된 사용자를 가져옴
    logged_in_user = get_user(request)
    return render(request, 'webs/access_error.html', {'logged_in_user': logged_in_user})  # 에러 페이지 렌더링

