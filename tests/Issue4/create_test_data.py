"""
==============================================================================
SCRIPT DE INICIALIZACIÓN DE DATOS
==============================================================================
Crea la siguiente estructura:
- 3 Tutores (Tutor 1, Tutor 2, Tutor 3)
- Cada Tutor crea 3 Estudiantes (Total 9 Estudiantes)
- Cada Tutor crea 3 Cursos: 1 demo, 1 level, 1 custom (Total 9 Cursos)

INSTRUCCIONES:
1. Asegúrate de haber aplicado todas las migraciones (Issue #1 y #4).
2. Ajusta 'RulingoClub.settings' y 'accounts.models' si tu proyecto usa nombres diferentes.
3. Ejecutar: python create_test_data.py
==============================================================================
"""

import os
import sys
import django
from django.db import transaction

# Configurar Django (Ajusta 'RulingoClub.settings' al nombre de tu proyecto)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RulingoClub.settings')
django.setup()

# Importar modelos (Ajusta 'accounts.models' al nombre de tu app)
from django.contrib.auth.models import User
from accounts.models import Tutor, Student, Course

# --- CONSTANTES DE CREACIÓN ---
TUTOR_COUNT = 3
STUDENT_PER_TUTOR = 3
COURSE_TYPES = ['demo', 'level', 'custom']
# ------------------------------

def print_header(text):
    """Imprime un header visual"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def cleanup():
    """Elimina todos los datos de prueba."""
    Course.objects.all().delete()
    Student.objects.all().delete()
    Tutor.objects.all().delete()
    # No eliminamos el Superuser si existe
    User.objects.filter(is_superuser=False).delete()


# ==============================================================================
# FUNCIONES DE CREACIÓN ATÓMICA
# ==============================================================================

def create_tutor(i):
    """Crea un User y un Tutor asociado."""
    try:
        username = f"tutor{i}"
        user = User.objects.create_user(
            username=username,
            email=f"{username}@mail.com",
            password='password123',
            first_name=f"Nombre{i}",
            last_name=f"Tutor{i}"
        )
        tutor = Tutor.objects.create(
            user=user,
            bio=f"Soy Tutor {i} y me especializo en A1 y A2.",
            experience_years=i * 2
        )
        print(f"  > Creado Tutor: {tutor.user.get_full_name()} ({username})")
        return tutor
    except Exception as e:
        print(f"  ❌ ERROR al crear Tutor {i}: {e}")
        return None

def create_student(tutor, i, j):
    """Crea un User y un Student asociado, asignado al Tutor."""
    try:
        username = f"std{i}_t{j}" # Ejemplo: std1_t1 (Estudiante 1 del Tutor 1)
        user = User.objects.create_user(
            username=username,
            email=f"{username}@mail.com",
            password='password123',
            first_name=f"Estudiante{i}",
            last_name=f"Apellido{i}"
        )
        student = Student.objects.create(
            user=user,
            created_by=tutor
        )
        print(f"    - Creado Estudiante: {student.user.get_full_name()} (Asignado a Tutor {j})")
        return student
    except Exception as e:
        print(f"  ❌ ERROR al crear Estudiante {i} para Tutor {j}: {e}")
        return None

def create_course(tutor, course_type, i):
    """Crea un Curso asociado al Tutor con el tipo especificado."""
    try:
        course_title = f"Curso {course_type.capitalize()} - {tutor.user.last_name}"
        course = Course.objects.create(
            tutor=tutor,
            title=course_title,
            description=f"Descripción para el curso de tipo {course_type} de {tutor.user.last_name}.",
            course_type=course_type
        )
        print(f"    - Creado Curso: {course_title} (Tipo: {course_type})")
        return course
    except Exception as e:
        print(f"  ❌ ERROR al crear Curso {course_type} para Tutor {tutor.user.last_name}: {e}")
        return None


# ==============================================================================
# EJECUCIÓN PRINCIPAL
# ==============================================================================

@transaction.atomic
def run_creation_script():
    """Ejecuta toda la lógica de creación de datos dentro de una transacción."""
    
    # 1. Limpieza de datos
    print_header("LIMPIANDO DATOS ANTERIORES...")
    cleanup()
    print("Limpieza completada.")
    
    print_header("INICIANDO CREACIÓN DE DATOS DE PRUEBA")
    
    created_tutors = []
    
    # Bucle principal para la creación de 3 Tutores
    for i in range(1, TUTOR_COUNT + 1):
        print(f"\n--- Creando Tutor #{i} ---")
        tutor = create_tutor(i)
        
        if not tutor:
            continue
            
        created_tutors.append(tutor)
        
        # 2. Creación de 3 Estudiantes por Tutor
        for j in range(1, STUDENT_PER_TUTOR + 1):
            create_student(tutor, j, i)
            
        # 3. Creación de 3 Cursos por Tutor
        for course_type in COURSE_TYPES:
            create_course(tutor, course_type, i)
            
    # Resumen final
    print_header("RESUMEN DE DATOS CREADOS")
    print(f"  TUTORES CREADOS:    {Tutor.objects.count()}")
    print(f"  ESTUDIANTES CREADOS: {Student.objects.count()}")
    print(f"  CURSOS CREADOS:     {Course.objects.count()}")
    print("==================================================================")
    
    if Tutor.objects.count() == 3 and Student.objects.count() == 9 and Course.objects.count() == 9:
        print("🎉 ¡INICIALIZACIÓN EXITOSA! Todos los datos fueron creados correctamente.")
    else:
        print("🛑 ATENCIÓN: Hubo un error. El conteo final de objetos no coincide con el objetivo.")

if __name__ == '__main__':
    run_creation_script()
