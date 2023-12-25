from main import Student, Group, find_students_starting_with_A, find_group_min_ratings, list_students_groups
import unittest
import sys
import os

# Добавляем путь к папке RK2 в PYTHONPATH
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


class TestProgram(unittest.TestCase):
    def setUp(self):
        self.group1 = Group(1, "Группа A")
        self.group2 = Group(2, "Группа B")
        self.student_group = [
            (Student(1, "Андреев", 1, 90), self.group1),
            (Student(2, "Борисов", 1, 85), self.group1),
            (Student(3, "Абрамов", 2, 92), self.group2)
        ]

    def test_find_students_starting_with_A(self):
        result = find_students_starting_with_A(self.student_group)
        self.assertEqual(len(result), 2)
        self.assertIn(("Андреев", "Группа A"), result)

    def test_find_group_min_ratings(self):
        result = find_group_min_ratings(self.student_group)
        self.assertEqual(result, [("Группа A", 85), ("Группа B", 92)])

    def test_list_students_groups(self):
        result = list_students_groups(self.student_group)
        self.assertEqual(len(result), 3)
        self.assertIn(("Борисов", "Группа A"), result)


if __name__ == '__main__':
    unittest.main()
