"""
==============================================================================
SCRIPT DE INSPECCIÓN RÁPIDA: VER TODOS LOS CURSOS (v2.0)
==============================================================================
Muestra el ID, Título, Tipo, Tutor, FECHA DE CREACIÓN Y ACTUALIZACIÓN 
de todos los cursos en la DB.

INSTRUCCIONES:
1. Asegúrate de tener datos de cursos (ejecuta 'create_test_data.py').
2. Ajusta la importación a la ruta de tu app si es necesario.
3. Ejecutar: python list_all_courses.py
==============================================================================
"""

import os
import django

# Configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RulingoClub.settings')
django.setup()

# Importar el modelo Course
from accounts.models import Course 

def print_header(text):
    """Imprime un header visual."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def list_all_courses():
    """Recupera y muestra la información de todos los cursos, incluyendo fechas."""
    
    print_header("REPORTE DE TODOS LOS CURSOS")
    
    # Usamos select_related('tutor__user') para obtener el nombre del tutor con una sola consulta
    courses = Course.objects.all().select_related('tutor__user').order_by('id')
    
    if not courses:
        print("🛑 No se encontraron cursos en la base de datos.")
        return

    for course in courses:
        tutor_name = course.tutor.user.get_full_name() or course.tutor.user.username
        
        # Se imprime la información completa del objeto
        print(f"ID: {course.id}")
        print(f"  Título: {course.title}")
        print(f"  Tipo: {course.get_course_type_display()} ({course.course_type})")
        print(f"  Tutor: {tutor_name} (ID: {course.tutor.id})")
        # --- CAMPOS DE FECHA AGREGADOS ---
        print(f"  Fecha Creación: {course.created_at}")
        print(f"  Última Actualización: {course.updated_at}")
        # --------------------------------
        print(f"  Descripción: {course.description[:50]}...") # Descripción truncada
        print("-" * 50)


if __name__ == '__main__':
    list_all_courses()
