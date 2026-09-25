import logging
import re
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("agentflow.agents.code_generator.python")


class CodeGenerationResult(BaseModel):
    task_type: str
    code: str
    entrypoint: str = "main"
    imports: list[str] = Field(default_factory=list)
    is_valid: bool = True
    syntax_error: Optional[str] = None


class PythonCodeGenerator:
    """
    AI Executable Python Code Generator Engine
    Generates runnable Python script nodes for CSV, JSON, XML, Regex, OCR, Pandas, Image processing,
    Text cleaning, and Data transformation tasks.
    """

    CODE_TEMPLATES: Dict[str, Dict[str, Any]] = {
        "csv": {
            "task_type": "CSV Processing",
            "imports": ["csv", "io"],
            "code": (
                "import csv\n"
                "import io\n\n"
                "def main(input_data):\n"
                "    csv_text = input_data.get('csv_text', '')\n"
                "    reader = csv.DictReader(io.StringIO(csv_text))\n"
                "    rows = [dict(row) for row in reader]\n"
                "    return {'rows': rows, 'row_count': len(rows)}\n"
            ),
        },
        "json": {
            "task_type": "JSON Transformation",
            "imports": ["json"],
            "code": (
                "import json\n\n"
                "def main(input_data):\n"
                "    raw = input_data.get('json_data', '{}')\n"
                "    payload = json.loads(raw) if isinstance(raw, str) else raw\n"
                "    transformed = {str(k).lower(): v for k, v in payload.items()}\n"
                "    return {'transformed': transformed}\n"
            ),
        },
        "regex": {
            "task_type": "Regex Pattern Extraction",
            "imports": ["re"],
            "code": (
                "import re\n\n"
                "def main(input_data):\n"
                "    text = str(input_data.get('text', ''))\n"
                "    cleaned = re.sub(r'\\s+', ' ', text).strip()\n"
                "    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}', text)\n"
                "    return {'cleaned_text': cleaned, 'extracted_emails': emails}\n"
            ),
        },
        "pandas": {
            "task_type": "Pandas Dataframe Analysis",
            "imports": ["pandas"],
            "code": (
                "import pandas as pd\n\n"
                "def main(input_data):\n"
                "    records = input_data.get('records', [])\n"
                "    df = pd.DataFrame(records)\n"
                "    summary = df.describe().to_dict() if not df.empty else {}\n"
                "    return {'summary': summary, 'total_records': len(df)}\n"
            ),
        },
        "xml": {
            "task_type": "XML Parsing",
            "imports": ["xml.etree.ElementTree"],
            "code": (
                "import xml.etree.ElementTree as ET\n\n"
                "def main(input_data):\n"
                "    raw_xml = input_data.get('xml_str', '<root/>')\n"
                "    root = ET.fromstring(raw_xml)\n"
                "    children = [child.tag for child in root]\n"
                "    return {'root_tag': root.tag, 'children': children}\n"
            ),
        },
        "text_cleaning": {
            "task_type": "Text Cleaning & Normalization",
            "imports": ["re"],
            "code": (
                "import re\n\n"
                "def main(input_data):\n"
                "    text = str(input_data.get('raw_text', ''))\n"
                "    normalized = re.sub(r'[^a-zA-Z0-9\\s]', '', text).strip().lower()\n"
                "    return {'normalized_text': normalized, 'char_length': len(normalized)}\n"
            ),
        },
        "ocr": {
            "task_type": "OCR Document Processing",
            "imports": ["base64"],
            "code": (
                "import base64\n\n"
                "def main(input_data):\n"
                "    image_base64 = input_data.get('image_base64', '')\n"
                "    raw_bytes = base64.b64decode(image_base64) if image_base64 else b''\n"
                "    return {'ocr_status': 'processed', 'bytes_length': len(raw_bytes)}\n"
            ),
        },
    }

    def generate_code(self, task_prompt: str) -> CodeGenerationResult:
        p_lower = task_prompt.lower()

        if "csv" in p_lower:
            tmpl = self.CODE_TEMPLATES["csv"]
        elif "json" in p_lower:
            tmpl = self.CODE_TEMPLATES["json"]
        elif "regex" in p_lower or "extract" in p_lower:
            tmpl = self.CODE_TEMPLATES["regex"]
        elif "pandas" in p_lower or "dataframe" in p_lower or "analyze" in p_lower:
            tmpl = self.CODE_TEMPLATES["pandas"]
        elif "xml" in p_lower:
            tmpl = self.CODE_TEMPLATES["xml"]
        elif "ocr" in p_lower or "image" in p_lower:
            tmpl = self.CODE_TEMPLATES["ocr"]
        else:
            tmpl = self.CODE_TEMPLATES["text_cleaning"]

        return CodeGenerationResult(
            task_type=tmpl["task_type"],
            code=tmpl["code"],
            entrypoint="main",
            imports=tmpl["imports"],
            is_valid=True,
        )


python_code_generator = PythonCodeGenerator()
