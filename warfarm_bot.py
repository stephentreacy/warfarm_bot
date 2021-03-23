import discord
import os
import time
import warfarm as wf
import pandas as pd
import pymongo

def help_message():
    """Create Embeded message with available commands"""
    embed_help = discord.Embed(title='Avilable Commands')
    embed_help.add_field(name='$hi', value='Say hello', inline=False)
    embed_help.add_field(name='$view', value='Show database (Not to you though)', inline=False)
    embed_help.add_field(name='$link https://tenno.zone/planner/<unique ID>', value='Save tenno.zone link.', inline=False)
    embed_help.add_field(name='$items', value='Show orders of items from warframe.market.', inline=False)

    return embed_help

client_disc = discord.Client()

client_db = pymongo.MongoClient()
user_links_db = client_db['links_db']
user_links = user_links_db['user_links']

@client_disc.event
async def on_ready():
    print(f'Logged in as {client_disc.user}')

@client_disc.event
async def on_message(message):
    """Reads message on Discord and replies to commands"""
    
    #Ignores messages sent by bot
    if message.author == client_disc.user:
        return

    #Test case to check bot is replying
    if message.content.startswith('$hi'):
        await message.channel.send('hello')

    #Create Embeded message with commands
    if message.content.startswith('$help'):
        await message.channel.send(embed=help_message())

    #View database contents in console, will be removed.
    if message.content.startswith('$view'):
        await message.channel.send('You have no power here')
        for user in user_links.find():
            print(user)

    #Saves link to MongoDB
    if message.content.startswith('$link'):
        #Delete the message to prevent others using the link
        await message.delete()
        temp_message = await message.channel.send(f'Received link command from {message.author.mention}. Please wait...')
        try:
            link = message.content.split()[1]

            if not link.startswith('https://tenno.zone/planner/'):
                raise Exception

        except:
            await message.channel.send(f'{message.author.mention} Enter a valid link or type $help')
        else:
            try:
                user_links.update_one(dict(user=message.author.id), {'$set':{'link':link}},upsert=True)
            except: 
                await message.channel.send(f'{message.author.mention} Cannot connect to Database. Please try again') 
            else:
                await message.channel.send(f'Successfully added tenno.zone link for {message.author.mention}')
        finally:
            await temp_message.delete()

    #Get link from database and replies with messages containing item orders
    if message.content.startswith('$items'):
        #TODO check link exists
            link= user_links.find_one({'user':message.author.id},{'link':1})['link']

            items = wf.get_item_list(link)

            for item in items:
                orders = wf.get_market_prices(item, 'item')
                if orders:
                    df_orders = pd.json_normalize(orders['orders'])
                    df_sell = df_orders[(df_orders['user.status'] == 'ingame') & (df_orders['order_type'] == 'sell')]
                    df_buy = df_orders[(df_orders['user.status'] == 'ingame') & (df_orders['order_type'] == 'buy')]
                    sell_orders = df_sell.nsmallest(5, 'platinum')['platinum'].values.tolist()
                    sell_orders = ', '.join(str(int(order)) for order in sell_orders) if sell_orders else 'None'
                    buy_orders = df_buy.nlargest(5, 'platinum')['platinum'].values.tolist()
                    buy_orders = ', '.join(str(int(order)) for order in buy_orders) if buy_orders else 'None'

                    #Create Embeded message with item information
                    embed_item = discord.Embed(title=item, url='https://warframe.market/items/' + item.lower().replace(' ','_').replace('-','_').replace("'",'').replace('&','and'))
                    embed_item.add_field(name='Buy Orders', value=buy_orders, inline=False)
                    embed_item.add_field(name='Sell Orders', value=sell_orders, inline=False)
                    await message.channel.send(embed=embed_item)

                #Wait between items to keep within 3 API requests per second
                await discord.asyncio.sleep(0.4)

client_disc.run(os.getenv('TOKEN'))
