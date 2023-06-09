import pickle
import unittest
import os
from tempfile import TemporaryDirectory

from DiskBackedList import DiskBackedList

class DiskBackedListTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.filename = os.path.join(self.temp_dir.name, 'data.pkl')
        self.list = DiskBackedList(self.filename)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_append_and_retrieve(self):
        self.list.append('value1')
        self.list.append('value2')

        self.assertEqual(self.list[0], 'value1')
        self.assertEqual(self.list[1], 'value2')

    def test_extend_and_retrieve(self):
        self.list.extend(['value1', 'value2'])

        self.assertEqual(self.list[0], 'value1')
        self.assertEqual(self.list[1], 'value2')

    def test_delete(self):
        self.list.extend(['value1', 'value2'])
        del self.list[0]

        self.assertEqual(len(self.list), 1)
        self.assertEqual(self.list[0], 'value2')

    def test_load_from_disk(self):
        self.list.extend(['value1', 'value2'])
        self.list.store_to_disk()

        new_list = DiskBackedList(self.filename)
        new_list.load_from_disk()

        self.assertEqual(len(new_list), 2)
        self.assertEqual(new_list[0], 'value1')
        self.assertEqual(new_list[1], 'value2')

    def test_store_to_disk_every_100_keys(self):
        for i in range(1000):
            self.list.append(f'value{i}')

            if (i + 1) % 100 == 99:
                file_exists = os.path.isfile(self.filename)
                if file_exists:
                    with open(self.filename, 'rb') as file:
                        dumped_list = pickle.load(file)
                        self.assertNotEquals(len(dumped_list), i + 1)
                        self.assertEqual(len(dumped_list), i - 98)

            if (i + 1) % 100 == 0:
                file_exists = os.path.isfile(self.filename)
                self.assertTrue(file_exists)

                with open(self.filename, 'rb') as file:
                    dumped_list = pickle.load(file)
                    self.assertEqual(len(dumped_list), i + 1)

if __name__ == '__main__':
    unittest.main()
