# ==============================================================================
# ISSUE #2: CONFIGURACIÓN DEL ADMIN
# ==============================================================================
# Interfaces de administración para Tutor y Student con permisos por rol
# ==============================================================================

from django.contrib import admin
from django.contrib.auth.models import User
from django.db import transaction
from .models import Tutor, Student, Enrollment
from .forms import StudentCreationForm, StudentChangeForm
from django.core.exceptions import ValidationError
from .models import Tutor, Student, Course, COURSE_TYPE_CHOICES
from django.forms.widgets import RadioSelect
from django.db.models import Q 
from django.contrib import messages 
from django.utils.html import format_html 

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



# ==============================================================================
# ISSUE #5: CONFIGURACIÓN ADMIN PARA CURSOS (CourseAdmin)
# ==============================================================================


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Course.
    Implementa permisos basados en rol, campos de solo lectura dinámicos
    y auto-asignación del tutor creador.
    """
    
    # ----------------------------------------------------------------------
    # 1. CONFIGURACIÓN BÁSICA
    # ----------------------------------------------------------------------

    # ✅ list_display: Tutor, título, descripción truncada, tipo, fechas
    list_display = [
        'tutor',
        'title',
        'get_description_truncated',
        'get_course_type_display',
        'created_at',
        'updated_at'
    ]
    
    # ✅ search_fields: title, description
    search_fields = ['title', 'description']
    
    # ✅ list_filter: course_type, created_at, tutor
    list_filter = ['course_type', 'created_at', 'tutor']
    
    # ✅ ordering: ['-created_at'] (más recientes primero)
    ordering = ['-created_at']

    # Método helper para truncar descripción en list_display
    def get_description_truncated(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    get_description_truncated.short_description = "Descripción"
    
    # ----------------------------------------------------------------------
    # 2. PERMISOS Y ACCESO (OVERRIDES)
    # ----------------------------------------------------------------------

    # 1. Override get_queryset()
    def get_queryset(self, request):
        """
        ✅ Override get_queryset(): superusuario ve todos, tutor solo sus cursos.
       
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # Ver todos
        
        # Filtrar solo por cursos del tutor logueado
        try:
            return qs.filter(tutor__user=request.user)
        except Tutor.DoesNotExist:
            # Si el user no es Superuser ni Tutor, no ve nada
            return qs.none()

    # 2. Override save_model()
    @transaction.atomic
    def save_model(self, request, obj, form, change):
        """
        ✅ Override save_model(): auto-asignar tutor al crear (si no es superusuario).
       
        """
        if not change:
            # Si es creación
            if not request.user.is_superuser:
                # Tutor: Auto-asignar el tutor logueado
                try:
                    obj.tutor = request.user.tutor
                except Tutor.DoesNotExist:
                    raise ValidationError("Tu usuario debe tener un perfil de Tutor para crear cursos.")
            # Si es Superusuario, el campo 'tutor' viene del formulario y se usa directamente.
            
            # Nota: Los campos de auditoría (created_at, updated_at) se llenan automáticamente.

        super().save_model(request, obj, form, change) # Guardar

    # 3. Override get_readonly_fields() (REVISADO)
    def get_readonly_fields(self, request, obj=None):
        """
        ✅ Override get_readonly_fields(): Define campos de solo lectura dinámicamente.
        
        - Creados/Actualizados: Siempre readonly.
        - course_type: Siempre readonly al editar (para ambos roles).
        - tutor: Readonly solo para Tutores.
        """
        
        readonly_list = ['created_at', 'updated_at'] # Siempre readonly
        
        if obj: # Editando un objeto existente
            
            # MODIFICACIÓN SOLICITADA: course_type es readonly para TODOS al editar
            readonly_list.append('course_type')
            readonly_list.append('tutor')
        
        return readonly_list
        
    # 4. Override formfield_for_choice_field()
    def formfield_for_choice_field(self, db_field, request, **kwargs):
        """
        ✅ course_type con widget Radio Buttons (mejor UX para 3 opciones).
       
        """
        if db_field.name == 'course_type':
            kwargs['widget'] = RadioSelect()
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    # 5. has_delete_permission()
    # ✅ Eliminación permitida sin restricciones (no se requiere override, Django lo permite por defecto)
    pass # Dejamos la implementación por defecto de Django, que es True para admins.

    # ----------------------------------------------------------------------
    # 3. CAMPOS DEL FORMULARIO (FIELDSETS/FIELDS)
    # ----------------------------------------------------------------------

    # Definir campos visibles según el rol (Controlado automáticamente por readonly y save_model)
    # El uso de fieldsets asegura la visibilidad y orden.
    
    def get_fieldsets(self, request, obj=None):
        """Define los campos visibles en los formularios de creación/edición."""
        
        if request.user.is_superuser:
            # Superusuario: puede ver y editar todos los campos (tutor, title, description, course_type)
            fields = ['tutor', 'title', 'description', 'course_type', 'created_at', 'updated_at']
        else:
            # Tutor: solo title, description, course_type al crear. tutor se auto-asigna.
            # Al editar, solo title y description son editables (controlado por get_readonly_fields)
            fields = ['title', 'description', 'course_type', 'created_at', 'updated_at']

        return (
            (None, {'fields': fields}),
        )

# ==============================================================================
# FIN DE IMPLEMENTACIÓN - ISSUE #5
# ==============================================================================



# ==============================================================================
# ADMIN: ENROLLMENT (Issue #6)
# ==============================================================================

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Enrollment.
    Implementa permisos para asegurar que los tutores solo matriculen
    a sus estudiantes en sus propios cursos.
    """

    # 1. CONFIGURACIÓN BÁSICA
    list_display = [
        'student',
        'course',
        'get_course_tutor', # Helper
        'status',
        'enrolled_at',
        'is_student_owned_by_tutor',
    ]
    list_filter = ['status', 'course', 'enrolled_at']
    search_fields = ['student__user__username', 'course__title']
    readonly_fields = ['enrolled_at', 'completed_at', 'updated_at']

    fieldsets = (
        ('Información de Matrícula', {
            'fields': (('student', 'course'), 'status',), 
        }),
        ('Fechas de Registro', {
            'fields': ('enrolled_at', 'completed_at', 'updated_at'),
         
        }),
    )
    
    def get_course_tutor(self, obj):
        return obj.course.tutor.user.get_full_name()
    get_course_tutor.short_description = "Tutor del Curso"
    
    # 2. PERMISOS Y ACCESO (OVERRIDES)
    
    # Override 1: get_queryset()
    def get_queryset(self, request):
        """✅ Superusuario ve todas, Tutor solo las de SUS cursos."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  
        
        # Tutor: Filtrar solo matrículas de sus propios cursos
        try:
            return qs.filter(course__tutor__user=request.user)
        except Tutor.DoesNotExist:
            return qs.none() 

    # Override 2: formfield_for_foreignkey()
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """✅ Filtra dropdowns: Tutor solo ve sus cursos y sus estudiantes."""
        if request.user.is_superuser:
            return super().formfield_for_foreignkey(db_field, request, **kwargs)

        try:
            tutor = request.user.tutor
        except Tutor.DoesNotExist:
            # Si no es tutor, no debe ver opciones
            kwargs['queryset'] = db_field.related_model.objects.none()
            return super().formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == "course":
            kwargs['queryset'] = Course.objects.filter(tutor=tutor)
        
        if db_field.name == "student":
            kwargs['queryset'] = Student.objects.filter(created_by=tutor)
            
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Override 3: get_readonly_fields()
    def get_readonly_fields(self, request, obj=None):
        """✅ Tutor NO puede editar status."""
        readonly = super().get_readonly_fields(request, obj)
        
        if obj and not request.user.is_superuser:
            readonly.append('status')
            
        return readonly

    # Override 4: save_model() para validaciones de negocio
    @transaction.atomic
    def save_model(self, request, obj, form, change):
        """✅ Valida que el tutor solo use sus cursos y sus estudiantes."""
        if not request.user.is_superuser:
            tutor = request.user.tutor
            course = form.cleaned_data['course']
            student = form.cleaned_data['student']
            
            # Validación 1: Curso pertenece al tutor
            if course.tutor != tutor:
                messages.error(request, 'Error de Validación: Solo puedes matricular estudiantes en TUS cursos.')
                raise ValidationError("Intento de matricular en curso de otro tutor.")
                
            # Validación 2: Estudiante fue creado por el tutor
            if student.created_by != tutor:
                messages.error(request, 'Error de Validación: Solo puedes matricular estudiantes que TÚ creaste.')
                raise ValidationError("Intento de matricular estudiante creado por otro tutor.")
        
        super().save_model(request, obj, form, change)

    def is_student_owned_by_tutor(self, obj):
            """
            Muestra una marca si el estudiante aún pertenece al tutor del curso.
            Esto es solo para fines de auditoría del Superusuario.
            """
            course_tutor = obj.course.tutor
            student_creator = obj.student.created_by
            
            if course_tutor == student_creator:
                return format_html('<span style="color: green;">✅ Propiedad OK</span>')
            else:
                return format_html('<span style="color: orange; font-weight: bold;">⚠️ Propiedad Transferida</span>')
            
    is_student_owned_by_tutor.short_description = "Coherencia Tutor/Estudiante"
    is_student_owned_by_tutor.admin_order_field = 'student__created_by'
