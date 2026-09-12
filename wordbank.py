# -*- coding: utf-8 -*-
# 3-6 岁儿童英语（CEFR Pre-A1 / A1）全量词表，用于一次性扩充满意发音库。
# 目标：让"当天 OCR 新挑的词"绝大多数直接命中，不必再等人工补音频。
import json, os, re

CATS = {}

CATS['动物'] = """
cat dog bird fish rabbit duck pig cow horse sheep chicken duckling goat mouse monkey tiger lion bear
elephant giraffe zebra panda kangaroo penguin dolphin whale shark turtle frog snake bee ant butterfly
spider worm snail crab octopus seal walrus fox wolf deer squirrel hedgehog bat owl parrot swan peacock
crab eagle hawk camel donkey lamb turkey goose frog crocodile hippo rhino sloth koala raccoon skunk
chick calf puppy kitten bunny lamb cub joey fawn tadpole caterpillar ladybug dragonfly grasshopper
"""

CATS['颜色形状'] = """
red blue yellow green orange purple pink black white brown gray grey gold silver
circle square triangle star heart diamond oval rectangle line dot cross cube sphere cone
big small long short tall short round flat wide narrow thick thin heavy light
"""

CATS['数字'] = """
one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen
sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred
first second third fourth fifth last next zero half double triple many few more less
"""

CATS['身体'] = """
head hair face eye ear nose mouth tooth teeth tongue lip chin cheek neck shoulder arm elbow
hand finger thumb nail leg knee foot toe skin bone belly back chest waist finger toes
body knee wrist ankle heel eyebrow eyelash forehead brain heart stomach
"""

CATS['家人人物'] = """
mother father mom dad parent sister brother grandmother grandfather grandma grandpa aunt uncle
cousin baby child kid boy girl man woman friend neighbor teacher doctor nurse police
family people son daughter husband wife children adult teenager
"""

CATS['食物'] = """
apple banana orange grape pear peach cherry strawberry watermelon lemon mango pineapple kiwi
bread milk egg cheese butter rice noodle soup meat chicken fish cake cookie candy chocolate
ice cream juice water tea coffee sugar salt pepper honey jam yogurt carrot potato tomato
onion cucumber pumpkin corn bean pea mushroom cabbage lettuce celery garlic ginger
pizza hamburger sandwich salad pasta breakfast lunch dinner snack dessert biscuit pancake
cereal oatmeal popcorn nuts peanut walnut raisin olive oil vinegar sauce
"""

CATS['衣物'] = """
shirt T-shirt dress skirt pants shorts jeans coat jacket sweater hoodie socks shoes boots
hat cap scarf glove mitten belt button pocket zipper uniform pajamas swimsuit
sweatshirt blouse tie suit raincoat sandal slipper sneaker
"""

CATS['家居'] = """
house home room kitchen bedroom bathroom living room door window wall floor ceiling roof
bed sofa chair table desk lamp light clock mirror shelf box bag basket bottle cup
bowl plate spoon fork knife glass pot pan towel soap brush comb key lock
curtain carpet pillow blanket quilt sheet wardrobe drawer fridge stove oven
"""

CATS['学校文具'] = """
school classroom book pen pencil eraser ruler bag backpack crayon marker glue scissors
paper notebook page word letter number picture drawing paint brush color chalk board
student class lesson homework test question answer story song game
"""

CATS['交通'] = """
car bus train plane ship boat bike bicycle truck taxi subway motorcycle rocket
wheel engine road street bridge station airport port ticket driver passenger
traffic light seat belt map sign
"""

CATS['动作'] = """
go come run walk jump hop skip climb swim fly fall sit stand lie sleep wake
eat drink bite chew swallow cook bake wash clean brush comb dress wear
open close push pull carry hold give take put pick drop throw catch kick
read write draw paint sing dance play work help look see watch listen hear
smell taste touch feel think know learn teach ask answer say speak talk
cry laugh smile hug kiss love like want need have make do
buy sell pay cost find lose keep save use fix build break cut
drive ride sail travel move stop start wait hurry stay leave arrive return
climb dance swim skate slide swing bounce spin turn bend stretch
"""

CATS['形容词'] = """
happy sad angry tired hungry thirsty hot cold warm cool wet dry clean dirty
fast slow quick early late new old young big small little large tiny huge
good bad nice kind funny pretty beautiful ugly loud quiet soft hard
easy difficult fun boring interesting exciting scary brave afraid
strong weak heavy light full empty open closed safe dangerous
sweet sour salty bitter spicy fresh delicious yucky
smart clever silly busy free ready careful
"""

CATS['天气自然'] = """
sun sunny rain rainy snow snowy wind windy cloud cloudy storm fog ice
hot warm cool cold weather sky star moon earth world sea ocean river lake
mountain hill forest tree flower grass leaf plant seed root branch
beach sand stone rock water fire air soil ground field garden farm
"""

CATS['时间'] = """
morning afternoon evening night today tomorrow yesterday day week month year
hour minute second now then soon later early late always never sometimes often
Monday Tuesday Wednesday Thursday Friday Saturday Sunday weekend
January February March April May June July August September October November December
spring summer autumn fall winter season birthday holiday
"""

CATS['方位介词'] = """
in on under over above below behind between next to near far
up down left right front back here there inside outside
"""

CATS['职业'] = """
teacher doctor nurse driver farmer cook baker painter singer dancer
police firefighter pilot soldier engineer artist writer dentist
worker cleaner seller builder gardener fisherman
"""

CATS['玩具游戏'] = """
toy ball doll teddy bear robot kite balloon puzzle block Lego
game play playground swing slide seesaw sandcastle
bike scooter skateboard yo-yo marble bubble
"""

CATS['情绪礼貌'] = """
hello hi bye goodbye please thank you thanks sorry excuse me welcome
yes no okay sure maybe really wow oops hooray
"""

CATS['日常短语'] = """
get up wake up wash face brush teeth have breakfast go to school come home
do homework take a bath go to bed good night good morning good afternoon
sit down stand up come here go there turn around look at me listen to me
be careful hurry up slow down wait a minute all done let's go
thank you very much you're welcome excuse me I'm sorry never mind
how are you I'm fine what's this where is it who is that
let's play I want it can I have help me look out well done
put on take off turn on turn off pick up put down
"""

CATS['常见名词'] = """
name age color size shape sound music song story book movie
picture photo gift present party candle light shadow
water juice bubble soap towel toothbrush bed story
park zoo shop store market hospital library museum
city town village building house street
money coin price bag basket
job work rest sleep dream
"""

CATS['运动音乐'] = """
soccer basketball tennis baseball volleyball ping pong ball game team
run race jump throw catch kick score win lose
piano guitar drum violin flute music note sing song dance
"""

CATS['反义与功能词'] = """
and but or so because if when where what who how why
this that these those here there all some any every
my your his her its our their mine yours
can could will would should may must
is am are was were be been being have has had do does did
"""

def build():
    words = []
    for cat, blob in CATS.items():
        for w in blob.split():
            w = w.strip()
            if w:
                words.append(w)
    # 短语按整行保留（日常短语那一段本身是短语，需要按行拆）
    return words

def build_with_phrases():
    words = []
    # 单行词：按空白拆
    for cat, blob in CATS.items():
        if cat == '日常短语':
            for line in blob.strip().split('\n'):
                line = line.strip()
                if line:
                    words.append(line)
            continue
        for w in blob.split():
            w = w.strip()
            if w:
                words.append(w)
    # 去重保序
    seen, out = set(), []
    for w in words:
        k = w.lower()
        if k not in seen:
            seen.add(k)
            out.append(w)
    return out

if __name__ == '__main__':
    ws = build_with_phrases()
    print('词表总数:', len(ws))
    # 排除已有音频的词
    import base64
    have = set()
    for f in os.listdir('/tmp/fc/audio'):
        b = f.split('_')[0]
        try:
            s = b + '=' * (-len(b) % 4)
            have.add(base64.urlsafe_b64decode(s).decode().lower())
        except Exception:
            pass
    print('已有音频:', len(have))
    need = [w for w in ws if w.lower() not in have]
    print('待补:', len(need))
    json.dump(need, open('/tmp/need.json', 'w'), ensure_ascii=False)
    print('前30:', need[:30])
