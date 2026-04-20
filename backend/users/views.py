from django.contrib.auth import authenticate, get_user_model
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Profile, UserEducation, UserExperience, UserSkill
from .serializers import (
    LoginSerializer,
    ProfileSerializer,
    RegisterSerializer,
    UserEducationSerializer,
    UserExperienceSerializer,
    UserSerializer,
    UserSkillSerializer,
)

User = get_user_model()


# ── Auth helpers ──────────────────────────────────────────────────────────────

def _token_response(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": UserSerializer(user).data,
    }


# ── Auth views ────────────────────────────────────────────────────────────────

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(_token_response(user), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if not user:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(_token_response(user))


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


# ── Profile ───────────────────────────────────────────────────────────────────

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_profile(self, user):
        profile, _ = Profile.objects.get_or_create(user=user)
        return profile

    def get(self, request):
        return Response(ProfileSerializer(self._get_profile(request.user)).data)

    def put(self, request):
        profile = self._get_profile(request.user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ── Skills ────────────────────────────────────────────────────────────────────

class UserSkillListCreateView(generics.ListCreateAPIView):
    serializer_class = UserSkillSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserSkill.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserSkillDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSkillSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserSkill.objects.filter(user=self.request.user)


# ── Education ─────────────────────────────────────────────────────────────────

class UserEducationListCreateView(generics.ListCreateAPIView):
    serializer_class = UserEducationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserEducation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserEducationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserEducationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserEducation.objects.filter(user=self.request.user)


# ── Experience ────────────────────────────────────────────────────────────────

class UserExperienceListCreateView(generics.ListCreateAPIView):
    serializer_class = UserExperienceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserExperience.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserExperienceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserExperienceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserExperience.objects.filter(user=self.request.user)
