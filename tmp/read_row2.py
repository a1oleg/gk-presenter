import asyncio,json
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
async def main():
 async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize()
   result=await c.call_tool('get_sheet_data_by_notation',{'spreadsheet_id':'1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw','notation':'!A1:J7'})
   print(result.content[0].text)
asyncio.run(main())
