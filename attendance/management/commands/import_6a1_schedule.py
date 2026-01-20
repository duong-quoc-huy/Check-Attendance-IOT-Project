from django.core.management.base import BaseCommand
from attendance.models import ClassSchedule, Class, SchoolPeriod, Teachers, AcademicYear
from django.db import transaction


class Command(BaseCommand):
    help = 'Import Class 6A1 weekly timetable'

    def handle(self, *args, **options):
        # Timetable data: (day_of_week, period_number, subject_name, teacher_code)
        schedule_data = [
            # Monday (1)
            (1, 1, 'Toán', 'GV001'),
            (1, 2, 'Toán', 'GV001'),
            (1, 3, 'Ngữ văn', 'GV002'),
            (1, 4, 'Ngữ văn', 'GV002'),
            (1, 5, 'Ngoại ngữ 1', 'GV004'),
            (1, 6, 'Lịch sử', 'GV005'),
            (1, 7, 'Sinh học', 'GV009'),
            (1, 8, 'Giáo dục công dân', 'GV003'),
            
            # Tuesday (2)
            (2, 1, 'Ngoại ngữ 1', 'GV004'),
            (2, 2, 'Ngoại ngữ 1', 'GV004'),
            (2, 3, 'Toán', 'GV001'),
            (2, 4, 'Toán', 'GV001'),
            (2, 5, 'Địa lí', 'GV006'),
            (2, 6, 'Ngữ văn', 'GV002'),
            (2, 7, 'Vật lý', 'GV008'),
            (2, 8, 'Tin học', 'GV011'),
            
            # Wednesday (3)
            (3, 1, 'Ngữ văn', 'GV002'),
            (3, 2, 'Ngữ văn', 'GV002'),
            (3, 3, 'Toán', 'GV001'),
            (3, 4, 'Ngoại ngữ 1', 'GV004'),
            (3, 5, 'Hóa học', 'GV007'),
            (3, 6, 'Giáo dục thể chất', 'GV012'),
            (3, 7, 'Giáo dục thể chất', 'GV012'),
            (3, 8, 'Công nghệ', 'GV010'),
            
            # Thursday (4)
            (4, 1, 'Toán', 'GV001'),
            (4, 2, 'Toán', 'GV001'),
            (4, 3, 'Ngoại ngữ 1', 'GV004'),
            (4, 4, 'Ngữ văn', 'GV002'),
            (4, 5, 'Địa lí', 'GV006'),
            (4, 6, 'Sinh học', 'GV009'),
            (4, 7, 'Vật lý', 'GV008'),
            (4, 8, 'Âm nhạc', 'GV013'),
            
            # Friday (5)
            (5, 1, 'Ngữ văn', 'GV002'),
            (5, 2, 'Ngoại ngữ 1', 'GV004'),
            (5, 3, 'Toán', 'GV001'),
            (5, 4, 'Lịch sử', 'GV005'),
            (5, 5, 'Hóa học', 'GV007'),
            (5, 6, 'Công nghệ', 'GV010'),
            (5, 7, 'Tin học', 'GV011'),
            (5, 8, 'Mĩ thuật', 'GV014'),
        ]

        try:
            with transaction.atomic():
                # Get required objects
                class_6a1 = Class.objects.get(class_name='6A1')
                academic_year = AcademicYear.objects.get(academic_year_active_status=True)
                
                self.stdout.write(f'Found Class: {class_6a1}')
                self.stdout.write(f'Found Academic Year: {academic_year}')
                
                
                created_count = 0
                skipped_count = 0
                
                for day, period_num, subject, teacher_code in schedule_data:
                    try:
                        # Get period and teacher
                        period = SchoolPeriod.objects.get(period_number=period_num)
                        teacher = Teachers.objects.get(teacher_card_id=teacher_code)
                        
                        # Create or update schedule entry
                        schedule, created = ClassSchedule.objects.get_or_create(
                            class_obj=class_6a1,
                            academic_year=academic_year,
                            day_of_week=day,
                            period=period,
                            defaults={
                                'subject_name': subject,
                                'teacher': teacher,
                                'is_active': True
                            }
                        )
                        
                        if created:
                            created_count += 1
                            day_name = dict(ClassSchedule.WEEKDAY_CHOICES).get(day)
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'✓ {day_name} - Period {period_num}: {subject} ({teacher.teacher_full_name})'
                                )
                            )
                        else:
                            skipped_count += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f'⚠ Already exists: {subject} - Period {period_num}'
                                )
                            )
                    
                    except SchoolPeriod.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(f'✗ Period {period_num} not found! Please create SchoolPeriod first.')
                        )
                    except Teachers.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(f'✗ Teacher {teacher_code} not found!')
                        )
                
                self.stdout.write(self.style.SUCCESS(f'\n=== Import Complete ==='))
                self.stdout.write(self.style.SUCCESS(f'Created: {created_count} schedule entries'))
                self.stdout.write(self.style.WARNING(f'Skipped: {skipped_count} existing entries'))
                self.stdout.write(self.style.SUCCESS(f'Total: {len(schedule_data)} entries processed'))
        
        except Class.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('✗ Class 6A1 not found! Please create it first.')
            )
        except AcademicYear.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('✗ Active Academic Year not found! Please create it first.')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error: {str(e)}')
            )