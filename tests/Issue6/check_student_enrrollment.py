"""
==============================================================================
SCRIPT DE INSPECCIÓN DE MATRÍCULAS POR ESTUDIANTE (Issue #6)
==============================================================================
1. Lista todos los estudiantes con su ID y nombre.
2. Pide al usuario que ingrese el ID de un estudiante.
3. Muestra todos los cursos en los que está matriculado el estudiante.

INSTRUCCIONES:
1. Asegúrate de tener datos de estudiantes y matrículas.
2. Ejecutar: python check_student_enrollments.py
==============================================================================
"""

import os
import sys
import django

# Configuración de Django (Ajusta si 'RulingoClub.settings' no es correcto)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RulingoClub.settings')
django.setup()

# Importar modelos
from accounts.models import Student, Enrollment 

def print_header(text):
    """Imprime un header visual."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def display_student_enrollments():
    """
    Lista estudiantes y permite seleccionar uno para ver sus matrículas.
    """
    
    # Obtener todos los estudiantes para la lista
    # Usamos select_related para obtener la info del User en la consulta inicial
    students = Student.objects.all().select_related('user').order_by('id')
    
    if not students:
        print_header("NO HAY ESTUDIANTES")
        print("🛑 No se encontraron estudiantes en la base de datos. Ejecuta un script de creación de datos.")
        return

    # 1. Mostrar lista de estudiantes
    print_header("LISTA DE ESTUDIANTES")
    for student in students:
        name = student.user.get_full_name() or student.user.username
        print(f"  ID: {student.id:<3} | Nombre: {name} (Tutor ID: {student.created_by.id})")
    print("-" * 80)

    # 2. Pedir selección
    while True:
        try:
            student_id = input("Ingrese el ID del estudiante a revisar (o 'q' para salir): ").strip()
            if student_id.lower() == 'q':
                return
            
            selected_id = int(student_id)
            selected_student = Student.objects.get(id=selected_id)
            break
        except ValueError:
            print("❌ ID no válido. Por favor, ingrese un número entero o 'q'.")
        except Student.DoesNotExist:
            print(f"❌ No se encontró ningún estudiante con ID {student_id}.")
    
    
    # 3. Obtener y mostrar matrículas
    
    # Usamos el related_name 'enrollments' y prefetch_related para obtener 
    # la info del curso y su tutor con pocas consultas.
    enrollments = selected_student.enrollments.all().select_related('course__tutor__user')
    
    student_name = selected_student.user.get_full_name() or selected_student.user.username
    
    print_header(f"CURSOS MATRICULADOS POR: {student_name} (ID: {selected_student.id})")
    
    if not enrollments.exists():
        print(f"El estudiante {student_name} no está matriculado en ningún curso.")
        return

    for enrollment in enrollments:
        course = enrollment.course
        tutor_name = course.tutor.user.get_full_name() or course.tutor.user.username
        
        print(f"📝 Curso: {course.title}")
        print(f"  - Tipo: {course.get_course_type_display()}")
        print(f"  - Tutor: {tutor_name}")
        print(f"  - Estado: {enrollment.get_status_display()}")
        print(f"  - Matrícula: {enrollment.enrolled_at.strftime('%Y-%m-%d %H:%M')}")
        print("-" * 40)


if __name__ == '__main__':
    display_student_enrollments()
