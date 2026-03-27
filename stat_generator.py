"""
stat_generator.py
Generates stat-based Facebook posts for Filipino professionals in SG + PH.
Topics: salary vs net worth, SGD vs PHP, compounding math,
        health costs of demanding careers, income stream statistics.
Uses Gemini → 40+ hand-written fallback stats.
"""

import os
import hashlib
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

TOPICS = ["salary_networth", "sgd_php", "compounding", "health_cost", "income_streams"]

DAY_TOPICS = {
    1: "salary_networth",   # Tuesday
    3: "sgd_php",           # Thursday
    5: "compounding",       # Saturday
}

# Rotate through remaining topics on other days if run manually
TOPIC_CYCLE = ["salary_networth", "sgd_php", "compounding", "health_cost", "income_streams"]


STAT_PROMPT = """You are writing a Facebook stat post for Filipino professionals
— nurses, IT workers, engineers, architects — in Singapore and the Philippines.

Write a short, punchy post built around ONE surprising financial or health statistic.
Topic: {topic_description}

LANGUAGE RULES:
- Simple everyday English. Max 15 words per sentence.
- Write like you're texting a smart friend, not writing an article.
- Contractions always: "you're", "it's", "don't", "can't"
- NEVER use: leverage, optimise, empower, transformative, actionable, holistic, synergy
- Never start with "Did you know" or "Are you aware" — too generic
- Max 1 Filipino word if it fits naturally (e.g. "Kaya mo ito." or "Ano na?")
- No brand or company names

STRUCTURE:
- Line 1: The stat itself — one sharp sentence. No emoji here.
  Make it specific: use real numbers, percentages, or timeframes.
- Lines 2–3: Two short sentences putting it in context for a Filipino professional.
  Connect it to their actual life — their salary, career, or daily habits.
- Line 4: One honest, thought-provoking question or observation.
- Last line: Short CTA — "Does this surprise you? Comment below 👇"
  or "Save this and share it with someone who needs to see it."

Use 2 emojis max. Total post: under 120 words. Sound human, not AI.

Topic context: {topic_description}

Write ONLY the post. No preamble, no quotes."""


FALLBACK_STATS = {
    "salary_networth": [
        """8 out of 10 high-earning professionals retire with less than 3 months of savings.

A good salary feels like security. But without a plan, it's just a faster way to spend.
Most professionals in SG earn well — and still feel financially behind after 10 years.

The income was never the problem. The system around it was. 💡

Does this hit close to home? Drop a comment below 👇""",

        """The average Filipino professional in Singapore earns SGD 40,000–60,000 a year. Most save less than 5% of it.

That's SGD 2,000–3,000 saved in a year — while spending SGD 37,000–57,000.
One missed paycheck away from pressure. Even on a good salary.

Your salary is not your safety net. Your savings rate is. 📊

Does this surprise you? Comment below 👇""",

        """A nurse earning SGD 3,500/month who saves nothing will have zero net worth after 10 years — despite earning over SGD 420,000 total.

That's not a small amount. That's a house deposit. An investment portfolio. A business.
It went somewhere. Just not somewhere intentional.

Where does yours go? 💬

Save this. It's worth sitting with. 👇""",

        """Studies show that income above SGD 5,000/month stops correlating with happiness — but it keeps correlating with lifestyle inflation.

Most professionals don't get richer as they earn more. They just spend more.
The raises come. The savings don't follow.

Ano na? Is your lifestyle growing faster than your wealth? 📈

Drop your honest answer below 👇""",

        """The top 20% of earners in the Philippines save less than 8% of their income on average.

High earners. Low savers. It's more common than you think.
The gap isn't income — it's financial habits built before the salary arrived.

What percentage do you actually save? No judgment — just awareness. 💡

Comment your honest number below 👇""",

        """A professional who earns SGD 4,000/month for 20 years collects SGD 960,000 in gross income.

Most end up with less than SGD 100,000 to show for it.
The other SGD 860,000 built someone else's wealth — landlords, banks, brands.

It's not about earning more. It's about keeping more. 💸

Does this change how you see your salary? 👇""",

        """Research shows high-earning professionals are 40% more likely to experience lifestyle creep than average earners.

Every raise becomes a bigger apartment, a newer phone, a pricier lifestyle.
The gap between income and wealth stays exactly the same — just at a higher level.

Your next raise is coming. What will you do differently with it? 🎯

Comment below 👇""",

        """7 in 10 Filipino professionals say they feel financially behind despite having a stable job.

A stable income and financial security are two very different things.
One is what you earn. The other is what you keep, grow, and protect.

Which one do you actually have right now? 💬

Drop your letter: A) Stable income only  B) Both  C) Working on it 👇""",
    ],

    "sgd_php": [
        """SGD 500 invested monthly in SG for 10 years at 6% annual return = SGD 81,000.

The same SGD 500 sent to the Philippines as remittance = SGD 500 consumed.
One builds. One disappears. Both feel like love.

The question is — are you building anything for yourself too? 💡

Does this hit different? Comment below 👇""",

        """1 SGD = approximately 45 PHP today.

A Filipino professional in SG earning SGD 3,500/month earns the equivalent of PHP 157,500/month.
The average professional salary in the Philippines is PHP 30,000–50,000/month.

You're earning 3–5x more. Is your wealth growing 3–5x faster? 📊

Honest answer below 👇""",

        """If you invest SGD 300/month for 15 years at 7% return, you'll have SGD 93,000.

That's PHP 4.1 million — enough to buy property in most Philippine provinces outright.
Built slowly. From one decision made today.

How much do you currently invest monthly? 💬

Drop your answer below 👇""",

        """The cost of living in Singapore is 4x higher than in the Philippines.

But salaries in SG are often 5–8x higher than equivalent roles in PH.
That gap — the difference between the cost multiplier and the salary multiplier — is your wealth-building window.

Are you using that window? Or living at Singapore cost on a Singapore salary? 🎯

Comment below 👇""",

        """A Filipino professional who returns home after 10 years in SG with SGD 100,000 saved has PHP 4.5 million.

That's enough to start a small business, buy a property, or generate passive income of PHP 30,000/month.
Most return with far less — not because the salary wasn't enough, but because the plan wasn't there.

What's your return-home financial target? 💡

Drop it in the comments 👇""",

        """Sending SGD 1,000 home every month for 10 years = SGD 120,000 total sent.

Investing SGD 300 of that monthly instead = SGD 49,000 in savings after 10 years.
Both can happen at the same time. Most people never try.

You can support your family and build your own future. They're not opposites. ❤️

Save this and share it with someone who needs to see it 👇""",

        """The Philippine peso has lost 35% of its value against the SGD in the last 10 years.

Money kept in PHP savings loses purchasing power over time.
Professionals earning in SGD have an advantage — but only if they use it strategically.

Is your money working in the right currency? 📈

Comment below 👇""",

        """A nurse in SG earning SGD 3,800/month earns more in one month than the average Filipino nurse earns in 4 months.

That's not a small advantage. That's a generational wealth-building opportunity.
The question is whether it's being treated like one.

What are you doing with that advantage? 💬

Drop your honest answer below 👇""",
    ],

    "compounding": [
        """SGD 200 invested at age 25 becomes SGD 2,900 by age 65. The same SGD 200 invested at age 35 becomes only SGD 1,400.

One decade of delay costs you more than half the result.
The money doesn't change. The time does.

How old are you — and when did you start? 💡

Comment your answer below 👇""",

        """If you invest SGD 400/month starting at 30, you'll have SGD 480,000 by 60 at 7% return.

Wait until 40 to start the same habit? You get SGD 204,000.
SGD 276,000 difference — from a 10-year delay.

The best time to start was 10 years ago. The second best time is now. 📊

Does this change anything for you? Comment below 👇""",

        """Compounding doubles money roughly every 10 years at 7% return.

SGD 10,000 invested at 30 → SGD 20,000 at 40 → SGD 40,000 at 50 → SGD 80,000 at 60.
No extra contributions. No extra effort. Just time.

You can't buy time back. But you can start using what's left. 💬

How many doubling cycles do you have left? Comment below 👇""",

        """Warren Buffett made 97% of his wealth after age 65 — because of compounding.

Most professionals wait until they feel "ready" to invest.
By then, the most powerful years of compounding are already gone.

You don't need a lot of money. You need a lot of time — and you're spending it right now. ⏳

Save this. It's worth thinking about. 👇""",

        """At 7% annual return, money doubles every 10.2 years.

A Filipino professional who invests SGD 500/month from age 28 to 38 — then stops completely — still ends up with more at 65 than one who invests SGD 500/month from age 38 to 65.

10 years of early investing beats 27 years of late investing. 📈

Does this surprise you? Comment below 👇""",

        """The difference between 5% and 7% annual return on SGD 1,000/month over 30 years?

5% = SGD 832,000
7% = SGD 1,219,000

That SGD 387,000 difference came from just 2% more return — not from saving more.
This is why where you invest matters as much as how much you invest.

What return are your savings currently getting? 💡

Drop your answer below 👇""",

        """SGD 1 invested at birth, growing at 7% annually, becomes SGD 768 by age 100.

Money is patient. Humans are not.
Every year you wait to invest is a year that math is working against you instead of for you.

Kaya mo ito — but you have to start. 💬

What's stopping you right now? Be honest below 👇""",

        """If you save SGD 50/day — about the cost of lunch and one coffee in SG — that's SGD 18,250/year.

Invested at 7% for 20 years: SGD 798,000.
From lunch money. From daily small choices.

The math isn't complicated. The habits are the hard part. 🎯

What's one daily spend you could redirect? Comment below 👇""",
    ],

    "health_cost": [
        """Nurses who work more than 12-hour shifts regularly have a 37% higher risk of burnout-related illness.

Burnout costs the Singapore healthcare system SGD 2.4 billion a year.
But it costs the individual nurse far more — in health, in career longevity, in quality of life.

How are you protecting yourself from the system you're keeping running? 💬

Drop a comment below 👇""",

        """A professional who develops chronic stress-related illness before 50 spends an average of SGD 30,000–80,000 on treatment over their lifetime.

That's more than most professionals save in 5 years.
Prevention isn't just a health choice — it's a financial one.

When did you last have a full health check? 🏥

Comment below 👇""",

        """IT professionals sit an average of 9–11 hours per day.

Prolonged sitting is associated with a 34% higher risk of cardiovascular disease — regardless of exercise.
Your gym session after work helps. But it doesn't fully cancel 10 hours of sitting.

What does your movement look like on a normal workday? 💡

Drop your honest answer below 👇""",

        """Filipino nurses working abroad have a 2.4x higher rate of depression than the general population.

Isolation, shift work, and financial pressure compound over time.
High performance at work and poor mental health at home is not a sustainable combination.

How are you actually doing — not at work, but in life? 💬

No judgment. Just checking in. Drop a ❤️ below 👇""",

        """The average cost of a heart attack in Singapore is SGD 50,000–100,000.

The average cost of a gym membership, healthy food, and annual check-ups: SGD 3,000–5,000/year.
Prevention is 10–30x cheaper than treatment.

Where does health sit in your budget right now? 📊

Comment below 👇""",

        """Engineers and architects have some of the highest rates of occupational stress in Singapore — second only to healthcare workers.

Project deadlines, client pressure, long hours. Sound familiar?
The career is demanding. The body keeps the score.

What's one thing you do to decompress after a hard week? 💬

Share it below — your answer might help someone else 👇""",

        """Research shows that employees who sleep less than 6 hours per night are 4x more likely to get sick than those who sleep 7+ hours.

One sick day in Singapore costs an employer SGD 500–800 on average.
It costs you far more — in energy, focus, and long-term health.

How many hours did you sleep last night? 😴

Drop your number below 👇""",

        """Workers with poor financial health are 34% more likely to report physical health problems.

Financial stress and physical health are directly connected.
When you're worried about money, your body pays for it.

This is why financial literacy isn't just about money — it's about your health too. 💡

Save this and share it with someone who needs to hear it 👇""",
    ],

    "income_streams": [
        """People with 3 or more income streams are 4x less likely to experience financial stress — regardless of how much they earn.

It's not about earning more. It's about not depending on one source.
One job. One boss. One decision that isn't yours — and your income stops.

How many income streams do you currently have? 📊

Drop your number below 👇""",

        """The average millionaire has 7 income streams.

Not 7 businesses. Just 7 sources — salary, investments, rental, dividends, side income, royalties, interest.
Most professionals have exactly 1.

You don't need to build all 7 overnight. But which #2 are you building? 💡

Comment below 👇""",

        """A professional earning SGD 4,500/month from one job has a monthly income risk of 100%.

If that one job disappears — so does 100% of the income.
A second stream of SGD 500/month reduces that risk to 90%. A third reduces it further.

Every additional stream is financial insurance. 🎯

What's your current income risk percentage? Comment below 👇""",

        """Research from the US Federal Reserve shows that 40% of adults couldn't cover an unexpected SGD 550 expense without borrowing.

This cuts across income levels — high earners included.
One income + no emergency fund = financial fragility, no matter the salary.

Do you have 3–6 months of expenses saved? 💬

Drop your honest answer below 👇""",

        """Filipino professionals in Singapore who build a side income of SGD 500–1,000/month reduce their financial anxiety by 60%, according to community surveys.

Not because SGD 500 solves everything.
But because it proves you're not completely dependent on one source.

It changes how you think, not just what you earn. 💡

Are you building yours? Comment below 👇""",

        """Network marketing, freelancing, investments, online selling — Filipinos in Singapore are building second incomes in all of these.

The ones who succeed share one thing in common: they started before they felt ready.
Waiting for the perfect time costs you compounding time.

What's your reason for not starting yet? Be honest below 💬

Comment and let's talk about it 👇""",

        """A professional with 2 income streams earning SGD 500 combined extra per month invests that consistently for 15 years.

Result: SGD 155,000 at 6% return.
That SGD 500/month wasn't life-changing. But what it built over time was.

Small second income. Long time horizon. Big result. 📈

What would you do with an extra SGD 500/month? Comment below 👇""",

        """Studies show that starting a side income while employed is safer than quitting to start full time — 80% of successful entrepreneurs kept their day job initially.

You don't have to choose between security and ambition.
The best time to build something new is while you still have stability.

What's one skill you have that others would pay for? 💡

Share it below 👇""",
    ],
}


def get_topic_for_today() -> str:
    weekday = datetime.now().weekday()
    if weekday in DAY_TOPICS:
        return DAY_TOPICS[weekday]
    # Fallback for manual runs on other days
    week_num = datetime.now().isocalendar()[1]
    return TOPIC_CYCLE[week_num % len(TOPIC_CYCLE)]


def _topic_description(topic: str) -> str:
    descriptions = {
        "salary_networth": (
            "The gap between high salaries and low net worth — professionals who earn well "
            "but never build real wealth. Use specific numbers relevant to Singapore salaries "
            "(SGD 3,000–6,000/month range) and Filipino professional context."
        ),
        "sgd_php":         (
            "The financial advantage of earning in SGD vs spending/saving in PHP. "
            "Comparisons between SG salary levels and Philippine equivalents, "
            "or investment outcomes in SGD vs remittance behaviour."
        ),
        "compounding":     (
            "The math of compound interest and how time affects investment outcomes. "
            "Use specific numbers — monthly investment amounts, % returns, years. "
            "Relevant to professionals aged 25–45 in Singapore."
        ),
        "health_cost":     (
            "The financial and physical cost of demanding professional careers — nurses, "
            "IT workers, engineers. Burnout statistics, illness risk, prevention vs treatment costs. "
            "Real numbers from healthcare or occupational health research."
        ),
        "income_streams":  (
            "Statistics about single vs multiple income sources and financial resilience. "
            "How having 2–3 income streams changes financial stress levels, risk, and outcomes. "
            "Relevant to Filipino professionals considering side income in Singapore."
        ),
    }
    return descriptions.get(topic, descriptions["salary_networth"])


def _generate_via_gemini(topic: str) -> str | None:
    if not GEMINI_API_KEY:
        return None
    try:
        prompt = STAT_PROMPT.format(topic_description=_topic_description(topic))
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30,
        )
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        print(f"  ✅ Gemini generated stat for topic: {topic}")
        return text
    except Exception as e:
        print(f"  ⚠️  Gemini stat error: {e}")
        print(f"  ⚠️  Response: {resp.text[:200] if 'resp' in locals() else 'no response'}")
        return None


def _get_fallback_stat(topic: str) -> str:
    stats = FALLBACK_STATS.get(topic, FALLBACK_STATS["salary_networth"])
    seed  = datetime.now().strftime("%Y-%m-%d") + topic
    idx   = int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(stats)
    return stats[idx]


def generate_stat(topic: str = None) -> dict:
    if not topic:
        topic = get_topic_for_today()

    print(f"\n📊 Generating stat post for topic: {topic.upper()}")

    caption = _generate_via_gemini(topic)
    if not caption:
        print("  ⚠️  Using fallback stat library.")
        caption = _get_fallback_stat(topic)

    return {"topic": topic, "caption": caption}


if __name__ == "__main__":
    for topic in TOPICS:
        result = generate_stat(topic)
        print(f"\n{'='*60}")
        print(f"Topic: {result['topic'].upper()}")
        print(f"{'='*60}")
        print(result["caption"])
