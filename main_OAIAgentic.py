from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import (
    Agent, Runner, function_tool, OpenAIChatCompletionsModel
)
from typing import Dict, Any
import os
import pandas as pd
import shutil
from pydantic import BaseModel

load_dotenv()

# Set ROOT_DIR to current working directory by default for portability
ROOT_DIR = os.getenv("ROOT_DIR", os.getcwd())
CONFIG_FILE_PATH = os.path.join(ROOT_DIR, "config", "configfile.xlsx")
LOCAL_SHAREPOINT_DIR = os.path.join(ROOT_DIR, "local_sharepoint")
TEMP_DIR = os.path.join(ROOT_DIR, "temp_files")
S3_UPLOAD_DIR = os.path.join(ROOT_DIR, "S3_upload")
SFX_DEST_DIR = os.path.join(ROOT_DIR, "SP_upload")

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(S3_UPLOAD_DIR, exist_ok=True)
os.makedirs(SFX_DEST_DIR, exist_ok=True)

# ---------------------- Tool Definitions ----------------------

class ConfigRowInput(BaseModel):
    Filename: str
    File_Routing: str
    OutputFile: str
    Columns: Any = None
    OutputExt: str = "csv"
    AddFileName: str = "N"
    Download: str = "Y"
    # Add other fields as needed
    class Config:
        extra = "ignore"

@function_tool
def config_analyzer(input: ConfigRowInput) -> Dict[str, Any]:
    """Reads and validates a config row, returns a structured task plan."""
    row = input.dict()
    required = ["Filename", "File_Routing", "OutputFile"]
    for key in required:
        if not row.get(key):
            return {"error": f"Missing required field: {key}", "row": row}
    return {"task": row, "status": "ok"}

class FileLocatorInput(BaseModel):
    filename: str

@function_tool
def smart_file_locator(input: FileLocatorInput) -> Dict[str, Any]:
    """Finds the latest relevant file in SharePoint (simulated)."""
    path = os.path.join(LOCAL_SHAREPOINT_DIR, f"{input.filename}.xlsx")
    if not os.path.exists(path):
        return {"error": f"File not found: {path}"}
    return {"file_path": path}

class SchemaValidationInput(BaseModel):
    file_path: str
    expected_columns: Any

@function_tool
def schema_validator(input: SchemaValidationInput) -> Dict[str, Any]:
    df = pd.read_excel(input.file_path)
    expected = input.expected_columns
    if isinstance(expected, str) and ":" in expected:
        from_col, to_col = expected.split(":")
        actual_cols = df.columns.tolist()
        if len(actual_cols) < 1:
            return {"error": "No columns found"}
    return {"status": "pass", "columns": df.columns.tolist()}

class DataExtractorInput(BaseModel):
    file_path: str
    columns: Any
    add_filename: str

@function_tool
def data_extractor(input: DataExtractorInput) -> Dict[str, Any]:
    df = pd.read_excel(input.file_path)
    col_range = input.columns
    if pd.isna(col_range):
        df_selected = df
    elif ":" in str(col_range):
        from_col, to_col = col_range.split(":")
        def excel_col_to_idx(col):
            col = col.strip().upper()
            idx = 0
            for char in col:
                idx = idx * 26 + (ord(char) - ord('A') + 1)
            return idx - 1
        start_idx = excel_col_to_idx(from_col)
        end_idx = excel_col_to_idx(to_col)
        df_selected = df.iloc[:, start_idx:end_idx+1]
    else:
        df_selected = df[col_range.split(",")]
    if str(input.add_filename).upper() == "Y":
        df_selected["SourceFileName"] = os.path.basename(input.file_path)
    temp_csv = input.file_path.replace(".xlsx", "_extracted.csv")
    df_selected.to_csv(temp_csv, index=False)
    return {"csv_path": temp_csv, "columns": df_selected.columns.tolist()}

class DataProfilerInput(BaseModel):
    csv_path: str

@function_tool
def data_profiler(input: DataProfilerInput) -> Dict[str, Any]:
    df = pd.read_csv(input.csv_path)
    nulls = df.isnull().sum().sum()
    dups = df.duplicated().sum()
    return {"nulls": int(nulls), "duplicates": int(dups), "status": "ok"}

class OutputFormatterInput(BaseModel):
    csv_path: str
    output_file: str
    output_ext: str

@function_tool
def output_formatter(input: OutputFormatterInput) -> Dict[str, Any]:
    df = pd.read_csv(input.csv_path)
    out_path = os.path.join(TEMP_DIR, f"{input.output_file}.{input.output_ext}")
    df.to_csv(out_path, index=False)
    return {"final_csv": out_path}

class DestinationRouterInput(BaseModel):
    final_csv: str
    File_Routing: str

@function_tool
def destination_router(input: DestinationRouterInput) -> Dict[str, Any]:
    s3_path = os.path.join(S3_UPLOAD_DIR, os.path.basename(input.final_csv))
    sfx_path = os.path.join(SFX_DEST_DIR, os.path.basename(input.final_csv))
    if input.File_Routing.lower() == "process":
        shutil.copy2(input.final_csv, s3_path)
        shutil.copy2(input.final_csv, sfx_path)
        return {"uploaded": [s3_path, sfx_path]}
    elif input.File_Routing.lower() == "move":
        shutil.copy2(input.final_csv, sfx_path)
        return {"uploaded": [sfx_path]}
    else:
        return {"error": f"Unknown File_Routing: {input.File_Routing}"}

class AuditLogInput(BaseModel):
    log: str

@function_tool
def audit_logger(input: AuditLogInput) -> Dict[str, Any]:
    print(f"[AUDIT LOG] {input.log}")
    return {"status": "logged"}

# ---------------------- Agent Prompt ----------------------

instructions = """
You are a multi-step file processing agent. For each config row:
- Analyze the config and validate schema.
- Locate the correct file in SharePoint.
- Validate the file's schema.
- Extract the required columns.
- Profile the data for quality.
- Format the output as a standardized CSV.
- Route the file to the correct destination(s) based on File_Routing.
- Log all actions and errors.
- If a critical error occurs, escalate to a human.
Use the available tools to perform each step. Report your actions and results.
"""

# ---------------------- Agent and Runner ----------------------

openai_client = AsyncOpenAI()

agent = Agent(
    name="FileProcessingAgent",
    instructions=instructions,
    tools=[
        config_analyzer, smart_file_locator, schema_validator, data_extractor,
        data_profiler, output_formatter, destination_router, audit_logger
    ],
    model=OpenAIChatCompletionsModel(openai_client=openai_client, model="gpt-4o-mini"),
)

def _config_analyzer(input: ConfigRowInput) -> Dict[str, Any]:
    row = input.dict()
    required = ["Filename", "File_Routing", "OutputFile"]
    for key in required:
        if not row.get(key):
            return {"error": f"Missing required field: {key}", "row": row}
    return {"task": row, "status": "ok"}

def _smart_file_locator(input: FileLocatorInput) -> Dict[str, Any]:
    path = os.path.join(LOCAL_SHAREPOINT_DIR, f"{input.filename}.xlsx")
    if not os.path.exists(path):
        return {"error": f"File not found: {path}"}
    return {"file_path": path}

def _schema_validator(input: SchemaValidationInput) -> Dict[str, Any]:
    df = pd.read_excel(input.file_path)
    expected = input.expected_columns
    if isinstance(expected, str) and ":" in expected:
        from_col, to_col = expected.split(":")
        actual_cols = df.columns.tolist()
        if len(actual_cols) < 1:
            return {"error": "No columns found"}
    return {"status": "pass", "columns": df.columns.tolist()}

def _data_extractor(input: DataExtractorInput) -> Dict[str, Any]:
    df = pd.read_excel(input.file_path)
    col_range = input.columns
    if pd.isna(col_range):
        df_selected = df
    elif ":" in str(col_range):
        from_col, to_col = col_range.split(":")
        def excel_col_to_idx(col):
            col = col.strip().upper()
            idx = 0
            for char in col:
                idx = idx * 26 + (ord(char) - ord('A') + 1)
            return idx - 1
        start_idx = excel_col_to_idx(from_col)
        end_idx = excel_col_to_idx(to_col)
        df_selected = df.iloc[:, start_idx:end_idx+1]
    else:
        df_selected = df[col_range.split(",")]
    if str(input.add_filename).upper() == "Y":
        df_selected["SourceFileName"] = os.path.basename(input.file_path)
    temp_csv = input.file_path.replace(".xlsx", "_extracted.csv")
    df_selected.to_csv(temp_csv, index=False)
    return {"csv_path": temp_csv, "columns": df_selected.columns.tolist()}

def _data_profiler(input: DataProfilerInput) -> Dict[str, Any]:
    df = pd.read_csv(input.csv_path)
    nulls = df.isnull().sum().sum()
    dups = df.duplicated().sum()
    return {"nulls": int(nulls), "duplicates": int(dups), "status": "ok"}

def _output_formatter(input: OutputFormatterInput) -> Dict[str, Any]:
    df = pd.read_csv(input.csv_path)
    out_path = os.path.join(TEMP_DIR, f"{input.output_file}.{input.output_ext}")
    df.to_csv(out_path, index=False)
    return {"final_csv": out_path}

def _destination_router(input: DestinationRouterInput) -> Dict[str, Any]:
    s3_path = os.path.join(S3_UPLOAD_DIR, os.path.basename(input.final_csv))
    sfx_path = os.path.join(SFX_DEST_DIR, os.path.basename(input.final_csv))
    if input.File_Routing.lower() == "process":
        shutil.copy2(input.final_csv, s3_path)
        shutil.copy2(input.final_csv, sfx_path)
        return {"uploaded": [s3_path, sfx_path]}
    elif input.File_Routing.lower() == "move":
        shutil.copy2(input.final_csv, sfx_path)
        return {"uploaded": [sfx_path]}
    else:
        return {"error": f"Unknown File_Routing: {input.File_Routing}"}

def _audit_logger(input: AuditLogInput) -> Dict[str, Any]:
    print(f"[AUDIT LOG] {input.log}")
    return {"status": "logged"}

async def main():
    df = pd.read_excel(CONFIG_FILE_PATH)
    for _, row in df.iterrows():
        if str(row.get("Download", "Y")).strip().upper() != "Y":
            continue
        row_dict = row.to_dict()
        # Step 1: Analyze config
        result = _config_analyzer(ConfigRowInput(**row_dict))
        print(f"Config analysis result: {result}")
        if "error" in result:
            _audit_logger(AuditLogInput(log=f"Config error: {result['error']}"))
            continue
        task = result["task"]
        # Step 2: Locate file
        file_result = _smart_file_locator(FileLocatorInput(filename=task["Filename"]))
        print(f"File location result: {file_result}")
        if "error" in file_result:
            _audit_logger(AuditLogInput(log=f"File error: {file_result['error']}"))
            continue
        file_path = file_result["file_path"]
        # Step 3: Schema validation
        schema_result = _schema_validator(SchemaValidationInput(file_path=file_path, expected_columns=task["Columns"]))
        print(f"Schema validation result: {schema_result}")
        if "error" in schema_result:
            _audit_logger(AuditLogInput(log=f"Schema error: {schema_result['error']}"))
            continue
        # Step 4: Data extraction
        extract_result = _data_extractor(DataExtractorInput(file_path=file_path, columns=task["Columns"], add_filename=task.get("AddFileName", "N")))
        print(f"Data extraction result: {extract_result}")
        # Step 5: Data profiling
        profile_result = _data_profiler(DataProfilerInput(csv_path=extract_result["csv_path"]))
        print(f"Data profiling result: {profile_result}")
        # Step 6: Output formatting
        format_result = _output_formatter(OutputFormatterInput(csv_path=extract_result["csv_path"], output_file=task["OutputFile"], output_ext=task["OutputExt"]))
        print(f"Output formatting result: {format_result}")
        # Step 7: Destination routing
        route_result = _destination_router(DestinationRouterInput(final_csv=format_result["final_csv"], File_Routing=task["File_Routing"]))
        print(f"Destination routing result: {route_result}")
        # Step 8: Audit log
        _audit_logger(AuditLogInput(log=f"Task {task['Filename']} complete. Uploaded: {route_result.get('uploaded', [])}"))
    print("\n🎯 Pipeline complete.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())