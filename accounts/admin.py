# ==============================================================================
# ISSUE #2: CONFIGURACIÓN DEL ADMIN
# ==============================================================================
# Interfaces de administración para Tutor y Student con permisos por rol
# ==============================================================================

from django.contrib import admin
from django.contrib.auth.models import User
from django.db import transaction
from .models import Tutor, Student
from .forms import StudentCreationForm, StudentChangeForm
from django.core.exceptions import ValidationError


# ==============================================================================
# ADMIN: TUTOR
# ==============================================================================

@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Tutor.
    
    Permisos:
    - Superusuario: ve todos los tutores
    - Tutor: solo ve su propio perfil
    
    Funcionalidad:
    - Tutores pueden editar su bio y experiencia
    - Campo user es readonly (no se puede cambiar)
    """
    
    list_display = [
        'get_username',
        'get_full_name',
        'get_bio_truncated',
        'experience_years',
        'created_at'
    ]
    
    search_fields = [
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email'
    ]
    
    list_filter = ['experience_years', 'created_at']
    
    def get_readonly_fields(self, request, obj=None):
        """
        user es readonly solo al EDITAR.
        Al crear, se puede seleccionar.
        """
        if obj:  # Editando un tutor existente
            return ['user', 'created_at']
        else:  # Creando un tutor nuevo
            return ['created_at']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filtrar usuarios disponibles (sin tutor asignado)."""
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(tutor__isnull=True,student__isnull=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    fields = ['user', 'bio', 'experience_years', 'created_at']
    
    def get_username(self, obj):
        """Mostrar username del User asociado."""
        return obj.user.username
    get_username.short_description = 'Usuario'
    get_username.admin_order_field = 'user__username'
    
    def get_full_name(self, obj):
        """Mostrar nombre completo."""
        return obj.user.get_full_name() or '-'
    get_full_name.short_description = 'Nombre completo'
    
    def get_bio_truncated(self, obj):
        """Mostrar bio truncada."""
        if obj.bio:
            return obj.bio[:50] + '...' if len(obj.bio) > 50 else obj.bio
        return '-'
    get_bio_truncated.short_description = 'Biografía'
    
    def get_queryset(self, request):
        """
        Filtrar queryset según el usuario:
        - Superusuario: ve todos los tutores
        - Tutor: solo ve su propio perfil
        """
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        
        # Si es tutor, solo ve su propio perfil
        return qs.filter(user=request.user)
    
    def has_add_permission(self, request):
        """
        Control de permisos para agregar tutores.
        Solo superusuario puede crear tutores desde aquí.
        """
        return request.user.is_superuser


# ==============================================================================
# ADMIN: STUDENT
# ==============================================================================

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Student.
    
    Permisos:
    - Superusuario: ve y gestiona todos los estudiantes
    - Tutor: solo ve estudiantes que él creó
    
    Funcionalidad:
    - Crear estudiante = crear User + Student en un paso
    - Auto-asignar created_by al tutor logueado
    - Tutores NO pueden eliminar estudiantes
    """
    
    list_display = [
        'get_username',
        'get_full_name',
        'get_email',
        'created_by',
        'created_at'
    ]
    
    search_fields = [
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email'
    ]
    
    list_filter = ['created_by', 'created_at']
    
    readonly_fields = ['created_at']
    
    def get_username(self, obj):
        """Mostrar username del User asociado."""
        return obj.user.username
    get_username.short_description = 'Usuario'
    get_username.admin_order_field = 'user__username'
    
    def get_full_name(self, obj):
        """Mostrar nombre completo."""
        return obj.user.get_full_name() or '-'
    get_full_name.short_description = 'Nombre completo'
    
    def get_email(self, obj):
        """Mostrar email del User asociado."""
        return obj.user.email
    get_email.short_description = 'Email'
    get_email.admin_order_field = 'user__email'
    
    def get_queryset(self, request):
        """
        Filtrar queryset según el usuario:
        - Superusuario: ve todos los estudiantes
        - Tutor: solo ve estudiantes creados por él
        """
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        
        # Si es tutor, solo ve sus estudiantes
        try:
            return qs.filter(created_by=request.user.tutor)
        except Tutor.DoesNotExist:
            # Si el user no tiene perfil de tutor, no ve nada
            return qs.none()

    def get_form(self, request, obj=None, **kwargs):
        """
        Retornar formulario correcto según si es creación o edición.
        
        - Crear: StudentCreationForm (con campos de User)
        - Editar: StudentChangeForm (campos limitados)
        
        NUEVO: Si es Superuser en modo creación, inyectar 'created_by'.
        """
        is_creation = obj is None
        form_class = StudentCreationForm if is_creation else StudentChangeForm
        
        # Lógica para inyectar 'created_by' al Superuser
        if is_creation and request.user.is_superuser:
            # Se crea una clase de formulario temporal que herede y añada el campo
            class SuperuserCreationForm(form_class):
                class Meta(form_class.Meta):
                    fields = list(form_class.Meta.fields) + ['created_by']
            
            kwargs['form'] = SuperuserCreationForm
        elif is_creation:
            # Si es Tutor, sigue usando el formulario sin created_by
            kwargs['form'] = StudentCreationForm
        else:
            # Edición
            kwargs['form'] = StudentChangeForm
        
        return super().get_form(request, obj, **kwargs)


    @transaction.atomic
    def save_model(self, request, obj, form, change):
        """
        Guardar datos del formulario para crear un estudiante.
        
        Al crear:
        1. Crear User con datos del formulario
        2. Crear Student vinculado al User
        3. Asignar created_by: Automático (Tutor) o Seleccionado (Superuser)
        
        Al editar:
        1. Actualizar datos del User
        2. created_by no se modifica
        """
        if not change:
            # CREAR NUEVO ESTUDIANTE
            
            # Crear el User
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name']
            )
            
            # Asignar el User al Student
            obj.user = user
            
            # Lógica de asignación de created_by
            if request.user.is_superuser:
                # Si es Superusuario, toma el Tutor seleccionado del formulario (dropdown)
                # El campo 'created_by' está disponible gracias a la modificación en get_form.
                if 'created_by' in form.cleaned_data:
                    obj.created_by = form.cleaned_data['created_by']
                else:
                    raise ValidationError("El Superusuario debe seleccionar un Tutor.")
            else:
                # Si es Tutor, auto-asignación
                try:
                    obj.created_by = request.user.tutor
                except Tutor.DoesNotExist:
                    raise ValidationError(
                        "Tu usuario no tiene un perfil de tutor asociado. "
                        "Contacta al administrador."
                    )
        else:
            # EDITAR ESTUDIANTE EXISTENTE
            
            # Actualizar datos del User
            user = obj.user
            user.first_name = form.cleaned_data.get('first_name', user.first_name)
            user.last_name = form.cleaned_data.get('last_name', user.last_name)
            user.email = form.cleaned_data.get('email', user.email)
            user.save()
        
        # Guardar el Student (ahora con created_by asignado)
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        """
        Campos de solo lectura según contexto.
        
        Al editar: created_by y created_at son readonly, 
        EXCEPTO si es Superusuario, quien SÍ puede modificar created_by.
        """
        readonly_fields = ['created_at']
        
        if obj:  # Editando
            # created_by es siempre de solo lectura al editar...
            if not request.user.is_superuser:
                # ... excepto si NO es superusuario
                readonly_fields.append('created_by')

        # Si el usuario es un Superusuario en modo edición, 'created_by' NO se añade a la lista
        # y por lo tanto es editable.
        return readonly_fields


# ==============================================================================
# FIN DE IMPLEMENTACIÓN - ISSUE #2
# ==============================================================================
