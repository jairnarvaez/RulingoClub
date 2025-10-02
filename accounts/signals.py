# ==============================================================================
# ISSUE #6: IMPLEMENTAR MODELO ENROLLMENT
# ==============================================================================


from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from .models import Course, Enrollment, Student


@receiver(post_save, sender=Course)
def auto_enroll_students_in_demo_courses(sender, instance, created, **kwargs):
    """
    Signal post_save para el modelo Course.

    Si se crea un nuevo curso y es de tipo 'demo', automáticamente 
    matricula a TODOS los estudiantes del tutor creador en ese curso.
    """
    
    # ✅ Condición 1: Solo si es una creación
    # ✅ Condición 2: Solo si el tipo de curso es 'demo'
    if created and instance.is_demo():
        
        try:
            tutor = instance.tutor
            # Obtener todos los estudiantes creados por ese tutor
            students = tutor.students.all() 
            
            print(f"🤖 SIGNAL: Auto-matriculando {students.count()} estudiantes del Tutor {tutor.user.username} en el curso DEMO: {instance.title}")

            for student in students:
                # ✅ Usar get_or_create() para evitar duplicados
                enrollment, created_enrollment = Enrollment.objects.get_or_create(
                    student=student,
                    course=instance,
                    defaults={'status': 'active'} 
                )
                
                if created_enrollment:
                    print(f"  - ✅ Matrícula creada para: {student.user.username}")
                # else: El estudiante ya estaba matriculado, no hace nada.

        except ObjectDoesNotExist:
            # Esto puede ocurrir si un superusuario crea un curso y borra el tutor
            # inmediatamente después (aunque save_model debe proteger esto).
            print("❌ ERROR SIGNAL: No se pudo encontrar el Tutor asociado al curso.")
        except Exception as e:
            print(f"❌ ERROR SIGNAL inesperado: {e}")


# En signals.py, añade esta función justo después del primer signal.

# ==============================================================================
# NUEVO SIGNAL (REVERSO) - Auto-Matrícula de NUEVOS ESTUDIANTES
# ==============================================================================

@receiver(post_save, sender=Student)
def auto_enroll_new_student_in_demos(sender, instance, created, **kwargs):
    """
    Signal post_save para el modelo Student.

    Si se crea un nuevo estudiante, lo matricula automáticamente en 
    TODOS los cursos demo existentes de su tutor creador (created_by).
    """

    # Condición: Solo si es una creación (nuevo estudiante)
    if created:
        try:
            # El tutor creador del estudiante
            tutor = instance.created_by
            
            # Obtener todos los cursos de tipo 'demo' de ESE tutor
            demo_courses = Course.objects.filter(
                tutor=tutor, 
                course_type='demo'
            )
            
            print(f"🤖 SIGNAL REVERSO: Matriculando nuevo estudiante {instance.user.username} en {demo_courses.count()} cursos DEMO existentes.")

            for course in demo_courses:
                # Usar get_or_create() para asegurar que no haya duplicados si 
                # alguna lógica manual intentó matricularlo antes.
                enrollment, created_enrollment = Enrollment.objects.get_or_create(
                    student=instance,
                    course=course,
                    defaults={'status': 'active'}
                )
                
                if created_enrollment:
                    print(f"  - ✅ Matriculado en: {course.title}")
        
        except ObjectDoesNotExist:
            print("❌ ERROR SIGNAL REVERSO: El estudiante fue creado sin un Tutor válido.")
        except Exception as e:
            print(f"❌ ERROR SIGNAL REVERSO inesperado: {e}")
