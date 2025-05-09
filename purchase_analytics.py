import psycopg2
import pandas as pd
import google.generativeai as genai
from psycopg2 import sql
import textwrap
import re  # Added for markdown parsing

genai.configure(api_key="AIzaSyAe8rheF4wv2ZHJB2YboUhyyVlM2y0vmlk")

class GeminiDBAgent:
    def __init__(self, dbname="analyticbot", user="yavar", password="", 
                 host="localhost", port="5432", table_name="Purchase_Report _1000_astral"):
        # Database connection
        self.conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.table_name = table_name
        
        # Configure Gemini model
        generation_config = {
            "temperature": 0.2,
            "top_p": 1,
            "top_k": 32,
            "max_output_tokens": 2000,
        }
        
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        # Get schema for prompt engineering
        self.schema = self._get_table_schema()
    
    def _get_table_schema(self):
        """Fetch table schema from PostgreSQL"""
        query = """
            SELECT column_name, data_type 
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """
        with self.conn.cursor() as cursor:
            cursor.execute(query, (self.table_name.strip('"'),))
            return cursor.fetchall()
    
    def _generate_sql_prompt(self, question):
        """Create a detailed prompt for Gemini to generate SQL"""
        schema_info = "\n".join([f"{col[0]} ({col[1]})" for col in self.schema])
        
        return textwrap.dedent(f"""
        You are a senior PostgreSQL analyst. Convert this natural language question into a precise SQL query.
        
        Database Schema for table '{self.table_name}':
        {schema_info}
        
        Important Notes:
        1. Always use quoted identifiers (e.g., "Net price") because columns have spaces
        2. The table name is '{self.table_name}' with a space between words
        3. Use proper JOINs if querying multiple tables
        4. Include only the SQL query in your response (no markdown formatting)
        5. Never include ```sql or ``` in your response
        
        Question: {question}
        
        SQL Query:
        """)
    
    def generate_sql(self, question):
        """Use Gemini to convert question to SQL and clean the response"""
        prompt = self._generate_sql_prompt(question)
        response = self.model.generate_content(prompt)
        
        # Extract SQL from markdown code block if present
        sql_query = response.text.strip()
        if sql_query.startswith("```sql"):
            sql_query = re.sub(r'^```sql\s*|\s*```$', '', sql_query, flags=re.DOTALL)
        elif sql_query.startswith("```"):
            sql_query = re.sub(r'^```\s*|\s*```$', '', sql_query, flags=re.DOTALL)
            
        return sql_query.strip()
    
    def execute_query(self, sql_query):
        """Execute SQL query safely"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql_query)
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    data = cursor.fetchall()
                    return pd.DataFrame(data, columns=columns)
                return pd.DataFrame()
        except Exception as e:
            return f"Error executing query: {str(e)}"
    
    def explain_results(self, question, results):
        """Use Gemini to explain the results in natural language"""
        prompt = textwrap.dedent(f"""
        You're a data analyst explaining query results to a business user.
        
        Original Question: {question}
        
        Data Results:
        {results.head().to_string()}
        
        Please provide:
        1. A concise summary of what the data shows
        2. Any interesting patterns or outliers
        3. Business implications
        
        Use bullet points and keep it under 200 words.
        """)
        
        response = self.model.generate_content(prompt)
        return response.text
    
    def ask_question(self, question):
        """End-to-end question answering"""
        print(f"\nQuestion: {question}")
        
        # Step 1: Generate SQL
        sql_query = self.generate_sql(question)
        print(f"\nGenerated SQL:\n{sql_query}\n")
        
        # Step 2: Execute Query
        results = self.execute_query(sql_query)
        
        if isinstance(results, str):
            print(results)  # Error message
            return
        
        # Step 3: Display Results
        print("Query Results:")
        print(results.to_string(index=False))
        
        # Step 4: Generate Explanation
        explanation = self.explain_results(question, results)
        print(f"\nAnalysis:\n{explanation}")
    
    def close(self):
        self.conn.close()


if __name__ == "__main__":
    agent = GeminiDBAgent()
    
    questions = [
        "Show me items with zero value",
        "List materials where the net price is above average",
        "Compare current prices with previous purchase prices",
        "Find vendors with the highest total purchase amounts",
        "Show the distribution of prices across material groups"
    ]
    
    for question in questions:
        print(f"\n{'='*50}")
        print(f"Question: {question}")
        try:
            sql_query = agent.generate_sql(question)
            print(f"\nGenerated SQL:\n{sql_query}")
            
            results = agent.execute_query(sql_query)
            if isinstance(results, str):
                print(f"\nError: {results}")
            else:
                print("\nResults:")
                print(results.to_string(index=False))
                
                explanation = agent.explain_results(question, results)
                print(f"\nAnalysis:\n{explanation}")
        except Exception as e:
            print(f"Error processing question: {str(e)}")
    
    agent.close()