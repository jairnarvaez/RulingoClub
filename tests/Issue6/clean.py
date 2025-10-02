"""
==============================================================================
SCRIPT DE LIMPIEZA TOTAL DE DATOS DE PRUEBA
==============================================================================
Elimina todos los registros de los modelos creados hasta el Issue #6:
- Enrollment (Matrículas)
- Course (Cursos)
- Student (Estudiantes)
- Tutor (Tutores)
- User (Usuarios NO Superusuarios)

INSTRUCCIONES:
1. Asegúrate de que los modelos están importados correctamente desde tu app.
2. Ejecutar: python cleanup.py
==============================================================================
"""

import os
import django
from django.db import transaction

# Configuración de Django (Ajusta si 'RulingoClub.settings' no es correcto)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RulingoClub.settings')
django.setup()

# Importar modelos (Asegúrate de que la ruta sea correcta, ej. from accounts.models import...)
from django.contrib.auth.models import User
from accounts.models import Tutor, Student, Course, Enrollment 

def print_header(text):
    """Imprime un header visual"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

@transaction.atomic
def run_cleanup():
    """Ejecuta la limpieza de datos dentro de una transacción."""
    
    print_header("INICIANDO LIMPIEZA TOTAL DE DATOS DE PRUEBA")

    try:
        # Eliminar las matrículas (debe ir primero ya que depende de Course y Student)
        deleted_enrollments = Enrollment.objects.all().delete()[0]
        print(f"✅ Matrículas eliminadas (Enrollment): {deleted_enrollments}")
        
        # Eliminar cursos
        deleted_courses = Course.objects.all().delete()[0]
        print(f"✅ Cursos eliminados (Course): {deleted_courses}")
        
        # Eliminar estudiantes (la eliminación en cascada de User se produce aquí)
        deleted_students = Student.objects.all().delete()[0]
        print(f"✅ Estudiantes eliminados (Student): {deleted_students}")

        # Eliminar tutores (la eliminación en cascada de User se produce aquí)
        deleted_tutors = Tutor.objects.all().delete()[0]
        print(f"✅ Tutores eliminados (Tutor): {deleted_tutors}")
        
        # Eliminar Usuarios que no sean superusuarios (los que no tienen perfil de Tutor/Student)
        deleted_users = User.objects.filter(is_superuser=False).delete()[0]
        print(f"✅ Usuarios NO Superusuarios eliminados (User): {deleted_users}")

        
        # Conteo final
        print("\n--- CONTEO FINAL ---")
        print(f"Tutores restantes: {Tutor.objects.count()}")
        print(f"Estudiantes restantes: {Student.objects.count()}")
        print(f"Cursos restantes: {Course.objects.count()}")
        print(f"Matrículas restantes: {Enrollment.objects.count()}")
        print(f"Usuarios restantes (incl. Superusers): {User.objects.count()}")
        
        print_header("LIMPIEZA COMPLETA. Base de datos lista para pruebas frescas.")

    except Exception as e:
        print(f"\n🛑 ERROR CRÍTICO durante la limpieza: {e}")
        # Si hay un error, el transaction.atomic asegura que no se haga commit parcial.
        
if __name__ == '__main__':
    run_cleanup()
