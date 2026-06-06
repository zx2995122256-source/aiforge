from api.project import AGENT_SYSTEM_PROMPT
try:
    result = AGENT_SYSTEM_PROMPT.format(project_context="test")
    print("OK - format works")
    print(result[:200])
except KeyError as e:
    print(f"KeyError: {e}")
except Exception as e:
    print(f"Error: {e}")
