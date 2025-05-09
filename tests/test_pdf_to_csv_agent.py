# tests/test_pdf_to_csv_agent.py

import unittest
from state.state_schema import AgentState
from agents.pdf_to_csv_agent import pdf_to_csv_agent

class TestPDFToCSVAgent(unittest.TestCase):
    def test_valid_pdf_extraction(self):
        test_state = AgentState(
            file_path="tests/wf.pdf",  # Replace with your test file
            file_type="pdf"
        )
        new_state = pdf_to_csv_agent(test_state)
        self.assertIsNone(new_state.error)
        self.assertIsNotNone(new_state.data_frame)
        self.assertGreater(len(new_state.data_frame), 0)
        self.assertIn("|", new_state.display_preview)  # Markdown table preview

    def test_skip_non_pdf(self):
        test_state = AgentState(file_path="dummy.csv", file_type="csv")
        new_state = pdf_to_csv_agent(test_state)
        self.assertEqual(new_state.error, "Skipped: Not a PDF file.")

    def test_missing_file(self):
        test_state = AgentState(file_path="not_found.pdf", file_type="pdf")
        new_state = pdf_to_csv_agent(test_state)
        self.assertIn("PDF file not found", new_state.error)

if __name__ == "__main__":
    unittest.main()
