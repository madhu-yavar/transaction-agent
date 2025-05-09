import unittest
import os
import pandas as pd
from agents.language_agent import language_agent
from state.state_schema import AgentState

class TestLanguageAgent(unittest.TestCase):

    def test_translate_pdf(self):
        state = AgentState(file_path="tests/wf.pdf", file_type="pdf", source="local")
        result = language_agent.invoke({"state": state.model_dump()})
        print("\n[PDF Translation Result]:", result.raw_text[:300] if result.raw_text else result.error)
        self.assertTrue(result.translated or result.error)

    def test_translate_excel(self):
        df = pd.DataFrame({"Región": ["LIMA", "CUSCO"], "Entidad": ["Mun. Lima", "Mun. Cusco"]})
        sample_path = "tests/sample.xlsx"
        df.to_excel(sample_path, index=False)

        state = AgentState(file_path=sample_path, file_type="excel", source="local")
        result = language_agent.invoke({"state": state.model_dump()})
        print("\n[Excel Translation Preview]:", result.internal_data.head() if result.internal_data is not None else result.error)

        os.remove(sample_path)
        self.assertTrue(result.translated or result.error)

    def test_translate_csv(self):
        df = pd.DataFrame({"Nombre": ["Juan", "Maria"], "Edad": [25, 30]})
        sample_path = "tests/sample.csv"
        df.to_csv(sample_path, index=False)

        state = AgentState(file_path=sample_path, file_type="csv", source="local")
        result = language_agent.invoke({"state": state.model_dump()})
        print("\n[CSV Translation Preview]:", result.internal_data.head() if result.internal_data is not None else result.error)

        os.remove(sample_path)
        self.assertTrue(result.translated or result.error)

    def test_invalid_file_type(self):
        sample_path = "tests/sample.txt"
        with open(sample_path, "w") as f:
            f.write("Dummy text")

        state = AgentState(file_path=sample_path, file_type="txt", source="local")
        result = language_agent.invoke({"state": state.model_dump()})
        print("\n[Invalid File Type Result]:", result.error)

        os.remove(sample_path)
        self.assertIn("Unsupported file type", result.error or "")

    def test_missing_file(self):
        state = AgentState(file_path="tests/nonexistent.pdf", file_type="pdf", source="local")
        result = language_agent.invoke({"state": state.model_dump()})
        print("\n[Missing File Result]:", result.error)
        self.assertIn("File not found", result.error or "")

if __name__ == "__main__":
    unittest.main()
