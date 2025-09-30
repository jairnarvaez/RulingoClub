# ==============================================================================
# ISSUE #1: CONFIGURAR MODELOS DE USUARIO
# ==============================================================================
# Implementación de modelos Tutor y Student como extensiones de User
# Con validación de rol único y relaciones establecidas
# ==============================================================================

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


# ==============================================================================
# MODELO: TUTOR
# ==============================================================================
# ✅ Criterio: Existe modelo Tutor en models.py
# ✅ Objetivo: Extender User para tutores con información adicional
# ==============================================================================

class Tutor(models.Model):
    """
    Perfil de Tutor vinculado a un User de Django.
    
    Un tutor puede:
    - Crear y gestionar cursos
    - Crear y gestionar estudiantes
    - Ver progreso de sus estudiantes
    
    Restricción: Un User solo puede ser Tutor O Student, no ambos.
    """
    
    # ✅ Criterio: Tiene relación OneToOneField con User (on_delete=CASCADE)
    # ✅ Concepto: Relación 1:1 - cada User tiene máximo 1 perfil de Tutor
    # ✅ on_delete=CASCADE: Si se borra User, se borra Tutor automáticamente
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name="Usuario",
        help_text="Usuario de Django asociado a este tutor"
    )
    
    # ✅ Criterio: Tiene campo bio (TextField, blank=True)
    # ✅ Objetivo: Información opcional sobre el tutor
    bio = models.TextField(
        blank=True,
        verbose_name="Biografía",
        help_text="Información sobre el tutor y su experiencia"
    )
    
    # ✅ Criterio: Tiene campo experience_years (PositiveIntegerField, default=0)
    # ✅ Objetivo: Años de experiencia enseñando
    experience_years = models.PositiveIntegerField(
        default=0,
        verbose_name="Años de experiencia",
        help_text="Años de experiencia enseñando ruso"
    )
    
    # ✅ Criterio: Tiene campo created_at (DateTimeField, auto_now_add=True)
    # ✅ auto_now_add: Se establece SOLO al crear, nunca se modifica
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    
    # ✅ Criterio: Tiene class Meta con verbose_name en español
    class Meta:
        verbose_name = "Tutor"
        verbose_name_plural = "Tutores"
        ordering = ['-created_at']  # Más recientes primero
    
    # ✅ Criterio: Tiene método __str__() que retorna nombre completo
    def __str__(self):
        """
        Representación en string del tutor.
        Muestra: "Nombre Apellido (Tutor)"
        """
        full_name = self.user.get_full_name() or self.user.username
        return f"{full_name} (Tutor)"
    
    # ✅ Criterio: Método clean() valida que el User no tenga el otro rol
    # ✅ Validación: Si User ya es Student, no puede ser Tutor
    def clean(self):
        """
        Validación personalizada antes de guardar.
        
        REGLA DE NEGOCIO CRÍTICA:
        Un usuario NO puede ser Tutor y Student simultáneamente.
        
        Valida:
        - Si el User asociado ya tiene un perfil de Student
        - Si es así, lanza ValidationError con mensaje claro
        """
        # Llamar al clean() del padre primero
        if self.pk:
            super().clean()
        
        # ✅ Validación de rol único
        # Verificar si este User ya es Student
        if hasattr(self.user, 'student'):
            raise ValidationError(
                "Este usuario ya es Estudiante. Un usuario no puede tener ambos roles."
            )
    
    def save(self, *args, **kwargs):
        """
        Override de save para asegurar validación.
        
        IMPORTANTE: Django NO llama clean() automáticamente en save().
        Lo llamamos manualmente para garantizar validación.
        """
        # Ejecutar validaciones antes de guardar
        self.full_clean()
        # Guardar normalmente
        super().save(*args, **kwargs)


# ==============================================================================
# MODELO: STUDENT
# ==============================================================================
# ✅ Criterio: Existe modelo Student en models.py
# ✅ Objetivo: Extender User para estudiantes con tracking de quién los creó
# ==============================================================================

class Student(models.Model):
    """
    Perfil de Estudiante vinculado a un User de Django.
    
    Un estudiante puede:
    - Acceder a cursos en los que está matriculado
    - Realizar actividades/juegos
    - Ver su progreso y posición en leaderboard
    
    Características:
    - Cada estudiante es creado por un Tutor específico
    - Un User solo puede ser Student O Tutor, no ambos
    - No tienen acceso al panel de administración
    """
    
    # ✅ Criterio: Tiene relación OneToOneField con User (on_delete=CASCADE)
    # ✅ Concepto: Relación 1:1 - cada User tiene máximo 1 perfil de Student
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name="Usuario",
        help_text="Usuario de Django asociado a este estudiante"
    )
    
    # ✅ Criterio: Tiene campo created_by (ForeignKey a Tutor)
    # ✅ Concepto: Relación 1:N - un Tutor puede crear muchos Students
    # ✅ on_delete=PROTECT: NO permite borrar Tutor si tiene estudiantes
    # ✅ related_name='students': Permite hacer tutor.students.all()
    created_by = models.ForeignKey(
        Tutor,
        on_delete=models.PROTECT,
        related_name='students',
        verbose_name="Creado por",
        help_text="Tutor que creó este estudiante"
    )
    
    # ✅ Criterio: Tiene campo created_at (DateTimeField, auto_now_add=True)
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    
    # ✅ Criterio: Tiene class Meta con verbose_name en español
    class Meta:
        verbose_name = "Estudiante"
        verbose_name_plural = "Estudiantes"
        ordering = ['-created_at']  # Más recientes primero
    
    # ✅ Criterio: Tiene método __str__() que retorna nombre completo
    def __str__(self):
        """
        Representación en string del estudiante.
        Muestra: "Nombre Apellido (Estudiante)"
        """
        full_name = self.user.get_full_name() or self.user.username
        return f"{full_name} (Estudiante)"
    
    # ✅ Criterio: Método clean() valida que el User no tenga el otro rol
    # ✅ Validación: Si User ya es Tutor, no puede ser Student
    def clean(self):
        """
        Validación personalizada antes de guardar.
        
        REGLA DE NEGOCIO CRÍTICA:
        Un usuario NO puede ser Student y Tutor simultáneamente.
        
        Valida:
        - Si el User asociado ya tiene un perfil de Tutor
        - Si es así, lanza ValidationError con mensaje claro
        """
        # Llamar al clean() del padre primero
        super().clean()
        
        # ✅ Validación de rol único
        # Verificar si este User ya es Tutor
        if hasattr(self, 'user') and self.user: 
            if hasattr(self.user, 'tutor'):
                raise ValidationError(
                    "Este usuario ya es Tutor. Un usuario no puede tener ambos roles."
                )
        
    def save(self, *args, **kwargs):
        """
        Override de save para asegurar validación.
        
        IMPORTANTE: Django NO llama clean() automáticamente en save().
        Lo llamamos manualmente para garantizar validación.
        """
        # Ejecutar validaciones antes de guardar
        if self.pk:
            self.full_clean()
        # Guardar normalmente
        super().save(*args, **kwargs)


# ==============================================================================
# ISSUE #4: IMPLEMENTAR MODELO COURSE
# ==============================================================================

# CHOICES para el campo course_type
COURSE_TYPE_CHOICES = [
    ('demo', 'Demo'),
    ('level', 'Por Nivel'),
    ('custom', 'Personalizado'),
]

class Course(models.Model):
    """
    Modelo para representar cursos de ruso en la plataforma.
    
    Un curso tiene un tipo (demo, nivel, personalizado) y está 
    vinculado a un Tutor específico.
    """

    # ✅ Campo tutor (ForeignKey a Tutor, on_delete=CASCADE, related_name='courses')
    tutor = models.ForeignKey(
        Tutor,
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name="Tutor",
        help_text="Tutor dueño y creador de este curso."
    )
    
    # ✅ Campo title (CharField, max_length=200, required)
    title = models.CharField(
        blank=False,
        max_length=200,
        verbose_name="Título del Curso"
    )
    
    # ✅ Campo description (TextField, required)
    description = models.TextField(
        blank=False,
        verbose_name="Descripción Detallada"
    )
    
    # ✅ Campo course_type (CharField con CHOICES, default='level')
    course_type = models.CharField(
        max_length=20,
        choices=COURSE_TYPE_CHOICES,
        default='level',
        verbose_name="Tipo de Curso",
        help_text="Demo, Por Nivel o Personalizado."
    )
    
    # ✅ Campo created_at (DateTimeField, auto_now_add=True)
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    
    # ✅ Campo updated_at (DateTimeField, auto_now=True)
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Modificación"
    )

    # ✅ Meta options
    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        ordering = ['-created_at']

    # ✅ Método __str__()
    def __str__(self):
        """
        Retorna: "{title} ({course_type}) - {tutor}"
        """
        return f"{self.title} ({self.course_type}) - {self.tutor}"
    
    # ✅ Método is_demo()
    def is_demo(self):
        """Retorna True si el curso es de tipo Demo."""
        return self.course_type == 'demo'
    
    # ✅ Método is_level()
    def is_level(self):
        """Retorna True si el curso es de tipo Por Nivel."""
        return self.course_type == 'level'
        
    # ✅ Método is_custom()
    def is_custom(self):
        """Retorna True si el curso es de tipo Personalizado."""
        return self.course_type == 'custom'


# ==============================================================================
# FIN DE IMPLEMENTACIÓN - ISSUE #1 Y #4
# ==============================================================================


