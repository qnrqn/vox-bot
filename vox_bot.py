import datetime
import os
import random
import discord
from discord.ext import commands, tasks

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="티비할배 ", intents=intents)

# ==================== [채널 ID 설정] ====================
MEAL_CHANNEL_ID = 1540214199853260900  # 식단 인증 채널 ID (포럼 채널)
NAG_CHANNEL_ID = 1540247977979809854  # 잔소리 채널 ID
# ========================================================

# 귀찮아하는 툭툭 던지는 호출 응답 대사 (20개)
CALL_RESPONSES = [
    "📺 뭐야?",
    "📺 아 왜 또 불러.",
    "📺 볼일 없으면 부르지 마라.",
    "📺 귀찮게 굴지 말고 식단이나 올려.",
    "📺 뭐. 할 말 있냐?",
    "📺 바쁘니까 용건만 말해.",
    "📺 식단 사진 안 올리고 왜 헛소리야?",
    "📺 아, 진짜 귀찮게 하네.",
    "📺 또 왜. 식단은 올렸냐?",
    "📺 헛소리할 시간에 운동이나 해라.",
    "📺 쓸데없이 부르지 마.",
    "📺 뭔데. 말해봐.",
    "📺 귀찮아 죽겠네, 진짜.",
    "📺 내가 네 심심풀이냐?",
    "📺 그럴 시간 있으면 몸이나 움직여.",
    "📺 아 어쩌라고. 사진이나 제출해.",
    "📺 안 바빠 보이니까 당장 식단이나 찍어 올려.",
    "📺 호출 버튼 눌러서 뭐 하게?",
    "📺 짹짹거리지 말고 할 일이나 해라.",
    "📺 또 뭔 헛소리를 하려고.",
]

# 간결한 시간대별 알림
MORNING_QUOTES = [
    "📺 아침 먹었나? 사진 올려라.",
    "📺 아침 인증 시작한다. 제출해.",
    "📺 아침 식단 등록해라, 등신들아.",
    "📺 오늘도 보고 있다. 아침 사진 올려.",
    "📺 아침 식단 제출 시간이다. 당장 올려라.",
    "📺 아침부터 멍때리지 말고 사진 제출해.",
    "📺 굶지 마라. 아침 식단 찍어서 올려.",
    "📺 아침 데이터 수집 시작한다.",
    "📺 게으르게 굴지 말고 아침 식단 제출해라.",
    "📺 아침이다. 사진 올리고 시작해.",
]

LUNCH_QUOTES = [
    "📺 점심시간이다. 식단 사진 제출해.",
    "📺 점심 인증해라.",
    "📺 점심 올릴 시간이다. 사진 준비해라.",
    "📺 점심 식단 입력해라.",
    "📺 딴짓 말고 점심 사진이나 딱 올려라.",
    "📺 점심 먹고 있냐? 지켜보고 있다.",
    "📺 점심 식사 제대로 찍어서 제출해.",
    "📺 점심이다. 식단 사진 올려라.",
    "📺 점심에 뭐 먹는지 똑똑히 보여라.",
    "📺 점심 식단 제출해라. 바로 확인한다.",
]

DINNER_QUOTES = [
    "📺 저녁 사진 올려라.",
    "📺 저녁 식단 제출해. 야식 생각은 접어라.",
    "📺 저녁 시간이다. 사진 찍어서 제출해라.",
    "📺 오늘 저녁은 뭐냐? 사진 올리고 끝내라.",
    "📺 방심하지 마라. 저녁 식단 인증해.",
    "📺 저녁 스레드 열었다. 식단 사진 남겨라.",
    "📺 저녁 데이터 수집한다. 사진 제출해라.",
    "📺 오늘 하루 마무리다. 저녁 식단 올려.",
    "📺 저녁 사진 제출해라. 보고 있다.",
    "📺 저녁 식사 인증 개시. 당장 올려라.",
]

# 간결하고 직관적인 돌발 독설/동기부여 대사
RANDOM_VOX_QUOTES = [
    '📺 "VoxTek 감시 시스템 작동 중이다. 당장 움직여."',
    '📺 "살 빼라, 이 등신들아."',
    '📺 "화면 너머로 다 보고 있다. 똑바로 해라."',
    '📺 "칼로리 계산은 제대로 하고 입에 넣는 건가?"',
    '📺 "오늘 쉴 생각이었나? 당장 운동해라."',
    '📺 "지방이나 태워라. 노는 꼴 못 본다."',
    '📺 "거울이나 봐라. 그게 만족스럽나?"',
    '📺 "유혹에 넘어가는 순간 내 손아귀 안이다."',
    '📺 "의지력이 그것밖에 안 되나? 더 올려라."',
    '📺 "핑계 대지 마라. 결과로 증명해."',
    '📺 "CCTV는 거짓말을 안 한다. 똑바로 해."',
    '📺 "포기할 거면 미리 말해라. 바로 걸러낼 테니."',
]


@bot.event
async def on_ready():
  print(f"📺 [VoxTek Network] {bot.user.name} 가동 시작!")
  meal_check_loop.start()
  random_event_loop.start()


# ---------------------------------------------------------
# [기능 1] 식사 인증 포럼 포스트 자동 생성 (포럼 채널 전용)
# ---------------------------------------------------------
@tasks.loop(minutes=1)
async def meal_check_loop():
  now = datetime.datetime.now()
  time_str = now.strftime("%H:%M")
  today = now.strftime("%Y-%m-%d")

  channel = bot.get_channel(MEAL_CHANNEL_ID)
  if not channel:
    return

  # 포럼 채널인지 일반 채널인지에 따라 전송 방식 자동 분기
  async def send_meal_notice(title, quote):
    if isinstance(channel, discord.ForumChannel):
      # 포럼 채널일 경우: 새 포스트(스레드) 바로 생성
      await channel.create_thread(
          name=title, content=f"**[VoxTek] {today}**\n{quote}"
      )
    else:
      # 일반 텍스트 채널일 경우: 메시지 전송 후 하위 스레드 생성
      msg = await channel.send(f"**[VoxTek] {today}**\n{quote}")
      await msg.create_thread(name=title)

  # 시간대별 알림
  if time_str == "06:00":
    await send_meal_notice(
        f"📺 {today} 아침 식단 포스트", random.choice(MORNING_QUOTES)
    )

  elif time_str == "11:30":
    await send_meal_notice(
        f"📺 {today} 점심 식단 포스트", random.choice(LUNCH_QUOTES)
    )

  elif time_str == "18:00":
    await send_meal_notice(
        f"📺 {today} 저녁 식단 포스트", random.choice(DINNER_QUOTES)
    )


# ---------------------------------------------------------
# [기능 2] 돌발 대사 이벤트
# ---------------------------------------------------------
@tasks.loop(hours=2)
async def random_event_loop():
  now = datetime.datetime.now()

  if 6 <= now.hour < 24:
    if random.random() < 0.4:
      nag_channel = bot.get_channel(NAG_CHANNEL_ID)
      if nag_channel:
        quote = random.choice(RANDOM_VOX_QUOTES)
        await nag_channel.send(f"📺 **[VoxTek 경고]**\n{quote}")


# ---------------------------------------------------------
# [기능 3] 포럼 포스트/채널 감시 및 "티비할배" 호출 처리
# ---------------------------------------------------------
@bot.event
async def on_message(message):
  if message.author.bot:
    return

  # '티비할배'로 시작하는 호출 응답
  if message.content.startswith("티비할배"):
    reply = random.choice(CALL_RESPONSES)
    await message.channel.send(reply)
    return

  # 메시지가 포럼 본문이거나 포럼 안의 답글인지 확인
  is_target_channel = message.channel.id == MEAL_CHANNEL_ID
  is_target_thread = (
      getattr(message.channel, "parent_id", None) == MEAL_CHANNEL_ID
  )

  if is_target_channel or is_target_thread:
    # 사진이 첨부되어 있으면 반응 달기
    if message.attachments:
      await message.add_reaction("👍")
      await message.add_reaction("📺")

    # 사진이 없으면 경고 후 5초 뒤 자동 삭제
    elif not message.attachments:
      await message.channel.send(
          f"{message.author.mention} 사진올려.", delete_after=5
      )

  await bot.process_commands(message)


bot.run(os.environ["DISCORD_TOKEN"])
