"""
==============================================================================
SCRIPT DE REPORTE DE ESTRUCTURA DE DATOS
==============================================================================
Recorre todos los Tutores y muestra:
- Información del Tutor
- Lista de todos los Cursos asociados
- Lista de todos los Estudiantes asociados (created_by)

INSTRUCCIONES:
1. Asegúrate de haber ejecutado create_test_data.py para tener datos.
2. Ajusta la configuración de Django si es necesario.
3. Ejecutar: python data_report.py
==============================================================================
"""

import os
import django

# Configuración de Django (Ajusta si 'RulingoClub.settings' no es correcto)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RulingoClub.settings')
django.setup()

# Importar modelos (Ajusta si 'accounts.models' no es correcto)
from accounts.models import Tutor, Course, Student

def print_header(text, char="="):
    """Imprime un header visual."""
    print("\n" + char * 80)
    print(f"  {text}")
    print(char * 80)

def generate_report():
    """
    Genera el reporte, mostrando tutores, cursos y estudiantes asociados.
    """
    print_header("REPORTE DE ESTRUCTURA DE DATOS DE TUTORES")
    
    # 1. Obtener todos los Tutores
    tutores = Tutor.objects.all().prefetch_related('courses', 'students')
    
    if not tutores.exists():
        print("🛑 No se encontraron datos de Tutores. Ejecuta 'create_test_data.py' primero.")
        return

    total_courses = 0
    total_students = 0
    
    # 2. Iterar sobre cada Tutor
    for i, tutor in enumerate(tutores):
        # Información del Tutor
        tutor_full_name = tutor.user.get_full_name() or tutor.user.username
        print_header(f"TUTOR #{i+1}: {tutor_full_name} (ID: {tutor.id})", "-")

        # 3. Mostrar Cursos Asociados
        courses = tutor.courses.all()
        total_courses += courses.count()
        print(f"\n  📝 CURSOS ASOCIADOS ({courses.count()}):")
        
        if courses:
            for course in courses:
                print(f"    - [{course.get_course_type_display()}] {course.title}")
        else:
            print("    (Ningún curso asociado)")

        # 4. Mostrar Estudiantes Asociados
        # El related_name 'students' se usa para acceder a los estudiantes creados por este tutor
        students = tutor.students.all() 
        total_students += students.count()
        print(f"\n  🧑‍🎓 ESTUDIANTES ASOCIADOS ({students.count()}):")
        
        if students:
            for student in students:
                student_name = student.user.get_full_name() or student.user.username
                print(f"    - {student_name} (ID: {student.id})")
        else:
            print("    (Ningún estudiante asociado)")
        
        print("-" * 80)

    # 5. Resumen final
    print_header("RESUMEN GENERAL")
    print(f"Tutores encontrados: {tutores.count()}")
    print(f"Total de Cursos:     {total_courses}")
    print(f"Total de Estudiantes: {total_students}")
    print("==================================================================")

if __name__ == '__main__':
    generate_report()
