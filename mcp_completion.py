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

# Load environment variables from .env file
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

mcp = FastMCP(
    "LLMCodeGen_with_completion",
    instructions="""
    This is a code generation server that generates Dart and Java code based on user input. 
    It can handle both JSON input for structured validation and natural language requests for dynamic code generation. Use the `/generate_dart_code` or `/generate_java_code` endpoints to generate code based on the provided JSON context or user request.
    The server supports dynamic code generation for Dart and Java, allowing users to input JSON schemas or natural language requests.
    The server will generate code based on the input, ensuring that the generated code adheres to the specified requirements and patterns.
    """
)


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


@mcp.completion()
async def handle_completion(
        ref: PromptReference | ResourceTemplateReference,
        argument: CompletionArgument,
        context: CompletionContext | None,
) -> Completion | None:
    # Only handle resource template completions
    if isinstance(ref, ResourceTemplateReference):
        # Target specific template
        if ref.uri == "github://repos/{owner}/{repo}" and argument.name == "repo":
            # Use previous 'owner' value from context
            owner = context.arguments.get("owner") if context and context.arguments else None
            if owner == "modelcontextprotocol":
                repos = ["python-sdk", "typescript-sdk", "specification"]
                # Filter suggestions based on current value
                matches = [r for r in repos if r.startswith(argument.value)]
                return Completion(values=matches)
    return None


# @mcp.completion()
# async def dynamic_completion(
#     ctx: CompletionContext,
#     mcp_ctx: Context,
# ) -> Completion:
#     """Handles dynamic code generation based on user input.
#     This function reads user input, checks if it's JSON, and generates Dart code accordingly.
#     If the input is not JSON, it uses OpenAI's API to generate code based on the user's natural language request.
#     Parameters:
#     - ctx (CompletionContext): The context containing the user's input prompt.
#     Returns:
#     - Completion: A completion object containing the generated code or error message.

#     1. If the user input is valid JSON, it generates Dart code using the `generate_dart_code` function.
#     2. If the input is not JSON, it sends the input to OpenAI's ChatCompletion API to generate Dart validation code based on the user's request.
#     3. The generated code is returned as a `Completion` object.

#     """
#     # Read whatever the user just typed

#     user_text = ctx.prompt
#     await mcp_ctx.info(f"Dynamic request: {user_text}")

#     # For example, let user enter JSON or a natural request
#     # You can inspect it: if it's JSON, parse; otherwise, embed directly.
#     try:
#         import json
#         json_context = json.loads(user_text)
#         await mcp_ctx.info("Detected JSON input; calling generate_dart_code tool")
#         code = generate_dart_code(json_context)
#         return Completion(text=code)
#     except json.JSONDecodeError:
#         resp = openai.chat.completions.create(
#           model="gpt-4o",
#           messages=[
#             {"role": "system", "content": "You're a Dart expert."},
#             {"role": "user", "content": user_text},
#           ]
#         )
#         return Completion(text=resp.choices[0].message.content)


if __name__ == "__main__":
    mcp.run(transport="stdio")

