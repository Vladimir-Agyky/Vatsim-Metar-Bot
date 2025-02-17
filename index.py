import discord
from discord import app_commands
from discord.ext import commands
import requests
import re
from config import TOKEN 

# 봇 초기화
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents)

def parse_metar(metar_text):
    metar_data = {
        "Station": "Unknown",
        "Time": "Unknown",
        "Wind": "Unknown",
        "Visibility": "Unknown",
        "Clouds": "None",
        "Temperature": "Unknown",
        "Dew Point": "Unknown",
        "Pressure": "Unknown",
        "Remarks": "None"
    }

    metar_info = metar_text.strip()

    time_match = re.search(r'(\d{6}Z)', metar_info)
    if time_match:
        metar_data["Time"] = time_match.group(1)


    wind_match = re.search(r'(\d{3})(\d{2})KT', metar_info)
    if wind_match:
        metar_data["Wind"] = f'{wind_match.group(1)}° {wind_match.group(2)}KT'

 
    visibility_match = re.search(r'(\d{2,4})(SM|KM|M)?', metar_info[20:])
    if visibility_match:
        metar_data["Visibility"] = visibility_match.group(1) + (visibility_match.group(2) if visibility_match.group(2) else "")


    clouds = []
    clouds_match = re.findall(r'(FEW|SCT|BKN|OVC)(\d{3,4})', metar_info)
    for cloud in clouds_match:
        clouds.append(f"{cloud[0]} {cloud[1]}ft")
    if clouds:
        metar_data["Clouds"] = ", ".join(clouds)

    
    temperature_match = re.search(r'(\d{2}|M\d{2})/(\d{2}|M\d{2})', metar_info)
    if temperature_match:
       
        temp = temperature_match.group(1)
        if "M" in temp:
            temp = f"-{temp[1:]}"
        metar_data["Temperature"] = f'{temp}°C'
        
        
        dew_point = temperature_match.group(2)
        if "M" in dew_point:
            dew_point = f"-{dew_point[1:]}"
        metar_data["Dew Point"] = f'{dew_point}°C'


    pressure_match = re.search(r'[QA](\d{4})', metar_info)
    if pressure_match:
        pressure_value = pressure_match.group(0)
        if pressure_value[0] == 'Q':
            metar_data["Pressure"] = f'{pressure_value} hPa (Default) / A{round(int(pressure_value[1:]) * 0.02953, 2)} inHg'
        elif pressure_value[0] == 'A':
            pressure_in_inhg = round(int(pressure_value[1:]) / 100, 2)
            metar_data["Pressure"] = f'A{pressure_in_inhg} inHg (Default) / Q{round(pressure_in_inhg * 33.864, 2)} hPa'


    remarks_match = re.search(r'(NOSIG|RMK.*)', metar_info)
    if remarks_match:
        metar_data["Remarks"] = remarks_match.group(1)

    return metar_data


def get_metar_from_php(icao_code):
    url = f'https://metar.vatsim.net/metar.php?id={icao_code.upper()}'
    response = requests.get(url)

    if response.status_code == 200:
        return response.text.strip()
    else:
        return f'Error: {response.status_code} - 데이터를 가져오는 데 실패했습니다.'

@bot.tree.command(name="metar", description="METAR 정보를 가져옵니다")
async def metar(interaction: discord.Interaction, icao_code: str):
    metar_text = get_metar_from_php(icao_code)
    
    if "Error" in metar_text:
        await interaction.response.send_message(metar_text)
    else:
        metar_data = parse_metar(metar_text)


        embed = discord.Embed(
            title=f"{icao_code.upper()} METAR",
            description=f"**METAR 정보**",
            color=discord.Color.blue()
        )
        embed.add_field(name="발행 시간", value=metar_data["Time"], inline=False)
        embed.add_field(name="바람", value=metar_data["Wind"], inline=True)
        embed.add_field(name="가시성", value=metar_data["Visibility"], inline=True)
        embed.add_field(name="구름", value=metar_data["Clouds"], inline=True)
        embed.add_field(name="온도", value=metar_data["Temperature"], inline=True)
        embed.add_field(name="이슬점", value=metar_data["Dew Point"], inline=True)
        embed.add_field(name="기압", value=metar_data["Pressure"], inline=True)
        embed.add_field(name="추가 정보", value=metar_data["Remarks"], inline=False)


        embed.add_field(name="RAW METAR", value=metar_text, inline=False)

        await interaction.response.send_message(embed=embed)


@bot.event
async def on_ready():
    await bot.tree.sync()  # 슬래시 명령어 동기화
    print(f"{bot.user}로 로그인되었습니다.")

# 봇 실행
bot.run(TOKEN)