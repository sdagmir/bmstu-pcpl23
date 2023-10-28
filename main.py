class Student:
    def __init__(self, student_id, name, group_id, academic_rating):
        self.student_id = student_id
        self.name = name
        self.group_id = group_id
        self.academic_rating = academic_rating


class Group:
    def __init__(self, group_id, name):
        self.group_id = group_id
        self.name = name


# Создаем объекты класса Group
group1 = Group(1, "Группа A")
group2 = Group(2, "Группа B")
group3 = Group(3, "Группа C")

# Создаем объекты класса Student
student1 = Student(1, "Андреев", 1, 90)
student2 = Student(2, "Борисов", 1, 85)
student3 = Student(3, "Абрамов", 2, 92)
student4 = Student(4, "Григорьев", 2, 88)
student5 = Student(5, "Иванов", 3, 94)

# Создаем список "Студенты и их группы" для связи один-ко-многим
student_group = [
    (student1, group1),
    (student2, group1),
    (student3, group2),
    (student4, group2),
    (student5, group3)
]


def main():
    # Задание В1
    print("Задание В1")
    for student, group in student_group:
        if student.name.startswith('А'):
            print(f"{student.name} - {group.name}")

    # Задание В2
    print("\nЗадание В2")
    group_min_ratings = {}
    for student, group in student_group:
        if group.name in group_min_ratings:
            if student.academic_rating < group_min_ratings[group.name]:
                group_min_ratings[group.name] = student.academic_rating
        else:
            group_min_ratings[group.name] = student.academic_rating

    sorted_groups = sorted(group_min_ratings.items(), key=lambda x: x[1])
    for group, min_rating in sorted_groups:
        print(f"{group} - Минимальный рейтинг: {min_rating}")

    # Задание В3
    print("\nЗадание В3")
    for student, group in student_group:
        print(f"{student.name} - {group.name}")


if __name__ == '__main__':
    main()
