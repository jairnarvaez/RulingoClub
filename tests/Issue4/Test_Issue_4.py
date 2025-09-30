"""
==============================================================================
SCRIPT DE VALIDACIÓN AUTOMÁTICA - ISSUE #4
==============================================================================
Este script valida TODOS los criterios de aceptación del Issue #4:
- Modelo Course creado correctamente.
- Relación ForeignKey a Tutor con CASCADE.
- Campos requeridos (title, description).
- Tipos de curso (demo, level, custom) y valor por defecto.
- Métodos helper (is_demo, is_level, is_custom).

INSTRUCCIONES:
1. Asegúrate de haber aplicado las migraciones de Issue #4.
2. Guardar este archivo en la raíz del proyecto como: Test_Issue_4.py
3. Ejecutar: python Test_Issue_4.py
4. Revisar los resultados en consola.
==============================================================================
"""

import os
import sys
import django
from django.db.models.fields.related import ForeignKey
from django.db.models import CASCADE

# Configurar Django (Ajusta 'tu_proyecto.settings' al nombre de tu proyecto)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RulingoClub.settings')
django.setup()

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import connection

# Importar los modelos del Issue #1 y #4 (Ajusta 'accounts.models' al nombre de tu app)
from accounts.models import Tutor, Student, Course


# ==============================================================================
# UTILIDADES PARA PRINTS CLAROS
# ==============================================================================

def print_header(text):
    """Imprime un header visual"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def print_result(test_name, success, message):
    """Imprime el resultado de un test"""
    status = "PASSED" if success else "FAILED"
    indicator = "✅" if success else "❌"
    print(f"{indicator} {status:<8} | {test_name:<50} | {message}")


# ==============================================================================
# UTILIDADES DE CREACIÓN DE DATOS
# ==============================================================================

def cleanup():
    """Elimina todos los datos de prueba."""
    Course.objects.all().delete()
    Tutor.objects.all().delete()
    User.objects.all().delete()

def setup_test_data():
    """Crea un usuario y un tutor para usar en los tests."""
    try:
        user = User.objects.create_user('tutor_test_4', 'test@test.com', 'password')
        tutor = Tutor.objects.create(user=user)
        return tutor
    except Exception as e:
        print(f"Error al configurar datos: {e}")
        return None

def create_valid_course(tutor_instance, course_type='level'):
    """Crea una instancia válida de Course."""
    try:
        course = Course.objects.create(
            tutor=tutor_instance,
            title=f"Curso de Prueba - {course_type}",
            description="Descripción detallada para el test.",
            course_type=course_type
        )
        return course
    except Exception as e:
        return None


# ==============================================================================
# TESTS DE CRITERIOS DE ACEPTACIÓN
# ==============================================================================

def validate_field_structure(tutor):
    """
    Criterios: title, description, tutor (ForeignKey), on_delete=CASCADE.
    """
    test_name = "Estructura de Campo y Relaciones"
    
    # 1. Comprobar que los campos existen y son requeridos
    try:
        Course(tutor=tutor, description="D").full_clean()
        print_result(test_name, False, "❌ Falla: 'title' no lanzó ValidationError (debe ser requerido).")
        return False
    except ValidationError as e:
        if 'title' not in e.message_dict:
            print_result(test_name, False, "❌ Falla: 'title' no es reconocido como campo requerido.")
            return False
        
    # 2. Comprobar el tipo de campo `tutor` y `on_delete=CASCADE`
    tutor_field = Course._meta.get_field('tutor')
    if not isinstance(tutor_field, ForeignKey):
        print_result(test_name, False, f"❌ Falla: 'tutor' debe ser ForeignKey, es {type(tutor_field)}.")
        return False

    if tutor_field.remote_field.on_delete != CASCADE:
        print_result(test_name, False, f"❌ Falla: 'tutor' on_delete debe ser CASCADE, es {tutor_field.remote_field.on_delete}.")
        return False
        
    print_result(test_name, True, "✅ Campos 'title', 'tutor' y on_delete=CASCADE validados.")
    return True


def validate_on_delete_cascade_action(tutor):
    """
    Criterio: Si se elimina el Tutor, el Course asociado se elimina.
    """
    test_name = "On Delete CASCADE (Eliminación)"
    
    course_count_before = Course.objects.count()
    if course_count_before == 0:
        create_valid_course(tutor)
    
    course_to_delete = Course.objects.first()
    if not course_to_delete:
        print_result(test_name, False, "❌ Falla: No se pudo crear curso para la prueba.")
        return False
        
    tutor_id = course_to_delete.tutor.id
    course_id = course_to_delete.id
    
    # Eliminar el tutor
    Tutor.objects.filter(id=tutor_id).delete()
    
    # Verificar si el curso también fue eliminado
    course_exists = Course.objects.filter(id=course_id).exists()
    
    if not course_exists:
        print_result(test_name, True, "✅ Al eliminar Tutor, Course se eliminó (CASCADE).")
        return True
    else:
        print_result(test_name, False, "❌ Falla: Course persistió después de eliminar Tutor (CASCADE falló).")
        return False


def validate_course_type_default_and_choices(tutor):
    """
    Criterios: course_type por defecto es 'level' y acepta solo CHOICES.
    """
    test_name = "course_type: Default y CHOICES"
    
    # 1. Validación de valor por defecto ('level')
    default_course = Course.objects.create(
        tutor=tutor,
        title="Default Test",
        description="Desc"
    )
    if default_course.course_type != 'level':
        print_result(test_name, False, f"❌ Falla: Valor por defecto no es 'level', es '{default_course.course_type}'.")
        return False
    default_course.delete() # Limpiar
    
    # 2. Validación de CHOICES (prueba de valor no válido)
    try:
        invalid_course = Course(
            tutor=tutor, 
            title="Invalid Test", 
            description="Desc", 
            course_type='invalid_type'
        )
        invalid_course.full_clean()
        print_result(test_name, False, "❌ Falla: Valor 'invalid_type' no lanzó ValidationError (CHOICES falló).")
        return False
    except ValidationError as e:
        if 'course_type' not in e.message_dict:
            print_result(test_name, False, "❌ Falla: ValidationError lanzado pero no para 'course_type'.")
            return False
    
    print_result(test_name, True, "✅ Valor por defecto ('level') y restricción CHOICES validados.")
    return True


def validate_helper_methods(tutor):
    """
    Criterios: Métodos is_demo(), is_level(), is_custom() funcionan correctamente.
    """
    test_name = "Métodos Helper (is_demo, is_level, is_custom)"
    
    # Crear un curso de cada tipo
    course_demo = create_valid_course(tutor, 'demo')
    course_level = create_valid_course(tutor, 'level')
    course_custom = create_valid_course(tutor, 'custom')
    
    if not course_demo or not course_level or not course_custom:
        print_result(test_name, False, "❌ Falla: Error al crear cursos de prueba para helpers.")
        return False

    # Test 1: is_demo()
    is_demo_ok = course_demo.is_demo() and not course_level.is_demo() and not course_custom.is_demo()
    if not is_demo_ok:
        print_result(test_name, False, "❌ Falla: is_demo() no funciona correctamente.")
        return False

    # Test 2: is_level()
    is_level_ok = course_level.is_level() and not course_demo.is_level() and not course_custom.is_level()
    if not is_level_ok:
        print_result(test_name, False, "❌ Falla: is_level() no funciona correctamente.")
        return False

    # Test 3: is_custom()
    is_custom_ok = course_custom.is_custom() and not course_demo.is_custom() and not course_level.is_custom()
    if not is_custom_ok:
        print_result(test_name, False, "❌ Falla: is_custom() no funciona correctamente.")
        return False
        
    print_result(test_name, True, "✅ Métodos helper is_demo(), is_level(), is_custom() validados.")
    return True


# ==============================================================================
# EJECUCIÓN PRINCIPAL
# ==============================================================================

if __name__ == '__main__':
    
    total_tests = 4
    passed_tests = 0
    
    # 1. Limpiar datos anteriores
    cleanup()
    
    print_header("INICIANDO VALIDACIÓN DEL ISSUE #4 (MODELO COURSE)")
    
    # 2. Configurar datos de prueba (Tutor es necesario para crear Course)
    tutor_data = setup_test_data()
    if not tutor_data:
        print("\n❌ PRUEBA CANCELADA: No se pudo crear el Tutor de prueba.")
        sys.exit(1)
    
    # Test 1: Estructura de Campo y Relaciones
    if validate_field_structure(tutor_data):
        passed_tests += 1
    
    # Test 2: On Delete CASCADE
    if validate_on_delete_cascade_action(tutor_data):
        passed_tests += 1
    
    # Recrear Tutor y Course para la siguiente prueba (porque el anterior fue borrado)
    cleanup()
    tutor_data = setup_test_data()
    course_for_helpers = create_valid_course(tutor_data)
    
    # Test 3: course_type: Default y CHOICES
    if validate_course_type_default_and_choices(tutor_data):
        passed_tests += 1
    
    # Test 4: Métodos Helper
    if validate_helper_methods(tutor_data):
        passed_tests += 1

    # Limpiar datos de prueba
    cleanup()
    
    # Resumen final
    print_header("RESUMEN DE VALIDACIÓN")
    print(f"\n{'='*80}")
    print(f"  TESTS EJECUTADOS: {total_tests}")
    print(f"  TESTS PASADOS:    {passed_tests}")
    print(f"  TESTS FALLIDOS:   {total_tests - passed_tests}")
    print(f"{'='*80}\n")
    
    if passed_tests == total_tests:
        print("🎉 ¡FELICIDADES! Todos los criterios del Issue #4 están cumplidos.")
        print("✅ El Issue #4 está COMPLETO.")
    else:
        print("🛑 ATENCIÓN: Fallaron algunos tests. Revisa el código de models.py.")
