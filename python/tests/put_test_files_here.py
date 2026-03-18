# #import unittest
# # fake test for example

# class TestTimeTravelingToaster(unittest.TestCase):

#     def setUp(self):
#         self.toaster = TimeTravelingToaster()

#     def test_default_darkness(self):
#         result = self.toaster.toast("sourdough")
#         self.assertEqual(result, "sourdough toasted to level 3")

#     def test_set_darkness_valid(self):
#         self.toaster.set_darkness(7)
#         result = self.toaster.toast("rye")
#         self.assertEqual(result, "rye toasted to level 7")

#     def test_set_darkness_invalid(self):
#         with self.assertRaises(ValueError):
#             self.toaster.set_darkness(42)

#     def test_rewind_removes_last_toast(self):
#         self.toaster.toast("white")
#         self.assertEqual(self.toaster.history_count(), 1)
#         last = self.toaster.rewind_last_toast()
#         self.assertEqual(last, "white toasted to level 3")
#         self.assertEqual(self.toaster.history_count(), 0)

#     def test_rewind_without_history_raises(self):
#         with self.assertRaises(Runti
# meError):
#             self.toaster.rewind_last_toast()


# if __name__ == "__main__":
#     unittest.main()






