import asyncio,json
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
text='Кодекс предложил поставить заглушку между логикой агента и обращением к модели — в самом начале queryModel, до вызова клиента Anthropic.\nЕсли заглушка включена, записываем попытку вызова и возвращаем заранее заданное сообщение. На этом функция заканчивает работу: запрос до модели не доходит, токены не тратятся.\nВыключаем заглушку — работает прежний путь.'
async def main():
 async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize()
   sid='1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'
   r=await c.call_tool('update_cells',{'spreadsheet_id':sid,'range_a1':"'Видео'!A35",'values_json':json.dumps([[text]],ensure_ascii=False),'value_input_option':'RAW'})
   assert not r.isError
   r=await c.call_tool('get_sheet_data_by_notation',{'spreadsheet_id':sid,'notation':'!A35'})
   assert json.loads(r.content[0].text)['values']==[[text]]
   print('A35 written and verified')
asyncio.run(main())
