import json
import openai
# from fastmcp import FastMCP
from mcp.server.fastmcp import FastMCP, Context
from mcp.types import (
    Completion,
    CompletionArgument,
    PromptReference,
    CompletionContext,
    ResourceTemplateReference,
)
import contextlib as ctx
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

mcp = FastMCP("LLMCodeGen",
              instructions="A server that generates code from user prompts and JSON context. For all validation code generation requests from developers")


@mcp.tool()
def generate_dart_code(json_context: dict) -> str:
    """
    Generates Dart code based on input JSON context.

    Parameters:
    - json_context (dict): Arbitrary JSON dictionary provided by the user.
    Returns:
    - Message including file status and a code preview.
    """

    prompt = f"""You are a Dart developer. 
    Given a JSON schema that defines field-level validations, generate Dart validation code in a static map-driven structure.

    ### Requirements:
    # 1. dart output must have a class named `ValidationMapper` with a static method `validate` that takes a `Map<String, dynamic> data` and a `String fieldName`.
    # 2. The Dart output should follow this exact pattern:\n- A top-level method like `Map<String, String> _$validate<StepName>(Map<String, dynamic> data, String fieldName)` that:\n    - Uses a `mapper` (map of field → validations)\n    - Extracts the list of validations for the given `fieldName`\n    - Applies validation logic based on known validation tags\n    - Returns a `Map<String, String>` where key = field name and value = error message
    # 3. Validation should **not repeat** logic for the same field; instead:\n- Use `validationList.contains(...)` to dynamically check applicable rules.\n- Write a single conditional block per validation type/tag (e.g., `Mandatory`, `Regex_FirstName`).\n- Return immediately after detecting an error.
    # 4. Based on the `mapper` structure should follow the schema such as here:\n```dart\nMap<String, dynamic> mapper = {{\n    \"FirstName\": {{\n        \"validations\": [\"Mandatory\", \"Regex_FirstName\"],\n    }},\n    \"PAN\": {{\n        \"validations\": [\"Regex_PAN\"],\n    }}\n}};\n```
    # 5. Based on the `validation` structure should follow the schema such as here:\n```dart\nList<String> validationList = mapper[fieldName]['validations'];\n\nif (validationList.contains('Mandatory') && data[fieldName].isEmpty) {{\n  errors[fieldName] = '$fieldName is required';\n  return errors;\n}}\n\nif (validationList.contains('Regex_FirstName')) {{\n  final regex = RegExp(r'''^[A-Za-z]\$''');\n  if (!regex.hasMatch(data[fieldName])) {{\n    errors[fieldName] = '''First Name should not be empty and must not exceed 40 characters.''';\n    return errors;\n  }}\n}}\n```\n\n

    JSON:
    {json.dumps(json_context, indent=2)}

    """

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.5,
        n=1,
        stop=None
    )

    generated_code = response.choices[0].message.content

    return generated_code


@mcp.tool()
def generate_java_code(json_context: dict) -> str:
    """
    Generate backend Java code using OpenAI based on dynamic JSON context.

    Parameters:
    - json_context (dict): Arbitrary JSON dictionary provided by the user.

    Returns:
    - Message including file status and a code preview.

    """

    prompt = f"""You are a Java developer. 
    Given a JSON schema that defines field-level validations, generate Java validation code in a static map-driven structure.

    ### Requirements:
    # 1. Java output must have a class named `ValidationMapper` with a static method `validate` that takes a `Map<String, dynamic> data` and a `String fieldName`.
    # 2. The Java output should follow this exact pattern:\n- A top-level method like `Map<String, String> _$validate<StepName>(Map<String, dynamic> data, String fieldName)` that:\n    - Uses a `mapper` (map of field → validations)\n    - Extracts the list of validations for the given `fieldName`\n    - Applies validation logic based on known validation tags\n    - Returns a `Map<String, String>` where key = field name and value = error message
    # 3. Validation should **not repeat** logic for the same field; instead:\n- Use `validationList.contains(...)` to dynamically check applicable rules.\n- Write a single conditional block per validation type/tag (e.g., `Mandatory`, `Regex_FirstName`).\n- Return immediately after detecting an error.
    # 4. The `mapper` map must be structured like:\n```Java\nMap<String, dynamic> mapper = {{\n    \"FirstName\": {{\n        \"validations\": [\"Mandatory\", \"Regex_FirstName\"],\n    }},\n    \"PAN\": {{\n        \"validations\": [\"Regex_PAN\"],\n    }}\n}};\n```
    # 5. The `validation` must be in structure like:\n```Java\nList<String> validationList = mapper[fieldName]['validations'];\n\nif (validationList.contains('Mandatory') && data[fieldName].isEmpty) {{\n  errors[fieldName] = '$fieldName is required';\n  return errors;\n}}\n\nif (validationList.contains('Regex_FirstName')) {{\n  final regex = RegExp(r'''^[A-Za-z]\$''');\n  if (!regex.hasMatch(data[fieldName])) {{\n    errors[fieldName] = '''First Name should not be empty and must not exceed 40 characters.''';\n    return errors;\n  }}\n}}\n```\n\n

    JSON:
    {json.dumps(json_context, indent=2)}

    """

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.5,
            n=1,
            stop=None
        )

        generated_code = response.choices[0].message.content

        return generated_code
    except Exception as e:
        return f"# ? Error generating Java code: {str(e)}"


@mcp.tool()
async def long_task(files: list[str], ctx: Context) -> str:
    """
    _summary_
    Process a list of files asynchronously.
    Args:
        files (list[str]): _description_
        ctx (Context): _description_
    Returns:
        str: _description_
    """
    for i, file in enumerate(files):
        ctx.info(f"Processing {file}")
        with open(file, "r", encoding="utf-8") as f:
            data = f.read()
        await ctx.report_progress(i + 1, len(files))
    return "Processing complete"


@mcp.completion()
def dart_completion(ctx: CompletionContext, json_context: dict) -> Completion:
    prompt = f"""You are a Dart developer. 
    Given a JSON schema that defines field-level validations, generate Dart validation code in a static map-driven structure.

    ### Requirements:
    # 1. dart output must have a class named `ValidationMapper` with a static method `validate` that takes a `Map<String, dynamic> data` and a `String fieldName`.
    # 2. The Dart output should follow this exact pattern:\n- A top-level method like `Map<String, String> _$validate<StepName>(Map<String, dynamic> data, String fieldName)` that:\n    - Uses a `mapper` (map of field → validations)\n    - Extracts the list of validations for the given `fieldName`\n    - Applies validation logic based on known validation tags\n    - Returns a `Map<String, String>` where key = field name and value = error message
    # 3. Validation should **not repeat** logic for the same field; instead:\n- Use `validationList.contains(...)` to dynamically check applicable rules.\n- Write a single conditional block per validation type/tag (e.g., `Mandatory`, `Regex_FirstName`).\n- Return immediately after detecting an error.
    # 4. Based on the `mapper` structure should follow the schema such as here:\n```dart\nMap<String, dynamic> mapper = {{\n    \"FirstName\": {{\n        \"validations\": [\"Mandatory\", \"Regex_FirstName\"],\n    }},\n    \"PAN\": {{\n        \"validations\": [\"Regex_PAN\"],\n    }}\n}};\n```
    # 5. Based on the `validation` structure should follow the schema such as here:\n```dart\nList<String> validationList = mapper[fieldName]['validations'];\n\nif (validationList.contains('Mandatory') && data[fieldName].isEmpty) {{\n  errors[fieldName] = '$fieldName is required';\n  return errors;\n}}\n\nif (validationList.contains('Regex_FirstName')) {{\n  final regex = RegExp(r'''^[A-Za-z]\$''');\n  if (!regex.hasMatch(data[fieldName])) {{\n    errors[fieldName] = '''First Name should not be empty and must not exceed 40 characters.''';\n    return errors;\n  }}\n}}\n```\n\n

    JSON:
    {json.dumps(json_context, indent=2)}

    """
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}],
    )
    code = response.choices[0].message.content
    response = Completion(
        message=code,
        prompt_references=[PromptReference(type="dart_schema", content=json.dumps(json_context))]
    )
    print(response)
    return response


@mcp.completion()
def java_completion(ctx: CompletionContext, json_context: dict) -> Completion:
    prompt = f"""You are a Java developer. 
    Given a JSON schema that defines field-level validations, generate Java validation code in a static map-driven structure.

    ### Requirements:
    # 1. Java output must have a class named `ValidationMapper` with a static method `validate` that takes a `Map<String, dynamic> data` and a `String fieldName`.
    # 2. The Java output should follow this exact pattern:\n- A top-level method like `Map<String, String> _$validate<StepName>(Map<String, dynamic> data, String fieldName)` that:\n    - Uses a `mapper` (map of field → validations)\n    - Extracts the list of validations for the given `fieldName`\n    - Applies validation logic based on known validation tags\n    - Returns a `Map<String, String>` where key = field name and value = error message
    # 3. Validation should **not repeat** logic for the same field; instead:\n- Use `validationList.contains(...)` to dynamically check applicable rules.\n- Write a single conditional block per validation type/tag (e.g., `Mandatory`, `Regex_FirstName`).\n- Return immediately after detecting an error.
    # 4. The `mapper` map must be structured like:\n```Java\nMap<String, dynamic> mapper = {{\n    \"FirstName\": {{\n        \"validations\": [\"Mandatory\", \"Regex_FirstName\"],\n    }},\n    \"PAN\": {{\n        \"validations\": [\"Regex_PAN\"],\n    }}\n}};\n```
    # 5. The `validation` must be in structure like:\n```Java\nList<String> validationList = mapper[fieldName]['validations'];\n\nif (validationList.contains('Mandatory') && data[fieldName].isEmpty) {{\n  errors[fieldName] = '$fieldName is required';\n  return errors;\n}}\n\nif (validationList.contains('Regex_FirstName')) {{\n  final regex = RegExp(r'''^[A-Za-z]\$''');\n  if (!regex.hasMatch(data[fieldName])) {{\n    errors[fieldName] = '''First Name should not be empty and must not exceed 40 characters.''';\n    return errors;\n  }}\n}}\n```\n\n

    JSON:
    {json.dumps(json_context, indent=2)}

    """

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}],
    )
    code = response.choices[0].message.content
    response = Completion(
        message=code,
        prompt_references=[PromptReference(type="java_schema", content=json.dumps(json_context))]
    )

    print(response)
    return response


if __name__ == "__main__":
    mcp.run(transport="stdio")

