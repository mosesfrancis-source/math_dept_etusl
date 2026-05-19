from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, StudentProfile, LecturerProfile, RegistrationPIN


class StudentRegistrationForm(UserCreationForm):
    registration_pin = forms.CharField(
        max_length=8, required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your PIN', 'class': 'form-control', 'style': 'text-transform:uppercase'}),
        label='Registration PIN',
    )
    first_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name  = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email      = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    student_id = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    year_of_study = forms.ChoiceField(
        choices=[(1,'Year 1'),(2,'Year 2'),(3,'Year 3'),(4,'Year 4'),(5,'Year 5')],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email',
                  'student_id', 'year_of_study', 'registration_pin',
                  'password1', 'password2']
        widgets = {'username': forms.TextInput(attrs={'class': 'form-control'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'

    def clean_registration_pin(self):
        pin = self.cleaned_data['registration_pin'].strip().upper()
        if not RegistrationPIN.objects.filter(pin=pin, role='student', is_used=False).exists():
            raise forms.ValidationError('Invalid or already-used PIN. Contact the admin.')
        return pin

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student'
        user.first_name = self.cleaned_data['first_name']
        user.last_name  = self.cleaned_data['last_name']
        user.email      = self.cleaned_data['email']
        if commit:
            user.save()
            StudentProfile.objects.create(
                user=user,
                student_id=self.cleaned_data['student_id'],
                year_of_study=self.cleaned_data['year_of_study'],
            )
            from django.utils import timezone
            pin_obj = RegistrationPIN.objects.get(
                pin=self.cleaned_data['registration_pin'], role='student'
            )
            pin_obj.is_used = True
            pin_obj.used_at = timezone.now()
            pin_obj.used_by = user
            pin_obj.save()
        return user


class LecturerRegistrationForm(UserCreationForm):
    registration_pin = forms.CharField(
        max_length=8, required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your PIN', 'class': 'form-control', 'style': 'text-transform:uppercase'}),
        label='Registration PIN',
    )
    first_name     = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name      = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email          = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    staff_id       = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    specialization = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email',
                  'staff_id', 'specialization', 'registration_pin',
                  'password1', 'password2']
        widgets = {'username': forms.TextInput(attrs={'class': 'form-control'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'

    def clean_registration_pin(self):
        pin = self.cleaned_data['registration_pin'].strip().upper()
        try:
            RegistrationPIN.objects.get(pin=pin, role__in=['lecturer', 'hod'], is_used=False)
        except RegistrationPIN.DoesNotExist:
            raise forms.ValidationError('Invalid or already-used PIN. Contact the admin.')
        return pin

    def save(self, commit=True):
        user = super().save(commit=False)
        pin_obj = RegistrationPIN.objects.get(
            pin=self.cleaned_data['registration_pin'], role__in=['lecturer', 'hod']
        )
        user.role = pin_obj.role  # 'lecturer' or 'hod'
        user.first_name = self.cleaned_data['first_name']
        user.last_name  = self.cleaned_data['last_name']
        user.email      = self.cleaned_data['email']
        if commit:
            user.save()
            LecturerProfile.objects.create(
                user=user,
                staff_id=self.cleaned_data['staff_id'],
                specialization=self.cleaned_data.get('specialization', ''),
                is_hod=(pin_obj.role == 'hod'),
            )
            from django.utils import timezone
            pin_obj.is_used = True
            pin_obj.used_at = timezone.now()
            pin_obj.used_by = user
            pin_obj.save()
        return user
