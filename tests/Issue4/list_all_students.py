"""
==============================================================================
SCRIPT DE INSPECCIÓN RÁPIDA: VER TODOS LOS ESTUDIANTES
==============================================================================
Muestra el ID, Nombre, Email, Fecha de Creación y el Tutor Creador 
de todos los estudiantes en la DB.

INSTRUCCIONES:
1. Asegúrate de tener datos de estudiantes (ejecuta 'create_test_data.py').
2. Ajusta la importación a la ruta de tu app si es necesario.
3. Ejecutar: python list_all_students.py
==============================================================================
"""

import os
import django

# Configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RulingoClub.settings')
django.setup()

# Importar el modelo Student (y User/Tutor para la información relacionada)
from accounts.models import Student 

def print_header(text):
    """Imprime un header visual."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def list_all_students():
    """Recupera y muestra la información de todos los estudiantes, incluyendo fechas."""
    
    print_header("REPORTE DE TODOS LOS ESTUDIANTES")
    
    # Usamos select_related para obtener la información del User y del Tutor Creador 
    # en una sola consulta.
    students = Student.objects.all().select_related('user', 'created_by__user').order_by('id')
    
    if not students:
        print("🛑 No se encontraron estudiantes en la base de datos.")
        return

    for student in students:
        # Información del estudiante (desde el modelo User)
        student_username = student.user.username
        student_full_name = student.user.get_full_name()
        student_email = student.user.email

        # Información del Tutor Creador (desde el campo created_by)
        creator_name = student.created_by.user.get_full_name() or student.created_by.user.username
        
        # Se imprime la información completa
        print(f"ID Student: {student.id}")
        print(f"  Usuario: {student_username}")
        print(f"  Nombre: {student_full_name}")
        print(f"  Email: {student_email}")
        print(f"  Fecha Creación: {student.created_at}")
        print(f"  Tutor Creador: {creator_name} (ID: {student.created_by.id})")
        print("-" * 50)


if __name__ == '__main__':
    list_all_students()
