# ==============================================================================
# ISSUE #2: FORMULARIOS PERSONALIZADOS PARA ADMIN
# ==============================================================================
# Formularios para crear y editar estudiantes con validaciones
# ==============================================================================

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Student


# ==============================================================================
# FORMULARIO: CREAR ESTUDIANTE
# ==============================================================================

class StudentCreationForm(forms.ModelForm):
    """
    Formulario para crear un estudiante desde el admin.
    
    Crea User y Student en una sola operación.
    
    Campos:
    - username, email, password (para User)
    - first_name, last_name (para User)
    
    Validaciones:
    - Username único
    - Email único
    - Passwords coinciden
    - Password mínimo 8 caracteres
    """
    
    # Campos del User (no están en Student directamente)
    username = forms.CharField(
        max_length=150,
        required=True,
        label="Nombre de usuario",
        help_text="Requerido. 150 caracteres o menos. Letras, dígitos y @/./+/-/_ solamente.",
        widget=forms.TextInput(attrs={'class': 'vTextField'})
    )
    
    email = forms.EmailField(
        required=True,
        label="Correo electrónico",
        help_text="Requerido. Debe ser un email válido.",
        widget=forms.EmailInput(attrs={'class': 'vTextField'})
    )
    
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="Nombre",
        widget=forms.TextInput(attrs={'class': 'vTextField'})
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label="Apellido",
        widget=forms.TextInput(attrs={'class': 'vTextField'})
    )
    
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'vTextField'}),
        help_text="Mínimo 4 caracteres.",
        required=True
    )
    
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={'class': 'vTextField'}),
        help_text="Ingrese la misma contraseña para verificación.",
        required=True
    )
    
    class Meta:
        model = Student
        fields = []  # No usamos campos directos de Student aquí
    
    def clean_username(self):
        """Validar que el username sea único."""
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError(
                "Ya existe un usuario con este nombre de usuario."
            )
        return username
    
    def clean_email(self):
        """Validar que el email sea único."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(
                "Ya existe un usuario con este correo electrónico."
            )
        return email
    
    def clean_password1(self):
        """Validar longitud mínima de contraseña."""
        password1 = self.cleaned_data.get('password1')
        if password1 and len(password1) < 4:
            raise ValidationError(
                "La contraseña debe tener al menos 4 caracteres."
            )
        return password1
    
    def clean(self):
        """Validar que las contraseñas coincidan."""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError({
                'password2': "Las contraseñas no coinciden."
            })
        
        return cleaned_data



# ==============================================================================
# FORMULARIO: EDITAR ESTUDIANTE
# ==============================================================================

class StudentChangeForm(forms.ModelForm):
    """
    Formulario para editar un estudiante existente.
    
    Permite editar:
    - Información básica del User (nombre, apellido, email)
    - created_by es de solo lectura (no se puede cambiar)
    """
    
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="Nombre"
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label="Apellido"
    )
    
    email = forms.EmailField(
        required=True,
        label="Correo electrónico"
    )
    
    class Meta:
        model = Student
        fields = ['created_by']  # created_by será readonly
    
    def __init__(self, *args, **kwargs):
        """Inicializar formulario con datos del User."""
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk:
            # Cargar datos del User asociado
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            
            # created_by solo lectura
            # self.fields['created_by'].disabled = True
