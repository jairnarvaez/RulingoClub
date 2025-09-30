"""
==============================================================================
SCRIPT DE PRUEBA RÁPIDA: CREACIÓN DE CURSOS DEMO
==============================================================================
Crea:
- 1 Tutor (TutorDemo)
- 3 Cursos, todos de tipo 'demo', asignados a ese tutor.

INSTRUCCIONES:
1. Ajusta la importación a la ruta de tu app si es necesario (accounts.models).
2. Ejecutar: python create_3_demo_courses.py
==============================================================================
"""

import os
import django
from django.db import transaction

# Configuración de Django (Ajusta si 'RulingoClub.settings' no es correcto)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RulingoClub.settings')
django.setup()

# Importar modelos (Ajusta si 'accounts.models' no es correcto)
from django.contrib.auth.models import User
from accounts.models import Tutor, Course

# --- CONSTANTES ---
TUTOR_USERNAME = "TutorDemo"
COURSE_COUNT = 3
COURSE_TYPE = 'demo'
# ------------------

def print_header(text):
    """Imprime un header visual"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def cleanup():
    """Elimina datos de Course, Tutor, y User (excepto superuser)."""
    Course.objects.all().delete()
    Tutor.objects.all().delete()
    User.objects.filter(is_superuser=False, username=TUTOR_USERNAME).delete()

@transaction.atomic
def create_demo_data():
    """Ejecuta la creación de datos de prueba de forma atómica."""
    
    # 1. Limpieza inicial
    cleanup()
    print_header("CREANDO UN TUTOR Y 3 CURSOS DEMO")

    # 2. Creación del Tutor
    try:
        user = User.objects.create_user(
            username=TUTOR_USERNAME,
            email=f"{TUTOR_USERNAME}@test.com",
            password='demo_password',
            first_name="Demo",
            last_name="Creator"
        )
        tutor = Tutor.objects.create(user=user)
        print(f"✅ Tutor Creado: {tutor.user.get_full_name()} ({TUTOR_USERNAME})")
    except Exception as e:
        print(f"❌ ERROR: Falló la creación del Tutor. {e}")
        return

    # 3. Creación de 3 Cursos Demo
    created_count = 0
    for i in range(1, COURSE_COUNT + 1):
        try:
            Course.objects.create(
                tutor=tutor,
                title=f"Curso Demo Introductorio #{i}",
                description="Contenido de muestra para nuevos usuarios.",
                course_type=COURSE_TYPE
            )
            created_count += 1
        except Exception as e:
            print(f"❌ ERROR: Falló la creación del Curso #{i}. {e}")
            break

    # 4. Resumen
    print("\n--- RESUMEN ---")
    print(f"Tutor en DB: {Tutor.objects.count()}")
    print(f"Cursos '{COURSE_TYPE}' creados: {Course.objects.count()}")
    
    if created_count == COURSE_COUNT:
        print("🎉 ¡CREACIÓN EXITOSA! Los 3 cursos demo fueron asignados al tutor.")
    else:
        print("🛑 FALLO PARCIAL: No se crearon los 3 cursos.")

if __name__ == '__main__':
    create_demo_data()
