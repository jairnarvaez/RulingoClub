"""
==============================================================================
SCRIPT DE PRUEBA DE FLUJO COMPLETO DE MATRÍCULAS (Issue #6)
==============================================================================
1. Crea 1 Tutor.
2. Tutor crea 3 Cursos (Demo, Custom, Level).
3. Tutor crea 5 Estudiantes (activa el Signal de auto-matrícula).
4. Tutor matricula manualmente a los 5 estudiantes en el curso Custom.
5. Verifica que cada estudiante tiene 2 matrículas (Demo y Custom).

INSTRUCCIONES:
1. Asegúrate de tener todas las migraciones aplicadas (hasta Issue #6).
2. Ajusta la configuración de Django si es necesario.
3. Ejecutar: python test_full_enrollment_flow.py
==============================================================================
"""

import os
import sys
import django
from django.db import transaction

# Configuración de Django (Ajusta si 'RulingoClub.settings' no es correcto)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RulingoClub.settings')
django.setup()

# Importar modelos
from django.contrib.auth.models import User
from accounts.models import Tutor, Student, Course, Enrollment 

# --- CONSTANTES DE PRUEBA ---
TUTOR_NAME = "TutorPruebaMatricula"
STUDENT_COUNT = 5
# ------------------------------

def print_header(text):
    """Imprime un header visual"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def cleanup():
    """Elimina todos los datos de prueba."""
    Enrollment.objects.all().delete()
    Course.objects.all().delete()
    Student.objects.all().delete()
    User.objects.filter(is_superuser=False).delete()


@transaction.atomic
def run_enrollment_test():
    """Ejecuta el flujo de prueba completo."""
    
    print_header("INICIANDO PRUEBA DE FLUJO DE MATRÍCULAS")
    cleanup()
    
    # ----------------------------------------------------------------------
    # 1. CREACIÓN DEL TUTOR Y CURSOS
    # ----------------------------------------------------------------------
    
    # Crear Tutor
    try:
        user_tutor = User.objects.create_user(TUTOR_NAME, f"{TUTOR_NAME}@mail.com", 'password123')
        tutor = Tutor.objects.create(user=user_tutor)
        print(f"✅ 1. Tutor Creado: {tutor.user.username}")
    except Exception as e:
        print(f"❌ ERROR: Falló la creación del Tutor: {e}")
        return

    # Crear Cursos (Demo, Custom, Level)
    course_demo = Course.objects.create(tutor=tutor, title="Curso DEMO - Básico", description="Demo", course_type='demo')
    course_custom = Course.objects.create(tutor=tutor, title="Curso CUSTOM - Individual", description="Custom", course_type='custom')
    course_level = Course.objects.create(tutor=tutor, title="Curso LEVEL - A1", description="Level", course_type='level')
    
    print(f"✅ 2. Cursos Creados: Demo ({course_demo.id}), Custom ({course_custom.id}), Level ({course_level.id})")

    # ----------------------------------------------------------------------
    # 3. CREACIÓN DE ESTUDIANTES (ACTIVA SIGNAL REVERSO)
    # ----------------------------------------------------------------------
    
    students = []
    for i in range(1, STUDENT_COUNT + 1):
        username = f"std_test_{i}"
        user_std = User.objects.create_user(username, f"{username}@mail.com", 'student_pass')
        # Al crearse, el signal auto_enroll_new_student_in_demos debería dispararse
        student = Student.objects.create(user=user_std, created_by=tutor)
        students.append(student)
        
    print(f"✅ 3. {STUDENT_COUNT} Estudiantes creados. Revisando auto-matrículas...")

    # Verificación de auto-matrícula (Signal)
    # Cada estudiante debe tener 1 matrícula en el curso demo
    errors = 0
    for student in students:
        demo_enrollment_count = Enrollment.objects.filter(student=student, course=course_demo).count()
        if demo_enrollment_count != 1:
            print(f"❌ Error Matrícula Demo para {student.user.username}: {demo_enrollment_count} encontradas (Esperado: 1)")
            errors += 1
    
    if errors == 0:
        print("✅ Auto-Matrícula en Curso DEMO (Signal Reverso) verificada correctamente.")

    # ----------------------------------------------------------------------
    # 4. MATRÍCULA MANUAL EN CUSTOM
    # ----------------------------------------------------------------------

    print("\n--- 4. Matriculando manualmente en Curso Custom ---")
    
    manual_enrollments_created = 0
    for student in students:
        # El tutor matricula a sus estudiantes en su curso custom
        enrollment, created = Enrollment.objects.get_or_create(
            student=student,
            course=course_custom,
            defaults={'status': 'active'}
        )
        if created:
            manual_enrollments_created += 1

    print(f"✅ {manual_enrollments_created} matrículas manuales creadas en Curso Custom.")

    # ----------------------------------------------------------------------
    # 5. VERIFICACIÓN FINAL
    # ----------------------------------------------------------------------
    
    print_header("RESUMEN DE VERIFICACIÓN FINAL")
    
    passed_students = 0
    
    for student in students:
        total_enrollments = student.enrollments.count()
        
        if total_enrollments == 2:
            print(f"✅ {student.user.username:<15}: Total Matrículas: {total_enrollments} (OK)")
            passed_students += 1
        else:
            print(f"❌ {student.user.username:<15}: Total Matrículas: {total_enrollments} (FALLÓ, esperado 2)")

    # Resumen final
    total_expected = STUDENT_COUNT * 2
    total_found = Enrollment.objects.count()
    
    print("\n--- Conteo de Matrículas ---")
    print(f"Total de Estudiantes: {STUDENT_COUNT}")
    print(f"Matrículas esperadas: {total_expected}")
    print(f"Matrículas encontradas: {total_found}")
    
    if passed_students == STUDENT_COUNT and total_found == total_expected:
        print("\n🎉 ¡PRUEBA EXITOSA! El flujo completo de auto-matrícula y matrícula manual funciona.")
        print("✅ El Issue #6 está validado para este escenario.")
    else:
        print("\n🛑 ATENCIÓN: La prueba FALLÓ. Revisa la lógica del signal y la matrícula manual.")

    # Limpieza
    # cleanup()


if __name__ == '__main__':
    run_enrollment_test()
