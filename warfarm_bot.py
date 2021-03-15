import discord
import os
import time
import warfarm as wf
import pandas as pd

client = discord.Client()

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hi'):
        await message.channel.send('hello')

    if message.content.startswith('$link'):
        await message.delete()
        try:
            link = message.content.split()[1]
        except:
            await message.channel.send("Enter a valid link")
        else:
            item_orders = {}

            items = wf.get_item_list(link)

            for item in items:
                orders = wf.get_market_prices(item, 'item')
                if orders:
                    df_orders = pd.json_normalize(orders['orders'])
                    df_sell = df_orders[(df_orders['user.status'] == 'ingame') & (df_orders['order_type'] == 'sell')]
                    df_buy = df_orders[(df_orders['user.status'] == 'ingame') & (df_orders['order_type'] == 'buy')]
                    sell_orders = df_sell.nsmallest(5, 'platinum')['platinum'].values
                    buy_orders = df_buy.nlargest(5, 'platinum')['platinum'].values
                    item_orders.update({item : [sell_orders, buy_orders, item.lower().replace(' ','_').replace('-','_').replace("'",'').replace('&','and')]})

                time.sleep(0.4)

            await message.channel.send(item_orders)

client.run(os.getenv('TOKEN'))
